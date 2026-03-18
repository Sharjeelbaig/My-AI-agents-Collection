from langchain_core.tools import StructuredTool
from typing import List, Optional
from src.shared.jira_client import jira_client
from src.features.agent.schemas import (
    BulkDeleteInput,
    BulkTransitionInput,
    DeleteByStatusInput,
)


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _do_bulk_delete(ticket_keys: List[str]) -> str:
    """Execute deletion for a list of ticket keys and return a summary."""
    if not ticket_keys:
        return "No tickets to delete."

    results: dict = {"deleted": [], "failed": []}
    for key in ticket_keys:
        result = jira_client.delete_ticket(key)
        if result.get("success"):
            results["deleted"].append(key)
        else:
            results["failed"].append(f"{key}: {result.get('message')}")

    lines = [f"✅ Deleted {len(results['deleted'])} ticket(s)."]
    if results["deleted"]:
        lines.append("  " + ", ".join(results["deleted"]))
    if results["failed"]:
        lines.append(f"❌ Failed to delete {len(results['failed'])} ticket(s):")
        for e in results["failed"]:
            lines.append(f"  {e}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# bulk_delete_tickets — delete an explicit list of keys
# ─────────────────────────────────────────────────────────

def bulk_delete_func(ticket_keys: List[str], confirm: bool = False) -> str:
    """Delete multiple Jira tickets at once."""
    if not ticket_keys:
        return "No ticket keys provided. Please specify which tickets to delete."

    if not confirm:
        return (
            f"You are about to delete {len(ticket_keys)} ticket(s):\n"
            f"{', '.join(ticket_keys)}\n\n"
            "⚠️  This cannot be undone. Reply 'yes' to confirm."
        )

    return _do_bulk_delete(ticket_keys)


bulk_delete_tickets = StructuredTool(
    name="bulk_delete_tickets",
    func=bulk_delete_func,
    description=(
        "Delete a specific list of tickets by their keys. "
        "First call with confirm=false to show what will be deleted, "
        "then call again with confirm=true once user says yes. "
        "Args: ticket_keys (required list of keys e.g. ['DEV-1','DEV-2']), confirm (bool)"
    ),
    args_schema=BulkDeleteInput,
)


# ─────────────────────────────────────────────────────────
# delete_tickets_by_status — fetch + delete by status in one step
# ─────────────────────────────────────────────────────────

def delete_by_status_func(status: Optional[str] = None, confirm: bool = False) -> str:
    """Fetch all tickets with a given status (or all tickets) and delete them."""
    ok, message = jira_client.ensure_project_selected()
    if not ok:
        return message

    # Fetch the matching tickets
    if status:
        tickets = jira_client.get_tickets_by_status(status)
        scope_label = f"with status '{status}'"
    else:
        tickets = jira_client.get_all_tickets()
        scope_label = "in the project (ALL tickets)"

    if not tickets:
        return f"No tickets found {scope_label}. Nothing to delete."

    keys = [t["key"] for t in tickets if t.get("key")]

    if not confirm:
        preview = "\n".join(
            f"  [{t.get('key')}] {t.get('summary', '')} — {t.get('status')}"
            for t in tickets[:20]
        )
        more = f"\n  ... and {len(tickets) - 20} more" if len(tickets) > 20 else ""
        return (
            f"Found {len(keys)} ticket(s) {scope_label}:\n"
            f"{preview}{more}\n\n"
            "⚠️  This cannot be undone. Reply 'yes' to confirm deletion."
        )

    return _do_bulk_delete(keys)


delete_tickets_by_status = StructuredTool(
    name="delete_tickets_by_status",
    func=delete_by_status_func,
    description=(
        "Delete all tickets matching a status, or ALL tickets if no status given. "
        "USE THIS instead of bulk_delete_tickets when user says things like: "
        "'empty the done list', 'delete all to do tickets', 'clear the project', 'empty whole project'. "
        "First call with confirm=false to preview what will be deleted, "
        "then call with confirm=true after user confirms. "
        "Args: status (optional, e.g. 'Done', 'To Do', 'In Progress'; omit for ALL), "
        "confirm (bool, default false)"
    ),
    args_schema=DeleteByStatusInput,
)


# ─────────────────────────────────────────────────────────
# bulk_transition_tickets — move all (or filtered) tickets to a new status
# ─────────────────────────────────────────────────────────

def bulk_transition_func(
    to_status: str,
    from_status: Optional[str] = None,
    confirm: bool = False
) -> str:
    """Transition multiple tickets to a new status in one operation."""
    ok, message = jira_client.ensure_project_selected()
    if not ok:
        return message

    if from_status:
        tickets = jira_client.get_tickets_by_status(from_status)
        scope_label = f"in '{from_status}'"
    else:
        tickets = jira_client.get_all_tickets()
        scope_label = "in the project"

    if not tickets:
        return f"No tickets found {scope_label}. Nothing to transition."

    transitionable = []
    skipped = 0
    for ticket in tickets:
        status = (ticket.get("status") or "").lower()
        if status == to_status.lower():
            skipped += 1
            continue
        transitionable.append(ticket)

    if not transitionable:
        return f"All tickets {scope_label} are already in '{to_status}'."

    if not confirm:
        preview = "\n".join(
            f"  [{t.get('key')}] {t.get('summary', '')} — {t.get('status')}"
            for t in transitionable[:20]
        )
        more = (
            f"\n  ... and {len(transitionable) - 20} more"
            if len(transitionable) > 20 else ""
        )
        skip_note = (
            f"\n\nSkipped {skipped} ticket(s) already in '{to_status}'."
            if skipped else ""
        )
        return (
            f"Found {len(transitionable)} ticket(s) to move to '{to_status}' {scope_label}:\n"
            f"{preview}{more}{skip_note}\n\n"
            "⚠️  This will change the current status. Reply 'yes' to confirm."
        )

    moved, failed = [], []
    for t in transitionable:
        key = t.get("key")
        if not key:
            continue
        result = jira_client.transition_ticket(key, to_status)
        if result.get("success"):
            moved.append(key)
        else:
            failed.append(f"{key}: {result.get('message')}")

    lines = []
    if moved:
        lines.append(f"✅ Moved {len(moved)} ticket(s) to '{to_status}':")
        lines.append("  " + ", ".join(moved))
    if failed:
        lines.append(f"❌ Failed to transition {len(failed)} ticket(s):")
        for e in failed:
            lines.append(f"  {e}")
    if skipped:
        lines.append(f"Skipped {skipped} ticket(s) already in '{to_status}'.")

    return "\n".join(lines)


bulk_transition_tickets = StructuredTool(
    name="bulk_transition_tickets",
    func=bulk_transition_func,
    description=(
        "Move multiple tickets to a new status. "
        "Always call with confirm=false first to preview, then call again with "
        "confirm=true once the user explicitly says yes. "
        "USE THIS instead of calling transition_ticket one-by-one when user says things like: "
        "'move all to do tickets to done', 'move everything in progress to done', "
        "'mark all tickets as complete'. "
        "Args: to_status (required, target status e.g. 'Done', 'In Progress', 'To Do'), "
        "from_status (optional filter — only move tickets currently in this status), "
        "confirm (bool, default false)"
    ),
    args_schema=BulkTransitionInput,
)


__all__ = ["bulk_delete_tickets", "delete_tickets_by_status", "bulk_transition_tickets"]
