"""Profile loading: YAML is the canonical source; PDF is best-effort enrichment.

Pure-tool code: no LLM calls, just parsing.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Tuple

import yaml

from src.features.agent.schemas.profile_schemas import Profile


def load_profile_from_yaml(path: str) -> Profile:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Profile YAML not found at {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return Profile.model_validate(data)


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d \-().]{6,}\d)")
_LINKEDIN_RE = re.compile(r"linkedin\.com/in/[A-Za-z0-9\-_/]+", re.I)
_GITHUB_RE = re.compile(r"github\.com/[A-Za-z0-9\-_]+", re.I)
_URL_RE = re.compile(r"https?://[^\s)]+", re.I)


def extract_text_from_pdf(path: str) -> str:
    """Best-effort PDF -> text. Returns "" if extraction fails (e.g. corrupted)."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        chunks: list[str] = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(chunks).strip()
    except Exception:
        return ""


def enrich_from_resume_text(profile: Profile, text: str) -> Profile:
    """Light deterministic enrichment: only fills *blank* fields, never overwrites."""
    if not text:
        return profile

    if not profile.basics.email:
        m = _EMAIL_RE.search(text)
        if m:
            profile.basics.email = m.group(0)

    if not profile.basics.phone:
        m = _PHONE_RE.search(text)
        if m:
            profile.basics.phone = m.group(0).strip()

    if not profile.links.linkedin:
        m = _LINKEDIN_RE.search(text)
        if m:
            profile.links.linkedin = "https://" + m.group(0).rstrip("/")

    if not profile.links.github:
        m = _GITHUB_RE.search(text)
        if m:
            profile.links.github = "https://" + m.group(0).rstrip("/")

    return profile


def load_profile(
    profile_path: Optional[str] = None,
    resume_pdf_path: Optional[str] = None,
) -> Tuple[Profile, str]:
    """Load profile from YAML and optionally enrich from a resume PDF.

    Returns (profile, status_message).
    """
    profile_path = profile_path or os.getenv("JOB_AGENT_PROFILE", "profile.yaml")
    resume_pdf_path = resume_pdf_path or os.getenv("JOB_AGENT_RESUME") or None

    notes: list[str] = []
    profile = load_profile_from_yaml(profile_path)
    notes.append(f"Loaded profile from {profile_path}.")

    if resume_pdf_path and Path(resume_pdf_path).expanduser().exists():
        text = extract_text_from_pdf(resume_pdf_path)
        if text:
            profile = enrich_from_resume_text(profile, text)
            profile.raw_resume_text = text
            notes.append(f"Enriched profile from resume PDF ({len(text)} chars).")
        else:
            notes.append(
                f"WARNING: could not extract text from {resume_pdf_path} — "
                "the PDF may be corrupted or image-only. Profile YAML is authoritative."
            )
        profile.resume_path = str(Path(resume_pdf_path).expanduser().resolve())

    return profile, " ".join(notes)


__all__ = [
    "load_profile",
    "load_profile_from_yaml",
    "extract_text_from_pdf",
    "enrich_from_resume_text",
]
