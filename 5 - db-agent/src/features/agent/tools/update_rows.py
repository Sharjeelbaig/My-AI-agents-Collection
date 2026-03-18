from typing import Any, Dict, Optional
from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import UpdateRowsInput


def update_rows_func(
    table: str,
    updates: Dict[str, Any],
    condition: str,
    condition_params: Optional[Dict[str, Any]] = None,
    confirm: bool = False,
) -> str:
    if not confirm:
        count_result = db_client.count_rows(table, condition, condition_params)
        if not count_result.get("success"):
            return f"Could not preview update: {count_result.get('message')}"
        count = count_result["count"]
        if count == 0:
            return f"No rows in '{table}' match the condition '{condition}'. Nothing to update."
        changes = ", ".join(f"{k} = {v!r}" for k, v in updates.items())
        return (
            f"You are about to update {count} row(s) in '{table}':\n"
            f"  SET {changes}\n"
            f"  WHERE {condition}\n\n"
            "⚠️  Reply 'yes' to confirm."
        )

    result = db_client.update_rows(table, updates, condition, condition_params)
    if result.get("success"):
        return f"✅ {result.get('message')}"
    return f"❌ Update failed: {result.get('message')}"


update_rows = StructuredTool(
    name="update_rows",
    func=lambda table, updates, condition, condition_params=None, confirm=False: update_rows_func(
        table, updates, condition, condition_params, confirm
    ),
    description=(
        "Update rows in a table that match a condition. "
        "ALWAYS call with confirm=false first to preview how many rows will change, "
        "then call again with confirm=true after the user confirms. "
        "Args: table, updates (dict of col→value), condition (SQL WHERE clause), "
        "condition_params (optional bind params), confirm (default false)."
    ),
    args_schema=UpdateRowsInput,
)

__all__ = ["update_rows"]
