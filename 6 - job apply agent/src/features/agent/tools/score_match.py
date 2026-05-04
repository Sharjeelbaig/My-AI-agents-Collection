import json
import re
from typing import Set

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import ScoreMatchInput
from src.features.agent.schemas.job_schemas import JobDetails
from src.shared import state
from src.shared.llm import chat


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+/.#-]*")


def _tokens(text: str) -> Set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1}


def _deterministic_score(skills: list[str], jd_text: str) -> float:
    """Skill-overlap heuristic — a fast, free signal.

    Returns 0..1: fraction of the user's skills that appear verbatim in the JD.
    """
    if not skills:
        return 0.0
    jd_tokens = _tokens(jd_text)
    hits = sum(1 for s in skills if s.lower() in jd_tokens)
    return hits / len(skills)


_SYSTEM = (
    "You are a hiring-fit classifier for a job-application bot. "
    "Given the candidate's skills/profile and a job description, output ONLY "
    "a single decimal between 0 and 1 indicating fit (1 = strong, 0 = none). "
    "Do not explain. Do not add prose."
)


def score_match_func(job_details_json: str, threshold: float = 0.5) -> str:
    """Score how well the loaded profile matches the supplied job.

    Returns JSON: {score: float, threshold: float, decision: 'match'|'skip',
    method: 'heuristic'|'llm'}.

    The LLM is consulted ONLY when the deterministic skill-overlap heuristic
    is in the ambiguous band [0.25, 0.65]. Otherwise the heuristic decides
    directly. This is one of the only two LLM uses in the whole agent.
    """
    profile = state.get_profile()
    details = JobDetails.model_validate_json(job_details_json)
    jd_text = "\n".join(
        [details.listing.title, details.listing.department, details.description]
    )

    h_score = _deterministic_score(profile.skills, jd_text)

    if h_score < 0.25 or h_score > 0.65:
        decision = "match" if h_score >= threshold else "skip"
        return json.dumps(
            {
                "score": round(h_score, 3),
                "threshold": threshold,
                "decision": decision,
                "method": "heuristic",
            }
        )

    # Ambiguous band -> ask the LLM.
    user = (
        f"Candidate skills: {', '.join(profile.skills) or '(none listed)'}\n"
        f"Candidate elevator pitch: {profile.elevator_pitch or '(none)'}\n\n"
        f"Job title: {details.listing.title}\n"
        f"Department: {details.listing.department}\n"
        f"Description:\n{(details.description or '')[:4000]}\n"
    )
    raw = chat(_SYSTEM, user)
    try:
        score = float(re.findall(r"[01](?:\.\d+)?", raw)[0])
        score = max(0.0, min(1.0, score))
    except (IndexError, ValueError):
        score = h_score
    decision = "match" if score >= threshold else "skip"
    return json.dumps(
        {
            "score": round(score, 3),
            "threshold": threshold,
            "decision": decision,
            "method": "llm",
        }
    )


score_match = StructuredTool(
    name="score_match",
    func=score_match_func,
    description=(
        "Score how well the loaded profile matches a job (0..1). "
        "Uses a deterministic skill-overlap heuristic by default; only consults "
        "the LLM when the heuristic is in the ambiguous band [0.25, 0.65]. "
        "Args: job_details_json (output of get_job_details), threshold (default 0.5)."
    ),
    args_schema=ScoreMatchInput,
)


__all__ = ["score_match"]
