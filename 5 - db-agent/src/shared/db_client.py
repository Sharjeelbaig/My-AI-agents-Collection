import os
import csv
import io
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


class DBClient:
    """SQLAlchemy-backed database client for the DB agent."""

    def __init__(self):
        self.db_url = os.getenv("DB_URL", "sqlite:///./database.db")
        self._engine = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.db_url)
        return self._engine

    def is_configured(self) -> bool:
        """Return True if a DB URL is set."""
        return bool(self.db_url)

    def ensure_configured(self) -> Tuple[bool, str]:
        if self.is_configured():
            return True, ""
        return False, "No database URL configured. Set DB_URL in your .env file."

    def test_connection(self) -> Tuple[bool, str]:
        """Verify the database is reachable."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connected successfully."
        except SQLAlchemyError as exc:
            return False, f"Connection failed: {exc}"

    # ------------------------------------------------------------------
    # Schema inspection
    # ------------------------------------------------------------------

    def list_tables(self) -> List[str]:
        """Return all table names in the database."""
        ok, _ = self.ensure_configured()
        if not ok:
            return []
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except SQLAlchemyError as exc:
            print(f"[DBClient] list_tables error: {exc}")
            return []

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Return column definitions and primary-key info for a table."""
        ok, msg = self.ensure_configured()
        if not ok:
            return {"success": False, "message": msg}
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            pk = inspector.get_pk_constraint(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            return {
                "success": True,
                "data": {
                    "table": table_name,
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col.get("nullable", True),
                            "default": str(col.get("default", "")),
                        }
                        for col in columns
                    ],
                    "primary_keys": pk.get("constrained_columns", []),
                    "foreign_keys": [
                        {
                            "column": fk["constrained_columns"],
                            "references": f"{fk['referred_table']}.{fk['referred_columns']}",
                        }
                        for fk in foreign_keys
                    ],
                },
            }
        except SQLAlchemyError as exc:
            return {"success": False, "message": f"Error describing table '{table_name}': {exc}"}

    def get_schema(self) -> Dict[str, Any]:
        """Return a full schema dump for every table in the database."""
        tables = self.list_tables()
        if not tables:
            return {"success": True, "data": {}}
        schema: Dict[str, Any] = {}
        for table in tables:
            result = self.describe_table(table)
            if result.get("success"):
                schema[table] = result["data"]
        return {"success": True, "data": schema}

    def get_row_counts(self) -> Dict[str, int]:
        """Return {table_name: row_count} for all tables."""
        tables = self.list_tables()
        counts: Dict[str, int] = {}
        try:
            with self.engine.connect() as conn:
                for table in tables:
                    row = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    counts[table] = row[0] if row else 0
        except SQLAlchemyError as exc:
            print(f"[DBClient] get_row_counts error: {exc}")
        return counts

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def run_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a SELECT query and return rows as a list of dicts."""
        ok, msg = self.ensure_configured()
        if not ok:
            return {"success": False, "message": msg}
        # Safety guard — only allow SELECT statements
        clean = sql.strip().upper()
        if not clean.startswith("SELECT") and not clean.startswith("WITH"):
            return {
                "success": False,
                "message": (
                    "Only SELECT (and WITH…SELECT) queries are allowed via run_query. "
                    "Use insert_row, update_rows, or delete_rows for write operations."
                ),
            }
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                keys = list(result.keys())
                rows = [dict(zip(keys, row)) for row in result.fetchall()]
            return {"success": True, "data": rows, "columns": keys, "row_count": len(rows)}
        except SQLAlchemyError as exc:
            return {"success": False, "message": f"Query error: {exc}"}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def insert_row(self, table: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single row into *table*."""
        ok, msg = self.ensure_configured()
        if not ok:
            return {"success": False, "message": msg}
        cols = ", ".join(values.keys())
        placeholders = ", ".join(f":{k}" for k in values.keys())
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        try:
            with self.engine.begin() as conn:
                conn.execute(text(sql), values)
            return {"success": True, "message": f"1 row inserted into '{table}'."}
        except SQLAlchemyError as exc:
            return {"success": False, "message": f"Insert error: {exc}"}

    def update_rows(
        self,
        table: str,
        updates: Dict[str, Any],
        condition: str,
        condition_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """UPDATE *table* SET <updates> WHERE <condition>."""
        ok, msg = self.ensure_configured()
        if not ok:
            return {"success": False, "message": msg}
        set_clause = ", ".join(f"{k} = :set_{k}" for k in updates.keys())
        params = {f"set_{k}": v for k, v in updates.items()}
        if condition_params:
            params.update(condition_params)
        sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), params)
                affected = result.rowcount
            return {
                "success": True,
                "message": f"{affected} row(s) updated in '{table}'.",
                "affected_rows": affected,
            }
        except SQLAlchemyError as exc:
            return {"success": False, "message": f"Update error: {exc}"}

    def delete_rows(
        self,
        table: str,
        condition: str,
        condition_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """DELETE FROM *table* WHERE <condition>."""
        ok, msg = self.ensure_configured()
        if not ok:
            return {"success": False, "message": msg}
        sql = f"DELETE FROM {table} WHERE {condition}"
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), condition_params or {})
                affected = result.rowcount
            return {
                "success": True,
                "message": f"{affected} row(s) deleted from '{table}'.",
                "affected_rows": affected,
            }
        except SQLAlchemyError as exc:
            return {"success": False, "message": f"Delete error: {exc}"}

    def count_rows(self, table: str, condition: str = "1=1",
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the number of rows matching *condition* in *table*."""
        sql = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
        result = self.run_query(sql, params)
        if not result.get("success"):
            return result
        row = result["data"][0] if result["data"] else {}
        count = list(row.values())[0] if row else 0
        return {"success": True, "count": count}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_to_csv(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run *sql* and return results as a CSV string."""
        result = self.run_query(sql, params)
        if not result.get("success"):
            return result
        rows = result["data"]
        columns = result["columns"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return {
            "success": True,
            "csv": buf.getvalue(),
            "row_count": len(rows),
            "columns": columns,
        }


db_client = DBClient()

__all__ = ["DBClient", "db_client"]
