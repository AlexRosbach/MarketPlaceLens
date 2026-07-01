from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.auth import hash_password, verify_password
from app.cli import reset_password


class ResetPasswordCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "marketplacelens.db")
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1,
              updated_at TEXT NOT NULL
            );
            """
        )
        self.db.execute(
            """
            INSERT INTO users(username, password_hash, role, enabled, updated_at)
            VALUES (?, ?, 'admin', 0, 'old')
            """,
            ("admin", hash_password("old-password")),
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def test_reset_password_updates_admin_and_enables_account(self) -> None:
        with patch.dict(os.environ, {"MARKETPLACELENS_DB_PATH": self.db_path}):
            reset_password.reset_password("new-password-123")

        row = self.db.execute("SELECT password_hash, enabled, updated_at FROM users WHERE username = 'admin'").fetchone()
        self.assertTrue(verify_password("new-password-123", row["password_hash"]))
        self.assertEqual(row["enabled"], 1)
        self.assertNotEqual(row["updated_at"], "old")

    def test_reset_password_rejects_non_admin_user(self) -> None:
        self.db.execute(
            """
            INSERT INTO users(username, password_hash, role, enabled, updated_at)
            VALUES (?, ?, 'user', 1, 'old')
            """,
            ("buyer", hash_password("old-password")),
        )
        self.db.commit()

        with patch.dict(os.environ, {"MARKETPLACELENS_DB_PATH": self.db_path}):
            with self.assertRaises(SystemExit):
                reset_password.reset_password("new-password-123", username="buyer")


if __name__ == "__main__":
    unittest.main()
