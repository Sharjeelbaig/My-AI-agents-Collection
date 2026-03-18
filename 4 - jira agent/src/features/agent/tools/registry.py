from .create_ticket import create_ticket
from .assign_ticket import assign_ticket
from .delete_ticket import delete_ticket
from .get_ticket import get_ticket
from .get_tickets import get_in_progress, get_done, get_all_tickets
from .search_tickets import search_tickets
from .bulk_operations import bulk_delete_tickets, delete_tickets_by_status, bulk_transition_tickets
from .comment_tools import add_comment, get_comments
from .transition_ticket import transition_ticket
from .project_summary import get_project_summary

__all__ = [
    "create_ticket",
    "assign_ticket",
    "delete_ticket",
    "get_ticket",
    "get_in_progress",
    "get_done",
    "get_all_tickets",
    "search_tickets",
    "bulk_delete_tickets",
    "delete_tickets_by_status",
    "bulk_transition_tickets",
    "add_comment",
    "get_comments",
    "transition_ticket",
    "get_project_summary",
]

tools = [
    get_project_summary,           # first — used for summary/count queries
    delete_tickets_by_status,      # before bulk_delete so LLM prefers it for status-based deletes
    bulk_transition_tickets,       # before transition_ticket for bulk moves
    create_ticket,
    assign_ticket,
    delete_ticket,
    get_ticket,
    get_in_progress,
    get_done,
    get_all_tickets,
    search_tickets,
    bulk_delete_tickets,
    add_comment,
    get_comments,
    transition_ticket,
]

tool_names = [t.name for t in tools]
