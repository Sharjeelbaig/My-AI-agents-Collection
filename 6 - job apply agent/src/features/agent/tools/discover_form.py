import json

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import DiscoverFormInput
from src.shared.boards import ADAPTERS


def discover_form_func(board: str, company: str, job_id: str) -> str:
    """Return the application form's fields for a specific job posting.

    Output is a JSON list of FormField objects. Used as input to map_fields.
    """
    adapter = ADAPTERS.get(board)
    if not adapter:
        return f"Unknown board: {board}"
    fields = adapter.discover_form(company, job_id)
    return json.dumps([f.model_dump() for f in fields], indent=2, ensure_ascii=False)


discover_form = StructuredTool(
    name="discover_form",
    func=discover_form_func,
    description=(
        "Discover the fields of a specific job's application form. "
        "Args: board, company, job_id. Returns a JSON list of FormField objects."
    ),
    args_schema=DiscoverFormInput,
)


__all__ = ["discover_form"]
