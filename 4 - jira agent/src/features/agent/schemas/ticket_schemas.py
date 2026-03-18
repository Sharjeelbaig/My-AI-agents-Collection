from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TicketStatus(str, Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BLOCKED = "Blocked"


class Ticket(BaseModel):
    key: str
    summary: str
    description: Optional[str] = None
    status: str
    assignee: Optional[str] = None
    priority: Optional[str] = None


class TicketList(BaseModel):
    tickets: list[Ticket]
    total: int


class CreateTicketInput(BaseModel):
    summary: str = Field(description="Summary/title of the ticket")
    description: Optional[str] = Field(
        default="",
        description="Detailed description of the ticket"
    )
    priority: Optional[str] = Field(
        default="Medium",
        description="Priority level (Low, Medium, High, Highest)"
    )
    issue_type: Optional[str] = Field(
        default="Task",
        description="Type of issue (Task, Bug, Story, Epic)"
    )


class DeleteTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the deletion"
    )


class GetTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")


class NoInput(BaseModel):
    """Schema for tools that don't require any input."""
    pass


class TransitionTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")
    transition_name: str = Field(
        description="Target status name (e.g., 'In Progress', 'Done', 'To Do')"
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the transition"
    )


class AssignTicketInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key (e.g., 'PROJ-123')")
    assignee_name: str = Field(
        description="Exact Jira display name to assign the ticket to (e.g., 'Sharjeel Baig')"
    )


__all__ = [
    "TicketStatus",
    "Ticket",
    "TicketList",
    "CreateTicketInput",
    "DeleteTicketInput",
    "GetTicketInput",
    "NoInput",
    "TransitionTicketInput",
    "AssignTicketInput",
]
