from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import NoInput


def list_tables_func() -> str:
    """List all tables available in the database."""
    tables = db_client.list_tables()
    if not tables:
        return "No tables found in the database (or database is empty)."
    lines = [f"Found {len(tables)} table(s):\n"]
    for table in sorted(tables):
        lines.append(f"  - {table}")
    return "\n".join(lines)


list_tables = StructuredTool(
    name="list_tables",
    func=list_tables_func,
    description=(
        "List all tables in the connected database. "
        "Use this when the user asks 'what tables do I have?', "
        "'show me the database', or before describing a table."
    ),
    args_schema=NoInput,
)

__all__ = ["list_tables"]
