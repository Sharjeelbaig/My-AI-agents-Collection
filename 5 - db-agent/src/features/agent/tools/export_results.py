import os
from typing import Optional
from langchain_core.tools import StructuredTool
from src.shared.db_client import db_client
from src.features.agent.schemas import ExportResultsInput


EXPORT_DIR = os.getenv("EXPORT_DIR", "./exports")


def export_results_func(sql: str, filename: Optional[str] = None) -> str:
    result = db_client.export_to_csv(sql)
    if not result.get("success"):
        return f"Export failed: {result.get('message')}"

    os.makedirs(EXPORT_DIR, exist_ok=True)
    safe_name = (filename or "export").replace(" ", "_").replace("/", "_")
    filepath = os.path.join(EXPORT_DIR, f"{safe_name}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        f.write(result["csv"])

    return (
        f"✅ Exported {result['row_count']} row(s) to '{filepath}'.\n"
        f"Columns: {', '.join(result['columns'])}"
    )


export_results = StructuredTool(
    name="export_results",
    func=lambda sql, filename=None: export_results_func(sql, filename),
    description=(
        "Run a SELECT query and save the results as a CSV file in the exports directory. "
        "Args: sql (required SELECT query), filename (optional, without .csv extension). "
        "Use when the user says 'export to CSV', 'download results', or 'save this query'."
    ),
    args_schema=ExportResultsInput,
)

__all__ = ["export_results"]
