from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import TransitionTicketInput


def transition_ticket_func(
    ticket_key: str,
    transition_name: str,
    confirm: bool = False
) -> str:
    """Transition a ticket to a new status."""
    if not confirm:
        return (
            f"You are about to move 1 ticket(s) to '{transition_name}':\n"
            f"{ticket_key}\n\n"
            "⚠️  This will change the current status. Reply 'yes' to confirm."
        )

    result = jira_client.transition_ticket(ticket_key, transition_name)
    if result.get("success"):
        return f"✅ Moved 1 ticket(s) to '{transition_name}':\n  {ticket_key}"
    return (
        "❌ Failed to transition 1 ticket(s):\n"
        f"  {ticket_key}: {result.get('message')}"
    )


transition_ticket = StructuredTool(
    name="transition_ticket",
    func=transition_ticket_func,
    description=(
        "Move a ticket to a different status. "
        "Always call with confirm=false first to preview, then call again with "
        "confirm=true once the user explicitly says yes. "
        "Common transitions: 'In Progress', 'Done', 'To Do', 'Blocked'. "
        "Args: ticket_key (required), transition_name (required), confirm (bool)"
    ),
    args_schema=TransitionTicketInput
)

__all__ = ["transition_ticket"]
