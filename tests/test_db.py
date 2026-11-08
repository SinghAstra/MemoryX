from app import db
from app.ingest import add_document


def test_add_and_get():
    result = add_document("demo", "User lives in San Francisco.")
    doc = db.get_document(result["id"])
    assert doc is not None
    assert doc.container_tag == "demo"
    assert doc.status == "done"
    assert result["chunks"] == 1


def test_same_custom_id_is_idempotent():
    first = add_document("demo", "User likes tea.", custom_id="c1")
    second = add_document("demo", "User likes tea.", custom_id="c1")
    assert first["id"] == second["id"]
    assert second["created"] is False


def test_changed_custom_id_replaces_chunks():
    first = add_document("demo", "User likes tea.", custom_id="c1")
    second = add_document("demo", "User likes coffee now.", custom_id="c1")
    assert first["id"] == second["id"]
    assert second["created"] is False
    docs = db.list_documents("demo")
    assert len(docs) == 1
    assert "coffee" in docs[0].content


def test_reset_removes_documents():
    add_document("demo", "hello world")
    db.reset_container("demo")
    assert db.list_documents("demo") == []
