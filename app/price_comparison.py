"""Opt-in new-item comparison via the eBay Browse API.

Amazon Creators API is explicitly opt-in for deployments with approval for
this specific use case. Never scrape or use Amazon data for price alerts.
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
_amazon_token: tuple[float, str] = (0, "")
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


def select_amazon_offers(query: str, items: list[dict]) -> list[dict]:
    result = []
    for item in items:
        title = str((item.get("itemInfo") or {}).get("title", {}).get("displayValue", ""))
        score = match_score(query, title)
        url = str(item.get("detailPageURL") or "")
        parsed = urlparse(url)
        if score < 0.7 or parsed.scheme != "https" or parsed.hostname not in {"www.amazon.de", "amazon.de"}:
            continue
        by_condition = {}
        for listing in (item.get("offersV2") or {}).get("listings", []):
            condition = str((listing.get("condition") or {}).get("value", "")).lower()
            if condition not in {"new", "used"} or listing.get("violatesMAP"):
                continue
            if (listing.get("availability") or {}).get("type") != "IN_STOCK":
                continue
            money = (listing.get("price") or {}).get("money") or {}
            try:
                amount = float(money["amount"])
                if money["currency"] != "EUR" or not 0 < amount < 1e8:
                    continue
            except (TypeError, ValueError, KeyError):
                continue
            if condition not in by_condition or by_condition[condition]["price"] > amount:
                by_condition[condition] = {"provider": "Amazon", "title": title, "price": amount,
                    "currency": "EUR", "shipping": None, "url": url, "match_confidence": round(score, 2),
                    "condition": condition}
        if "new" in by_condition:
            result.extend(by_condition.values())
    return result[:10]


def amazon_configured():
    return os.getenv("MARKETPLACELENS_AMAZON_APPROVED", "").lower() == "true" and all(
        os.getenv("MARKETPLACELENS_AMAZON_" + name) for name in ("CLIENT_ID", "CLIENT_SECRET", "PARTNER_TAG"))


async def fetch_amazon_offers(query: str) -> list[dict]:
    global _amazon_token
    endpoints = {"3.1": "https://api.amazon.com/auth/o2/token", "3.2": "https://api.amazon.co.uk/auth/o2/token", "3.3": "https://api.amazon.co.jp/auth/o2/token"}
    endpoint = endpoints.get(os.getenv("MARKETPLACELENS_AMAZON_CREDENTIAL_VERSION", "3.2"))
    if not endpoint:
        raise ValueError("Unsupported credential version")
    async with httpx.AsyncClient(timeout=12, trust_env=False, follow_redirects=False) as client:
        now = time.monotonic()
        if _amazon_token[0] <= now:
            response = await client.post(endpoint, json={"grant_type": "client_credentials",
                "client_id": os.environ["MARKETPLACELENS_AMAZON_CLIENT_ID"],
                "client_secret": os.environ["MARKETPLACELENS_AMAZON_CLIENT_SECRET"],
                "scope": "creatorsapi::default"})
            response.raise_for_status()
            data = response.json()
            _amazon_token = (now + max(1, int(data["expires_in"]) - 60), data["access_token"])
        response = await client.post("https://creatorsapi.amazon/catalog/v1/searchItems",
            headers={"Authorization": "Bearer " + _amazon_token[1], "x-marketplace": "www.amazon.de"},
            json={"keywords": query, "partnerTag": os.environ["MARKETPLACELENS_AMAZON_PARTNER_TAG"],
                "marketplace": "www.amazon.de", "condition": "Any", "itemCount": 5,
                "resources": ["itemInfo.title", "offersV2.listings.price", "offersV2.listings.condition",
                    "offersV2.listings.availability", "offersV2.listings.violatesMAP"]})
        response.raise_for_status()
        return select_amazon_offers(query, (response.json().get("searchResult") or {}).get("items", []))


async def compare_new_prices(title: str, refresh: bool = False) -> dict:
    global _token
    query = product_query(title)
    links = {"amazon": "https://www.amazon.de/s?" + urlencode({"k": query}),
             "ebay": "https://www.ebay.de/sch/i.html?" + urlencode({"_nkw": query, "LH_ItemCondition": "1000"})}
    result = {"query": query, "offers": [], "links": links, "fetched_at": None,
              "amazon_status": "search_link_only", "ebay_status": "not_configured"}
    client_id, secret = os.getenv("MARKETPLACELENS_EBAY_CLIENT_ID"), os.getenv("MARKETPLACELENS_EBAY_CLIENT_SECRET")
    amazon_enabled = amazon_configured()
    if not query or (not (client_id and secret) and not amazon_enabled):
        return result
    async with _lock:
        now = time.monotonic()
        cached = _cache.get(query)
        # Even explicit refresh cannot bypass the provider quota window.
        if cached and now - cached[0] < TTL:
            _cache.move_to_end(query)
            return cached[1]
        try:
            if not client_id or not secret:
                raise ValueError("eBay is not configured")
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
            result["ebay_status"] = "unavailable" if client_id and secret else "not_configured"
        if amazon_enabled:
            try:
                offers = await fetch_amazon_offers(query)
                result["offers"].extend(offers)
                result["amazon_status"] = "ok" if offers else "no_match"
                result["fetched_at"] = datetime.now(UTC).isoformat()
            except (httpx.HTTPError, KeyError, ValueError, TypeError):
                result["amazon_status"] = "unavailable"
        _cache[query] = (now, result)
        _cache.move_to_end(query)
        while len(_cache) > MAX_CACHE:
            _cache.popitem(last=False)
        return result
