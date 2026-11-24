from __future__ import annotations

import sqlite3
import unittest

from app.connectors import ListingCandidate
from app.main import apply_listing_watchlist_update, refresh_existing_listing_fields, should_auto_assess_new_listing


def candidate() -> ListingCandidate:
    return ListingCandidate(
        source_type="kleinanzeigen",
        source_listing_id="1",
        title="Stuhl",
        price_text="25 EUR VB",
        price_value=25.0,
        location_text="10115 Mitte",
        category_text="Haus & Garten",
        posted_at_text="Heute",
        description_snippet="Massiver Stuhl.",
        listing_url="https://www.kleinanzeigen.de/s-anzeige/stuhl/1",
        thumbnail_url="https://example.test/stuhl.jpg",
        content_hash="hash-with-price",
    )


class ListingRefreshTests(unittest.TestCase):
    def test_contacted_side_effect_can_add_default_watchlist(self) -> None:
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.executescript(
            """
            CREATE TABLE users(id INTEGER PRIMARY KEY, default_watchlist_id INTEGER, updated_at TEXT);
            CREATE TABLE watchlists(id INTEGER PRIMARY KEY, name TEXT, updated_at TEXT);
            CREATE TABLE app_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE listing_watchlists(listing_id INTEGER, watchlist_id INTEGER, created_at TEXT, PRIMARY KEY(listing_id, watchlist_id));
            INSERT INTO watchlists(id, name, updated_at) VALUES (4, 'Default', '');
            INSERT INTO users(id, default_watchlist_id, updated_at) VALUES (1, 4, '');
            """
        )

        watchlisted = apply_listing_watchlist_update(db, 10, True, None, {"id": 1})

        self.assertEqual(watchlisted, 1)
        row = db.execute("SELECT * FROM listing_watchlists WHERE listing_id = 10").fetchone()
        self.assertEqual(row["watchlist_id"], 4)
        db.close()

    def test_duplicate_listing_refreshes_missing_marketplace_fields(self) -> None:
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.execute(
            """
            CREATE TABLE listings(
              price_text TEXT, price_value REAL, location_text TEXT, category_text TEXT,
              posted_at_text TEXT, description_snippet TEXT, thumbnail_url TEXT, content_hash TEXT
            )
            """
        )
        db.execute("INSERT INTO listings VALUES ('', NULL, '', '', '', '', '', 'hash-without-price')")
        existing = db.execute("SELECT * FROM listings").fetchone()
        updates: list[str] = []
        values: list[object] = []

        refresh_existing_listing_fields(existing, candidate(), updates, values)

        self.assertEqual(
            updates,
            [
                "price_text = ?",
                "location_text = ?",
                "category_text = ?",
                "posted_at_text = ?",
                "description_snippet = ?",
                "thumbnail_url = ?",
                "price_value = ?",
                "content_hash = ?",
            ],
        )
        self.assertEqual(values[0], "25 EUR VB")
        self.assertEqual(values[6], 25.0)
        self.assertEqual(values[7], "hash-with-price")
        db.close()

    def test_new_listing_auto_assessment_requires_all_ai_switches(self) -> None:
        self.assertTrue(
            should_auto_assess_new_listing(
                {
                    "ai_enabled": "1",
                    "ai_listing_assessments_enabled": "1",
                    "ai_listing_assessments_new_enabled": "1",
                }
            )
        )
        self.assertFalse(
            should_auto_assess_new_listing(
                {
                    "ai_enabled": "1",
                    "ai_listing_assessments_enabled": "1",
                    "ai_listing_assessments_new_enabled": "0",
                }
            )
        )

    def test_duplicate_listing_keeps_existing_marketplace_fields(self) -> None:
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.execute(
            """
            CREATE TABLE listings(
              price_text TEXT, price_value REAL, location_text TEXT, category_text TEXT,
              posted_at_text TEXT, description_snippet TEXT, thumbnail_url TEXT, content_hash TEXT
            )
            """
        )
        db.execute(
            "INSERT INTO listings VALUES ('10 EUR', 10, 'Hamburg', 'Alt', 'Gestern', 'Alt', 'old.jpg', 'hash-with-price')"
        )
        existing = db.execute("SELECT * FROM listings").fetchone()
        updates: list[str] = []
        values: list[object] = []

        refresh_existing_listing_fields(existing, candidate(), updates, values)

        self.assertEqual(updates, ["price_text = ?", "price_value = ?"])
        self.assertEqual(values, ["25 EUR VB", 25.0])
        db.close()


if __name__ == "__main__":
    unittest.main()
