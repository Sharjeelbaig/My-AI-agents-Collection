from pydantic import BaseModel, Field
from typing import Optional, List


class SearchTicketsInput(BaseModel):
    query: str = Field(
        description="Search keywords or ticket title/description to find matching tickets"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status (e.g., 'To Do', 'In Progress', 'Done', 'Blocked')"
    )


class BulkDeleteInput(BaseModel):
    ticket_keys: List[str] = Field(
        description="List of ticket keys to delete (e.g., ['PROJ-1', 'PROJ-2'])"
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after user confirms the deletion"
    )


class AddCommentInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")
    comment: str = Field(description="Comment text to add to the ticket")


class GetCommentsInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")


class DeleteByStatusInput(BaseModel):
    status: Optional[str] = Field(
        default=None,
        description=(
            "Status of tickets to delete: 'Done', 'To Do', 'In Progress', etc. "
            "Leave empty to delete all tickets in the current project."
        )
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the deletion"
    )


class BulkTransitionInput(BaseModel):
    from_status: Optional[str] = Field(
        default=None,
        description=(
            "Only transition tickets currently in this status. "
            "Leave empty to transition all tickets in the current project."
        )
    )
    to_status: str = Field(
        description="Target status to move tickets to (e.g., 'Done', 'In Progress', 'To Do')"
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the transition"
    )


class OperationResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


__all__ = [
    "SearchTicketsInput",
    "BulkDeleteInput",
    "AddCommentInput",
    "GetCommentsInput",
    "DeleteByStatusInput",
    "BulkTransitionInput",
    "OperationResult",
]
