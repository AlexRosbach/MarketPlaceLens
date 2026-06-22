from __future__ import annotations

import asyncio
import ipaddress
import json
import random
import sqlite3
import time
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .auth import COOKIE_NAME, create_session, current_user_from_session, hash_password, valid_credentials
from .config import settings
from .connectors import ListingCandidate, facebook_browser_headers, get_connector, is_non_listing_artifact, parse_listing_availability, safe_cookie_header, validate_public_fetch_host
from .database import connect, encode_list, ensure_default_watchlist, init_db, row_to_listing, row_to_profile, utc_now
from .filters import FilterResult, apply_filters
from .notifier import TelegramNotifier, WebhookNotifier
from .schemas import AccountProfilePayload, InquiryPayload, ListingStatusPayload, LoginPayload, PasswordPayload, ProfilePayload, SearchDraftPayload, SettingsPayload, SetupPayload, UserPayload, UserUpdatePayload, WatchlistPayload
from .version import APP_VERSION, version_payload

app = FastAPI(title="MarketPlaceLens", version=APP_VERSION)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
open_check_state = {"running": False, "last_started": 0.0}
open_check_lock = asyncio.Lock()


@app.middleware("http")
async def require_session(request: Request, call_next):
    path = request.url.path
    public = path.startswith("/static/") or path in {"/setup", "/api/setup", "/api/setup/status", "/login", "/api/auth/login", "/api/auth/status", "/api/version"}
    if setup_required() and path not in {"/setup", "/api/setup", "/api/setup/status", "/api/version"} and not path.startswith("/static/"):
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Initial setup required"}, status_code=423)
        return RedirectResponse("/setup", status_code=303)
    user = current_user_from_session(request.cookies.get(COOKIE_NAME))
    request.state.user = user
    if public or user:
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    if settings.poll_enabled:
        asyncio.create_task(poll_loop())


def static_page_response(filename: str) -> HTMLResponse:
    html = (static_dir / filename).read_text(encoding="utf-8")
    html = html.replace("__ASSET_VERSION__", version_payload().get("build_code") or APP_VERSION)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@app.get("/")
async def index() -> HTMLResponse:
    return static_page_response("index.html")


@app.get("/login")
async def login_page() -> HTMLResponse:
    return static_page_response("login.html")


@app.get("/setup")
async def setup_page() -> HTMLResponse:
    return static_page_response("setup.html")


@app.get("/api/setup/status")
async def setup_status() -> dict[str, bool]:
    return {"required": setup_required()}


@app.post("/api/setup")
async def setup(payload: SetupPayload) -> dict[str, bool]:
    if not setup_required():
        raise HTTPException(400, "Initial setup is already complete")
    now = utc_now()
    username = payload.username.strip()
    if not username:
        raise HTTPException(400, "Username is required")
    with connect() as db:
        row = db.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1").fetchone()
        if row:
            db.execute(
                """
                UPDATE users
                SET username = ?, password_hash = ?, role = 'admin', enabled = 1, updated_at = ?
                WHERE id = ?
                """,
                (username, hash_password(payload.password), now, row["id"]),
            )
        else:
            try:
                db.execute(
                    """
                    INSERT INTO users(username, password_hash, role, enabled, created_at, updated_at)
                    VALUES (?, ?, 'admin', 1, ?, ?)
                    """,
                    (username, hash_password(payload.password), now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise HTTPException(409, "User already exists") from exc
        db.execute(
            "INSERT INTO app_settings(key, value) VALUES ('setup_complete', '1') ON CONFLICT(key) DO UPDATE SET value = '1'"
        )
    return {"ok": True}


@app.post("/api/auth/login")
async def login(payload: LoginPayload, response: Response) -> dict[str, bool]:
    if not valid_credentials(payload.username, payload.password):
        raise HTTPException(401, "Invalid login")
    with connect() as db:
        db.execute("UPDATE users SET last_login_at = ? WHERE username = ?", (utc_now(), payload.username))
    response.set_cookie(
        COOKIE_NAME,
        create_session(payload.username),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return {"ok": True}


@app.post("/api/auth/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/api/auth/status")
async def auth_status(request: Request) -> dict[str, Any]:
    user = current_user_from_session(request.cookies.get(COOKIE_NAME))
    return {"authenticated": bool(user), "user": safe_user(user) if user else None}


@app.get("/api/version")
async def app_version() -> dict[str, str]:
    return version_payload()


def request_user(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


def require_admin(request: Request) -> dict[str, Any]:
    user = request_user(request)
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin role required")
    return user


def safe_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "enabled": bool(user["enabled"]),
        "display_name": user.get("display_name", ""),
        "buyer_location": user.get("buyer_location", ""),
        "contact_hint": user.get("contact_hint", ""),
        "inquiry_signature": user.get("inquiry_signature", ""),
    }


def setup_required() -> bool:
    try:
        with connect() as db:
            admin = db.execute("SELECT username FROM users WHERE role = 'admin' ORDER BY id LIMIT 1").fetchone()
            setup_row = db.execute("SELECT value FROM app_settings WHERE key = 'setup_complete'").fetchone()
    except Exception:
        return False
    if not admin:
        return True
    if setup_row and setup_row["value"] == "1":
        return False
    return valid_credentials(admin["username"], "admin")


@app.get("/api/users")
async def list_users(request: Request) -> list[dict[str, Any]]:
    require_admin(request)
    with connect() as db:
        rows = db.execute(
            """
            SELECT id, username, role, enabled, created_at, updated_at, last_login_at
            FROM users
            ORDER BY role ASC, username COLLATE NOCASE
            """
        ).fetchall()
    return [{**dict(row), "enabled": bool(row["enabled"])} for row in rows]


@app.post("/api/users")
async def create_user(payload: UserPayload, request: Request) -> dict[str, Any]:
    require_admin(request)
    now = utc_now()
    username = payload.username.strip()
    if not username:
        raise HTTPException(400, "Username is required")
    with connect() as db:
        try:
            cursor = db.execute(
                """
                INSERT INTO users(username, password_hash, role, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, hash_password(payload.password), payload.role, int(payload.enabled), now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "User already exists") from exc
        row = db.execute(
            "SELECT id, username, role, enabled, created_at, updated_at, last_login_at FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return {**dict(row), "enabled": bool(row["enabled"])}


@app.patch("/api/users/{user_id}")
async def update_user(user_id: int, payload: UserUpdatePayload, request: Request) -> dict[str, Any]:
    require_admin(request)
    now = utc_now()
    with connect() as db:
        row = db.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if row["role"] == "admin" and payload.role != "admin" and count_enabled_admins(db) <= 1:
            raise HTTPException(400, "At least one admin must remain")
        if row["role"] == "admin" and not payload.enabled and count_enabled_admins(db) <= 1:
            raise HTTPException(400, "At least one admin must remain")
        updates = ["role = ?", "enabled = ?", "updated_at = ?"]
        values: list[Any] = [payload.role, int(payload.enabled), now]
        if payload.password:
            if len(payload.password) < 8:
                raise HTTPException(400, "Password must be at least 8 characters")
            updates.append("password_hash = ?")
            values.append(hash_password(payload.password))
        values.append(user_id)
        db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
        updated = db.execute(
            "SELECT id, username, role, enabled, created_at, updated_at, last_login_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return {**dict(updated), "enabled": bool(updated["enabled"])}


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, request: Request) -> dict[str, bool]:
    require_admin(request)
    with connect() as db:
        row = db.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if row["role"] == "admin" and count_enabled_admins(db) <= 1:
            raise HTTPException(400, "At least one admin must remain")
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return {"ok": True}


@app.get("/api/summary")
async def summary(request: Request) -> dict[str, Any]:
    user = request_user(request)
    profile_clause, profile_values_for_user = profile_owner_filter(user, "watch_profiles")
    profile_where = f"WHERE {profile_clause}" if profile_clause else ""
    listing_clause, listing_values_for_user = profile_owner_filter(user, "watch_profiles")
    listing_where = f"WHERE {listing_clause}" if listing_clause else ""
    runs_where = f"WHERE {profile_clause}" if profile_clause else ""
    with connect() as db:
        profiles = db.execute(
            f"SELECT COUNT(*) total, SUM(enabled) enabled FROM watch_profiles {profile_where}",
            profile_values_for_user,
        ).fetchone()
        listings = db.execute(
            f"""
            SELECT
              COUNT(*) total,
              SUM(status = 'new') new_count,
              SUM(status = 'hidden') hidden_count,
              SUM(status = 'notified') notified_count,
              SUM(watchlisted = 1) watchlisted_count
            FROM listings
            JOIN watch_profiles ON watch_profiles.id = listings.profile_id
            {listing_where}
            """
            ,
            listing_values_for_user,
        ).fetchone()
        recent_runs = db.execute(
            f"""
            SELECT run_logs.*, watch_profiles.enabled
            FROM run_logs
            LEFT JOIN watch_profiles ON watch_profiles.id = run_logs.profile_id
            {runs_where}
            ORDER BY finished_at DESC
            LIMIT 5
            """,
            profile_values_for_user,
        ).fetchall()
        error_clause = "run_logs.status = 'error'"
        if profile_clause:
            error_clause += f" AND {profile_clause}"
        errors = db.execute(
            f"""
            SELECT COUNT(*) count
            FROM run_logs
            LEFT JOIN watch_profiles ON watch_profiles.id = run_logs.profile_id
            WHERE {error_clause}
            """,
            profile_values_for_user,
        ).fetchone()
        source_counts = db.execute(
            f"""
            SELECT watch_profiles.source_type,
                   COUNT(DISTINCT watch_profiles.id) profile_count,
                   COUNT(listings.id) listing_count
            FROM watch_profiles
            LEFT JOIN listings ON listings.profile_id = watch_profiles.id
            {listing_where}
            GROUP BY watch_profiles.source_type
            ORDER BY profile_count DESC, listing_count DESC
            """,
            listing_values_for_user,
        ).fetchall()
    return {
        "profiles_total": profiles["total"] or 0,
        "profiles_enabled": profiles["enabled"] or 0,
        "listings_total": listings["total"] or 0,
        "listings_new": listings["new_count"] or 0,
        "listings_hidden": listings["hidden_count"] or 0,
        "listings_notified": listings["notified_count"] or 0,
        "listings_watchlisted": listings["watchlisted_count"] or 0,
        "run_errors": errors["count"] or 0,
        "recent_runs": [dict(row) for row in recent_runs],
        "source_counts": [dict(row) for row in source_counts],
    }


@app.delete("/api/run-logs/errors")
async def clear_run_errors(request: Request) -> dict[str, int]:
    require_admin(request)
    with connect() as db:
        cursor = db.execute("DELETE FROM run_logs WHERE status = 'error'")
    return {"deleted": cursor.rowcount}


@app.delete("/api/run-logs/{run_id}")
async def delete_run_error(run_id: int, request: Request) -> dict[str, bool]:
    require_admin(request)
    with connect() as db:
        row = db.execute("SELECT id, status FROM run_logs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Run log not found")
        if row["status"] != "error":
            raise HTTPException(400, "Only error run logs can be deleted")
        db.execute("DELETE FROM run_logs WHERE id = ?", (run_id,))
    return {"ok": True}


@app.get("/api/profiles")
async def list_profiles(request: Request) -> list[dict[str, Any]]:
    user = request_user(request)
    owner_clause, values = profile_owner_filter(user)
    where = f"WHERE {owner_clause}" if owner_clause else ""
    with connect() as db:
        rows = db.execute(f"SELECT * FROM watch_profiles {where} ORDER BY updated_at DESC", values).fetchall()
    return [row_to_profile(row) for row in rows]


@app.post("/api/profiles")
async def create_profile(payload: ProfilePayload, request: Request) -> dict[str, Any]:
    user = request_user(request)
    now = utc_now()
    profile = payload.model_dump()
    profile["search_url"] = str(profile["search_url"])
    profile["poll_interval_minutes"] = max(settings.min_poll_minutes, profile["poll_interval_minutes"])
    validate_profile_search_url(profile)
    with connect() as db:
        cursor = db.execute(
            """
            INSERT INTO watch_profiles(
              name, enabled, source_type, search_url, poll_interval_minutes,
              include_keywords, exclude_keywords, required_keywords, excluded_categories,
              min_price, max_price, max_listing_age_days, location_hint, notify_telegram, notify_webhook, user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            profile_values(profile, now, user["id"]),
        )
        row = db.execute("SELECT * FROM watch_profiles WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_profile(row)


@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: int, payload: ProfilePayload, request: Request) -> dict[str, Any]:
    user = request_user(request)
    now = utc_now()
    profile = payload.model_dump()
    profile["search_url"] = str(profile["search_url"])
    profile["poll_interval_minutes"] = max(settings.min_poll_minutes, profile["poll_interval_minutes"])
    validate_profile_search_url(profile)
    with connect() as db:
        if not can_access_profile(db, profile_id, user):
            raise HTTPException(404, "Profile not found")
        db.execute(
            """
            UPDATE watch_profiles SET
              name = ?, enabled = ?, source_type = ?, search_url = ?, poll_interval_minutes = ?,
              include_keywords = ?, exclude_keywords = ?, required_keywords = ?, excluded_categories = ?,
              min_price = ?, max_price = ?, max_listing_age_days = ?, location_hint = ?, notify_telegram = ?, notify_webhook = ?, updated_at = ?
            WHERE id = ?
            """,
            profile_values(profile, now, include_created=False) + (profile_id,),
        )
        row = db.execute("SELECT * FROM watch_profiles WHERE id = ?", (profile_id,)).fetchone()
        if row:
            reapply_profile_filters(db, profile_id, row_to_profile(row))
    if not row:
        raise HTTPException(404, "Profile not found")
    return row_to_profile(row)


@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: int, request: Request) -> dict[str, bool]:
    user = request_user(request)
    with connect() as db:
        if not can_access_profile(db, profile_id, user):
            raise HTTPException(404, "Profile not found")
        cursor = db.execute("DELETE FROM watch_profiles WHERE id = ?", (profile_id,))
    if cursor.rowcount == 0:
        raise HTTPException(404, "Profile not found")
    return {"ok": True}


@app.post("/api/profiles/{profile_id}/run")
async def run_profile_endpoint(profile_id: int, request: Request) -> dict[str, Any]:
    user = request_user(request)
    with connect() as db:
        if not can_access_profile(db, profile_id, user):
            raise HTTPException(404, "Profile not found")
    return await run_profile(profile_id)


@app.post("/api/profiles/open-check")
async def trigger_open_check(request: Request) -> dict[str, Any]:
    if getattr(request.state, "user", None) and request.state.user.get("role") != "admin":
        return {"started": False, "reason": "admin_only"}
    async with open_check_lock:
        now = time.monotonic()
        if open_check_state["running"]:
            return {"started": False, "reason": "already_running"}
        if now - float(open_check_state["last_started"]) < 300:
            return {"started": False, "reason": "recently_started"}
        open_check_state["running"] = True
        open_check_state["last_started"] = now
    asyncio.create_task(run_open_check())
    return {"started": True}


@app.get("/api/watchlists")
async def list_watchlists(request: Request) -> list[dict[str, Any]]:
    request_user(request)
    with connect() as db:
        rows = db.execute(
            """
            SELECT watchlists.*, COUNT(listing_watchlists.listing_id) listing_count
            FROM watchlists
            LEFT JOIN listing_watchlists ON listing_watchlists.watchlist_id = watchlists.id
            GROUP BY watchlists.id
            ORDER BY watchlists.updated_at DESC, watchlists.id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/watchlists")
async def create_watchlist(payload: WatchlistPayload, request: Request) -> dict[str, Any]:
    request_user(request)
    now = utc_now()
    name = payload.name.strip()
    with connect() as db:
        try:
            cursor = db.execute(
                "INSERT INTO watchlists(name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Watchlist already exists") from exc
        row = db.execute(
            """
            SELECT watchlists.*, 0 listing_count
            FROM watchlists
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


@app.get("/api/listings")
async def list_listings(
    request: Request,
    profile_id: int | None = None,
    status: str | None = None,
    watchlisted: bool | None = None,
    include_hidden: bool = True,
    q: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "date_desc",
    limit: int = 300,
    offset: int = 0,
    paged: bool = False,
) -> list[dict[str, Any]] | dict[str, Any]:
    user = request_user(request)
    clauses: list[str] = []
    values: list[Any] = []
    owner_clause, owner_values = profile_owner_filter(user, "watch_profiles")
    if owner_clause:
        clauses.append(owner_clause)
        values.extend(owner_values)
    if profile_id:
        clauses.append("profile_id = ?")
        values.append(profile_id)
    if status:
        clauses.append("status = ?")
        values.append(status)
    elif not include_hidden:
        clauses.append("status NOT IN ('hidden', 'seen')")
    if watchlisted is not None:
        clauses.append("watchlisted = ?")
        values.append(int(watchlisted))
    if q:
        clauses.append("(listings.title LIKE ? OR listings.description_snippet LIKE ? OR listings.location_text LIKE ? OR listings.category_text LIKE ?)")
        like = f"%{q}%"
        values.extend([like, like, like, like])
    if min_price is not None:
        clauses.append("(price_value IS NULL OR price_value >= ?)")
        values.append(min_price)
    if max_price is not None:
        clauses.append("(price_value IS NULL OR price_value <= ?)")
        values.append(max_price)
    clauses.append(
        """
        NOT (
          listings.source_type = 'kleinanzeigen'
          AND (
            lower(listings.title) LIKE '%passwort vergessen%'
            OR lower(listings.listing_url) LIKE '%passwort-vergessen%'
            OR lower(listings.listing_url) LIKE '%/m-passwort%'
            OR lower(listings.title) LIKE '%erstelle ein konto%'
            OR lower(listings.title) LIKE '%konto erstellen%'
            OR lower(listings.title) LIKE '%registrieren%'
            OR lower(listings.listing_url) LIKE '%konto-erstellen%'
            OR lower(listings.listing_url) LIKE '%registrieren%'
            OR lower(listings.listing_url) LIKE '%/m-benutzer-anmeldung%'
          )
        )
        """
    )
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order_by = {
        "price_asc": "price_value IS NULL, price_value ASC, first_seen_at DESC",
        "price_desc": "price_value IS NULL, price_value DESC, first_seen_at DESC",
        "score_desc": "score DESC, first_seen_at DESC",
        "date_desc": "first_seen_at DESC",
    }.get(sort, "first_seen_at DESC")
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    with connect() as db:
        total = db.execute(
            f"""
            SELECT COUNT(*) count
            FROM listings
            JOIN watch_profiles ON watch_profiles.id = listings.profile_id
            {where}
            """,
            values,
        ).fetchone()["count"]
        rows = db.execute(
            f"""
            SELECT listings.*, watch_profiles.name profile_name
            FROM listings
            JOIN watch_profiles ON watch_profiles.id = listings.profile_id
            {where}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            values + [limit, offset],
        ).fetchall()
    items = attach_watchlists(db_listing_rows_to_items(rows))
    if paged:
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    return items


@app.patch("/api/listings/{listing_id}")
async def update_listing_status(listing_id: int, payload: ListingStatusPayload, request: Request) -> dict[str, Any]:
    user = request_user(request)
    with connect() as db:
        if not can_access_listing(db, listing_id, user):
            raise HTTPException(404, "Listing not found")
        updates: list[str] = []
        values: list[Any] = []
        if payload.status is not None:
            updates.append("status = ?")
            values.append(payload.status)
            updates.append("user_hidden = ?")
            values.append(1 if payload.status == "hidden" else 0)
            if payload.status == "hidden":
                updates.append("filter_reason = ?")
                values.append("")
        watchlisted_update: int | None = None
        if payload.watchlisted is not None:
            watchlisted_update = apply_listing_watchlist_update(
                db,
                listing_id,
                payload.watchlisted,
                payload.watchlist_id,
                user,
            )
        if payload.contacted is not None:
            updates.append("contacted = ?")
            values.append(int(payload.contacted))
            if payload.contacted:
                watchlisted_update = apply_listing_watchlist_update(db, listing_id, True, payload.watchlist_id, user)
        if watchlisted_update is not None:
            updates.append("watchlisted = ?")
            values.append(watchlisted_update)
        if not updates:
            raise HTTPException(400, "No listing changes supplied")
        values.append(listing_id)
        db.execute(f"UPDATE listings SET {', '.join(updates)} WHERE id = ?", values)
        row = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Listing not found")
    return attach_watchlists([row_to_listing(row)])[0]


@app.get("/api/listings/{listing_id}/image")
async def listing_image(listing_id: int, request: Request) -> Response:
    user = request_user(request)
    with connect() as db:
        if not can_access_listing(db, listing_id, user):
            raise HTTPException(404, "Listing not found")
        row = db.execute("SELECT thumbnail_url FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Listing not found")
    image_url = row["thumbnail_url"]
    if not image_url:
        raise HTTPException(404, "Listing has no image")
    validate_remote_image_url(image_url)
    parsed = urlparse(image_url)
    async with httpx.AsyncClient(
        headers={
            "User-Agent": settings.user_agent,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": f"{parsed.scheme}://{parsed.netloc}/",
        },
        follow_redirects=True,
        timeout=20.0,
    ) as client:
        response = await client.get(image_url)
        response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        raise HTTPException(502, "Remote URL did not return an image")
    if len(response.content) > 5 * 1024 * 1024:
        raise HTTPException(502, "Remote image is too large")
    return Response(content=response.content, media_type=content_type)


@app.post("/api/listings/{listing_id}/inquiry")
async def generate_listing_inquiry(listing_id: int, payload: InquiryPayload, request: Request) -> dict[str, str]:
    user = request_user(request)
    with connect() as db:
        if not can_access_listing(db, listing_id, user):
            raise HTTPException(404, "Listing not found")
        listing_row = db.execute(
            """
            SELECT listings.*, watch_profiles.name profile_name
            FROM listings
            JOIN watch_profiles ON watch_profiles.id = listings.profile_id
            WHERE listings.id = ?
            """,
            (listing_id,),
        ).fetchone()
        settings_rows = db.execute("SELECT key, value FROM app_settings").fetchall()
        account_row = db.execute(
            "SELECT display_name, buyer_location, contact_hint, inquiry_signature FROM users WHERE id = ?",
            (user["id"],),
        ).fetchone()
    if not listing_row:
        raise HTTPException(404, "Listing not found")
    app_settings = {item["key"]: item["value"] for item in settings_rows}
    if app_settings.get("ai_enabled") != "1":
        raise HTTPException(400, "AI inquiry generation is not enabled")
    listing = row_to_listing(listing_row)
    account_profile = dict(account_row) if account_row else {}
    prompt = inquiry_prompt(listing, app_settings.get("ai_tone", "normal"), payload.language, account_profile)
    text = await generate_ai_text(app_settings, prompt)
    return {"text": normalize_inquiry_text(text, account_profile)}


@app.post("/api/listings/{listing_id}/assessment")
async def generate_listing_assessment(listing_id: int, request: Request) -> dict[str, str]:
    user = request_user(request)
    with connect() as db:
        if not can_access_listing(db, listing_id, user):
            raise HTTPException(404, "Listing not found")
        listing_row = db.execute(
            """
            SELECT listings.*, watch_profiles.name profile_name
            FROM listings
            JOIN watch_profiles ON watch_profiles.id = listings.profile_id
            WHERE listings.id = ?
            """,
            (listing_id,),
        ).fetchone()
        settings_rows = db.execute("SELECT key, value FROM app_settings").fetchall()
    if not listing_row:
        raise HTTPException(404, "Listing not found")
    app_settings = {item["key"]: item["value"] for item in settings_rows}
    if app_settings.get("ai_enabled") != "1":
        raise HTTPException(400, "AI features are not enabled")
    if app_settings.get("ai_listing_assessments_enabled") != "1":
        raise HTTPException(400, "AI listing assessments are not enabled")
    listing = row_to_listing(listing_row)
    text = await generate_ai_text(app_settings, listing_assessment_prompt(listing), max_tokens=180)
    assessed_at = utc_now()
    cleaned = text.strip()
    with connect() as db:
        db.execute(
            "UPDATE listings SET ai_assessment_text = ?, ai_assessed_at = ? WHERE id = ?",
            (cleaned, assessed_at, listing_id),
        )
    return {"text": cleaned, "assessed_at": assessed_at}


@app.post("/api/ai/search-draft")
async def generate_search_draft(payload: SearchDraftPayload, request: Request) -> dict[str, Any]:
    request_user(request)
    with connect() as db:
        settings_rows = db.execute("SELECT key, value FROM app_settings").fetchall()
    app_settings = {item["key"]: item["value"] for item in settings_rows}
    if app_settings.get("ai_enabled") != "1":
        raise HTTPException(400, "AI features are not enabled")
    text = await generate_ai_text(app_settings, search_draft_prompt(payload.prompt, payload.language), max_tokens=420)
    return normalize_search_draft(text)


@app.post("/api/ai/test")
async def test_ai_provider(request: Request) -> dict[str, str]:
    require_admin(request)
    with connect() as db:
        settings_rows = db.execute("SELECT key, value FROM app_settings").fetchall()
    app_settings = {item["key"]: item["value"] for item in settings_rows}
    text = await generate_ai_text(
        app_settings,
        [
            {"role": "system", "content": "Return exactly the word OK and nothing else."},
            {"role": "user", "content": "OK"},
        ],
        max_tokens=20,
    )
    return {"text": text.strip()[:200]}


@app.get("/api/settings")
async def get_settings(request: Request) -> dict[str, Any]:
    user = request_user(request)
    with connect() as db:
        rows = db.execute("SELECT key, value FROM app_settings").fetchall()
        default_watchlist_id = normalized_user_default_watchlist_id(db, user)
    values = {row["key"]: row["value"] for row in rows}
    return {
        "telegram_bot_token": mask_secret(values.get("telegram_bot_token", "")),
        "telegram_bot_token_set": bool(values.get("telegram_bot_token")),
        "telegram_chat_id": values.get("telegram_chat_id", ""),
        "webhook_url": values.get("webhook_url", ""),
        "webhook_url_set": bool(values.get("webhook_url")),
        "global_rate_limit_seconds": int(values.get("global_rate_limit_seconds", "20") or 20),
        "default_watchlist_id": default_watchlist_id,
        "ai_enabled": values.get("ai_enabled", "0") == "1",
        "ai_listing_assessments_enabled": values.get("ai_listing_assessments_enabled", "0") == "1",
        "ai_listing_assessments_auto_enabled": values.get("ai_listing_assessments_auto_enabled", "0") == "1",
        "ai_listing_assessments_new_enabled": values.get("ai_listing_assessments_new_enabled", "0") == "1",
        "ai_provider": values.get("ai_provider", "openai") or "openai",
        "ai_api_key": mask_secret(values.get("ai_api_key", "")),
        "ai_api_key_set": bool(values.get("ai_api_key")),
        "ai_base_url": values.get("ai_base_url", ""),
        "ai_model": values.get("ai_model", "gpt-4o-mini") or "gpt-4o-mini",
        "ai_tone": values.get("ai_tone", "normal") or "normal",
        "facebook_cookie_header": mask_secret(values.get("facebook_cookie_header", "")),
        "facebook_cookie_header_set": bool(values.get("facebook_cookie_header")),
    }


@app.put("/api/settings")
async def update_settings(payload: SettingsPayload, request: Request) -> dict[str, Any]:
    user = request_user(request)
    with connect() as db:
        user_default_id = valid_watchlist_id(db, payload.default_watchlist_id)
        db.execute("UPDATE users SET default_watchlist_id = ?, updated_at = ? WHERE id = ?", (user_default_id, utc_now(), user["id"]))
        if user.get("role") == "admin":
            current_token = get_setting(db, "telegram_bot_token")
            current_ai_key = get_setting(db, "ai_api_key")
            current_facebook_cookie = get_setting(db, "facebook_cookie_header")
            values = {
                "telegram_bot_token": current_token if payload.telegram_bot_token == "********" else payload.telegram_bot_token,
                "telegram_chat_id": payload.telegram_chat_id,
                "webhook_url": payload.webhook_url,
                "global_rate_limit_seconds": str(payload.global_rate_limit_seconds),
                "ai_enabled": "1" if payload.ai_enabled else "0",
                "ai_listing_assessments_enabled": "1" if payload.ai_listing_assessments_enabled else "0",
                "ai_listing_assessments_auto_enabled": "1" if payload.ai_listing_assessments_auto_enabled else "0",
                "ai_listing_assessments_new_enabled": "1" if payload.ai_listing_assessments_new_enabled else "0",
                "ai_provider": payload.ai_provider,
                "ai_api_key": current_ai_key if payload.ai_api_key == "********" else payload.ai_api_key,
                "ai_base_url": payload.ai_base_url.strip(),
                "ai_model": payload.ai_model.strip(),
                "ai_tone": payload.ai_tone,
                "facebook_cookie_header": current_facebook_cookie if payload.facebook_cookie_header == "********" else safe_cookie_header(payload.facebook_cookie_header),
            }
            for key, value in values.items():
                db.execute(
                    "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, value),
                )
    return await get_settings(request)


@app.post("/api/settings/password")
async def update_password(payload: PasswordPayload, request: Request) -> dict[str, bool]:
    user = request_user(request)
    if not valid_credentials(user["username"], payload.current_password):
        raise HTTPException(401, "Current password is incorrect")
    with connect() as db:
        db.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (hash_password(payload.new_password), utc_now(), user["id"]),
        )
    return {"ok": True}


@app.get("/api/account")
async def get_account_profile(request: Request) -> dict[str, str]:
    user = request_user(request)
    with connect() as db:
        row = db.execute(
            "SELECT display_name, buyer_location, contact_hint, inquiry_signature FROM users WHERE id = ?",
            (user["id"],),
        ).fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    return dict(row)


@app.put("/api/account")
async def update_account_profile(payload: AccountProfilePayload, request: Request) -> dict[str, str]:
    user = request_user(request)
    values = {
        "display_name": payload.display_name.strip(),
        "buyer_location": payload.buyer_location.strip(),
        "contact_hint": payload.contact_hint.strip(),
        "inquiry_signature": payload.inquiry_signature.strip(),
    }
    with connect() as db:
        db.execute(
            """
            UPDATE users
            SET display_name = ?, buyer_location = ?, contact_hint = ?, inquiry_signature = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                values["display_name"],
                values["buyer_location"],
                values["contact_hint"],
                values["inquiry_signature"],
                utc_now(),
                user["id"],
            ),
        )
    return values


@app.post("/api/settings/telegram/test")
async def test_telegram(request: Request) -> dict[str, bool]:
    require_admin(request)
    with connect() as db:
        notifier = TelegramNotifier(get_setting(db, "telegram_bot_token"), get_setting(db, "telegram_chat_id"))
    await notifier.send_text("MarketPlaceLens Telegram test successful.")
    return {"ok": True}


@app.post("/api/settings/webhook/test")
async def test_webhook(request: Request) -> dict[str, bool]:
    require_admin(request)
    with connect() as db:
        notifier = WebhookNotifier(get_setting(db, "webhook_url"))
    await notifier.send_test()
    return {"ok": True}


async def run_profile(profile_id: int) -> dict[str, Any]:
    started_at = utc_now()
    with connect() as db:
        row = db.execute("SELECT * FROM watch_profiles WHERE id = ?", (profile_id,)).fetchone()
        settings_rows = db.execute("SELECT key, value FROM app_settings").fetchall()
    if not row:
        raise HTTPException(404, "Profile not found")
    profile = row_to_profile(row)
    app_settings = {item["key"]: item["value"] for item in settings_rows}
    if profile["source_type"] == "facebook":
        profile["facebook_cookie_header"] = app_settings.get("facebook_cookie_header", "")
    connector = get_connector(profile["source_type"])
    try:
        candidates = await connector.fetch_listings(profile)
    except Exception as exc:  # Manual runs should surface connector failures directly.
        with connect() as db:
            record_run(
                db,
                profile,
                "error",
                {"fetched": 0, "new": 0, "hidden": 0, "duplicates": 0, "notified": 0},
                started_at,
                str(exc),
            )
        raise HTTPException(502, f"Connector failed: {exc}") from exc

    notifier = TelegramNotifier(app_settings.get("telegram_bot_token", ""), app_settings.get("telegram_chat_id", ""))
    webhook = WebhookNotifier(app_settings.get("webhook_url", ""))
    stats = {"fetched": len(candidates), "new": 0, "hidden": 0, "duplicates": 0, "notified": 0}
    now = utc_now()
    with connect() as db:
        for candidate in candidates:
            if is_non_listing_artifact(candidate.source_type, candidate.title, candidate.listing_url):
                stats["hidden"] += 1
                continue
            existing = find_existing_listing(db, profile["id"], candidate)
            if existing:
                updates = ["last_seen_at = ?", "availability_status = ?", "availability_checked_at = ?"]
                values: list[Any] = [now, "active", now]
                refresh_existing_listing_fields(existing, candidate, updates, values)
                if not bool(existing["user_hidden"]):
                    result = apply_filters(candidate, profile)
                    result = apply_listing_age_limit(candidate, profile, result)
                    next_status = result.status
                    if next_status != "hidden" and existing["status"] in {"seen", "notified"}:
                        next_status = existing["status"]
                    updates.extend(["status = ?", "score = ?", "filter_reason = ?"])
                    values.extend([next_status, result.score, result.reason])
                values.append(existing["id"])
                db.execute(f"UPDATE listings SET {', '.join(updates)} WHERE id = ?", values)
                stats["duplicates"] += 1
                continue
            result = apply_filters(candidate, profile)
            result = apply_listing_age_limit(candidate, profile, result)
            status = result.status
            listing_id = insert_listing(db, profile["id"], candidate, status, result.score, result.reason, now)
            listing = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
            if status == "hidden":
                stats["hidden"] += 1
                continue
            stats["new"] += 1
            db.commit()
            if should_auto_assess_new_listing(app_settings):
                try:
                    assessment_text = await generate_ai_text(app_settings, listing_assessment_prompt(row_to_listing(listing)), max_tokens=220)
                    assessed_at = utc_now()
                    db.execute(
                        "UPDATE listings SET ai_assessment_text = ?, ai_assessed_at = ? WHERE id = ?",
                        (assessment_text.strip()[:1200], assessed_at, listing_id),
                    )
                    db.commit()
                    listing = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
                except HTTPException:
                    pass
            delivered = False
            if profile["notify_telegram"] and notifier.configured:
                try:
                    await notifier.send_listing(row_to_listing(listing), profile, result.matched_reason)
                    delivered = True
                except Exception:
                    pass
            if profile["notify_webhook"] and webhook.configured:
                try:
                    await webhook.send_listing(row_to_listing(listing), profile, result.matched_reason)
                    delivered = True
                except Exception:
                    pass
            if delivered:
                db.execute("UPDATE listings SET status = 'notified', notified_at = ? WHERE id = ?", (utc_now(), listing_id))
                db.commit()
                stats["notified"] += 1
        db.execute("UPDATE watch_profiles SET last_run_at = ?, updated_at = ? WHERE id = ?", (now, now, profile_id))
    stats.update(await verify_unseen_listing_availability(profile, app_settings, now))
    with connect() as db:
        record_run(db, profile, "success", stats, started_at, "")
    return {"profile_id": profile_id, **stats}


async def verify_unseen_listing_availability(
    profile: dict[str, Any],
    app_settings: dict[str, str],
    now: str,
) -> dict[str, int]:
    stats = {"availability_checked": 0, "availability_deleted": 0, "availability_reserved": 0}
    with connect() as db:
        rows = db.execute(
            """
            SELECT id, source_type, listing_url
            FROM listings
            WHERE profile_id = ?
              AND user_hidden = 0
              AND status IN ('new', 'notified')
            ORDER BY first_seen_at DESC
            """,
            (profile["id"],),
        ).fetchall()
    if not rows:
        return stats
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            if profile["source_type"] in {"facebook", "mobilede", "marktplaats"}
            else settings.user_agent
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "nl-NL,nl;q=0.9,de-DE;q=0.8,de;q=0.7,en;q=0.6"
        if profile["source_type"] == "marktplaats"
        else "de-DE,de;q=0.9,en;q=0.8",
    }
    if profile["source_type"] == "facebook":
        headers.update(facebook_browser_headers())
    facebook_cookie = safe_cookie_header(app_settings.get("facebook_cookie_header", ""))
    if profile["source_type"] == "facebook" and facebook_cookie:
        headers["Cookie"] = facebook_cookie
    updates: list[tuple[str, str, int]] = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=12.0) as client:
        for row in rows:
            availability = "unknown"
            try:
                response = await client.get(row["listing_url"])
                availability = parse_listing_availability(
                    row["source_type"],
                    response.status_code,
                    response.text,
                    str(response.url),
                )
            except httpx.HTTPError:
                availability = "unknown"
            updates.append((availability, now, row["id"]))
            stats["availability_checked"] += 1
            if availability == "deleted":
                stats["availability_deleted"] += 1
            if availability == "reserved":
                stats["availability_reserved"] += 1
    with connect() as db:
        db.executemany(
            "UPDATE listings SET availability_status = ?, availability_checked_at = ? WHERE id = ?",
            updates,
        )
    return stats


async def poll_loop() -> None:
    await asyncio.sleep(3)
    while True:
        try:
            due_profiles = get_due_profiles()
            for profile in due_profiles:
                await run_profile(profile["id"])
                await asyncio.sleep(max(get_global_rate_limit(), random.randint(8, 18)))
        except Exception:
            pass
        await asyncio.sleep(60)


def get_due_profiles() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT * FROM watch_profiles
            WHERE enabled = 1
              AND (
                last_run_at IS NULL OR
                datetime(last_run_at) <= datetime('now', '-' || poll_interval_minutes || ' minutes')
              )
            ORDER BY COALESCE(last_run_at, created_at) ASC
            LIMIT 3
            """
        ).fetchall()
    return [row_to_profile(row) for row in rows]


def get_enabled_profiles() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT * FROM watch_profiles WHERE enabled = 1 ORDER BY updated_at DESC").fetchall()
    return [row_to_profile(row) for row in rows]


async def run_open_check() -> None:
    try:
        for profile in get_enabled_profiles():
            try:
                await run_profile(profile["id"])
            except Exception:
                pass
            await asyncio.sleep(min(max(get_global_rate_limit(), 2), 5))
    finally:
        async with open_check_lock:
            open_check_state["running"] = False


def get_global_rate_limit() -> int:
    with connect() as db:
        value = get_setting(db, "global_rate_limit_seconds")
    try:
        return max(5, int(value or "20"))
    except ValueError:
        return 20


def profile_values(profile: dict[str, Any], now: str, user_id: int | None = None, include_created: bool = True) -> tuple[Any, ...]:
    values = (
        profile["name"],
        int(profile["enabled"]),
        profile["source_type"],
        profile["search_url"],
        profile["poll_interval_minutes"],
        encode_list(clean_words(profile["include_keywords"])),
        encode_list(clean_words(profile["exclude_keywords"])),
        encode_list(clean_words(profile["required_keywords"])),
        encode_list(clean_words(profile["excluded_categories"])),
        profile["min_price"],
        profile["max_price"],
        max(1, min(3650, int(profile.get("max_listing_age_days") or 365))),
        profile["location_hint"],
        int(profile["notify_telegram"]),
        int(profile["notify_webhook"]),
    )
    if include_created:
        return values + (user_id, now, now)
    return values + (now,)


def clean_words(values: list[str]) -> list[str]:
    return [item.strip() for item in values if item.strip()]


def apply_listing_age_limit(candidate: ListingCandidate, profile: dict[str, Any], result: FilterResult) -> FilterResult:
    if result.status == "hidden" or candidate.source_type == "mobilede":
        return result
    try:
        max_days = max(1, min(3650, int(profile.get("max_listing_age_days") or 365)))
    except (TypeError, ValueError):
        max_days = 365
    posted_at = parse_listing_posted_at(candidate.posted_at_text)
    if not posted_at:
        return result
    if posted_at < datetime.now(UTC) - timedelta(days=max_days):
        return FilterResult("hidden", 0, f"older_than:{max_days}_days", f"older than {max_days} days")
    return result


def parse_listing_posted_at(value: str | None) -> datetime | None:
    text = (value or "").strip().lower()
    if not text or text.startswith(("ez ", "erstzulassung")):
        return None
    now = datetime.now(UTC)
    if any(word in text for word in ("heute", "today", "gerade", "just now")):
        return now
    if any(word in text for word in ("gestern", "yesterday")):
        return now - timedelta(days=1)
    relative = re.search(r"(?:vor\s*)?(\d+)\s*(minute|minuten|std|stunde|stunden|tag|tage|tagen|day|days|week|weeks|woche|wochen|month|months|monat|monate)", text)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        if unit.startswith(("minute", "minuten")):
            return now - timedelta(minutes=amount)
        if unit.startswith(("std", "stunde")):
            return now - timedelta(hours=amount)
        if unit.startswith(("tag", "day")):
            return now - timedelta(days=amount)
        if unit.startswith(("week", "woche")):
            return now - timedelta(days=amount * 7)
        if unit.startswith(("month", "monat")):
            return now - timedelta(days=amount * 30)
    date_match = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", text)
    if date_match:
        day, month, year = [int(part) for part in date_match.groups()]
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day, tzinfo=UTC)
        except ValueError:
            return None
    short_date = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(?!\d)", text)
    if short_date:
        day, month = [int(part) for part in short_date.groups()]
        try:
            candidate = datetime(now.year, month, day, tzinfo=UTC)
        except ValueError:
            return None
        if candidate > now + timedelta(days=1):
            candidate = datetime(now.year - 1, month, day, tzinfo=UTC)
        return candidate
    return None


def validate_profile_search_url(profile: dict[str, Any]) -> None:
    try:
        get_connector(profile["source_type"]).validate_search_url(profile["search_url"])
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def get_setting(db, key: str) -> str:
    row = db.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else ""


def should_auto_assess_new_listing(app_settings: dict[str, str]) -> bool:
    return (
        app_settings.get("ai_enabled") == "1"
        and app_settings.get("ai_listing_assessments_enabled") == "1"
        and app_settings.get("ai_listing_assessments_new_enabled") == "1"
    )


def count_enabled_admins(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT COUNT(*) count FROM users WHERE role = 'admin' AND enabled = 1").fetchone()
    return int(row["count"] if row else 0)


def profile_owner_filter(user: dict[str, Any], alias: str = "watch_profiles") -> tuple[str, list[Any]]:
    if user.get("role") == "admin":
        return "", []
    return f"{alias}.user_id = ?", [user["id"]]


def can_access_profile(db: sqlite3.Connection, profile_id: int, user: dict[str, Any]) -> bool:
    clause, values = profile_owner_filter(user, "watch_profiles")
    clauses = ["id = ?"]
    query_values: list[Any] = [profile_id]
    if clause:
        clauses.append(clause)
        query_values.extend(values)
    row = db.execute(f"SELECT id FROM watch_profiles WHERE {' AND '.join(clauses)}", query_values).fetchone()
    return bool(row)


def can_access_listing(db: sqlite3.Connection, listing_id: int, user: dict[str, Any]) -> bool:
    clause, values = profile_owner_filter(user, "watch_profiles")
    clauses = ["listings.id = ?"]
    query_values: list[Any] = [listing_id]
    if clause:
        clauses.append(clause)
        query_values.extend(values)
    row = db.execute(
        f"""
        SELECT listings.id
        FROM listings
        JOIN watch_profiles ON watch_profiles.id = listings.profile_id
        WHERE {' AND '.join(clauses)}
        """,
        query_values,
    ).fetchone()
    return bool(row)


def valid_watchlist_id(db: sqlite3.Connection, watchlist_id: int | None) -> int:
    if watchlist_id:
        row = db.execute("SELECT id FROM watchlists WHERE id = ?", (watchlist_id,)).fetchone()
        if row:
            return int(row["id"])
    return ensure_default_watchlist(db)


def normalized_default_watchlist_id(db: sqlite3.Connection) -> int:
    try:
        configured = int(get_setting(db, "default_watchlist_id") or "0")
    except ValueError:
        configured = 0
    default_id = valid_watchlist_id(db, configured)
    if configured != default_id:
        db.execute(
            "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("default_watchlist_id", str(default_id)),
        )
    return default_id


def normalized_user_default_watchlist_id(db: sqlite3.Connection, user: dict[str, Any]) -> int:
    row = db.execute("SELECT default_watchlist_id FROM users WHERE id = ?", (user["id"],)).fetchone()
    configured = row["default_watchlist_id"] if row else None
    default_id = valid_watchlist_id(db, configured or normalized_default_watchlist_id(db))
    if configured != default_id:
        db.execute("UPDATE users SET default_watchlist_id = ?, updated_at = ? WHERE id = ?", (default_id, utc_now(), user["id"]))
    return default_id


def set_listing_watchlisted(
    db: sqlite3.Connection,
    listing_id: int,
    watchlisted: bool,
    watchlist_id: int | None,
    user: dict[str, Any],
) -> None:
    if watchlisted:
        target_id = valid_watchlist_id(db, watchlist_id or normalized_user_default_watchlist_id(db, user))
        db.execute(
            """
            INSERT OR IGNORE INTO listing_watchlists(listing_id, watchlist_id, created_at)
            VALUES (?, ?, ?)
            """,
            (listing_id, target_id, utc_now()),
        )
        db.execute("UPDATE watchlists SET updated_at = ? WHERE id = ?", (utc_now(), target_id))
        return
    if watchlist_id:
        db.execute(
            "DELETE FROM listing_watchlists WHERE listing_id = ? AND watchlist_id = ?",
            (listing_id, watchlist_id),
        )
    else:
        db.execute("DELETE FROM listing_watchlists WHERE listing_id = ?", (listing_id,))


def apply_listing_watchlist_update(
    db: sqlite3.Connection,
    listing_id: int,
    watchlisted: bool,
    watchlist_id: int | None,
    user: dict[str, Any],
) -> int:
    set_listing_watchlisted(db, listing_id, watchlisted, watchlist_id, user)
    return int(watchlisted) if watchlisted else listing_has_watchlists(db, listing_id)


def listing_has_watchlists(db: sqlite3.Connection, listing_id: int) -> int:
    row = db.execute(
        "SELECT COUNT(*) count FROM listing_watchlists WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    return 1 if row and row["count"] else 0


def db_listing_rows_to_items(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_listing(row) for row in rows]


def attach_watchlists(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return items
    listing_ids = [item["id"] for item in items]
    placeholders = ",".join("?" for _ in listing_ids)
    with connect() as db:
        rows = db.execute(
            f"""
            SELECT listing_watchlists.listing_id, watchlists.id, watchlists.name
            FROM listing_watchlists
            JOIN watchlists ON watchlists.id = listing_watchlists.watchlist_id
            WHERE listing_watchlists.listing_id IN ({placeholders})
            ORDER BY watchlists.name COLLATE NOCASE
            """,
            listing_ids,
        ).fetchall()
    grouped: dict[int, list[dict[str, Any]]] = {item["id"]: [] for item in items}
    for row in rows:
        grouped[int(row["listing_id"])].append({"id": row["id"], "name": row["name"]})
    for item in items:
        item["watchlists"] = grouped.get(item["id"], [])
        item["watchlisted"] = bool(item["watchlists"] or item.get("watchlisted"))
    return items


def mask_secret(value: str) -> str:
    return "********" if value else ""


def inquiry_prompt(
    listing: dict[str, Any],
    tone: str,
    language: str,
    account_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    tone_instruction = {
        "polite": "sehr höflich, respektvoll und warm",
        "normal": "freundlich, direkt und natürlich",
        "cheeky": "locker-frech, charmant, aber nicht respektlos",
    }.get(tone, "freundlich, direkt und natürlich")
    if language == "en":
        tone_instruction = {
            "polite": "very polite, respectful, and warm",
            "normal": "friendly, direct, and natural",
            "cheeky": "playfully cheeky and charming, never rude",
        }.get(tone, "friendly, direct, and natural")
    facts = "\n".join(
        [
            f"Titel: {listing.get('title') or ''}",
            f"Preis: {listing.get('price_text') or 'unbekannt'}",
            f"Ort: {listing.get('location_text') or 'unbekannt'}",
            f"Kategorie: {listing.get('category_text') or 'unbekannt'}",
            f"Beschreibung: {listing.get('description_snippet') or ''}",
        ]
    )
    account_profile = account_profile or {}
    buyer_facts = "\n".join(
        [
            f"Name: {account_profile.get('display_name') or ''}",
            f"Eigener Ort: {account_profile.get('buyer_location') or ''}",
            f"Kontakt-/Hinweis: {account_profile.get('contact_hint') or ''}",
            f"Signatur: {account_profile.get('inquiry_signature') or ''}",
        ]
    )
    output_language = "German" if language == "de" else "English"
    return [
        {
            "role": "system",
            "content": (
                "You write short buyer inquiry messages for marketplace listings. "
                "Return only the message text. Do not invent private facts, do not mention AI, "
                "and do not include placeholders, subject lines, or explanations. "
                "Use the buyer profile only when it is provided and useful. "
                "The buyer name belongs to the sender only: never use it as the greeting recipient."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Write one {output_language} inquiry message. Style: {tone_instruction}. "
                "Ask whether the item is still available and, if fitting, mention pickup or a quick viewing. "
                "Keep it concise. If a signature is provided, end with it. "
                "Do not greet the seller by the buyer's name; use a neutral greeting or no named greeting.\n\nListing facts:\n"
                f"{facts}\n\nBuyer profile:\n{buyer_facts}"
            ),
        },
    ]


def normalize_inquiry_text(text: str, account_profile: dict[str, Any] | None = None) -> str:
    cleaned = text.strip()
    buyer_name = clean_ai_string((account_profile or {}).get("display_name"))
    if not buyer_name:
        return cleaned

    escaped_name = re.escape(buyer_name)
    leading_named_greeting = re.compile(
        rf"^((?:hallo|hi|hey|hello|guten\s+tag|guten\s+morgen|guten\s+abend)\s+){escaped_name}([,!.:]?)",
        re.IGNORECASE,
    )
    cleaned = leading_named_greeting.sub(lambda match: f"{match.group(1).rstrip()}{match.group(2) or ','}", cleaned, count=1)
    leading_dear_greeting = re.compile(
        rf"^(?:liebe?r?|dear)\s+{escaped_name}([,!.:]?)\s*",
        re.IGNORECASE,
    )
    cleaned = leading_dear_greeting.sub("Hallo, ", cleaned, count=1)
    return cleaned.strip()


def listing_assessment_prompt(listing: dict[str, Any]) -> list[dict[str, str]]:
    facts = "\n".join(
        [
            f"Title: {listing.get('title') or ''}",
            f"Price: {listing.get('price_text') or 'unknown'}",
            f"Location: {listing.get('location_text') or 'unknown'}",
            f"Category: {listing.get('category_text') or 'unknown'}",
            f"Search job: {listing.get('profile_name') or ''}",
            f"Match score: {listing.get('score') or 0}",
            f"Filter note: {listing.get('filter_reason') or ''}",
            f"Description: {listing.get('description_snippet') or ''}",
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "You assess marketplace listings for a buyer. Return only a short German product assessment. "
                "Focus on the listing's usefulness for the search job, practical value or resale potential, "
                "and whether the asking price looks close to the currently usual used-market price. "
                "Estimate a typical market-price range only when the product details are sufficient; mark it as "
                "uncertain when key facts such as model, condition, storage, age, or accessories are missing. "
                "Do not mention AI. Do not invent exact facts. Keep it to two compact sentences with a clear "
                "buy/watch/pass tendency."
            ),
        },
        {
            "role": "user",
            "content": (
                "Assess whether this article is useful for the saved search. Weigh fit to the search job, "
                "practical usability, resale/value potential, description completeness, visible risk signs, "
                "and the asking price against a currently usual market-price range for comparable used items. "
                "Call out missing details that would make the article or market price hard to judge.\n\n"
                f"{facts}"
            ),
        },
    ]


def search_draft_prompt(prompt: str, language: str) -> list[dict[str, str]]:
    output_language = "German" if language == "de" else "English"
    return [
        {
            "role": "system",
            "content": (
                "You convert one natural-language marketplace search wish into a structured job draft. "
                "Return only one JSON object, without markdown or explanations. "
                "Allowed source_type values: kleinanzeigen, facebook, mobilede, marktplaats. "
                "Use kleinanzeigen unless the user clearly asks for Facebook Marketplace, mobile.de, cars, vehicles, Marktplaats, or Dutch listings. "
                "Keep query to the product/search words only; put prices, radius, location, and listing age only in their fields. "
                "For Kleinanzeigen category_hint, prefer a precise category path such as 'Elektronik > Notebooks' for laptops. "
                "Use null for unknown numeric values and [] for empty keyword arrays."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Language for labels: {output_language}.\n"
                "Return these fields exactly: "
                "name, source_type, query, category_hint, location, radius_km, max_price, "
                "max_listing_age_days, required_keywords, exclude_keywords.\n\n"
                f"Search wish: {prompt.strip()}"
            ),
        },
    ]


def normalize_search_draft(text: str) -> dict[str, Any]:
    raw = extract_json_object(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(502, "AI provider did not return a valid search draft") from exc
    if not isinstance(data, dict):
        raise HTTPException(502, "AI provider did not return a valid search draft")
    source_type = str(data.get("source_type") or "kleinanzeigen").strip().lower()
    if source_type not in {"kleinanzeigen", "facebook", "mobilede", "marktplaats"}:
        source_type = "kleinanzeigen"
    query = clean_ai_string(data.get("query")) or clean_ai_string(data.get("name"))
    if not query:
        raise HTTPException(502, "AI provider did not return a search query")
    max_price = bounded_float(data.get("max_price"), 0, 1_000_000)
    if max_price is None:
        max_price = infer_max_price(query)
    query = sanitize_search_query(query)
    if not query:
        raise HTTPException(502, "AI provider did not return a search query")
    category_hint = clean_ai_string(data.get("category_hint"))[:120]
    if not category_hint:
        category_hint = infer_category_hint(query)
    radius = bounded_int(data.get("radius_km"), 0, 200)
    max_age = bounded_int(data.get("max_listing_age_days"), 1, 3650) or 365
    return {
        "name": sanitize_search_name(clean_ai_string(data.get("name")) or query, query),
        "source_type": source_type,
        "query": query[:120],
        "category_hint": category_hint,
        "location": clean_ai_string(data.get("location"))[:120],
        "radius_km": radius,
        "max_price": max_price,
        "max_listing_age_days": max_age,
        "required_keywords": clean_ai_list(data.get("required_keywords"))[:12],
        "exclude_keywords": clean_ai_list(data.get("exclude_keywords"))[:12],
    }


def infer_max_price(value: str) -> float | None:
    match = re.search(r"(?:\b(?:unter|bis|max(?:imal)?|höchstens|under|below|up\s+to)\s*)?(\d{2,7})(?:[.,]\d{1,2})?\s*(?:€|eur|euro)(?=\s|$|[,.])", value, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(?:unter|bis|max(?:imal)?|höchstens|under|below|up\s+to)\s+(\d{2,7})(?:[.,]\d{1,2})?\b", value, re.IGNORECASE)
    if not match:
        return None
    return bounded_float(match.group(1), 0, 1_000_000)


def sanitize_search_query(value: str) -> str:
    cleaned = clean_ai_string(value)
    cleaned = re.sub(
        r"\b(?:unter|bis|max(?:imal)?|höchstens|under|below|up\s+to)\s+\d{2,7}(?:[.,]\d{1,2})?\s*(?:€|eur|euro)?(?=\s|$|[,.])",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b\d{2,7}(?:[.,]\d{1,2})?\s*(?:€|eur|euro)(?=\s|$|[,.])", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:kleinanzeigen|facebook marketplace|mobile\.de|marktplaats(?:\.nl)?)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:suche|suchen|gesucht|finde|finden|looking for)\b", " ", cleaned, flags=re.IGNORECASE)
    return clean_ai_string(cleaned).strip(" ,;:-")


def sanitize_search_name(value: str, fallback_query: str) -> str:
    cleaned = sanitize_search_query(value)
    return cleaned or fallback_query


def infer_category_hint(query: str) -> str:
    normalized = query.lower()
    if re.search(r"\b(macbook|notebook|laptop|thinkpad|chromebook)\b", normalized):
        return "Elektronik > Notebooks"
    return ""


def extract_json_object(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s*```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise HTTPException(502, "AI provider did not return JSON")
    return text[start : end + 1]


def clean_ai_string(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_ai_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        cleaned = clean_ai_string(item)
        if cleaned and cleaned not in result:
            result.append(cleaned[:80])
    return result


def bounded_int(value: Any, minimum: int, maximum: int) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return min(max(number, minimum), maximum)


def bounded_float(value: Any, minimum: float, maximum: float) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return min(max(number, minimum), maximum)


async def generate_ai_text(app_settings: dict[str, str], messages: list[dict[str, str]], max_tokens: int = 220) -> str:
    provider = app_settings.get("ai_provider", "openai") or "openai"
    model = app_settings.get("ai_model", "").strip() or default_ai_model(provider)
    base_url = normalized_ai_base_url(provider, app_settings.get("ai_base_url", ""))
    api_key = app_settings.get("ai_api_key", "")
    if provider == "openai" and not api_key:
        raise HTTPException(400, "OpenAI API key is missing")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    timeout = 180.0 if provider in {"ollama", "lmstudio"} else 45.0
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.65,
                    "stream": False,
                    **ai_token_limit_payload(provider, max_tokens),
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        raise HTTPException(502, f"AI provider request failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"AI provider is unreachable: {exc}") from exc
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(502, "AI provider returned an unsupported response") from exc
    if not str(content).strip():
        raise HTTPException(502, "AI provider returned an empty response")
    return str(content)


def ai_token_limit_payload(provider: str, max_tokens: int) -> dict[str, int]:
    if provider == "ollama":
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


def normalized_ai_base_url(provider: str, value: str) -> str:
    base_url = value.strip().rstrip("/")
    if not base_url:
        base_url = {
            "openai": "https://api.openai.com/v1",
            "ollama": "http://host.docker.internal:11434/v1",
            "lmstudio": "http://host.docker.internal:1234/v1",
        }.get(provider, "https://api.openai.com/v1")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def default_ai_model(provider: str) -> str:
    return {
        "openai": "gpt-4o-mini",
        "ollama": "llama3.1",
        "lmstudio": "local-model",
    }.get(provider, "gpt-4o-mini")


def validate_remote_image_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Unsupported image URL")
    try:
        validate_public_fetch_host(parsed.hostname)
    except ValueError as exc:
        raise HTTPException(400, "Local image URLs are not allowed") from exc
    host = parsed.hostname.lower()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise HTTPException(400, "Private image URLs are not allowed")


def find_existing_listing(db: sqlite3.Connection, profile_id: int, candidate: ListingCandidate) -> sqlite3.Row | None:
    return db.execute(
        """
        SELECT * FROM listings
        WHERE profile_id = ? AND (source_listing_id = ? OR content_hash = ?)
        """,
        (profile_id, candidate.source_listing_id, candidate.content_hash),
    ).fetchone()


def refresh_existing_listing_fields(
    existing: sqlite3.Row,
    candidate: ListingCandidate,
    updates: list[str],
    values: list[Any],
) -> None:
    fill_fields = [
        ("price_text", candidate.price_text),
        ("location_text", candidate.location_text),
        ("category_text", candidate.category_text),
        ("posted_at_text", candidate.posted_at_text),
        ("description_snippet", candidate.description_snippet),
        ("thumbnail_url", candidate.thumbnail_url),
    ]
    for field, value in fill_fields:
        if value and not existing[field]:
            updates.append(f"{field} = ?")
            values.append(value)
    if candidate.price_value is not None and existing["price_value"] is None:
        updates.append("price_value = ?")
        values.append(candidate.price_value)
    if candidate.content_hash and candidate.content_hash != existing["content_hash"]:
        updates.append("content_hash = ?")
        values.append(candidate.content_hash)


def insert_listing(
    db: sqlite3.Connection,
    profile_id: int,
    candidate: ListingCandidate,
    status: str,
    score: int,
    reason: str,
    now: str,
) -> int:
    cursor = db.execute(
        """
        INSERT INTO listings(
          source_type, source_listing_id, profile_id, title, price_text, price_value,
          location_text, category_text, posted_at_text, description_snippet, listing_url,
          thumbnail_url, content_hash, first_seen_at, last_seen_at, status, watchlisted, user_hidden,
          availability_status, availability_checked_at, score, filter_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidate.source_type,
            candidate.source_listing_id,
            profile_id,
            candidate.title,
            candidate.price_text,
            candidate.price_value,
            candidate.location_text,
            candidate.category_text,
            candidate.posted_at_text,
            candidate.description_snippet,
            candidate.listing_url,
            candidate.thumbnail_url,
            candidate.content_hash,
            now,
            now,
            status,
            0,
            0,
            "active",
            now,
            score,
            reason,
        ),
    )
    return int(cursor.lastrowid)


def reapply_profile_filters(db: sqlite3.Connection, profile_id: int, profile: dict[str, Any]) -> dict[str, int]:
    stats = {"checked": 0, "changed": 0, "hidden": 0, "visible": 0}
    rows = db.execute("SELECT * FROM listings WHERE profile_id = ?", (profile_id,)).fetchall()
    for row in rows:
        stats["checked"] += 1
        if bool(row["user_hidden"]):
            continue
        candidate = listing_candidate_from_row(row)
        result = apply_listing_age_limit(candidate, profile, apply_filters(candidate, profile))
        next_status = result.status
        if next_status != "hidden" and row["status"] in {"seen", "notified"}:
            next_status = row["status"]
        if next_status == "hidden":
            stats["hidden"] += 1
        else:
            stats["visible"] += 1
        if row["status"] == next_status and row["score"] == result.score and row["filter_reason"] == result.reason:
            continue
        stats["changed"] += 1
        db.execute(
            "UPDATE listings SET status = ?, score = ?, filter_reason = ? WHERE id = ?",
            (next_status, result.score, result.reason, row["id"]),
        )
    return stats


def listing_candidate_from_row(row: sqlite3.Row) -> ListingCandidate:
    return ListingCandidate(
        source_type=row["source_type"],
        source_listing_id=row["source_listing_id"],
        title=row["title"],
        price_text=row["price_text"],
        price_value=row["price_value"],
        location_text=row["location_text"],
        category_text=row["category_text"],
        posted_at_text=row["posted_at_text"],
        description_snippet=row["description_snippet"],
        listing_url=row["listing_url"],
        thumbnail_url=row["thumbnail_url"],
        content_hash=row["content_hash"],
    )


def record_run(
    db: sqlite3.Connection,
    profile: dict[str, Any],
    status: str,
    stats: dict[str, int],
    started_at: str,
    error_message: str,
) -> None:
    db.execute(
        """
        INSERT INTO run_logs(
          profile_id, profile_name, status, fetched, new_count, hidden_count,
          duplicate_count, notified_count, error_message, started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile["id"],
            profile["name"],
            status,
            stats.get("fetched", 0),
            stats.get("new", 0),
            stats.get("hidden", 0),
            stats.get("duplicates", 0),
            stats.get("notified", 0),
            error_message[:500],
            started_at,
            utc_now(),
        ),
    )
