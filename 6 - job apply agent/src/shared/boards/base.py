"""Common interface every ATS adapter implements.

Adapters are pure deterministic Python: HTTP + HTML parsing + Playwright. No
LLM calls happen here — they live in src/shared/llm.py and are invoked from
the tools layer for narrow decisions only.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List, Optional

from src.features.agent.schemas.job_schemas import (
    FormField,
    JobDetails,
    JobListing,
)


class BoardAdapter(ABC):
    """Base class for Greenhouse / Lever / Ashby adapters."""

    name: str = ""
    env_var: str = ""

    def configured_companies(self) -> List[str]:
        raw = os.getenv(self.env_var, "")
        return [c.strip() for c in raw.split(",") if c.strip()]

    @abstractmethod
    def list_jobs(self, company: str) -> List[JobListing]:
        """Return every open job at this company on this board."""

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 25,
        companies: Optional[List[str]] = None,
    ) -> List[JobListing]:
        """Search across configured companies for matching jobs.

        Filtering is deterministic substring matching against the title and
        location — exactly what a reasonable user would do without an LLM.
        """
        companies = companies if companies is not None else self.configured_companies()
        results: List[JobListing] = []
        q = (query or "").lower().strip()
        loc = (location or "").lower().strip()

        for company in companies:
            try:
                listings = self.list_jobs(company)
            except Exception:
                continue
            for j in listings:
                if q and q not in j.title.lower() and q not in j.department.lower():
                    continue
                if loc and loc not in j.location.lower():
                    continue
                results.append(j)
                if len(results) >= limit:
                    return results
        return results

    @abstractmethod
    def get_details(self, company: str, job_id: str) -> JobDetails:
        """Fetch full job description for a single posting."""

    @abstractmethod
    def discover_form(self, company: str, job_id: str) -> List[FormField]:
        """Return the application form's fields, normalised."""

    @abstractmethod
    def fill_and_submit(
        self,
        company: str,
        job_id: str,
        values_by_field_id: dict,
        resume_path: Optional[str],
        confirm: bool,
        headless: bool = True,
    ) -> dict:
        """Fill the form. Click submit only when confirm=True.

        Returns a dict like {"success": bool, "message": str, "submitted": bool}.
        """


__all__ = ["BoardAdapter"]
