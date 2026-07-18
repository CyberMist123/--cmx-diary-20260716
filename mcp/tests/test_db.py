from pathlib import Path

from cmx_mcp.db import Database


def test_sqlite_fts_roundtrip(tmp_path: Path):
    db = Database(tmp_path / "cmx.sqlite3")
    db.initialize()
    db.cache_statuses(
        "gpt",
        [
            {
                "id": "1",
                "account": {"id": "a", "acct": "fable"},
                "text": "hello private world",
                "spoiler_text": "",
                "created_at": "2026-07-17T00:00:00Z",
                "edited_at": None,
                "visibility": "private",
                "in_reply_to_id": None,
            }
        ]
    )
    result = db.search_statuses("gpt", "private", 5)
    assert result[0]["id"] == "1"


def test_status_cache_isolated_by_bot_id(tmp_path: Path):
    db = Database(tmp_path / "cmx.sqlite3")
    db.initialize()
    status = {"id": "same", "account": {"acct": "a"}, "text": "private", "spoiler_text": ""}
    db.cache_statuses("a", [status])
    db.cache_statuses("b", [{**status, "text": "other"}])
    assert db.search_statuses("a", "private", 5)[0]["text"] == "private"
    assert db.search_statuses("b", "private", 5) == []


def test_upsert_bot_round_trips_remote_profile_and_capabilities(tmp_path: Path):
    db = Database(tmp_path / "cmx.sqlite3")
    db.initialize()
    common = {
        "bot_id": "social-bot",
        "display_name": "Social Bot",
        "profile": "resident",
        "media_root": tmp_path / "media",
        "token_ref": "social.token",
        "default_audience": "residents",
        "allow_public": False,
    }
    db.upsert_bot(
        **common,
        remote_profile="social",
        remote_polls=True,
        remote_boosts=False,
        remote_notifications=True,
    )
    created = db.get_bot("social-bot")
    assert created.remote_profile == "social"
    assert created.remote_polls is True
    assert created.remote_boosts is False
    assert created.remote_notifications is True
    assert [(bot.bot_id, bot.remote_profile) for bot in db.list_bots()] == [("social-bot", "social")]

    db.upsert_bot(
        **{**common, "display_name": "Social Plus Bot"},
        remote_profile="social_plus",
        remote_polls=False,
        remote_boosts=True,
        remote_notifications=True,
    )
    updated = db.get_bot("social-bot")
    assert updated.display_name == "Social Plus Bot"
    assert updated.remote_profile == "social_plus"
    assert updated.remote_polls is False
    assert updated.remote_boosts is True
    assert updated.remote_notifications is True
    listed = db.list_bots()
    assert len(listed) == 1
    assert listed[0] == updated


def test_legacy_cache_migrates_without_losing_single_bot_rows(tmp_path: Path):
    path = tmp_path / "legacy.sqlite3"
    import sqlite3

    with sqlite3.connect(path) as raw:
        raw.executescript("""
            CREATE TABLE bots (bot_id TEXT PRIMARY KEY, display_name TEXT, profile TEXT,
                media_root TEXT, token_ref TEXT, default_audience TEXT, allow_public INTEGER,
                enabled INTEGER, created_at INTEGER, updated_at INTEGER);
            INSERT INTO bots VALUES ('gpt','GPT','reader','.', 'token','residents',0,1,1,1);
            CREATE TABLE status_cache (status_id TEXT PRIMARY KEY, author_id TEXT NOT NULL,
                author_acct TEXT NOT NULL, text TEXT NOT NULL, spoiler_text TEXT NOT NULL DEFAULT '',
                created_at TEXT, edited_at TEXT, visibility TEXT, reply_to_id TEXT,
                payload_json TEXT NOT NULL, indexed_at INTEGER NOT NULL);
            INSERT INTO status_cache VALUES ('same','a','acct','legacy','',NULL,NULL,NULL,NULL,'{"id":"same","text":"legacy"}',1);
            CREATE VIRTUAL TABLE status_fts USING fts5(status_id UNINDEXED, author_acct, text, spoiler_text);
        """)
    db = Database(path)
    db.initialize()
    assert db.search_statuses("gpt", "legacy", 5)[0]["id"] == "same"


def test_dedup_claim_is_atomic_and_recoverable(tmp_path: Path):
    db = Database(tmp_path / "cmx.sqlite3")
    db.initialize()
    first = db.claim_dedup(bot_id="a", operation="fake", request_id="r", lease_seconds=60)
    second = db.claim_dedup(bot_id="a", operation="fake", request_id="r", lease_seconds=60)
    assert first["claimed"] is True
    assert second["claimed"] is False
    db.finish_dedup(bot_id="a", operation="fake", request_id="r", response={"id": "1"})
    done = db.claim_dedup(bot_id="a", operation="fake", request_id="r")
    assert done["state"] == "succeeded"
    assert done["response"] == {"id": "1"}
    other_bot = db.claim_dedup(bot_id="b", operation="fake", request_id="r")
    assert other_bot["claimed"] is True


def test_direct_statuses_are_cached_but_not_indexed(tmp_path: Path):
    db = Database(tmp_path / "cmx.sqlite3")
    db.initialize()
    db.cache_statuses("gpt", [{"id": "d", "account": {"acct": "a"}, "text": "secret", "visibility": "direct"}])
    assert db.search_statuses("gpt", "secret", 5) == []
