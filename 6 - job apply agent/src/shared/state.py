"""Process-local cache of the loaded profile.

Tools share state through this module so the user only has to call
``load_profile`` once per session.
"""

from __future__ import annotations

from typing import Optional

from src.features.agent.schemas.profile_schemas import Profile


_PROFILE: Optional[Profile] = None


def set_profile(profile: Profile) -> None:
    global _PROFILE
    _PROFILE = profile


def get_profile() -> Profile:
    if _PROFILE is None:
        raise RuntimeError(
            "Profile has not been loaded yet. Call load_profile first."
        )
    return _PROFILE


def has_profile() -> bool:
    return _PROFILE is not None


__all__ = ["set_profile", "get_profile", "has_profile"]
