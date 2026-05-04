"""The brain of the deterministic field mapper.

Every entry maps a normalised label substring to the canonical profile key
that should fill it. The mapper iterates these in order and picks the first
match — so put more-specific aliases above more-general ones.

This is what lets the agent be "99% tools": instead of asking an LLM "what
goes here?", we look it up in this table.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


# Ordered list of (label_substring, canonical_profile_key).
# All comparisons are case-insensitive; spaces / underscores / hyphens are
# normalised to single spaces before matching.
ALIASES: List[Tuple[str, str]] = [
    # --- name ---
    ("preferred name", "preferred_name"),
    ("preferred first name", "preferred_name"),
    ("first name", "first_name"),
    ("given name", "first_name"),
    ("last name", "last_name"),
    ("surname", "last_name"),
    ("family name", "last_name"),
    ("legal name", "full_name"),
    ("full name", "full_name"),
    ("name", "full_name"),

    # --- contact ---
    ("email address", "email"),
    ("e-mail", "email"),
    ("email", "email"),
    ("phone number", "phone"),
    ("mobile", "phone"),
    ("telephone", "phone"),
    ("phone", "phone"),

    # --- location ---
    ("current location", "city"),
    ("city", "city"),
    ("state", "state"),
    ("province", "state"),
    ("country", "country"),

    # --- links ---
    ("linkedin profile", "linkedin"),
    ("linkedin url", "linkedin"),
    ("linkedin", "linkedin"),
    ("github profile", "github"),
    ("github url", "github"),
    ("github", "github"),
    ("portfolio", "portfolio"),
    ("personal website", "website"),
    ("website", "website"),
    ("twitter", "twitter"),
    ("x.com", "twitter"),

    # --- current role ---
    ("current company", "current_company"),
    ("current employer", "current_company"),
    ("company", "current_company"),
    ("current title", "current_title"),
    ("current role", "current_title"),
    ("job title", "current_title"),
    ("title", "current_title"),

    # --- comp ---
    ("expected salary", "expected_min"),
    ("desired salary", "expected_min"),
    ("salary expectation", "expected_min"),
    ("notice period", "notice_period_weeks"),

    # --- demographics ---
    ("gender", "gender"),
    ("ethnicity", "ethnicity"),
    ("race", "ethnicity"),
    ("veteran", "veteran_status"),
    ("disability", "disability_status"),

    # --- resume / cover letter ---
    ("resume", "resume_path"),
    ("cv", "resume_path"),
    ("cover letter", "elevator_pitch"),

    # --- elevator-pitch fallback for "tell us about yourself" ---
    ("about yourself", "elevator_pitch"),
    ("introduce yourself", "elevator_pitch"),
    ("summary", "elevator_pitch"),
]


# Yes/No-style boolean questions. value -> profile field that decides yes/no.
BOOLEAN_QUESTIONS: Dict[str, str] = {
    "willing to relocate": "willing_to_relocate",
    "open to relocation": "willing_to_relocate",
    "remote only": "remote_only",
    "work remotely": "remote_only",
}


# Work-authorisation questions are special: the answer depends on the
# country named in the question.  e.g. "Are you authorised to work in the
# United States?" -> True iff "United States" is in profile.authorized_countries
WORK_AUTH_PATTERNS: List[str] = [
    "authorized to work",
    "authorised to work",
    "legally authorized",
    "legally authorised",
    "right to work",
    "eligible to work",
]

SPONSORSHIP_PATTERNS: List[str] = [
    "require sponsorship",
    "need sponsorship",
    "visa sponsorship",
    "require visa",
    "need a visa",
]


__all__ = [
    "ALIASES",
    "BOOLEAN_QUESTIONS",
    "WORK_AUTH_PATTERNS",
    "SPONSORSHIP_PATTERNS",
]
