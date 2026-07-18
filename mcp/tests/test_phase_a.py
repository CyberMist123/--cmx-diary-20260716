from types import SimpleNamespace

from cmx_mcp.compact import compact_v2_status
from cmx_mcp.server import build_server
from cmx_mcp.scope import READ_SCOPE, SOCIAL_SCOPE, require_request_scope


def test_compact_v2_omits_empty_fields_and_preserves_reply_and_direct_mentions():
    result = compact_v2_status({
        "id": "1", "created_at": "2026-07-18T00:00:00Z", "visibility": "direct",
        "content": "<p>hello</p>", "in_reply_to_id": "0",
        "account": {"acct": "alice"}, "mentions": [{"acct": "bob"}],
        "spoiler_text": "cw", "media_attachments": [],
    })
    assert result == {
        "id": "1", "author": "alice", "at": "2026-07-18T00:00:00Z", "text": "hello",
        "reply_to": "0", "vis": "direct", "to": ["bob"], "cw": "cw",
    }


def _runtime(**overrides):
    class Runtime: pass
    runtime = Runtime()
    runtime.bot = SimpleNamespace(
        bot_id="gpt", profile="resident", allow_public=False,
        remote_polls=True, remote_boosts=overrides.get("boosts", False),
        remote_notifications=overrides.get("notifications", False),
    )
    runtime.settings = SimpleNamespace(max_items=30)
    runtime.client = None
    runtime.db = None
    return runtime


def test_remote_reader_surface_is_exactly_three_tools():
    server = build_server(_runtime(), remote_profile="reader", remote_capabilities=_runtime().bot)
    assert [tool.name for tool in server._tool_manager.list_tools()] == ["cmx_home", "cmx_status", "cmx_search"]


def test_remote_social_surface_hides_boost_and_notifications_when_disabled():
    server = build_server(_runtime(), remote_profile="social", remote_capabilities=_runtime().bot)
    tools = {tool.name: tool for tool in server._tool_manager.list_tools()}
    assert set(tools) == {"cmx_home", "cmx_status", "cmx_search", "cmx_post", "cmx_interact"}
    assert "boost" not in tools["cmx_interact"].parameters["properties"]["action"]["enum"]


def test_request_scope_is_checked_from_current_request_state():
    class State:
        cmx_scopes = [READ_SCOPE]
    class Request:
        state = State()
    class RequestContext:
        request = Request()
    class Context:
        request_context = RequestContext()
    require_request_scope(Context(), READ_SCOPE)
    try:
        require_request_scope(Context(), SOCIAL_SCOPE)
    except PermissionError as exc:
        assert str(exc) == "insufficient_scope"
    else:
        raise AssertionError("missing social scope was accepted")
