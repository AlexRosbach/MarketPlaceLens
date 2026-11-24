from __future__ import annotations

import copy
import hashlib
import json
import time
from collections import OrderedDict


class BoundedCache:
    """Process-local TTL/LRU cache; callers provide a suitable isolation key."""
    def __init__(self, ttl: int, max_entries: int, max_bytes: int | None = None):
        self.ttl, self.max_entries, self.max_bytes = ttl, max_entries, max_bytes
        self.entries = OrderedDict()
        self.bytes = 0

    def get(self, key):
        entry = self.entries.pop(key, None)
        if entry is None:
            return None
        expires, value, size = entry
        if expires <= time.monotonic():
            self.bytes -= size
            return None
        self.entries[key] = entry
        return copy.deepcopy(value)

    def put(self, key, value, size=0):
        if self.max_bytes is not None and size > self.max_bytes:
            return
        old = self.entries.pop(key, None)
        if old:
            self.bytes -= old[2]
        self.entries[key] = (time.monotonic() + self.ttl, copy.deepcopy(value), size)
        self.bytes += size
        while len(self.entries) > self.max_entries or (self.max_bytes is not None and self.bytes > self.max_bytes):
            _, removed = self.entries.popitem(last=False)
            self.bytes -= removed[2]


def search_key(profile: dict) -> str:
    # User and session isolation is intentional, even when two users share a URL.
    fields = [profile.get(key) for key in ("user_id", "source_type", "search_url", "location_hint", "facebook_cookie_header")]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode()).hexdigest()


def assessment_key(settings: dict, messages: list[dict]) -> str:
    fields = [settings.get(k) for k in ("ai_provider", "ai_model", "ai_base_url", "ai_tone")]
    return hashlib.sha256(json.dumps([fields, messages], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
