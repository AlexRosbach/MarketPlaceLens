import importlib
import sqlite3
import pytest

def test_local_mcp_user_scope(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE users(id INTEGER, enabled INTEGER);
        CREATE TABLE watch_profiles(id INTEGER, user_id INTEGER, name TEXT, source_type TEXT, enabled INTEGER, last_run_at TEXT);
        INSERT INTO users VALUES(1,1),(2,1);
        INSERT INTO watch_profiles VALUES(1,1,'Owned','html',1,NULL),(2,2,'Other','html',1,NULL);
        """)
    monkeypatch.setenv("MARKETPLACELENS_DB_PATH", str(path))
    monkeypatch.setenv("MARKETPLACELENS_MCP_USER_ID", "1")
    companion = importlib.import_module("app.mcp_companion")
    monkeypatch.setattr(companion, "DB_PATH", path)
    monkeypatch.setattr(companion, "USER_ID", 1)
    assert [job["name"] for job in companion.list_jobs()] == ["Owned"]
    with companion.read_db() as db, pytest.raises(sqlite3.OperationalError):
        db.execute("DELETE FROM watch_profiles")
