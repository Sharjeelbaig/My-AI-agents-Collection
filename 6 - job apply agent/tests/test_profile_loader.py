"""YAML profile loader tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

from src.features.agent.schemas.profile_schemas import Profile, ProfileBasics
from src.shared.profile_parser import (
    enrich_from_resume_text,
    load_profile_from_yaml,
)


def test_load_profile_yaml(tmp_path: Path) -> None:
    p = tmp_path / "profile.yaml"
    p.write_text(
        textwrap.dedent(
            """
            basics:
              first_name: Sharjeel
              last_name: Baig
              email: a@b.c
            location:
              city: Lahore
              country: Pakistan
              willing_to_relocate: true
            skills:
              - Python
              - LangChain
            """
        ).strip()
    )
    profile = load_profile_from_yaml(str(p))
    assert profile.basics.first_name == "Sharjeel"
    assert profile.location.willing_to_relocate is True
    assert "LangChain" in profile.skills


def test_resume_text_enrichment_only_fills_blank_fields() -> None:
    p = Profile(basics=ProfileBasics(first_name="Sharjeel", last_name="Baig"))
    text = (
        "Email: existing@example.com\n"
        "Phone: +92 300 1234567\n"
        "https://linkedin.com/in/sharjeelbaig\n"
        "https://github.com/Sharjeelbaig\n"
    )
    enriched = enrich_from_resume_text(p, text)
    assert enriched.basics.email == "existing@example.com"
    assert enriched.basics.phone == "+92 300 1234567"
    assert "linkedin.com/in/sharjeelbaig" in enriched.links.linkedin
    assert "github.com/Sharjeelbaig" in enriched.links.github


def test_resume_text_enrichment_does_not_overwrite_existing() -> None:
    p = Profile(
        basics=ProfileBasics(
            first_name="Sharjeel",
            last_name="Baig",
            email="manual@example.com",
        )
    )
    text = "Email: pdf@example.com"
    enriched = enrich_from_resume_text(p, text)
    assert enriched.basics.email == "manual@example.com"
