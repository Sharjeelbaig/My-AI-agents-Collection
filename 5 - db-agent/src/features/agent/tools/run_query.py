from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import RunQueryInput


def run_query_func(sql: str) -> str:
    result = db_client.run_query(sql)
    if not result.get("success"):
        return f"Query failed: {result.get('message')}"
    rows = result["data"]
    if not rows:
        return "Query returned no rows."
    columns = result["columns"]
    col_widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            col_widths[col] = max(col_widths[col], len(str(row.get(col, ""))))
    header = "  ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "  ".join("-" * col_widths[col] for col in columns)
    lines = [header, separator]
    for row in rows:
        lines.append("  ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in columns))
    lines.append(f"\n({result['row_count']} row(s))")
    return "\n".join(lines)


run_query = StructuredTool(
    name="run_query",
    func=lambda sql: run_query_func(sql),
    description=(
        "Execute a read-only SELECT query and return the results as a formatted table. "
        "Only SELECT and WITH…SELECT statements are permitted. "
        "Use for: 'show me all users', 'how many orders are pending', 'find products where stock < 10'."
    ),
    args_schema=RunQueryInput,
)

__all__ = ["run_query"]
