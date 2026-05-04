"""Greenhouse adapter.

Uses Greenhouse's public board API for listing/details and Playwright for
form discovery + submission.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from src.features.agent.schemas.job_schemas import (
    FormField,
    FormFieldOption,
    JobDetails,
    JobListing,
)

from .base import BoardAdapter


_API_LIST = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
_API_DETAIL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}?questions=true"
# Modern Greenhouse hosted boards live on job-boards.greenhouse.io and render
# the application form inline on the description page itself.
_APPLY_URL = (
    "https://job-boards.greenhouse.io/{company}/jobs/{job_id}?gh_jid={job_id}"
)


class GreenhouseAdapter(BoardAdapter):
    name = "greenhouse"
    env_var = "GREENHOUSE_BOARDS"

    def list_jobs(self, company: str) -> List[JobListing]:
        url = _API_LIST.format(company=company)
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return []
        data = r.json()
        out: List[JobListing] = []
        for j in data.get("jobs", []):
            out.append(
                JobListing(
                    board=self.name,
                    company=company,
                    job_id=str(j.get("id", "")),
                    title=j.get("title", ""),
                    location=(j.get("location") or {}).get("name", ""),
                    url=j.get("absolute_url", ""),
                    department=", ".join(
                        d.get("name", "") for d in j.get("departments") or []
                    ),
                    employment_type="",
                )
            )
        return out

    def get_details(self, company: str, job_id: str) -> JobDetails:
        url = _API_DETAIL.format(company=company, job_id=job_id)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        j = r.json()
        listing = JobListing(
            board=self.name,
            company=company,
            job_id=str(job_id),
            title=j.get("title", ""),
            location=(j.get("location") or {}).get("name", ""),
            url=j.get("absolute_url", ""),
            department=", ".join(
                d.get("name", "") for d in j.get("departments") or []
            ),
        )
        # The API returns description as HTML — strip tags for the LLM context.
        desc_html = j.get("content", "") or ""
        from bs4 import BeautifulSoup

        desc_text = BeautifulSoup(desc_html, "lxml").get_text("\n").strip()
        # Prefer the absolute_url returned by the API — it is the canonical
        # apply URL for this job and survives any future hosted-board moves.
        apply_url = j.get("absolute_url") or _APPLY_URL.format(
            company=company, job_id=job_id
        )
        return JobDetails(
            listing=listing,
            description=desc_text,
            requirements="",
            apply_url=apply_url,
        )

    # ------------------------------------------------------------------
    # Form discovery + submission via the Greenhouse-hosted form API.
    # ------------------------------------------------------------------
    _KIND_BY_TYPE = {
        "input_text": "text",
        "input_email": "email",
        "input_url": "url",
        "input_phone": "phone",
        "textarea": "textarea",
        "select": "select",
        "multi_value_single_select": "select",
        "multi_value_multi_select": "multi_select",
        "input_file": "file",
        "checkbox": "checkbox",
    }

    def _kind_for_field(self, f: dict) -> str:
        return self._KIND_BY_TYPE.get((f.get("type") or "").lower(), "text")

    @staticmethod
    def _fill_combobox(target, el, value: str) -> None:
        """Open a React Select combobox, type a value, click the listbox match.

        Greenhouse's hosted form renders single-select questions as a custom
        ARIA combobox (``<input role="combobox" class="select__input">``)
        rather than a native ``<select>``. Playwright's ``select_option`` does
        not work on these — we have to drive them like a user.
        """
        el.click()
        el.fill("")
        el.type(value, delay=20)
        # Wait briefly for filtered options to appear, then click the first
        # listbox option whose visible text matches the typed value.
        try:
            option = target.get_by_role("option", name=value, exact=False).first
            option.wait_for(state="visible", timeout=3_000)
            option.click()
        except Exception:
            # Fallback: press Enter to accept the highlighted option.
            el.press("Enter")

    def discover_form(self, company: str, job_id: str) -> List[FormField]:
        url = _API_DETAIL.format(company=company, job_id=job_id)
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return []
        questions = r.json().get("questions") or []
        out: List[FormField] = []
        for q in questions:
            label = q.get("label", "").strip()
            if not label:
                continue
            fields = q.get("fields") or []
            if not fields:
                continue
            # Greenhouse exposes some questions (Resume/CV, Cover Letter) as
            # *both* a file input and a textarea companion. Resume gets the
            # file path uploaded via the dedicated file-upload step, but for
            # cover letters the user typically only has text — prefer the
            # textarea variant in that case so the deterministic mapper can
            # fill it.
            label_lc = label.lower()
            f0 = fields[0]
            if (
                len(fields) > 1
                and (f0.get("type") or "").lower() == "input_file"
                and "resume" not in label_lc
                and "cv" not in label_lc
            ):
                textarea_alt = next(
                    (
                        f
                        for f in fields[1:]
                        if (f.get("type") or "").lower() == "textarea"
                    ),
                    None,
                )
                if textarea_alt is not None:
                    f0 = textarea_alt
            field_id = f0.get("name") or f0.get("id") or label
            options = [
                FormFieldOption(label=str(v.get("label", v)), value=str(v.get("value", v)))
                for v in (f0.get("values") or [])
            ]
            out.append(
                FormField(
                    field_id=str(field_id),
                    label=label,
                    kind=self._kind_for_field(f0),
                    required=bool(q.get("required")),
                    options=options,
                    # Modern Greenhouse hosted boards address fields by id;
                    # legacy embedded forms by name. Try both.
                    raw_selector=(
                        f"[id='{field_id}'], [name='{field_id}']"
                    ),
                )
            )
        return out

    def fill_and_submit(
        self,
        company: str,
        job_id: str,
        values_by_field_id: dict,
        resume_path: Optional[str],
        confirm: bool,
        headless: bool = True,
        apply_url: Optional[str] = None,
    ) -> dict:
        from src.shared.browser import browser_page

        url = apply_url or _APPLY_URL.format(company=company, job_id=job_id)
        with browser_page(headless=headless) as page:
            # SPAs never reach "networkidle" reliably — wait for the DOM
            # then explicitly wait for a known form input to appear.
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            try:
                page.wait_for_selector(
                    "#first_name, [name='first_name']", timeout=15_000
                )
            except Exception:
                pass

            # Modern hosted boards render inline. Legacy embeds use an iframe.
            target = page
            try:
                iframe = page.frame_locator("iframe[id='grnhse_iframe']")
                iframe.locator("#first_name, [name='first_name']").first.wait_for(
                    state="attached", timeout=2_000
                )
                target = iframe
            except Exception:
                target = page

            for field_id, value in values_by_field_id.items():
                if value in (None, ""):
                    continue
                # Try id selector first (modern), then name (legacy).
                selector = f"[id='{field_id}'], [name='{field_id}']"
                try:
                    el = target.locator(selector).first
                    info = el.evaluate(
                        "e => ({tag: e.tagName.toLowerCase(),"
                        " type: (e.type||'').toLowerCase(),"
                        " role: e.getAttribute('role')||''})"
                    )
                    tag, typ, role = info["tag"], info["type"], info["role"]

                    if tag == "select":
                        el.select_option(label=str(value))
                    elif role == "combobox" or (
                        tag == "input" and typ == "text"
                        and el.evaluate("e => e.classList.contains('select__input')")
                    ):
                        # React Select / custom combobox: click to open, type
                        # to filter, then click the matching listbox option.
                        self._fill_combobox(target, el, str(value))
                    elif tag == "input" and typ == "file":
                        # Skip — file inputs are populated by the dedicated
                        # upload block below.
                        continue
                    elif tag in ("textarea", "input"):
                        el.fill(str(value))
                    else:
                        el.click()
                except Exception:
                    continue

            # Resume upload — modern Greenhouse exposes a hidden
            # <input type="file" id="resume"> that the visible "Attach" button
            # delegates to. Setting input files directly bypasses the button.
            if resume_path:
                for sel in (
                    "input[type='file']#resume",
                    "input[type='file'][id*='resume' i]",
                    "input[type='file'][name*='resume' i]",
                ):
                    try:
                        target.locator(sel).first.set_input_files(resume_path)
                        break
                    except Exception:
                        continue

            if not confirm:
                return {
                    "success": True,
                    "submitted": False,
                    "message": "Dry-run: form filled but submit was not clicked.",
                    "final_url": page.url,
                }

            try:
                target.locator("button[type='submit']").first.click()
                page.wait_for_load_state("networkidle", timeout=15_000)
                return {
                    "success": True,
                    "submitted": True,
                    "message": "Submitted.",
                    "final_url": page.url,
                }
            except Exception as e:
                return {
                    "success": False,
                    "submitted": False,
                    "message": f"Submit failed: {e}",
                    "final_url": page.url,
                }


__all__ = ["GreenhouseAdapter"]
