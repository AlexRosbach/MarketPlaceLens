"""Explicit operator maintenance commands; safe defaults and dry-run retention."""
import argparse
import os
import sqlite3
from pathlib import Path
from datetime import UTC, datetime, timedelta

from app.config import settings

def backup(destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with sqlite3.connect(settings.db_path) as source, sqlite3.connect(destination) as target:
            source.backup(target)
            if target.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup verification failed")
    except Exception:
        destination.unlink(missing_ok=True)
        raise

def cleanup(days: int, apply: bool):
    if days < 30:
        raise ValueError("Retention must be at least 30 days")
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    with sqlite3.connect(settings.db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")
        queries = [
            ("listings", "last_seen_at < ? AND watchlisted = 0 AND contacted = 0 AND status IN ('seen','hidden') AND target_price IS NULL AND NOT EXISTS (SELECT 1 FROM listing_watchlists w WHERE w.listing_id = listings.id)"),
            ("run_logs", "finished_at < ?"),
        ]
        for table, condition in queries:
            count = db.execute(f"SELECT COUNT(*) FROM {table} WHERE {condition}", (cutoff,)).fetchone()[0]
            print(f"{table}: {count} eligible")
            if apply:
                db.execute(f"DELETE FROM {table} WHERE {condition}", (cutoff,))

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("backup")
    b.add_argument("destination", type=Path)
    c = sub.add_parser("cleanup")
    c.add_argument("--days", type=int, default=180)
    c.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.command == "backup":
        backup(args.destination)
    else:
        cleanup(args.days, args.apply)

if __name__ == "__main__":
    main()
