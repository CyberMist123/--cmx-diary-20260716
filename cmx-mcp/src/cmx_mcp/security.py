from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path


ALLOWED_MIME_PREFIXES = ("image/", "video/", "audio/")
DENIED_BASENAMES = {
    ".env",
    ".env.production",
    "credentials.json",
    "secrets.json",
}
DENIED_SUFFIXES = {
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".sql",
    ".dump",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
}


@dataclass(frozen=True, slots=True)
class SafeMediaFile:
    path: Path
    mime_type: str
    size_bytes: int


def resolve_safe_media_file(
    *,
    media_root: Path | None,
    requested_path: str,
    max_bytes: int,
) -> SafeMediaFile:
    if media_root is None:
        raise PermissionError("This connection has no CMX_MEDIA_ROOT")
    if not requested_path or "\x00" in requested_path:
        raise ValueError("Invalid media path")

    root = _real_path(media_root, require_exists=True)
    candidate = _real_path(Path(requested_path).expanduser(), require_exists=True)

    if not root.is_dir():
        raise ValueError("CMX_MEDIA_ROOT is not a directory")
    if not candidate.is_file():
        raise ValueError("Media path is not a regular file")

    if _is_unc(candidate):
        raise PermissionError("UNC/network media paths are not allowed")

    try:
        common = Path(os.path.commonpath([str(root), str(candidate)]))
    except ValueError as exc:
        raise PermissionError("Media path is on a different volume") from exc
    if os.path.normcase(str(common)) != os.path.normcase(str(root)):
        raise PermissionError("Media path is outside the configured media root")

    if candidate.name.lower() in DENIED_BASENAMES:
        raise PermissionError("Sensitive file name is not allowed")
    if candidate.suffix.lower() in DENIED_SUFFIXES:
        raise PermissionError("Sensitive or archive file type is not allowed")

    mime_type, _ = mimetypes.guess_type(candidate.name)
    if not mime_type or not mime_type.startswith(ALLOWED_MIME_PREFIXES):
        raise PermissionError("Only image, video, and audio files are allowed")

    size_bytes = candidate.stat().st_size
    if size_bytes <= 0:
        raise ValueError("Media file is empty")
    if size_bytes > max_bytes:
        raise ValueError(f"Media file exceeds the {max_bytes}-byte limit")

    return SafeMediaFile(path=candidate, mime_type=mime_type, size_bytes=size_bytes)


def _real_path(path: Path, *, require_exists: bool) -> Path:
    # Path.resolve follows symlinks and Windows junctions supported by the host.
    # realpath adds another normalization layer for cross-platform review.
    resolved = Path(os.path.realpath(path)).resolve(strict=require_exists)
    return resolved


def _is_unc(path: Path) -> bool:
    raw = str(path)
    return raw.startswith("\\\\") or raw.startswith("//")
