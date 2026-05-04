from langchain_core.tools import StructuredTool

from src.features.agent.schemas import GetJobDetailsInput
from src.shared.boards import ADAPTERS


def get_job_details_func(board: str, company: str, job_id: str) -> str:
    """Return the full description + apply URL for a specific job posting."""
    adapter = ADAPTERS.get(board)
    if not adapter:
        return f"Unknown board: {board}"
    details = adapter.get_details(company, job_id)
    return details.model_dump_json(indent=2)


get_job_details = StructuredTool(
    name="get_job_details",
    func=get_job_details_func,
    description=(
        "Fetch the full description + apply URL for one job. "
        "Args: board, company, job_id."
    ),
    args_schema=GetJobDetailsInput,
)


__all__ = ["get_job_details"]
