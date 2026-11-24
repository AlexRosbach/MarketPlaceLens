"""Opt-in new-item comparison via the eBay Browse API.

Amazon search links are provided separately. Do not scrape or store Amazon
prices without an approved data source and permission for this use case.
"""
from __future__ import annotations

import asyncio
import os
import re
import time
from collections import OrderedDict
from datetime import UTC, datetime
from urllib.parse import urlencode, urlparse

import httpx

_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()
_lock = asyncio.Lock()
_token: tuple[float, str] = (0, "")
TTL = 900
MAX_CACHE = 512


def product_query(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()[:160]


def tokens(title: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", title.casefold()))


def match_score(query: str, title: str) -> float:
    wanted, actual = tokens(query), tokens(title)
    if not wanted:
        return 0.0
    # Reject conflicting numeric variant/model identifiers. Never assert
    # identity based on a fuzzy keyword match alone.
    numeric = {word for word in wanted if any(c.isdigit() for c in word)}
    if numeric and not numeric.issubset(actual):
        return 0.0
    return len(wanted & actual) / len(wanted)


def select_ebay_offers(query: str, items: list[dict]) -> list[dict]:
    offers = []
    for item in items:
        title = str(item.get("title", ""))
        score = match_score(query, title)
        if score < 0.7 or str(item.get("conditionId")) != "1000":
            continue
        if any(word in tokens(title) for word in ("hülle", "case", "cover", "ersatzteil", "defekt")) and not any(word in tokens(query) for word in ("hülle", "case", "cover", "ersatzteil", "defekt")):
            continue
        price = item.get("price") or {}
        url = str(item.get("itemWebUrl") or "")
        if urlparse(url).scheme != "https" or urlparse(url).hostname not in {"ebay.de", "www.ebay.de"}:
            continue
        try:
            value = float(price["value"])
            if not 0 < value < 1e8 or price["currency"] != "EUR":
                continue
        except (ValueError, KeyError, TypeError):
            continue
        shipping = None
        try:
            costs = [float(option["shippingCost"]["value"]) for option in item.get("shippingOptions", [])
                     if option.get("shippingCost", {}).get("currency") == "EUR"]
            shipping = min(costs) if costs else None
        except (ValueError, KeyError, TypeError):
            pass
        offers.append({"provider": "eBay", "title": title, "price": value, "currency": "EUR",
                       "shipping": shipping, "url": url, "match_confidence": round(score, 2),
                       "condition": "new"})
    return sorted(offers, key=lambda offer: offer["price"] + (offer["shipping"] or 0))[:3]


async def compare_new_prices(title: str, refresh: bool = False) -> dict:
    global _token
    query = product_query(title)
    links = {"amazon": "https://www.amazon.de/s?" + urlencode({"k": query}),
             "ebay": "https://www.ebay.de/sch/i.html?" + urlencode({"_nkw": query, "LH_ItemCondition": "1000"})}
    result = {"query": query, "offers": [], "links": links, "fetched_at": None,
              "amazon_status": "search_link_only", "ebay_status": "not_configured"}
    client_id, secret = os.getenv("MARKETPLACELENS_EBAY_CLIENT_ID"), os.getenv("MARKETPLACELENS_EBAY_CLIENT_SECRET")
    if not query or not client_id or not secret:
        return result
    async with _lock:
        now = time.monotonic()
        cached = _cache.get(query)
        # Even explicit refresh cannot bypass the provider quota window.
        if cached and now - cached[0] < TTL:
            _cache.move_to_end(query)
            return cached[1]
        try:
            async with httpx.AsyncClient(timeout=12, trust_env=False, follow_redirects=False) as client:
                if _token[0] <= now:
                    response = await client.post("https://api.ebay.com/identity/v1/oauth2/token",
                                                 auth=(client_id, secret),
                                                 data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"})
                    response.raise_for_status()
                    data = response.json()
                    _token = (now + max(1, int(data["expires_in"]) - 60), data["access_token"])
                response = await client.get("https://api.ebay.com/buy/browse/v1/item_summary/search",
                                            headers={"Authorization": "Bearer " + _token[1],
                                                     "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE"},
                                            params={"q": query, "filter": "conditionIds:{1000},buyingOptions:{FIXED_PRICE}", "limit": 20})
                response.raise_for_status()
                result["offers"] = select_ebay_offers(query, response.json().get("itemSummaries", []))
                result["ebay_status"] = "ok" if result["offers"] else "no_match"
                result["fetched_at"] = datetime.now(UTC).isoformat()
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            result["ebay_status"] = "unavailable"
        _cache[query] = (now, result)
        _cache.move_to_end(query)
        while len(_cache) > MAX_CACHE:
            _cache.popitem(last=False)
        return result
