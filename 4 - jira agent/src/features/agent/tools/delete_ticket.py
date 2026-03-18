from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import DeleteTicketInput


def delete_ticket_func(ticket_key: str, confirm: bool = False) -> str:
    """Delete a Jira ticket by its key."""
    if not confirm:
        return (
            "You are about to delete 1 ticket(s):\n"
            f"{ticket_key}\n\n"
            "⚠️  This cannot be undone. Reply 'yes' to confirm."
        )

    result = jira_client.delete_ticket(ticket_key)
    if result.get("success"):
        return f"✅ Deleted 1 ticket(s).\n  {ticket_key}"
    return (
        "❌ Failed to delete 1 ticket(s):\n"
        f"  {ticket_key}: {result.get('message')}"
    )


delete_ticket = StructuredTool(
    name="delete_ticket",
    func=delete_ticket_func,
    description=(
        "Delete a single Jira ticket by its key. "
        "Always call with confirm=false first to preview, then call again with "
        "confirm=true once the user explicitly says yes. "
        "For deleting multiple tickets, use bulk_delete_tickets instead. "
        "Args: ticket_key (required, e.g., 'PROJ-123'), confirm (bool)"
    ),
    args_schema=DeleteTicketInput
)

__all__ = ["delete_ticket"]
