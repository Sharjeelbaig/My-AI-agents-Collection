from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import SearchTicketsInput


def search_tickets_func(query: str, status: str = None) -> str:
    """Search for Jira tickets matching a query."""
    ok, message = jira_client.ensure_project_selected()
    if not ok:
        return message

    safe_query = jira_client.escape_jql_value(query)
    jql_parts = [f'project = {jira_client.project_key}']

    jql_parts.append(f'(summary ~ "{safe_query}" OR description ~ "{safe_query}")')

    if status:
        jql_parts.append(f'status = "{jira_client.escape_jql_value(status)}"')

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
