from typing import List, Optional
from pydantic import BaseModel, Field


class JobListing(BaseModel):
    """A search-result entry returned by a board adapter."""

    board: str = Field(description="Board name: 'greenhouse', 'lever', 'ashby'")
    company: str = Field(description="Company slug or display name")
    job_id: str = Field(description="Board-specific job id")
    title: str
    location: str = ""
    url: str
    department: str = ""
    employment_type: str = ""

    def stable_key(self) -> str:
        return f"{self.board}:{self.company}:{self.job_id}"


class JobDetails(BaseModel):
    """Full description of a single job, including the application URL."""

    listing: JobListing
    description: str = ""
    requirements: str = ""
    apply_url: str = ""


class FormFieldOption(BaseModel):
    """A single option for select / radio / checkbox fields."""

    label: str
    value: str = ""


FIELD_KINDS = {"text", "email", "phone", "url", "textarea", "select",
               "multi_select", "radio", "checkbox", "file", "date", "number",
               "boolean", "unknown"}


class FormField(BaseModel):
    """A normalised representation of one application-form field.

    Board adapters emit these so the downstream mapper / filler can be agnostic
    about Greenhouse/Lever/Ashby/etc. specifics.
    """

    field_id: str = Field(description="Stable selector for fill_form to target")
    label: str = Field(description="Human-readable label, after normalisation")
    kind: str = "text"
    required: bool = False
    options: List[FormFieldOption] = Field(default_factory=list)
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    raw_selector: Optional[str] = None


__all__ = ["JobListing", "JobDetails", "FormField", "FormFieldOption", "FIELD_KINDS"]
