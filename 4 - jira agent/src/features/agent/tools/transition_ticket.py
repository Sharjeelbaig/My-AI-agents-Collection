from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from src.shared.jira_client import jira_client


class TransitionTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")
    transition_name: str = Field(
        description="Target status name (e.g., 'In Progress', 'Done', 'To Do', 'Blocked')"
    )


def transition_ticket_func(ticket_key: str, transition_name: str) -> str:
    """Transition a ticket to a new status."""
    result = jira_client.transition_ticket(ticket_key, transition_name)
    if result.get("success"):
        return result.get("message", "Ticket transitioned successfully")
    return f"Failed to transition ticket: {result.get('message')}"


transition_ticket = StructuredTool(
    name="transition_ticket",
    func=transition_ticket_func,
    description=(
        "Move a ticket to a different status. "
        "Common transitions: 'In Progress', 'Done', 'To Do', 'Blocked'. "
        "Args: ticket_key (required), transition_name (required)"
    ),
    args_schema=TransitionTicketInput
)

__all__ = ["transition_ticket"]