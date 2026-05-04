"""Unit tests for the deterministic field mapper.

These tests cover the "99% tools" core — no LLM, no browser, no network.
"""

from __future__ import annotations

from src.features.agent.schemas.job_schemas import FormField, FormFieldOption
from src.features.agent.schemas.profile_schemas import (
    Profile,
    ProfileBasics,
    ProfileLinks,
    ProfileLocation,
    ProfileWorkAuth,
)
from src.shared.field_mapper import map_fields, to_dict


def _profile() -> Profile:
    return Profile(
        basics=ProfileBasics(
            first_name="Sharjeel",
            last_name="Baig",
            full_name="Muhammad Sharjeel Baig",
            email="user@example.com",
            phone="+92 300 1234567",
            current_title="Senior AI Engineer",
            current_company="Acme",
        ),
        location=ProfileLocation(
            city="Lahore", country="Pakistan", willing_to_relocate=True
        ),
        links=ProfileLinks(
            linkedin="https://www.linkedin.com/in/sharjeelbaig",
            github="https://github.com/Sharjeelbaig",
        ),
        work_authorization=ProfileWorkAuth(
            authorized_countries=["Pakistan"],
            requires_sponsorship_in=["United States"],
        ),
        skills=["Python", "LangChain", "TypeScript"],
        elevator_pitch="AI engineer.",
    )


def test_basic_alias_mapping_fills_name_email_phone():
    fields = [
        FormField(field_id="first_name", label="First Name", kind="text", required=True),
        FormField(field_id="last_name", label="Last Name", kind="text", required=True),
        FormField(field_id="email", label="Email Address", kind="email", required=True),
        FormField(field_id="phone", label="Phone Number", kind="phone", required=False),
    ]
    filled, needs_llm = map_fields(fields, _profile())
    assert needs_llm == []
    values = to_dict(filled)
    assert values["first_name"] == "Sharjeel"
    assert values["last_name"] == "Baig"
    assert values["email"] == "user@example.com"
    assert values["phone"] == "+92 300 1234567"


def test_link_fields_map_to_profile_links():
    fields = [
        FormField(field_id="li", label="LinkedIn URL", kind="url"),
        FormField(field_id="gh", label="GitHub Profile", kind="url"),
    ]
    filled, _ = map_fields(fields, _profile())
    values = to_dict(filled)
    assert "linkedin.com/in/sharjeelbaig" in values["li"]
    assert "github.com/Sharjeelbaig" in values["gh"]


def test_work_authorisation_question_is_country_aware():
    fields = [
        FormField(
            field_id="us_auth",
            label="Are you legally authorized to work in the United States?",
            kind="radio",
            options=[FormFieldOption(label="Yes"), FormFieldOption(label="No")],
        ),
        FormField(
            field_id="pk_auth",
            label="Are you legally authorized to work in Pakistan?",
            kind="radio",
            options=[FormFieldOption(label="Yes"), FormFieldOption(label="No")],
        ),
    ]
    filled, _ = map_fields(fields, _profile())
    values = to_dict(filled)
    assert values["us_auth"] == "No"
    assert values["pk_auth"] == "Yes"


def test_sponsorship_question_uses_requires_sponsorship_in():
    fields = [
        FormField(
            field_id="sponsor_us",
            label="Will you require visa sponsorship in the United States?",
            kind="radio",
        ),
        FormField(
            field_id="sponsor_de",
            label="Will you require visa sponsorship in Germany?",
            kind="radio",
        ),
    ]
    filled, _ = map_fields(fields, _profile())
    values = to_dict(filled)
    assert values["sponsor_us"] == "Yes"
    assert values["sponsor_de"] == "No"


def test_relocation_boolean_question():
    fields = [
        FormField(
            field_id="reloc",
            label="Are you willing to relocate?",
            kind="radio",
        )
    ]
    filled, _ = map_fields(fields, _profile())
    assert to_dict(filled)["reloc"] == "Yes"


def test_unknown_freetext_field_routes_to_llm():
    fields = [
        FormField(
            field_id="essay",
            label="Tell us about a time you led a difficult cross-functional project.",
            kind="textarea",
            required=True,
        )
    ]
    filled, needs_llm = map_fields(fields, _profile())
    assert len(needs_llm) == 1
    assert needs_llm[0].field_id == "essay"
    assert needs_llm[0].needs_llm is True
    # Field is not also in 'filled' as a real value.
    values = to_dict(filled)
    assert values.get("essay", "") == ""


def test_select_field_picks_closest_option_label():
    fields = [
        FormField(
            field_id="country",
            label="Country",
            kind="select",
            options=[
                FormFieldOption(label="Pakistan"),
                FormFieldOption(label="India"),
                FormFieldOption(label="United States"),
            ],
        )
    ]
    filled, _ = map_fields(fields, _profile())
    assert to_dict(filled)["country"] == "Pakistan"
