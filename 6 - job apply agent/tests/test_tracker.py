"""Tracker DB tests — fully deterministic, no network."""

from __future__ import annotations

from src.shared import tracker_db


def test_upsert_and_status_for(tmp_path, monkeypatch):
    db = tmp_path / "track.db"
    monkeypatch.setenv("JOB_AGENT_DB", str(db))

    assert tracker_db.status_for("greenhouse", "stripe", "1") is None
    tracker_db.upsert(
        board="greenhouse",
        company="stripe",
        job_id="1",
        status="dry_run",
        title="Engineer",
        url="https://example.com",
        notes="filled",
    )
    assert tracker_db.status_for("greenhouse", "stripe", "1") == "dry_run"

    tracker_db.upsert(
        board="greenhouse",
        company="stripe",
        job_id="1",
        status="applied",
    )
    assert tracker_db.status_for("greenhouse", "stripe", "1") == "applied"
    assert tracker_db.already_processed("greenhouse", "stripe", "1") is True
    assert tracker_db.already_processed("greenhouse", "stripe", "2") is False

    rows = tracker_db.list_recent(limit=10)
    assert len(rows) == 1
    assert rows[0]["status"] == "applied"
    assert rows[0]["title"] == "Engineer"
