"""SQLite-backed application tracker.

Pure tool code — records which jobs have been seen, applied to, skipped, or
errored, so subsequent runs do not re-apply.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Iterable, List, Optional


_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    key TEXT PRIMARY KEY,         -- board:company:job_id
    board TEXT NOT NULL,
    company TEXT NOT NULL,
    job_id TEXT NOT NULL,
    title TEXT,
    url TEXT,
    status TEXT NOT NULL,         -- 'seen' | 'matched' | 'dry_run' | 'applied' | 'skipped' | 'error'
    notes TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_status ON applications(status);
"""


def _db_path() -> str:
    return os.getenv("JOB_AGENT_DB", "applications.db")


def _connect() -> sqlite3.Connection:
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def upsert(
    board: str,
    company: str,
    job_id: str,
    status: str,
    title: str = "",
    url: str = "",
    notes: Optional[str] = None,
) -> None:
    key = f"{board}:{company}:{job_id}"
    now = int(time.time())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO applications(key, board, company, job_id, title, url, status, notes, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                status=excluded.status,
                title=COALESCE(NULLIF(excluded.title, ''), applications.title),
                url=COALESCE(NULLIF(excluded.url, ''), applications.url),
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (key, board, company, job_id, title, url, status, notes, now, now),
        )


def status_for(board: str, company: str, job_id: str) -> Optional[str]:
    key = f"{board}:{company}:{job_id}"
    with _connect() as conn:
        row = conn.execute(
            "SELECT status FROM applications WHERE key = ?", (key,)
        ).fetchone()
        return row["status"] if row else None


def already_processed(board: str, company: str, job_id: str) -> bool:
    """A job is "processed" if we have already applied / dry-run'd / skipped it."""
    s = status_for(board, company, job_id)
    return s in {"applied", "dry_run", "skipped"}


def list_recent(limit: int = 50, statuses: Optional[Iterable[str]] = None) -> List[dict]:
    where = ""
    params: list = []
    if statuses:
        statuses = list(statuses)
        where = f" WHERE status IN ({','.join('?' * len(statuses))})"
        params.extend(statuses)
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM applications{where} ORDER BY updated_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [dict(r) for r in rows]


__all__ = ["upsert", "status_for", "already_processed", "list_recent"]
