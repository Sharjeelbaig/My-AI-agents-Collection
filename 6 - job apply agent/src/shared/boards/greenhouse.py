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
_APPLY_URL = "https://boards.greenhouse.io/{company}/jobs/{job_id}#app"


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
        return JobDetails(
            listing=listing,
            description=desc_text,
            requirements="",
            apply_url=_APPLY_URL.format(company=company, job_id=job_id),
        )

    # ------------------------------------------------------------------
    # Form discovery + submission via the Greenhouse-hosted form API.
    # ------------------------------------------------------------------
    def _question_kind(self, q: dict) -> str:
        fields = q.get("fields") or []
        if not fields:
            return "text"
        f = fields[0]
        t = (f.get("type") or "").lower()
        mapping = {
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
        return mapping.get(t, "text")

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
            f0 = fields[0]
            field_id = f0.get("name") or f0.get("id") or label
            options = [
                FormFieldOption(label=str(v.get("label", v)), value=str(v.get("value", v)))
                for v in (f0.get("values") or [])
            ]
            out.append(
                FormField(
                    field_id=str(field_id),
                    label=label,
                    kind=self._question_kind(q),
                    required=bool(q.get("required")),
                    options=options,
                    raw_selector=f"[name='{field_id}']",
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
    ) -> dict:
        from src.shared.browser import browser_page

        url = _APPLY_URL.format(company=company, job_id=job_id)
        with browser_page(headless=headless) as page:
            page.goto(url, wait_until="networkidle")
            iframe = None
            try:
                iframe = page.frame_locator("iframe[id='grnhse_iframe']")
                # Probe the iframe is present.
                iframe.locator("body").first.wait_for(state="attached", timeout=5_000)
                target = iframe
            except Exception:
                target = page  # form may be inlined

            for field_id, value in values_by_field_id.items():
                if value in (None, ""):
                    continue
                selector = f"[name='{field_id}']"
                try:
                    el = target.locator(selector).first
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    if tag == "select":
                        el.select_option(label=str(value))
                    elif tag == "textarea" or tag == "input":
                        el.fill(str(value))
                    else:
                        el.click()
                except Exception:
                    continue

            # Resume upload
            if resume_path:
                try:
                    target.locator("input[type='file'][name*='resume' i]").first.set_input_files(
                        resume_path
                    )
                except Exception:
                    pass

            if not confirm:
                return {
                    "success": True,
                    "submitted": False,
                    "message": "Dry-run: form filled but submit was not clicked.",
                }

            try:
                target.locator("button[type='submit']").first.click()
                page.wait_for_load_state("networkidle", timeout=15_000)
                return {"success": True, "submitted": True, "message": "Submitted."}
            except Exception as e:
                return {"success": False, "submitted": False, "message": f"Submit failed: {e}"}


__all__ = ["GreenhouseAdapter"]
