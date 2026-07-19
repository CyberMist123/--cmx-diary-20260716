from cmx_mcp.compact import strip_html, timeline_preview


def test_strip_html_preserves_paragraphs():
    assert strip_html("<p>one<br>two</p><p>three</p>") == "one\ntwo\nthree"


def test_timeline_preview_is_sparse_normalized_and_bounded():
    raw = {"id": "wrapper", "reblog": {"id": "source", "content": "<p>Hello\n   world " + "界" * 80 + "</p>",
           "account": {"id": "secret", "acct": "alice", "display_name": "Alice"},
           "replies_count": 4, "media_attachments": [{"url": "secret"}, {"url": "secret2"}],
           "created_at": "secret", "visibility": "private"}}
    result = timeline_preview(raw, 50)
    assert set(result) == {"id", "author", "preview", "replies", "media"}
    assert result["id"] == "source"
    assert result["preview"].startswith("Hello world")
    assert len(result["preview"]) <= 50
    assert result["replies"] == 4 and result["media"] == 2


def test_timeline_preview_omits_zero_replies_and_media():
    assert timeline_preview({"id": "1", "content": "ok", "account": {"acct": "a"}}) == {
        "id": "1", "author": "a", "preview": "ok"
    }
