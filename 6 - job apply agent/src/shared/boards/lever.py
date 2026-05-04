"""Lever adapter.

Lever's postings API is JSON and well-documented:
    https://api.lever.co/v0/postings/{company}?mode=json

Application forms have predictable HTML field names: ``name``, ``email``,
``phone``, ``org``, ``urls[LinkedIn]`` etc.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from src.features.agent.schemas.job_schemas import (
    FormField,
    JobDetails,
    JobListing,
)

from .base import BoardAdapter


_API_LIST = "https://api.lever.co/v0/postings/{company}?mode=json"
_APPLY_URL = "https://jobs.lever.co/{company}/{job_id}/apply"


# Lever forms always include this baseline. Custom questions are scraped at
# discover-time from the live page.
_LEVER_BASELINE_FIELDS: List[dict] = [
    {"field_id": "name", "label": "Full name", "kind": "text", "required": True},
    {"field_id": "email", "label": "Email", "kind": "email", "required": True},
    {"field_id": "phone", "label": "Phone", "kind": "phone", "required": False},
    {"field_id": "org", "label": "Current company", "kind": "text", "required": False},
    {"field_id": "urls[LinkedIn]", "label": "LinkedIn URL", "kind": "url", "required": False},
    {"field_id": "urls[GitHub]", "label": "GitHub URL", "kind": "url", "required": False},
    {"field_id": "urls[Portfolio]", "label": "Portfolio", "kind": "url", "required": False},
    {"field_id": "urls[Other]", "label": "Other website", "kind": "url", "required": False},
    {"field_id": "comments", "label": "Cover letter", "kind": "textarea", "required": False},
    {"field_id": "resume", "label": "Resume", "kind": "file", "required": True},
]


class LeverAdapter(BoardAdapter):
    name = "lever"
    env_var = "LEVER_BOARDS"

    def list_jobs(self, company: str) -> List[JobListing]:
        url = _API_LIST.format(company=company)
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return []
        out: List[JobListing] = []
        for j in r.json():
            categories = j.get("categories") or {}
            out.append(
                JobListing(
                    board=self.name,
                    company=company,
                    job_id=str(j.get("id", "")),
                    title=j.get("text", ""),
                    location=categories.get("location", ""),
                    url=j.get("hostedUrl", ""),
                    department=categories.get("team", ""),
                    employment_type=categories.get("commitment", ""),
                )
            )
        return out

    def get_details(self, company: str, job_id: str) -> JobDetails:
        # Lever doesn't have a single-job API; refetch the list and pick.
        listings = self.list_jobs(company)
        match = next((j for j in listings if j.job_id == str(job_id)), None)
        if not match:
            raise ValueError(f"Lever job {job_id} not found at {company}")

        # Pull the description page for full text.
        page = requests.get(match.url, timeout=20)
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(page.text, "lxml")
        desc = soup.select_one(".section-wrapper.page-full-width")
        description = desc.get_text("\n").strip() if desc else ""
        return JobDetails(
            listing=match,
            description=description,
            requirements="",
            apply_url=_APPLY_URL.format(company=company, job_id=job_id),
        )

    def discover_form(self, company: str, job_id: str) -> List[FormField]:
        out: List[FormField] = []
        for f in _LEVER_BASELINE_FIELDS:
            out.append(
                FormField(
                    field_id=f["field_id"],
                    label=f["label"],
                    kind=f["kind"],
                    required=f["required"],
                    raw_selector=f"[name='{f['field_id']}']",
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
                selector = f"[name='{field_id}']"
                try:
                    el = page.locator(selector).first
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    type_ = (
                        el.evaluate("e => e.getAttribute('type') || ''") or ""
                    ).lower()
                    if tag == "select":
                        el.select_option(label=str(value))
                    elif type_ == "file":
                        el.set_input_files(str(value))
                    else:
                        el.fill(str(value))
                except Exception:
                    continue

            if resume_path:
                try:
                    page.locator("input[name='resume']").first.set_input_files(
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
                page.locator("button[type='submit']").first.click()
                page.wait_for_load_state("networkidle", timeout=15_000)
                return {"success": True, "submitted": True, "message": "Submitted."}
            except Exception as e:
                return {"success": False, "submitted": False, "message": f"Submit failed: {e}"}


__all__ = ["LeverAdapter"]
