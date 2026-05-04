"""The all-in-one orchestrator tool.

This is what the LangChain agent normally calls — one tool that runs the
deterministic pipeline end-to-end, with two narrow LLM calls (score_match
in the ambiguous band, and answer_open_question for free-text fields).

Having one fat tool keeps the agent loop trivial and makes the "99% tools"
claim concrete: the LLM at the orchestrator layer just decides "call this
single tool with these args"; everything afterwards is Python.
"""

from __future__ import annotations

import json
from typing import List, Optional

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import RunPipelineInput
from src.shared import state, tracker_db
from src.shared.boards import ADAPTERS
from src.shared.field_mapper import map_fields as _map_fields, to_dict

from .answer_open_question import answer_open_question_func
from .score_match import score_match_func


def _ensure_profile():
    if not state.has_profile():
        from .load_profile import load_profile_func

        load_profile_func()


def run_pipeline_func(
    query: str,
    boards: Optional[List[str]] = None,
    location: Optional[str] = None,
    limit: int = 10,
    submit: bool = False,
    match_threshold: float = 0.5,
) -> str:
    """End-to-end pipeline: search -> score -> map -> fill -> (submit) -> log."""
    _ensure_profile()
    profile = state.get_profile()
    selected = boards or list(ADAPTERS.keys())

    out: list[dict] = []
    seen = 0

    for name in selected:
        adapter = ADAPTERS.get(name)
        if not adapter:
            continue
        listings = adapter.search(query=query, location=location, limit=limit)
        for j in listings:
            if seen >= limit:
                break
            seen += 1
            entry: dict = {
                "board": j.board,
                "company": j.company,
                "job_id": j.job_id,
                "title": j.title,
                "url": j.url,
            }
            if tracker_db.already_processed(j.board, j.company, j.job_id):
                entry["action"] = "skipped"
                entry["reason"] = "already processed"
                out.append(entry)
                continue

            try:
                details = adapter.get_details(j.company, j.job_id)
            except Exception as e:
                entry["action"] = "error"
                entry["reason"] = f"get_details failed: {e}"
                tracker_db.upsert(
                    j.board, j.company, j.job_id, "error",
                    title=j.title, url=j.url, notes=str(e),
                )
                out.append(entry)
                continue

            score_json = score_match_func(
                details.model_dump_json(), threshold=match_threshold
            )
            score = json.loads(score_json)
            entry["score"] = score
            if score["decision"] != "match":
                tracker_db.upsert(
                    j.board, j.company, j.job_id, "skipped",
                    title=j.title, url=j.url, notes=f"score={score['score']}",
                )
                entry["action"] = "skipped"
                entry["reason"] = f"score {score['score']} below threshold"
                out.append(entry)
                continue

            try:
                fields = adapter.discover_form(j.company, j.job_id)
            except Exception as e:
                entry["action"] = "error"
                entry["reason"] = f"discover_form failed: {e}"
                tracker_db.upsert(
                    j.board, j.company, j.job_id, "error",
                    title=j.title, url=j.url, notes=str(e),
                )
                out.append(entry)
                continue

            filled, needs_llm = _map_fields(fields, profile)
            values = to_dict(filled)

            for d in needs_llm:
                values[d.field_id] = answer_open_question_func(
                    question=d.label,
                    job_details_json=details.model_dump_json(),
                )

            try:
                result = adapter.fill_and_submit(
                    company=j.company,
                    job_id=j.job_id,
                    values_by_field_id=values,
                    resume_path=profile.resume_path,
                    confirm=bool(submit),
                    headless=True,
                )
            except Exception as e:
                tracker_db.upsert(
                    j.board, j.company, j.job_id, "error",
                    title=j.title, url=j.url, notes=str(e),
                )
                entry["action"] = "error"
                entry["reason"] = str(e)
                out.append(entry)
                continue

            status = "applied" if (submit and result.get("submitted")) else "dry_run"
            tracker_db.upsert(
                j.board, j.company, j.job_id, status,
                title=j.title, url=j.url, notes=result.get("message"),
            )
            entry["action"] = status
            entry["fields_filled"] = len([v for v in values.values() if v])
            entry["fields_freetext"] = len(needs_llm)
            entry["result"] = result
            out.append(entry)
        if seen >= limit:
            break

    summary = {
        "considered": len(out),
        "applied": sum(1 for e in out if e.get("action") == "applied"),
        "dry_run": sum(1 for e in out if e.get("action") == "dry_run"),
        "skipped": sum(1 for e in out if e.get("action") == "skipped"),
        "errors": sum(1 for e in out if e.get("action") == "error"),
        "results": out,
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


run_pipeline = StructuredTool(
    name="run_pipeline",
    func=run_pipeline_func,
    description=(
        "End-to-end job application pipeline: search -> score -> discover form -> "
        "deterministically map fields -> answer any free-text questions via LLM -> "
        "fill (and optionally submit) the application -> log the result. "
        "Args: query (required), boards (optional), location (optional), "
        "limit (default 10), submit (default False = dry run), "
        "match_threshold (default 0.5). "
        "Returns a JSON summary with per-job actions."
    ),
    args_schema=RunPipelineInput,
)


__all__ = ["run_pipeline"]
