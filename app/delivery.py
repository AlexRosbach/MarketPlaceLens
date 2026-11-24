"""Persistent notification queue; at-least-once delivery with bounded retries."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from .database import connect, row_to_listing, row_to_profile, utc_now
from .notifier import TelegramNotifier, WebhookNotifier

log = logging.getLogger(__name__)


def enqueue(db, profile, listing_id, app_settings, reason, event_key="new"):
    channels = []
    if profile.get("notify_telegram") and app_settings.get("telegram_bot_token") and app_settings.get("telegram_chat_id"):
        channels.append("telegram")
    if profile.get("notify_webhook") and app_settings.get("webhook_url"):
        channels.append("webhook")
    for channel in channels:
        db.execute("""INSERT OR IGNORE INTO notification_outbox(listing_id, channel, event_key, reason, next_attempt_at)
                      VALUES (?, ?, ?, ?, ?)""", (listing_id, channel, event_key, reason, utc_now()))


async def deliver_due():
    with connect() as db:
        rows = db.execute("SELECT * FROM notification_outbox WHERE state = 'pending' AND next_attempt_at <= ? ORDER BY next_attempt_at, id LIMIT 10", (utc_now(),)).fetchall()
    for row in rows:
        with connect() as db:
            listing = db.execute("SELECT * FROM listings WHERE id = ?", (row["listing_id"],)).fetchone()
            if not listing:
                continue
            profile = db.execute("SELECT * FROM watch_profiles WHERE id = ?", (listing["profile_id"],)).fetchone()
            values = {r["key"]: r["value"] for r in db.execute("SELECT key, value FROM app_settings")}
        if not profile or not profile["enabled"] or listing["user_hidden"] or listing["status"] == "hidden":
            with connect() as db:
                db.execute("UPDATE notification_outbox SET state = 'cancelled' WHERE id = ?", (row["id"],))
            continue
        try:
            if row["channel"] == "telegram" and profile["notify_telegram"]:
                await TelegramNotifier(values.get("telegram_bot_token", ""), values.get("telegram_chat_id", "")).send_listing(row_to_listing(listing), row_to_profile(profile), row["reason"])
            elif row["channel"] == "webhook" and profile["notify_webhook"]:
                await WebhookNotifier(values.get("webhook_url", "")).send_listing(row_to_listing(listing), row_to_profile(profile), row["reason"])
            else:
                with connect() as db:
                    db.execute("UPDATE notification_outbox SET state = 'cancelled' WHERE id = ?", (row["id"],))
                continue
        except Exception:
            attempts = row["attempts"] + 1
            next_at = (datetime.now(UTC) + timedelta(seconds=min(3600, 30 * 2 ** attempts))).isoformat()
            with connect() as db:
                db.execute("UPDATE notification_outbox SET attempts = ?, state = ?, next_attempt_at = ? WHERE id = ?",
                           (attempts, "failed" if attempts >= 5 else "pending", next_at, row["id"]))
            log.warning("Notification delivery failed (channel %s, attempt %s)", row["channel"], attempts)
        else:
            with connect() as db:
                db.execute("UPDATE notification_outbox SET state = 'delivered', attempts = attempts + 1 WHERE id = ?", (row["id"],))
                db.execute("UPDATE listings SET status = CASE WHEN status = 'new' THEN 'notified' ELSE status END, notified_at = ? WHERE id = ?", (utc_now(), row["listing_id"]))


async def delivery_loop():
    while True:
        try:
            await deliver_due()
        except Exception:
            log.warning("Notification queue processing failed")
        await asyncio.sleep(30)
