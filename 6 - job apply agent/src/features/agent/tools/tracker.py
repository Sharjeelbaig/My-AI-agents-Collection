import json
from typing import Optional

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import LogApplicationInput
from src.shared import tracker_db


def log_application_func(
    board: str, company: str, job_id: str, status: str, notes: Optional[str] = None
) -> str:
    """Insert or update an entry in the SQLite application tracker."""
    tracker_db.upsert(
        board=board, company=company, job_id=job_id, status=status, notes=notes
    )
    return f"Recorded {board}:{company}:{job_id} as '{status}'."


def list_applications_func() -> str:
    """List the 50 most recent applications recorded by the tracker."""
    rows = tracker_db.list_recent(limit=50)
    return json.dumps(rows, indent=2, ensure_ascii=False)


log_application = StructuredTool(
    name="log_application",
    func=log_application_func,
    description=(
        "Record the result of an application attempt in the SQLite tracker. "
        "Args: board, company, job_id, status ('applied'|'dry_run'|'skipped'|'error'), notes (optional)."
    ),
    args_schema=LogApplicationInput,
)


list_applications = StructuredTool.from_function(
    func=list_applications_func,
    name="list_applications",
    description="List the most recent application records from the tracker. No args.",
)


__all__ = ["log_application", "list_applications"]
