import json
from typing import List, Optional

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import SearchJobsInput
from src.shared.boards import ADAPTERS


def search_jobs_func(
    query: str,
    boards: Optional[List[str]] = None,
    location: Optional[str] = None,
    limit: int = 25,
) -> str:
    """Search Greenhouse / Lever / Ashby for jobs matching ``query``.

    Returns a JSON-encoded list of JobListing objects. Companies are taken
    from the per-board env-var configuration (GREENHOUSE_BOARDS, etc).
    """
    selected = boards or list(ADAPTERS.keys())
    results = []
    per_board_limit = max(1, limit // max(len(selected), 1))
    for name in selected:
        adapter = ADAPTERS.get(name)
        if not adapter:
            continue
        listings = adapter.search(
            query=query, location=location, limit=per_board_limit
        )
        results.extend(listings)
        if len(results) >= limit:
            break
    return json.dumps(
        [j.model_dump() for j in results[:limit]], indent=2, ensure_ascii=False
    )


search_jobs = StructuredTool(
    name="search_jobs",
    func=search_jobs_func,
    description=(
        "Search Greenhouse / Lever / Ashby boards for matching jobs. "
        "Args: query (required free-text), boards (optional list), "
        "location (optional substring filter), limit (default 25). "
        "Returns a JSON list of jobs."
    ),
    args_schema=SearchJobsInput,
)


__all__ = ["search_jobs"]
