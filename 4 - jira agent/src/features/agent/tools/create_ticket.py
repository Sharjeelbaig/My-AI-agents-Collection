from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import CreateTicketInput


def create_ticket_func(
    summary: str,
    description: str = "",
    priority: str = "Medium",
    issue_type: str = "Task"
) -> str:
    """Create a new Jira ticket."""
    result = jira_client.create_ticket(summary, description, priority, issue_type)
    if result.get("success"):
        return result.get("message", "Ticket created successfully")
    return f"Failed to create ticket: {result.get('message')}"


create_ticket = StructuredTool(
    name="create_ticket",
    func=create_ticket_func,
    description=(
        "Create a new Jira ticket in the current project. "
        "Args: summary (required), description (optional), "
        "priority (default: Medium — options: Low, Medium, High, Highest), "
        "issue_type (default: Task). "
        "Unsupported issue types auto-fall back to Task."
    ),
    args_schema=CreateTicketInput
)

__all__ = ["create_ticket"]
