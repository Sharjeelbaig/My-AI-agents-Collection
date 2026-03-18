from typing import Any, Dict, Optional
from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import DeleteRowsInput


def delete_rows_func(
    table: str,
    condition: str,
    condition_params: Optional[Dict[str, Any]] = None,
    confirm: bool = False,
) -> str:
    if not confirm:
        count_result = db_client.count_rows(table, condition, condition_params)
        if not count_result.get("success"):
            return f"Could not preview deletion: {count_result.get('message')}"
        count = count_result["count"]
        if count == 0:
            return f"No rows in '{table}' match the condition '{condition}'. Nothing to delete."
        return (
            f"You are about to delete {count} row(s) from '{table}'\n"
            f"  WHERE {condition}\n\n"
            "⚠️  This cannot be undone. Reply 'yes' to confirm."
        )

    result = db_client.delete_rows(table, condition, condition_params)
    if result.get("success"):
        return f"✅ {result.get('message')}"
    return f"❌ Delete failed: {result.get('message')}"


delete_rows = StructuredTool(
    name="delete_rows",
    func=lambda table, condition, condition_params=None, confirm=False: delete_rows_func(
        table, condition, condition_params, confirm
    ),
    description=(
        "Delete rows from a table that match a condition. "
        "ALWAYS call with confirm=false first — this shows how many rows will be deleted. "
        "Only call with confirm=true after the user explicitly confirms. "
        "Args: table, condition (SQL WHERE clause), condition_params (optional), confirm (default false)."
    ),
    args_schema=DeleteRowsInput,
)

__all__ = ["delete_rows"]
