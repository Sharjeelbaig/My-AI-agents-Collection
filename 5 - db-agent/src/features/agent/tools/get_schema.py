from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import NoInput


def get_schema_func() -> str:
    """Return the full schema for all tables in the database."""
    result = db_client.get_schema()
    if not result.get("success"):
        return f"Failed to retrieve schema: {result.get('message')}"

    schema = result["data"]
    if not schema:
        return "No tables found in the database."

    lines = [f"Database Schema ({len(schema)} table(s)):\n"]
    for table_name, table_data in schema.items():
        pks = table_data.get("primary_keys", [])
        lines.append(f"┌─ {table_name}  (PK: {', '.join(pks) if pks else 'none'})")
        for col in table_data["columns"]:
            nullable = "" if col["nullable"] else "  NOT NULL"
            lines.append(f"│   {col['name']}  {col['type']}{nullable}")
        lines.append("│")

    return "\n".join(lines)


get_schema = StructuredTool(
    name="get_schema",
    func=get_schema_func,
    description=(
        "Return the full schema for every table in the database — columns, types, and keys. "
        "Use when the user wants a complete overview, "
        "or before writing a complex multi-table query."
    ),
    args_schema=NoInput,
)

__all__ = ["get_schema"]
