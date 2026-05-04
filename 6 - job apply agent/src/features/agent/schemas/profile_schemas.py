from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProfileBasics(BaseModel):
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    preferred_name: str = ""
    email: str = ""
    phone: str = ""
    current_title: str = ""
    current_company: str = ""


class ProfileLocation(BaseModel):
    city: str = ""
    state: str = ""
    country: str = ""
    willing_to_relocate: bool = False
    remote_only: bool = False


class ProfileLinks(BaseModel):
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    website: str = ""
    twitter: str = ""


class ProfileWorkAuth(BaseModel):
    authorized_countries: List[str] = Field(default_factory=list)
    requires_sponsorship_in: List[str] = Field(default_factory=list)


class ProfileCompensation(BaseModel):
    expected_min: int = 0
    expected_max: int = 0
    currency: str = "USD"
    notice_period_weeks: int = 0


class ProfileDemographics(BaseModel):
    gender: str = ""
    ethnicity: str = ""
    veteran_status: str = ""
    disability_status: str = ""


class ProfileEducation(BaseModel):
    school: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""


class ProfileExperience(BaseModel):
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    summary: str = ""


class Profile(BaseModel):
    """Canonical job-application profile.

    All fields default to empty so the profile loader can be lenient with
    partial data (e.g. when parsing a PDF that only yields a subset of fields).
    """

    basics: ProfileBasics = Field(default_factory=ProfileBasics)
    location: ProfileLocation = Field(default_factory=ProfileLocation)
    links: ProfileLinks = Field(default_factory=ProfileLinks)
    work_authorization: ProfileWorkAuth = Field(default_factory=ProfileWorkAuth)
    compensation: ProfileCompensation = Field(default_factory=ProfileCompensation)
    demographics: ProfileDemographics = Field(default_factory=ProfileDemographics)
    education: List[ProfileEducation] = Field(default_factory=list)
    experience: List[ProfileExperience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    elevator_pitch: str = ""
    prepared_answers: Dict[str, str] = Field(default_factory=dict)

    resume_path: Optional[str] = None
    raw_resume_text: Optional[str] = None

    def to_flat(self) -> Dict[str, Any]:
        """Flatten the profile into a single-level dict keyed by canonical names.

        These are the canonical keys the deterministic field mapper looks up.
        """
        return {
            "first_name": self.basics.first_name,
            "last_name": self.basics.last_name,
            "full_name": self.basics.full_name
            or f"{self.basics.first_name} {self.basics.last_name}".strip(),
            "preferred_name": self.basics.preferred_name,
            "email": self.basics.email,
            "phone": self.basics.phone,
            "current_title": self.basics.current_title,
            "current_company": self.basics.current_company,
            "city": self.location.city,
            "state": self.location.state,
            "country": self.location.country,
            "linkedin": self.links.linkedin,
            "github": self.links.github,
            "portfolio": self.links.portfolio,
            "website": self.links.website,
            "twitter": self.links.twitter,
            "willing_to_relocate": self.location.willing_to_relocate,
            "remote_only": self.location.remote_only,
            "authorized_countries": self.work_authorization.authorized_countries,
            "requires_sponsorship_in": self.work_authorization.requires_sponsorship_in,
            "expected_min": self.compensation.expected_min,
            "expected_max": self.compensation.expected_max,
            "currency": self.compensation.currency,
            "notice_period_weeks": self.compensation.notice_period_weeks,
            "gender": self.demographics.gender,
            "ethnicity": self.demographics.ethnicity,
            "veteran_status": self.demographics.veteran_status,
            "disability_status": self.demographics.disability_status,
            "skills": self.skills,
            "elevator_pitch": self.elevator_pitch,
            "resume_path": self.resume_path or "",
        }


__all__ = [
    "Profile",
    "ProfileBasics",
    "ProfileLocation",
    "ProfileLinks",
    "ProfileWorkAuth",
    "ProfileCompensation",
    "ProfileDemographics",
    "ProfileEducation",
    "ProfileExperience",
]
