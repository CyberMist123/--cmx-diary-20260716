from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"p", "br", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line).strip()


def strip_html(value: str | None) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    return parser.text()


def timeline_preview(raw: dict[str, Any], max_chars: int = 50) -> dict[str, Any]:
    """Return the deliberately tiny representation used by remote timeline browsing."""
    source = raw.get("reblog") or raw
    account = source.get("account") or {}
    text = re.sub(r"\s+", " ", strip_html(source.get("content"))).strip()
    if len(text) > max_chars:
        text = text[: max(0, max_chars - 1)].rstrip() + "…"
    result: dict[str, Any] = {
        "id": str(source.get("id") or raw.get("id") or ""),
        "author": str(account.get("acct") or account.get("username") or ""),
        "preview": text,
    }
    replies = int(source.get("replies_count") or 0)
    if replies:
        result["replies"] = replies
    media_count = len(source.get("media_attachments") or [])
    if media_count:
        result["media"] = media_count
    return result


def compact_account(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(account.get("id") or ""),
        "acct": account.get("acct") or account.get("username") or "",
        "display_name": account.get("display_name") or "",
        "bot": bool(account.get("bot", False)),
        "locked": bool(account.get("locked", False)),
    }


def compact_media(media: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(media.get("id") or ""),
        "type": media.get("type"),
        "description": media.get("description"),
        "url": media.get("url"),
    }


def compact_status(raw: dict[str, Any]) -> dict[str, Any]:
    wrapper = raw
    source = raw.get("reblog") or raw
    account = source.get("account") or {}
    wrapper_account = wrapper.get("account") or {}
    mentions = [
        {"id": str(item.get("id") or ""), "acct": item.get("acct") or ""}
        for item in source.get("mentions") or []
    ]
    return {
        "id": str(wrapper.get("id") or ""),
        "interaction_target_id": str(source.get("id") or ""),
        "author": compact_account(account),
        "boosted_by": compact_account(wrapper_account) if raw.get("reblog") else None,
        "text": strip_html(source.get("content")),
        "spoiler_text": source.get("spoiler_text") or "",
        "sensitive": bool(source.get("sensitive", False)),
        "created_at": source.get("created_at"),
        "edited_at": source.get("edited_at"),
        "visibility": source.get("visibility"),
        "reply_to_id": source.get("in_reply_to_id"),
        "mentions": mentions,
        "media": [compact_media(item) for item in source.get("media_attachments") or []],
        "favourited": bool(source.get("favourited", False)),
        "bookmarked": bool(source.get("bookmarked", False)),
        "reblogged": bool(source.get("reblogged", False)),
    }


def compact_v2_status(raw: dict[str, Any]) -> dict[str, Any]:
    """Return the sparse Phase A representation; omit absent/empty fields."""
    wrapper = raw
    source = raw.get("reblog") or raw
    account = source.get("account") or {}
    result: dict[str, Any] = {
        "id": str(source.get("id") or wrapper.get("id") or ""),
        "author": str(account.get("acct") or account.get("username") or ""),
        "at": source.get("created_at"),
        "text": strip_html(source.get("content")),
    }
    optional = {
        "reply_to": source.get("in_reply_to_id"),
        "via": (raw.get("account") or {}).get("acct") if raw.get("reblog") else None,
        "vis": source.get("visibility") if source.get("visibility") not in (None, "private") else None,
        "cw": source.get("spoiler_text") or None,
    }
    if source.get("visibility") == "direct":
        recipients = [str(item.get("acct") or "") for item in source.get("mentions") or []]
        recipients = [item for item in recipients if item]
        if recipients:
            optional["to"] = recipients
    for key, value in optional.items():
        if value not in (None, "", [], False):
            result[key] = value
    attachments = source.get("media_attachments") or []
    if attachments:
        result["media"] = [
            {key: value for key, value in {
                "type": item.get("type"),
                "alt": item.get("description"),
            }.items() if value not in (None, "")}
            for item in attachments
        ]
    poll = source.get("poll")
    if poll:
        result["poll"] = {
            key: value for key, value in {
                "options": [str(item.get("title") or "") for item in poll.get("options") or []],
                "expired": poll.get("expired"),
                "multiple": poll.get("multiple"),
                "voted": poll.get("voted"),
            }.items() if value not in (None, "", [], False)
        }
    state = {
        key: value for key, value in {
            "favourite": source.get("favourited"),
            "bookmark": source.get("bookmarked"),
            "reblog": source.get("reblogged"),
        }.items() if value
    }
    if state:
        result["state"] = state
    return {key: value for key, value in result.items() if value not in (None, "", [], False)}
