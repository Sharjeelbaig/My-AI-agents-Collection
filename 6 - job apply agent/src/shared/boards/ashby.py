"""AshbyHQ adapter.

Ashby exposes a public job-board API:
    https://api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true

Form discovery happens via:
    https://api.ashbyhq.com/posting-api/job-board/{company}/{job_id}/application-form
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


_API_LIST = "https://api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true"
_APPLY_URL = "https://jobs.ashbyhq.com/{company}/{job_id}/application"
_PUBLIC_URL = "https://jobs.ashbyhq.com/{company}/{job_id}"


_TYPE_MAP = {
    "ShortText": "text",
    "LongText": "textarea",
    "Email": "email",
    "Phone": "phone",
    "Url": "url",
    "Boolean": "boolean",
    "Date": "date",
    "Number": "number",
    "File": "file",
    "ValueSelect": "select",
    "MultiValueSelect": "multi_select",
}


class AshbyAdapter(BoardAdapter):
    name = "ashby"
    env_var = "ASHBY_BOARDS"

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
                    location=j.get("locationName", ""),
                    url=j.get("jobUrl") or _PUBLIC_URL.format(company=company, job_id=j.get("id")),
                    department=j.get("departmentName", ""),
                    employment_type=j.get("employmentType", ""),
                )
            )
        return out

    def get_details(self, company: str, job_id: str) -> JobDetails:
        listings = self.list_jobs(company)
        match = next((j for j in listings if j.job_id == str(job_id)), None)
        if not match:
            raise ValueError(f"Ashby job {job_id} not found at {company}")

        # Description is in the listing API as descriptionHtml on a per-job endpoint.
        url = f"https://api.ashbyhq.com/posting-api/job-board/{company}/{job_id}"
        description = ""
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                body = r.json()
                from bs4 import BeautifulSoup

                description = BeautifulSoup(
                    body.get("descriptionHtml", ""), "lxml"
                ).get_text("\n").strip()
        except Exception:
            pass

        return JobDetails(
            listing=match,
            description=description,
            apply_url=_APPLY_URL.format(company=company, job_id=job_id),
        )

    def discover_form(self, company: str, job_id: str) -> List[FormField]:
        url = (
            f"https://api.ashbyhq.com/posting-api/job-board/{company}/"
            f"{job_id}/application-form"
        )
        try:
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception:
            return []

        out: List[FormField] = []
        for q in data.get("formDefinition", {}).get("fields", []):
            t = q.get("type") or q.get("fieldType") or "ShortText"
            kind = _TYPE_MAP.get(t, "text")
            options = [
                FormFieldOption(label=opt.get("label", ""), value=opt.get("value", ""))
                for opt in (q.get("selectableValues") or [])
            ]
            out.append(
                FormField(
                    field_id=str(q.get("path") or q.get("id") or q.get("name") or q.get("title")),
                    label=q.get("title") or q.get("label") or "",
                    kind=kind,
                    required=bool(q.get("isRequired")),
                    options=options,
                    raw_selector=None,
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
            for field_id, value in values_by_field_id.items():
                if value in (None, ""):
                    continue
                # Ashby's React form labels its inputs with aria-label = the question title.
                try:
                    el = page.get_by_label(field_id, exact=False).first
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    if tag == "select":
                        el.select_option(label=str(value))
                    else:
                        el.fill(str(value))
                except Exception:
                    continue

            if resume_path:
                try:
                    page.locator("input[type='file']").first.set_input_files(
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
                page.get_by_role("button", name="Submit").first.click()
                page.wait_for_load_state("networkidle", timeout=15_000)
                return {"success": True, "submitted": True, "message": "Submitted."}
            except Exception as e:
                return {"success": False, "submitted": False, "message": f"Submit failed: {e}"}


__all__ = ["AshbyAdapter"]
