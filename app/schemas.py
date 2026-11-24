from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class ProfilePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    source_type: str = "html"
    search_url: HttpUrl
    poll_interval_minutes: int = Field(default=60, ge=30, le=10080)
    include_keywords: list[str] = []
    exclude_keywords: list[str] = []
    required_keywords: list[str] = []
    excluded_categories: list[str] = []
    min_price: float | None = None
    max_price: float | None = None
    max_listing_age_days: int = Field(default=365, ge=1, le=3650)
    location_hint: str = ""
    notify_telegram: bool = True
    notify_webhook: bool = False


class ListingStatusPayload(BaseModel):
    status: str | None = Field(default=None, pattern="^(new|seen|hidden|notified)$")
    watchlisted: bool | None = None
    watchlist_id: int | None = None
    contacted: bool | None = None


class InquiryPayload(BaseModel):
    language: str = Field(default="de", pattern="^(de|en)$")


class SearchDraftPayload(BaseModel):
    prompt: str = Field(min_length=3, max_length=600)
    language: str = Field(default="de", pattern="^(de|en)$")


class WatchlistPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SettingsPayload(BaseModel):
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    webhook_url: str = ""
    global_rate_limit_seconds: int = Field(default=20, ge=5, le=3600)
    default_watchlist_id: int | None = None
    ai_enabled: bool = False
    ai_listing_assessments_enabled: bool = False
    ai_listing_assessments_auto_enabled: bool = False
    ai_listing_assessments_new_enabled: bool = False
    ai_provider: str = Field(default="openai", pattern="^(openai|ollama|lmstudio)$")
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""
    ai_tone: str = Field(default="normal", pattern="^(polite|normal|cheeky)$")
    facebook_cookie_header: str = Field(default="", max_length=12000)


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class SetupPayload(BaseModel):
    username: str = Field(default="admin", min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=200)


class PasswordPayload(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=200)


class AccountProfilePayload(BaseModel):
    display_name: str = Field(default="", max_length=120)
    buyer_location: str = Field(default="", max_length=120)
    contact_hint: str = Field(default="", max_length=240)
    inquiry_signature: str = Field(default="", max_length=120)


class UserPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    role: str = Field(default="user", pattern="^(admin|user)$")
    enabled: bool = True


class UserUpdatePayload(BaseModel):
    role: str = Field(default="user", pattern="^(admin|user)$")
    enabled: bool = True
    password: str = Field(default="", max_length=200)
