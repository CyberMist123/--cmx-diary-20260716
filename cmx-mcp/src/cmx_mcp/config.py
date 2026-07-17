from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse


class Profile(StrEnum):
    READER = "reader"
    RESIDENT = "resident"
    PERSONAL = "personal"


READ_ACTIONS = {
    "identity.read",
    "timeline.read",
    "status.read",
    "notifications.read",
    "search.read",
    "relationships.read",
    "lists.read",
    "profile.read",
}

RESIDENT_ACTIONS = READ_ACTIONS | {
    "status.write",
    "status.interact",
    "media.write",
    "notifications.write",
    "lists.write",
    "profile.write",
}

PERSONAL_ACTIONS = RESIDENT_ACTIONS | {
    "relationships.write",
}

PROFILE_CAPABILITIES: dict[Profile, frozenset[str]] = {
    Profile.READER: frozenset(READ_ACTIONS),
    Profile.RESIDENT: frozenset(RESIDENT_ACTIONS),
    Profile.PERSONAL: frozenset(PERSONAL_ACTIONS),
}

_HOST_PATTERN = re.compile(r"^[A-Za-z0-9.-]+(?::[0-9]{1,5})?$")
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    host_header: str
    access_token: str
    profile: Profile
    media_root: Path | None
    default_visibility: str
    max_items: int
    max_media_bytes: int
    timeout_seconds: float
    allow_remote_base_url: bool

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.getenv("CMX_MASTODON_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
        access_token = os.getenv("CMX_MASTODON_TOKEN", "").strip()
        if not access_token:
            raise RuntimeError("CMX_MASTODON_TOKEN is required")

        try:
            profile = Profile(os.getenv("CMX_PROFILE", Profile.READER.value).lower())
        except ValueError as exc:
            raise RuntimeError("CMX_PROFILE must be reader, resident, or personal") from exc

        allow_remote = os.getenv("CMX_ALLOW_REMOTE_BASE_URL", "false").lower() in {"1", "true", "yes"}
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RuntimeError("CMX_MASTODON_BASE_URL must be an absolute http/https URL")
        if not allow_remote and parsed.hostname not in _LOOPBACK_HOSTS:
            raise RuntimeError(
                "CMX_MASTODON_BASE_URL must be loopback unless CMX_ALLOW_REMOTE_BASE_URL=true"
            )

        host_header = os.getenv("CMX_MASTODON_HOST", "").strip()
        if not host_header:
            if parsed.hostname in _LOOPBACK_HOSTS:
                raise RuntimeError(
                    "CMX_MASTODON_HOST is required for loopback access so Rails sees the current WEB_DOMAIN"
                )
            host_header = parsed.netloc
        if "://" in host_header or "/" in host_header or not _HOST_PATTERN.fullmatch(host_header):
            raise RuntimeError("CMX_MASTODON_HOST must be a hostname, optionally with a port")

        media_root_raw = os.getenv("CMX_MEDIA_ROOT", "").strip()
        media_root = Path(media_root_raw).expanduser() if media_root_raw else None

        default_visibility = os.getenv("CMX_DEFAULT_VISIBILITY", "private").lower()
        if default_visibility not in {"public", "unlisted", "private", "direct"}:
            raise RuntimeError("CMX_DEFAULT_VISIBILITY is invalid")

        max_items = _bounded_int("CMX_MAX_ITEMS", default=30, minimum=1, maximum=100)
        max_media_bytes = _bounded_int(
            "CMX_MAX_MEDIA_BYTES",
            default=40 * 1024 * 1024,
            minimum=1,
            maximum=1024 * 1024 * 1024,
        )
        timeout_seconds = _bounded_float(
            "CMX_TIMEOUT_SECONDS", default=20.0, minimum=1.0, maximum=120.0
        )

        return cls(
            base_url=base_url,
            host_header=host_header,
            access_token=access_token,
            profile=profile,
            media_root=media_root,
            default_visibility=default_visibility,
            max_items=max_items,
            max_media_bytes=max_media_bytes,
            timeout_seconds=timeout_seconds,
            allow_remote_base_url=allow_remote,
        )

    def require(self, capability: str) -> None:
        if capability not in PROFILE_CAPABILITIES[self.profile]:
            raise PermissionError(
                f"Profile '{self.profile.value}' does not allow capability '{capability}'"
            )

    def clamp_limit(self, requested: int | None, default: int = 10) -> int:
        value = default if requested is None else requested
        if value < 1:
            raise ValueError("limit must be at least 1")
        return min(value, self.max_items)


def _bounded_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    try:
        value = default if raw is None else int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


def _bounded_float(name: str, *, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    try:
        value = default if raw is None else float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be numeric") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value
