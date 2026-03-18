from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from src.shared.jira_client import jira_client


class DeleteTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")


def delete_ticket_func(ticket_key: str) -> str:
    """Delete a Jira ticket by its key."""
    result = jira_client.delete_ticket(ticket_key)
    if result.get("success"):
        return result.get("message", "Ticket deleted successfully")
    return f"Failed to delete ticket: {result.get('message')}"


delete_ticket = StructuredTool(
    name="delete_ticket",
    func=delete_ticket_func,
    description=(
        "Delete a single Jira ticket by its key. "
        "Use this for deleting one ticket at a time. "
        "For deleting multiple tickets, use bulk_delete_tickets instead. "
        "Args: ticket_key (required, e.g., 'PROJ-123')"
    ),
    args_schema=DeleteTicketInput
)

__all__ = ["delete_ticket"]