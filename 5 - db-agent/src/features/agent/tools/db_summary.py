from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import NoInput


def get_db_summary_func() -> str:
    tables = db_client.list_tables()
    if not tables:
        return "The database appears to be empty — no tables found."

    counts = db_client.get_row_counts()
    total_rows = sum(counts.values())

    lines = [f"Database Summary — {len(tables)} table(s), {total_rows} total row(s)\n"]
    for table in sorted(tables):
        row_count = counts.get(table, 0)
        lines.append(f"  {table:<30} {row_count:>8} row(s)")

    return "\n".join(lines)


get_db_summary = StructuredTool(
    name="get_db_summary",
    func=get_db_summary_func,
    description=(
        "Show a high-level overview of the database: all tables and their row counts. "
        "Use for: 'summarize the database', 'how many rows in each table?', "
        "'give me an overview of the data'."
    ),
    args_schema=NoInput,
)

__all__ = ["get_db_summary"]
