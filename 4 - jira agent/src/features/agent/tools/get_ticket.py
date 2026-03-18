from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import GetTicketInput


def get_ticket_func(ticket_key: str) -> str:
    """Get details of a specific Jira ticket."""
    result = jira_client.get_ticket(ticket_key)
    if result.get("success"):
        data = result.get("data", {})
        return f"""
Ticket: {data.get('key')}
Summary: {data.get('summary')}
Status: {data.get('status')}
Priority: {data.get('priority')}
Assignee: {data.get('assignee')}
Description: {data.get('description') or 'No description'}
"""
    return f"Failed to get ticket: {result.get('message')}"


get_ticket = StructuredTool(
    name="get_ticket",
    func=get_ticket_func,
    description=(
        "Get detailed information about a specific Jira ticket. "
        "Args: ticket_key (required, e.g., 'PROJ-123')"
    ),
    args_schema=GetTicketInput
)

__all__ = ["get_ticket"]
