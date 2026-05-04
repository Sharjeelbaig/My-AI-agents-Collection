"""Deterministic field -> profile-value mapper.

This is the heart of the "99% tools" guarantee. Given a list of FormField
objects and a flat profile dict, it returns a list of ``(field_id, value)``
pairs deciding what to type into each field.

Resolution order, top to bottom — first hit wins:

1.  Direct alias hit from ``ALIASES`` (case/space-insensitive substring).
2.  Boolean-question pattern match (e.g. "Are you willing to relocate?").
3.  Work-authorisation / sponsorship pattern match (country-aware).
4.  Pre-canned answer from ``profile.prepared_answers``.
5.  Fuzzy match against the alias keys via ``rapidfuzz``.

If everything misses, the field is left for the LLM ``answer_open_question``
call (the only place the agent uses an LLM at fill time).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

from src.features.agent.schemas.job_schemas import FormField
from src.features.agent.schemas.profile_schemas import Profile
from src.shared.field_aliases import (
    ALIASES,
    BOOLEAN_QUESTIONS,
    SPONSORSHIP_PATTERNS,
    WORK_AUTH_PATTERNS,
)


_NORMALISE_RE = re.compile(r"[\s_\-]+")


def _norm(label: str) -> str:
    return _NORMALISE_RE.sub(" ", label.lower()).strip()


@dataclass
class FieldDecision:
    field_id: str
    label: str
    value: object
    source: str          # "alias" | "boolean" | "work_auth" | "sponsorship" |
                         # "prepared" | "fuzzy" | "select_match" |
                         # "needs_freetext" | "skipped"
    needs_llm: bool = False


def _country_in_text(text: str, countries: List[str]) -> Optional[str]:
    t = text.lower()
    for c in countries:
        if c and c.lower() in t:
            return c
    return None


def _select_value(field: FormField, candidate: str) -> str:
    """For select / radio fields, pick the option whose label is closest to
    ``candidate``. Returns the option's *label* because Greenhouse / Ashby
    expect labels in their fill APIs."""
    if not field.options or not candidate:
        return candidate
    labels = [o.label for o in field.options]
    match = process.extractOne(candidate, labels, scorer=fuzz.WRatio)
    if match and match[1] >= 60:
        return match[0]
    return candidate


def _resolve_alias(label_norm: str) -> Optional[str]:
    """First exact-substring pass over the ordered alias list."""
    for needle, key in ALIASES:
        if needle in label_norm:
            return key
    return None


def _fuzzy_alias(label_norm: str) -> Optional[str]:
    """Fuzzy-match short field labels to alias keys.

    Long labels (questions, essays) are skipped — partial-ratio scoring would
    produce false positives like 'about yourself' matching 'tell us about a
    time you ...'. Those should route to the open-question LLM instead.
    """
    if len(label_norm) > 30 or len(label_norm.split()) > 4:
        return None
    needles = [n for n, _ in ALIASES]
    match = process.extractOne(label_norm, needles, scorer=fuzz.ratio)
    if not match:
        return None
    score, idx = match[1], match[2]
    if score < 80:
        return None
    return ALIASES[idx][1]


def map_fields(
    fields: List[FormField], profile: Profile
) -> Tuple[List[FieldDecision], List[FieldDecision]]:
    """Return (filled, needs_llm).

    *filled* — decisions that are ready to send to the form.
    *needs_llm* — fields that require the open-question LLM call before fill.
    """
    flat = profile.to_flat()
    filled: List[FieldDecision] = []
    needs_llm: List[FieldDecision] = []

    for f in fields:
        label_norm = _norm(f.label)

        # ---- 1. boolean / yes-no patterns ------------------------------------
        bool_key = next(
            (key for k, key in BOOLEAN_QUESTIONS.items() if k in label_norm), None
        )
        if bool_key is not None:
            val = bool(flat.get(bool_key, False))
            filled.append(
                FieldDecision(f.field_id, f.label, "Yes" if val else "No", "boolean")
            )
            continue

        # ---- 2. work-authorisation -------------------------------------------
        if any(p in label_norm for p in WORK_AUTH_PATTERNS):
            country = _country_in_text(
                f.label, flat.get("authorized_countries", [])
            )
            if country is not None:
                filled.append(FieldDecision(f.field_id, f.label, "Yes", "work_auth"))
            else:
                # Not in the user's authorized list -> assume "No".
                filled.append(FieldDecision(f.field_id, f.label, "No", "work_auth"))
            continue

        if any(p in label_norm for p in SPONSORSHIP_PATTERNS):
            country = _country_in_text(
                f.label, flat.get("requires_sponsorship_in", [])
            )
            answer = "Yes" if country else "No"
            filled.append(FieldDecision(f.field_id, f.label, answer, "sponsorship"))
            continue

        # ---- 3. prepared answers (free text) ---------------------------------
        prepared = next(
            (
                v
                for k, v in (profile.prepared_answers or {}).items()
                if k.lower() in label_norm and v
            ),
            None,
        )
        if prepared:
            filled.append(FieldDecision(f.field_id, f.label, prepared, "prepared"))
            continue

        # ---- 4. alias / fuzzy alias ------------------------------------------
        key = _resolve_alias(label_norm) or _fuzzy_alias(label_norm)
        if key is not None:
            value = flat.get(key, "")
            if f.kind in {"select", "radio"} and isinstance(value, str):
                value = _select_value(f, value)
            elif f.kind == "checkbox" and isinstance(value, bool):
                value = "Yes" if value else "No"
            elif isinstance(value, list):
                value = ", ".join(str(x) for x in value)
            filled.append(
                FieldDecision(f.field_id, f.label, value, "alias")
            )
            continue

        # ---- 5. nothing matched ----------------------------------------------
        if f.kind in {"textarea", "text"} and len(f.label) > 12:
            # Long-ish prompt that didn't match anything -> needs LLM.
            needs_llm.append(
                FieldDecision(f.field_id, f.label, "", "needs_freetext", needs_llm=True)
            )
        else:
            filled.append(
                FieldDecision(f.field_id, f.label, "", "skipped")
            )

    return filled, needs_llm


def to_dict(decisions: List[FieldDecision]) -> Dict[str, object]:
    return {d.field_id: d.value for d in decisions}


__all__ = ["map_fields", "FieldDecision", "to_dict"]
