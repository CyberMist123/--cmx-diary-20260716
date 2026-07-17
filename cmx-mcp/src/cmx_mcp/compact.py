from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Iterable


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts).strip()


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return parser.get_text()


def compact_account(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(account.get("id", "")),
        "username": account.get("acct") or account.get("username") or "",
        "display_name": account.get("display_name") or "",
        "bot": bool(account.get("bot", False)),
    }


def compact_media(media: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(media.get("id", "")),
        "type": media.get("type") or "unknown",
        "description": media.get("description") or "",
    }


def compact_status(status: dict[str, Any]) -> dict[str, Any]:
    reblog = status.get("reblog")
    source = reblog if isinstance(reblog, dict) else status
    account = source.get("account") if isinstance(source.get("account"), dict) else {}
    media = source.get("media_attachments") or []
    return {
        "id": str(status.get("id", "")),
        "source_id": str(source.get("id", "")),
        "author": account.get("acct") or account.get("username") or "",
        "text": strip_html(source.get("content")),
        "created_at": source.get("created_at"),
        "visibility": source.get("visibility"),
        "reply_to": source.get("in_reply_to_id"),
        "reblogged": bool(reblog),
        "media": [compact_media(item) for item in media if isinstance(item, dict)],
    }


def compact_status_page(
    statuses: Iterable[dict[str, Any]], *, next_cursor: str | None = None
) -> dict[str, Any]:
    return {
        "items": [compact_status(item) for item in statuses],
        "next_cursor": next_cursor,
    }


def compact_notification(notification: dict[str, Any]) -> dict[str, Any]:
    account = notification.get("account") if isinstance(notification.get("account"), dict) else {}
    status = notification.get("status") if isinstance(notification.get("status"), dict) else None
    result: dict[str, Any] = {
        "id": str(notification.get("id", "")),
        "type": notification.get("type"),
        "created_at": notification.get("created_at"),
        "account": compact_account(account),
    }
    if status is not None:
        result["status"] = compact_status(status)
    return result


def compact_search(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "accounts": [compact_account(item) for item in result.get("accounts", [])],
        "statuses": [compact_status(item) for item in result.get("statuses", [])],
        "hashtags": [
            {"name": item.get("name", "")}
            for item in result.get("hashtags", [])
            if isinstance(item, dict)
        ],
    }
