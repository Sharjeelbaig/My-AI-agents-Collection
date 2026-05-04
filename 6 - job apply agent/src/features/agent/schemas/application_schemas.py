from typing import List, Optional
from pydantic import BaseModel, Field


class LoadProfileInput(BaseModel):
    profile_path: Optional[str] = Field(
        default=None,
        description="Path to a YAML profile file. Defaults to JOB_AGENT_PROFILE env var."
    )
    resume_pdf_path: Optional[str] = Field(
        default=None,
        description="Optional path to a resume PDF. Used to enrich the profile and as the upload payload."
    )


class SearchJobsInput(BaseModel):
    query: str = Field(description="Free-text search terms, e.g. 'senior frontend engineer'")
    boards: Optional[List[str]] = Field(
        default=None,
        description="Subset of boards to search. Defaults to all configured boards."
    )
    location: Optional[str] = Field(
        default=None,
        description="Optional location filter (case-insensitive substring match)."
    )
    limit: int = Field(default=25, description="Maximum number of listings to return")


class GetJobDetailsInput(BaseModel):
    board: str = Field(description="'greenhouse', 'lever', or 'ashby'")
    company: str = Field(description="Company slug as used by the board")
    job_id: str = Field(description="Board-specific job id")


class DiscoverFormInput(BaseModel):
    board: str = Field(description="'greenhouse', 'lever', or 'ashby'")
    company: str
    job_id: str


class MapFieldsInput(BaseModel):
    fields_json: str = Field(
        description="JSON-encoded list of FormField objects (output of discover_form)"
    )
    job_details_json: Optional[str] = Field(
        default=None,
        description="JSON-encoded JobDetails — used as context for free-text answers"
    )


class FillFormInput(BaseModel):
    board: str
    company: str
    job_id: str
    mapping_json: str = Field(
        description="JSON-encoded list of {field_id, value} pairs from map_fields"
    )


class SubmitInput(BaseModel):
    board: str
    company: str
    job_id: str
    confirm: bool = Field(
        default=False,
        description="Must be True to actually click submit. Otherwise behaves as dry-run."
    )


class ScoreMatchInput(BaseModel):
    job_details_json: str = Field(description="JSON-encoded JobDetails")
    threshold: float = Field(
        default=0.5,
        description="Score 0..1 above which the job is considered a match"
    )


class AnswerOpenQuestionInput(BaseModel):
    question: str = Field(description="The free-text question from the form")
    job_details_json: Optional[str] = Field(
        default=None,
        description="Optional JSON-encoded JobDetails for company / role context"
    )
    max_chars: int = Field(default=600)


class LogApplicationInput(BaseModel):
    board: str
    company: str
    job_id: str
    status: str = Field(description="'applied', 'dry_run', 'skipped', 'error'")
    notes: Optional[str] = None


class RunPipelineInput(BaseModel):
    query: str = Field(description="Search query, e.g. 'remote senior react engineer'")
    boards: Optional[List[str]] = None
    location: Optional[str] = None
    limit: int = Field(default=10, description="Max number of jobs to consider this run")
    submit: bool = Field(
        default=False,
        description="When False (default), runs in dry-run mode: forms are filled but not submitted."
    )
    match_threshold: float = Field(default=0.5)


__all__ = [
    "LoadProfileInput",
    "SearchJobsInput",
    "GetJobDetailsInput",
    "DiscoverFormInput",
    "MapFieldsInput",
    "FillFormInput",
    "SubmitInput",
    "ScoreMatchInput",
    "AnswerOpenQuestionInput",
    "LogApplicationInput",
    "RunPipelineInput",
]
