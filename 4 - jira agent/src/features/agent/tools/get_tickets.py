from typing import List, Dict, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from src.shared.jira_client import jira_client


class NoInput(BaseModel):
    """Schema for tools that don't require any input."""
    pass


def _format_tickets(tickets: List[Dict[str, Any]], label: str = "") -> str:
    """Format a list of tickets for display."""
    if not tickets:
        return f"No tickets found{' for ' + label if label else ''}."

    header = f"Found {len(tickets)} ticket(s){' — ' + label if label else ''}:\n"
    lines = [header]
    for ticket in tickets:
        key = ticket.get("key") or "???"
        summary = ticket.get("summary") or "(no summary)"
        status = ticket.get("status") or "Unknown"
        priority = ticket.get("priority") or "—"
        assignee = ticket.get("assignee") or "Unassigned"
        itype = ticket.get("issue_type") or "Task"
        lines.append(f"- [{key}] {summary}")
        lines.append(
            f"  Type: {itype} | Status: {status} | "
            f"Priority: {priority} | Assignee: {assignee}"
        )
    return "\n".join(lines)



def get_in_progress_func(**kwargs) -> str:
    """Get all tickets that are in progress."""
    tickets = jira_client.get_in_progress_tickets()
    return _format_tickets(tickets)


def get_done_func(**kwargs) -> str:
    """Get all tickets that are done."""
    tickets = jira_client.get_done_tickets()
    return _format_tickets(tickets)


def get_all_tickets_func(**kwargs) -> str:
    """Get all tickets in the current project."""
    tickets = jira_client.get_all_tickets()
    return _format_tickets(tickets)


get_in_progress = StructuredTool(
    name="get_in_progress",
    func=get_in_progress_func,
    description="Get all tickets currently in progress. No args required.",
    args_schema=NoInput
)

get_done = StructuredTool(
    name="get_done",
    func=get_done_func,
    description="Get all tickets that are done. No args required.",
    args_schema=NoInput
)

get_all_tickets = StructuredTool(
    name="get_all_tickets",
    func=get_all_tickets_func,
    description="Get all tickets in the current project. No args required.",
    args_schema=NoInput
)

__all__ = ["get_in_progress", "get_done", "get_all_tickets"]