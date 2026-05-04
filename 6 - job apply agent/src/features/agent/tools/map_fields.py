import json
from typing import Optional

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import MapFieldsInput
from src.features.agent.schemas.job_schemas import FormField
from src.shared import state
from src.shared.field_mapper import map_fields as _map_fields, to_dict


def map_fields_func(fields_json: str, job_details_json: Optional[str] = None) -> str:
    """Deterministically map form fields to profile values.

    No LLM call happens here. The result has two sections:

    *filled* — fields ready to fill (alias / boolean / work-auth / etc.)
    *needs_llm* — fields that need answer_open_question before fill.

    Returns a JSON object with both lists plus the simple field_id -> value
    dict that ``fill_form`` consumes.
    """
    profile = state.get_profile()
    raw = json.loads(fields_json)
    fields = [FormField.model_validate(f) for f in raw]
    filled, needs_llm = _map_fields(fields, profile)
    return json.dumps(
        {
            "filled": [d.__dict__ for d in filled],
            "needs_llm": [d.__dict__ for d in needs_llm],
            "values_by_field_id": to_dict(filled),
        },
        indent=2,
        ensure_ascii=False,
    )


map_fields = StructuredTool(
    name="map_fields",
    func=map_fields_func,
    description=(
        "Map a discovered form's fields to profile values using a deterministic "
        "alias table. NO LLM call is made here. "
        "Args: fields_json (output of discover_form), "
        "job_details_json (optional, used by free-text fallback). "
        "Returns JSON with filled, needs_llm, and values_by_field_id."
    ),
    args_schema=MapFieldsInput,
)


__all__ = ["map_fields"]
