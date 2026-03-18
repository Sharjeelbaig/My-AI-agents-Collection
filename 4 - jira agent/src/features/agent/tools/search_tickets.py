from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
from src.shared.jira_client import jira_client


class SearchTicketsInput(BaseModel):
    query: str = Field(
        description="Search keywords or ticket title/description to find matching tickets"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status (e.g., 'To Do', 'In Progress', 'Done', 'Blocked')"
    )


def search_tickets_func(query: str, status: str = None) -> str:
    """Search for Jira tickets matching a query."""
    jql_parts = [f'project = {jira_client.project_key}']

    jql_parts.append(f'(summary ~ "{query}" OR description ~ "{query}")')

    if status:
        jql_parts.append(f'status = "{status}"')

    jql = " AND ".join(jql_parts)
    tickets = jira_client.search_tickets(jql)

    if not tickets:
        return f"No tickets found matching '{query}'"

    lines = [f"Found {len(tickets)} tickets matching '{query}':\n"]
    for ticket in tickets:
        lines.append(f"[{ticket['key']}] {ticket['summary']}")
        lines.append(f"  Status: {ticket['status']} | Assignee: {ticket['assignee']}\n")

    return "\n".join(lines)


search_tickets = StructuredTool(
    name="search_tickets",
    func=search_tickets_func,
    description=(
        "Search for Jira tickets by keywords, title, or description. "
        "Use this when you need to find ticket keys from partial names or descriptions. "
        "Args: query (required), status (optional filter)"
    ),
    args_schema=SearchTicketsInput
)

__all__ = ["search_tickets"]