"""Optional local stdio MCP server, read-only and restricted to one user.

Run with the optional official MCP Python SDK installed. This is NOT an HTTP
server; local process/OS access is the trust boundary.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MarketPlaceLens")
USER_ID = int(os.environ["MARKETPLACELENS_MCP_USER_ID"])
DB_PATH = Path(os.environ["MARKETPLACELENS_DB_PATH"]).resolve()


@contextmanager
def read_db():
    db = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only = ON")
        if not db.execute("SELECT id FROM users WHERE id = ? AND enabled = 1", (USER_ID,)).fetchone():
            raise RuntimeError("Configured user is unavailable")
        yield db
    finally:
        db.close()


@mcp.tool()
def list_jobs(limit: int = 50) -> list[dict]:
    """List the configured user's search jobs without credentials or search URLs."""
    with read_db() as db:
        return [dict(row) for row in db.execute(
            "SELECT id, name, source_type, enabled, last_run_at FROM watch_profiles WHERE user_id = ? ORDER BY id LIMIT ?",
            (USER_ID, max(1, min(limit, 100))))]


@mcp.tool()
def list_listings(query: str = "", watchlisted: bool = False, limit: int = 30) -> list[dict]:
    """Search owned marketplace listings or watchlisted items (read only)."""
    with read_db() as db:
        return [dict(row) for row in db.execute(
            """SELECT l.id, l.title, l.source_type, l.price_value, l.price_text, l.status,
                      l.availability_status, l.first_seen_at, l.watchlisted
               FROM listings l JOIN watch_profiles p ON p.id = l.profile_id
               WHERE p.user_id = ? AND l.user_hidden = 0 AND l.title LIKE ?
                 AND (? = 0 OR l.watchlisted = 1)
               ORDER BY l.first_seen_at DESC LIMIT ?""",
            (USER_ID, "%" + query[:120] + "%", int(watchlisted), max(1, min(limit, 100))))]


@mcp.tool()
def price_history(listing_id: int) -> list[dict]:
    """Return observed marketplace prices for one owned listing."""
    with read_db() as db:
        return [dict(row) for row in db.execute(
            """SELECT h.price_value, h.observed_at FROM listing_price_history h
               JOIN listings l ON l.id = h.listing_id JOIN watch_profiles p ON p.id = l.profile_id
               WHERE l.id = ? AND p.user_id = ? ORDER BY h.observed_at DESC LIMIT 100""",
            (listing_id, USER_ID))]


if __name__ == "__main__":
    mcp.run(transport="stdio")
