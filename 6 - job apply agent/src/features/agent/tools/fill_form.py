import json

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import FillFormInput, SubmitInput
from src.shared import state
from src.shared.boards import ADAPTERS


def fill_form_func(board: str, company: str, job_id: str, mapping_json: str) -> str:
    """Open the application page in a headless browser and fill every field.

    Does NOT click submit — that's the responsibility of submit_application.
    """
    adapter = ADAPTERS.get(board)
    if not adapter:
        return f"Unknown board: {board}"

    profile = state.get_profile()
    mapping = json.loads(mapping_json)
    if isinstance(mapping, dict) and "values_by_field_id" in mapping:
        values = mapping["values_by_field_id"]
    elif isinstance(mapping, dict):
        values = mapping
    else:
        return "mapping_json must be a JSON object."

    result = adapter.fill_and_submit(
        company=company,
        job_id=job_id,
        values_by_field_id=values,
        resume_path=profile.resume_path,
        confirm=False,
        headless=True,
    )
    return json.dumps(result)


def submit_application_func(
    board: str, company: str, job_id: str, confirm: bool = False
) -> str:
    """Submit a previously-filled application. Set confirm=True to actually click submit.

    NOTE: this re-opens the form to fill it once more (browsers don't persist
    state across runs). When confirm=False this is equivalent to fill_form.
    """
    adapter = ADAPTERS.get(board)
    if not adapter:
        return f"Unknown board: {board}"
    profile = state.get_profile()
    # Re-discover and re-map to keep the API simple — the user already saw
    # the dry-run output, so this is a deterministic re-fill.
    fields = adapter.discover_form(company, job_id)
    from src.shared.field_mapper import map_fields as _map_fields, to_dict

    filled, _ = _map_fields(fields, profile)
    values = to_dict(filled)
    result = adapter.fill_and_submit(
        company=company,
        job_id=job_id,
        values_by_field_id=values,
        resume_path=profile.resume_path,
        confirm=bool(confirm),
        headless=True,
    )
    return json.dumps(result)


fill_form = StructuredTool(
    name="fill_form",
    func=fill_form_func,
    description=(
        "Open the application form in a headless browser and fill every field "
        "from a mapping. Does not submit. "
        "Args: board, company, job_id, mapping_json."
    ),
    args_schema=FillFormInput,
)


submit_application = StructuredTool(
    name="submit_application",
    func=submit_application_func,
    description=(
        "Submit a job application. Pass confirm=True to actually click submit. "
        "When confirm is False, this is a dry-run that fills the form only. "
        "Args: board, company, job_id, confirm (default False)."
    ),
    args_schema=SubmitInput,
)


__all__ = ["fill_form", "submit_application"]
