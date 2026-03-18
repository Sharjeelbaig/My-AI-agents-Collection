from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import AssignTicketInput


def assign_ticket_func(ticket_key: str, assignee_name: str) -> str:
    """Assign a Jira ticket to an exact matching Jira user."""
    result = jira_client.assign_ticket(ticket_key, assignee_name)
    if result.get("success"):
        return result.get("message", f"Ticket {ticket_key} assigned to {assignee_name}")
    return f"Failed to assign ticket: {result.get('message')}"


assign_ticket = StructuredTool(
    name="assign_ticket",
    func=assign_ticket_func,
    description=(
        "Assign a Jira ticket to a user by exact Jira display name. "
        "Use this when the user says things like 'assign PROJ-123 to Sharjeel Baig'. "
        "Args: ticket_key (required), assignee_name (required exact display name)"
    ),
    args_schema=AssignTicketInput,
)

__all__ = ["assign_ticket"]
