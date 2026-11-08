from app import db
from app.ingest import add_document, chunk_text
from app.search import keyword_chunks


def test_keyword_finds_phrase():
    add_document("demo", "User lives in San Francisco.")
    hits = keyword_chunks("demo", "san francisco")
    assert hits
    assert "San Francisco" in hits[0]["content"]


def test_container_isolation():
    add_document("alpha", "User likes tea.")
    assert keyword_chunks("beta", "tea") == []


def test_reset_clears_keyword_index():
    add_document("demo", "User likes tea.")
    db.reset_container("demo")
    assert keyword_chunks("demo", "tea") == []


def test_replacing_content_clears_old_index():
    add_document("demo", "User likes tea.", custom_id="c1")
    add_document("demo", "User likes coffee.", custom_id="c1")
    assert keyword_chunks("demo", "tea") == []
    assert keyword_chunks("demo", "coffee")


def test_punctuation_is_safe():
    add_document("demo", "User's favorite is C++? Yes!")
    hits = keyword_chunks("demo", 'what is "C++"?')
    assert hits


def test_empty_query_returns_nothing():
    add_document("demo", "User likes tea.")
    assert keyword_chunks("demo", "   ") == []


def test_chunking_empty_text():
    assert chunk_text("   ") == []


def test_chunking_splits_long_text():
    chunks = chunk_text("word " * 100, max_chars=100, overlap=10)
    assert len(chunks) > 1
    assert all(chunks)
