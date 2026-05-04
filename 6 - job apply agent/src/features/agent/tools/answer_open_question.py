from typing import Optional

from langchain_core.tools import StructuredTool

from src.features.agent.schemas import AnswerOpenQuestionInput
from src.features.agent.schemas.job_schemas import JobDetails
from src.shared import state
from src.shared.llm import chat


_SYSTEM = (
    "You are a writing assistant for a job-application bot. Given the "
    "candidate's profile and a single open-text question from a job form, "
    "produce a concise, first-person answer using only facts from the profile. "
    "Do not invent experience, companies, or numbers. Keep it under the supplied "
    "character limit. Output the answer text only — no preamble, no quotes."
)


def answer_open_question_func(
    question: str,
    job_details_json: Optional[str] = None,
    max_chars: int = 600,
) -> str:
    """Generate a short free-text answer for one open form question.

    This is the second (and final) place the agent uses an LLM. Everything
    else is deterministic.
    """
    profile = state.get_profile()

    job_context = ""
    if job_details_json:
        try:
            d = JobDetails.model_validate_json(job_details_json)
            job_context = (
                f"Role: {d.listing.title} at {d.listing.company}\n"
                f"Department: {d.listing.department}\n"
                f"Snippet:\n{(d.description or '')[:1500]}\n"
            )
        except Exception:
            job_context = ""

    profile_summary = (
        f"Name: {profile.basics.full_name or profile.basics.first_name}\n"
        f"Title: {profile.basics.current_title}\n"
        f"Skills: {', '.join(profile.skills)}\n"
        f"Elevator pitch: {profile.elevator_pitch}\n"
    )

    user = (
        f"{profile_summary}\n"
        f"{job_context}\n"
        f"Question: {question}\n"
        f"Character limit: {max_chars}.\n"
    )

    answer = chat(_SYSTEM, user)
    return answer[:max_chars]


answer_open_question = StructuredTool(
    name="answer_open_question",
    func=answer_open_question_func,
    description=(
        "Generate a short, profile-grounded answer to a free-text application "
        "question. ONLY use this for fields that map_fields returned in its "
        "needs_llm list — never for fields the deterministic mapper already "
        "filled. Args: question (required), job_details_json (optional), "
        "max_chars (default 600)."
    ),
    args_schema=AnswerOpenQuestionInput,
)


__all__ = ["answer_open_question"]
