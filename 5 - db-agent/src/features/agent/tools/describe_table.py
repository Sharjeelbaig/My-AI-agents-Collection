from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import DescribeTableInput


def describe_table_func(table_name: str) -> str:
    """Describe the columns and constraints of a table."""
    result = db_client.describe_table(table_name)
    if not result.get("success"):
        return f"Failed to describe table '{table_name}': {result.get('message')}"

    data = result["data"]
    lines = [f"Table: {data['table']}\n"]

    pks = data.get("primary_keys", [])
    lines.append(f"Primary Key(s): {', '.join(pks) if pks else 'none'}\n")

    lines.append("Columns:")
    for col in data["columns"]:
        nullable = "NULL" if col["nullable"] else "NOT NULL"
        default = f"  default={col['default']}" if col["default"] else ""
        lines.append(f"  {col['name']}  {col['type']}  {nullable}{default}")

    fks = data.get("foreign_keys", [])
    if fks:
        lines.append("\nForeign Keys:")
        for fk in fks:
            lines.append(f"  {fk['column']} → {fk['references']}")

    return "\n".join(lines)


describe_table = StructuredTool(
    name="describe_table",
    func=lambda table_name: describe_table_func(table_name),
    description=(
        "Show the column names, data types, nullability, and key constraints for a table. "
        "Use this when the user asks 'what columns does X have?', "
        "'describe the orders table', or before building an INSERT/UPDATE."
    ),
    args_schema=DescribeTableInput,
)

__all__ = ["describe_table"]
