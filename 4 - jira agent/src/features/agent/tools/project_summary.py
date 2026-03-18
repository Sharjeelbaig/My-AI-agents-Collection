from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from src.shared.jira_client import jira_client


class NoInput(BaseModel):
    """Schema for tools that don't require any input."""
    pass


def get_project_summary_func(**kwargs) -> str:
    """Get a full summary of the project: ticket counts by status, done vs remaining."""
    summary = jira_client.get_project_summary()

    if summary["total"] == 0:
        return "No tickets found in the current project."

    lines = [
        f"📊 **Project Summary — {jira_client.project_key}**\n",
        f"Total tickets : {summary['total']}",
        f"Done          : {summary['done']}",
        f"Remaining     : {summary['remaining']}",
        "",
        "Status Breakdown:",
    ]
    for status, count in sorted(summary["by_status"].items()):
        bar = "█" * min(count, 20)
        lines.append(f"  {status:<18} {bar} ({count})")

    lines.append("\nAll Tickets:")
    for t in summary["tickets"]:
        lines.append(
            f"  [{t.get('key')}] {t.get('summary', '')[:60]}"
            f"  |  {t.get('status')}  |  {t.get('priority')}"
        )

    return "\n".join(lines)


get_project_summary = StructuredTool(
    name="get_project_summary",
    func=get_project_summary_func,
    description=(
        "Get a complete summary of the current project: total tickets, "
        "how many are Done vs remaining, and a status breakdown. "
        "Use this for questions like 'what's going on?', 'how many tickets are done?', "
        "'summarize the project', 'how many are left?'. No args required."
    ),
    args_schema=NoInput,
)

__all__ = ["get_project_summary"]
