from typing import Any, Dict
from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import InsertRowInput


def insert_row_func(table: str, values: Dict[str, Any]) -> str:
    result = db_client.insert_row(table, values)
    if result.get("success"):
        return result.get("message", f"Row inserted into '{table}'.")
    return f"Failed to insert row: {result.get('message')}"


insert_row = StructuredTool(
    name="insert_row",
    func=lambda table, values: insert_row_func(table, values),
    description=(
        "Insert a single new row into a table. "
        "Args: table (required), values (required) — a dict of column→value pairs. "
        "Use describe_table first if you are unsure of the column names or types."
    ),
    args_schema=InsertRowInput,
)

__all__ = ["insert_row"]
