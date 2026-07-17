from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import Paths
from .db import Database


READ_TOOLS = {
    "cmx_identity",
    "cmx_timeline",
    "cmx_status",
    "cmx_search",
}

WRITE_TOOLS = {
    "cmx_publish",
    "cmx_react",
    "cmx_media_upload",
    "cmx_notifications",
    "cmx_quote_link",
    "cmx_pin",
    "cmx_profile_update",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end local CMX MCP smoke test without Telegram"
    )
    parser.add_argument("--bot", required=True, help="Bot ID stored in local SQLite")
    args = parser.parse_args()
    asyncio.run(_run(args.bot))


async def _run(bot_id: str) -> None:
    paths = Paths.discover()
    paths.ensure()
    database = Database(paths.database)
    database.initialize()
    bot = database.get_bot(bot_id)

    executable = paths.home / ".venv" / "Scripts" / "cmx-mcp.exe"
    if not executable.exists():
        raise SystemExit(f"MCP executable is missing: {executable}")

    expected = set(READ_TOOLS)
    if bot.profile in {"resident", "personal"}:
        expected.update(WRITE_TOOLS)

    environment = os.environ.copy()
    environment["CMX_MCP_HOME"] = str(paths.home)
    parameters = StdioServerParameters(
        command=str(executable),
        args=["--bot", bot_id],
        env=environment,
    )

    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}

            missing = sorted(expected - names)
            unexpected_write = sorted((names & WRITE_TOOLS) if bot.profile == "reader" else [])
            if missing or unexpected_write:
                raise SystemExit(
                    json.dumps(
                        {
                            "ok": False,
                            "reason": "tool exposure mismatch",
                            "missing": missing,
                            "unexpected_write": unexpected_write,
                            "tools": sorted(names),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            identity = await session.call_tool("cmx_identity", arguments={})
            if getattr(identity, "isError", False):
                raise SystemExit("cmx_identity returned an MCP tool error")

            timeline = await session.call_tool("cmx_timeline", arguments={"limit": 1})
            if getattr(timeline, "isError", False):
                raise SystemExit("cmx_timeline returned an MCP tool error")

            print(
                json.dumps(
                    {
                        "ok": True,
                        "bot": bot_id,
                        "profile": bot.profile,
                        "tools": sorted(names),
                        "identity": _result_summary(identity),
                        "timeline": _result_summary(timeline),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )


def _result_summary(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    content = getattr(result, "content", None) or []
    text_parts = [
        block.text
        for block in content
        if getattr(block, "type", None) == "text" and getattr(block, "text", None)
    ]
    return {
        "structured": structured,
        "text": "\n".join(text_parts)[:4000] if text_parts else None,
    }


if __name__ == "__main__":
    main()
