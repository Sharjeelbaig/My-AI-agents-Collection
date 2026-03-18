from langchain_core.tools import StructuredTool
from src.shared.jira_client import jira_client
from src.features.agent.schemas import AddCommentInput, GetCommentsInput


def add_comment_func(ticket_key: str, comment: str) -> str:
    """Add a comment to a Jira ticket."""
    result = jira_client.add_comment(ticket_key, comment)
    if result.get("success"):
        return result.get("message", "Comment added successfully")
    return f"Failed to add comment: {result.get('message')}"


def get_comments_func(ticket_key: str) -> str:
    """Get all comments for a Jira ticket."""
    comments = jira_client.get_comments(ticket_key)
    if not comments:
        return f"No comments found for {ticket_key}."

    lines = [f"Comments on {ticket_key}:"]
    for comment in comments:
        lines.append(
            f"- {comment.get('author')} ({comment.get('created')}): "
            f"{comment.get('body')}"
        )
    return "\n".join(lines)


add_comment = StructuredTool(
    name="add_comment",
    func=add_comment_func,
    description=(
        "Add a comment to a Jira ticket. "
        "Args: ticket_key (required), comment (required)"
    ),
    args_schema=AddCommentInput
)

get_comments = StructuredTool(
    name="get_comments",
    func=get_comments_func,
    description=(
        "Get all comments for a Jira ticket. "
        "Args: ticket_key (required, e.g., 'PROJ-123')"
    ),
    args_schema=GetCommentsInput
)

__all__ = ["add_comment", "get_comments"]
