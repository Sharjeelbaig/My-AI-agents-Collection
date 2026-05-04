from langchain_core.tools import StructuredTool

from src.features.agent.schemas import LoadProfileInput
from src.shared import state
from src.shared.profile_parser import load_profile as _load_profile


def load_profile_func(
    profile_path: str | None = None, resume_pdf_path: str | None = None
) -> str:
    """Load the canonical YAML profile (and optionally a resume PDF) into memory."""
    profile, notes = _load_profile(profile_path, resume_pdf_path)
    state.set_profile(profile)
    flat = profile.to_flat()
    summary = (
        f"Loaded profile for {flat.get('full_name') or 'unknown user'} "
        f"<{flat.get('email') or 'no-email'}>. "
        f"{len(profile.skills)} skills, {len(profile.experience)} experience entries, "
        f"{len(profile.education)} education entries. "
        f"Resume path: {profile.resume_path or '(none)'}."
    )
    return f"{summary}\n{notes}"


load_profile = StructuredTool(
    name="load_profile",
    func=load_profile_func,
    description=(
        "Load the user's canonical job-application profile from a YAML file. "
        "Optionally enriches blank fields by parsing a resume PDF. "
        "MUST be called once before any other application tool. "
        "Args: profile_path (optional, defaults to JOB_AGENT_PROFILE env var); "
        "resume_pdf_path (optional, defaults to JOB_AGENT_RESUME)."
    ),
    args_schema=LoadProfileInput,
)


__all__ = ["load_profile"]
