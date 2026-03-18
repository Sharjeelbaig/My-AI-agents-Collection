from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class RunQueryInput(BaseModel):
    sql: str = Field(description="A valid SELECT (or WITH…SELECT) SQL query to execute.")


class DescribeTableInput(BaseModel):
    table_name: str = Field(description="Name of the table to describe.")


class InsertRowInput(BaseModel):
    table: str = Field(description="Name of the table to insert into.")
    values: Dict[str, Any] = Field(
        description="Column-to-value mapping for the new row, e.g. {\"name\": \"Alice\", \"age\": 30}."
    )


class UpdateRowsInput(BaseModel):
    table: str = Field(description="Name of the table to update.")
    updates: Dict[str, Any] = Field(
        description="Column-to-new-value mapping, e.g. {\"status\": \"shipped\"}."
    )
    condition: str = Field(
        description=(
            "SQL WHERE clause (without the WHERE keyword) that identifies the rows to update, "
            "e.g. \"id = :row_id\" or \"status = 'pending'\"."
        )
    )
    condition_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Named bind parameters for the condition, e.g. {\"row_id\": 42}. "
            "Use this instead of interpolating values directly into the condition."
        ),
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the update.",
    )


class DeleteRowsInput(BaseModel):
    table: str = Field(description="Name of the table to delete from.")
    condition: str = Field(
        description=(
            "SQL WHERE clause (without the WHERE keyword) that identifies rows to delete, "
            "e.g. \"active = false\" or \"id = :row_id\"."
        )
    )
    condition_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Named bind parameters for the condition, e.g. {\"row_id\": 99}.",
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after the user explicitly confirms the deletion.",
    )


class ExportResultsInput(BaseModel):
    sql: str = Field(description="A SELECT query whose results will be exported to a CSV file.")
    filename: Optional[str] = Field(
        default=None,
        description="Optional filename for the exported CSV (without the .csv extension).",
    )


class NoInput(BaseModel):
    """Schema for tools that take no arguments."""
    pass


__all__ = [
    "RunQueryInput",
    "DescribeTableInput",
    "InsertRowInput",
    "UpdateRowsInput",
    "DeleteRowsInput",
    "ExportResultsInput",
    "NoInput",
]
