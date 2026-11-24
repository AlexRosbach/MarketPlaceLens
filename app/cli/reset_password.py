#!/usr/bin/env python3
"""
Reset a MarketPlaceLens admin password directly in the SQLite database.

Usage:
    docker exec -it marketplacelens reset-password
    docker exec marketplacelens reset-password --password "newpassword"
"""
from __future__ import annotations

import argparse
import getpass
import os
import sqlite3
import sys

from app.auth import hash_password
from app.config import settings
from app.database import utc_now


def database_path() -> str:
    return os.environ.get("MARKETPLACELENS_DB_PATH", settings.db_path)


def reset_password(new_password: str, username: str = "admin") -> None:
    if len(new_password) < 8:
        print("ERROR: Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    db_path = database_path()
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT id, username, role
            FROM users
            WHERE username = ? AND role = 'admin'
            """,
            (username,),
        ).fetchone()
        if not row:
            print(f"ERROR: No admin user named '{username}' found in database.", file=sys.stderr)
            sys.exit(1)

        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, enabled = 1, updated_at = ?
            WHERE id = ?
            """,
            (hash_password(new_password), utc_now(), row["id"]),
        )
        conn.commit()
        print("Password reset successfully.")
        print(f"Admin user '{row['username']}' is enabled and can sign in with the new password.")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset a MarketPlaceLens admin password",
        prog="reset-password",
    )
    parser.add_argument(
        "--password",
        help="New password (if not provided, will prompt interactively)",
        default=None,
    )
    parser.add_argument(
        "--username",
        help="Admin username to reset",
        default="admin",
    )
    args = parser.parse_args()

    if args.password:
        new_password = args.password
    else:
        print("Reset MarketPlaceLens Admin Password")
        print("=" * 40)
        new_password = getpass.getpass("New password (min 8 chars): ")
        confirm = getpass.getpass("Confirm new password: ")
        if new_password != confirm:
            print("ERROR: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    reset_password(new_password, args.username)


if __name__ == "__main__":
    main()
