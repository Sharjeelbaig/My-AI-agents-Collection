from .answer_open_question import answer_open_question
from .discover_form import discover_form
from .fill_form import fill_form, submit_application
from .get_job_details import get_job_details
from .load_profile import load_profile
from .map_fields import map_fields
from .run_pipeline import run_pipeline
from .score_match import score_match
from .search_jobs import search_jobs
from .tracker import list_applications, log_application

__all__ = [
    "load_profile",
    "search_jobs",
    "get_job_details",
    "discover_form",
    "map_fields",
    "score_match",
    "answer_open_question",
    "fill_form",
    "submit_application",
    "log_application",
    "list_applications",
    "run_pipeline",
]

# Order matters: the most common entry points come first so the LLM picks them.
tools = [
    load_profile,
    run_pipeline,
    search_jobs,
    get_job_details,
    discover_form,
    map_fields,
    score_match,
    answer_open_question,
    fill_form,
    submit_application,
    log_application,
    list_applications,
]

tool_names = [t.name for t in tools]
