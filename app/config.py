from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


def persistent_session_secret(db_path: str) -> str:
    env_secret = os.getenv("MARKETPLACELENS_SESSION_SECRET", "").strip()
    if env_secret:
        if len(env_secret) < 32:
            raise ValueError("MARKETPLACELENS_SESSION_SECRET must contain at least 32 characters")
        return env_secret
    secret_file = Path(os.getenv("MARKETPLACELENS_SESSION_SECRET_FILE", "") or Path(db_path).with_name("session.secret"))
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if secret_file.exists():
        value = secret_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = secrets.token_urlsafe(48)
    try:
        fd = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        existing = secret_file.read_text(encoding="utf-8").strip()
        if not existing:
            raise RuntimeError("Session secret file is empty")
        return existing
    with os.fdopen(fd, "w", encoding="utf-8") as target:
        target.write(value)
    try:
        secret_file.chmod(0o600)
    except OSError:
        pass
    return value


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("MARKETPLACELENS_DB_PATH", "./data/marketplacelens.db")
    poll_enabled: bool = os.getenv("MARKETPLACELENS_POLL_ENABLED", "true").lower() == "true"
    min_poll_minutes: int = int(os.getenv("MARKETPLACELENS_MIN_POLL_MINUTES", "30"))
    default_poll_minutes: int = int(os.getenv("MARKETPLACELENS_DEFAULT_POLL_MINUTES", "60"))
    user_agent: str = os.getenv(
        "MARKETPLACELENS_USER_AGENT",
        "MarketPlaceLens/0.2 (+self-hosted listing watcher)",
    )
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    webhook_url: str = os.getenv("MARKETPLACELENS_WEBHOOK_URL", "")
    admin_username: str = os.getenv("MARKETPLACELENS_ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("MARKETPLACELENS_ADMIN_PASSWORD", "")
    cookie_secure: bool = os.getenv("MARKETPLACELENS_COOKIE_SECURE", "false").lower() == "true"
    session_secret: str = persistent_session_secret(db_path)


settings = Settings()
