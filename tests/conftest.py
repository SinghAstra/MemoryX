import pytest

from app import db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db.connect(tmp_path / "test.db")
    yield
    db.close()
