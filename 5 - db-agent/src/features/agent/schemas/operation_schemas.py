from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class QueryResult(BaseModel):
    success: bool
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
    row_count: int = 0
    message: Optional[str] = None


class WriteResult(BaseModel):
    success: bool
    affected_rows: int = 0
    message: str = ""


class TableInfo(BaseModel):
    table: str
    columns: List[Dict[str, Any]] = []
    primary_keys: List[str] = []
    foreign_keys: List[Dict[str, Any]] = []


__all__ = ["QueryResult", "WriteResult", "TableInfo"]
