from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup, Tag

from .config import settings


LOCAL_HOSTS = {"localhost", "localhost.localdomain", "host.docker.internal"}


@dataclass
class ListingCandidate:
    source_type: str
    source_listing_id: str
    title: str
    price_text: str
    price_value: float | None
    location_text: str
    category_text: str
    posted_at_text: str
    description_snippet: str
    listing_url: str
    thumbnail_url: str
    content_hash: str


class MarketplaceConnector:
    source_type = "base"

    def validate_search_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Search URL must be an absolute http(s) URL.")
        validate_public_fetch_host(parsed.hostname or "")
        if self.source_type == "facebook":
            host = parsed.netloc.lower()
            path = parsed.path.rstrip("/").lower()
            if host not in {"facebook.com", "www.facebook.com", "m.facebook.com"}:
                raise ValueError("Facebook jobs need a facebook.com Marketplace URL.")
            if path != "/marketplace" and not path.startswith("/marketplace/"):
                raise ValueError("Facebook jobs need a Marketplace URL.")
            if path == "/marketplace/search" and not parse_qs(parsed.query).get("query", [""])[0].strip():
                raise ValueError("Facebook Marketplace search URLs need a query term.")
        if self.source_type == "mobilede":
            host = parsed.netloc.lower()
            if host not in {"mobile.de", "www.mobile.de", "suchen.mobile.de"}:
                raise ValueError("mobile.de jobs need a mobile.de or suchen.mobile.de URL.")
        if self.source_type == "marktplaats":
            host = parsed.netloc.lower()
            if host not in {"marktplaats.nl", "www.marktplaats.nl"}:
                raise ValueError("Marktplaats jobs need a marktplaats.nl URL.")

    async def fetch_listings(self, profile: dict) -> list[ListingCandidate]:
        raise NotImplementedError


def validate_public_fetch_host(hostname: str) -> None:
    host = hostname.lower().strip("[]")
    if host in LOCAL_HOSTS or host.endswith(".local"):
        raise ValueError("Search URLs must not target local or private network hosts.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise ValueError("Search URLs must not target local or private network hosts.")


class HtmlListingConnector(MarketplaceConnector):
    source_type = "html"

    def __init__(self, source_type: str = "html") -> None:
        self.source_type = source_type

    async def fetch_listings(self, profile: dict) -> list[ListingCandidate]:
        search_url = profile["search_url"]
        if self.source_type == "kleinanzeigen":
            search_url = apply_kleinanzeigen_location_to_url(search_url, profile.get("location_hint", ""))
        if self.source_type == "facebook":
            search_url = normalize_facebook_marketplace_url(search_url)
        self.validate_search_url(search_url)
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            if self.source_type in {"facebook", "mobilede", "marktplaats"}
            else settings.user_agent
        )
        request_headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "nl-NL,nl;q=0.9,de-DE;q=0.8,de;q=0.7,en;q=0.6"
            if self.source_type == "marktplaats"
            else "de-DE,de;q=0.9,en;q=0.8",
        }
        if self.source_type == "facebook":
            request_headers.update(facebook_browser_headers())
        facebook_cookie = safe_cookie_header(profile.get("facebook_cookie_header", ""))
        if self.source_type == "facebook" and facebook_cookie:
            if not facebook_cookie_has_login_session(facebook_cookie):
                raise ValueError(
                    "Facebook Cookie header is incomplete. "
                    "Copy the full Cookie header from a logged-in Marketplace browser request; it must include c_user and xs."
                )
            request_headers["Cookie"] = facebook_cookie
        async with httpx.AsyncClient(
            headers=request_headers,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            try:
                response = await client.get(search_url)
                response.raise_for_status()
            except httpx.TooManyRedirects as exc:
                if self.source_type == "facebook":
                    raise ValueError(
                        "Facebook redirected this Marketplace request too many times. "
                        "Use a normal Marketplace search URL and a complete logged-in Cookie header including c_user and xs."
                    ) from exc
                raise
            except httpx.HTTPStatusError as exc:
                if self.source_type == "facebook" and exc.response.status_code in {400, 401, 403}:
                    raise ValueError(
                        "Facebook blocked the server request. "
                        "If this is a Facebook job, add a Cookie header from your own browser session in Settings and try again."
                    ) from exc
                if self.source_type == "mobilede" and exc.response.status_code in {401, 403}:
                    raise ValueError(
                        "mobile.de blocked the anonymous server request. "
                        "Try a concrete public search result URL; if mobile.de still returns 403, the page cannot be watched from this server."
                    ) from exc
                if self.source_type == "marktplaats" and exc.response.status_code in {401, 403}:
                    raise ValueError(
                        "Marktplaats.nl blocked the anonymous server request. "
                        "Try a concrete public search result URL; if Marktplaats still returns 403, the page cannot be watched from this server."
                    ) from exc
                raise
            if self.source_type == "kleinanzeigen":
                return await self.fetch_paginated_kleinanzeigen(
                    client,
                    {**profile, "search_url": search_url},
                    response.text,
                    str(response.url),
                )
        if self.source_type == "facebook" and facebook_requires_login(response.text, str(response.url)):
            raise ValueError(
                "Facebook returned a login, consent, or upsell page instead of public Marketplace listings. "
                "Add a Cookie header from your own browser session in Settings if this URL works in your browser."
            )
        if self.source_type == "facebook" and "/marketplace/item/" not in response.text:
            raise ValueError(
                "Facebook returned Marketplace HTML without listing links. "
                "This usually means the page is login-, location-, consent-, or JavaScript-rendered for this server session."
            )
        if self.source_type == "facebook":
            return self.parse_facebook_listings(response.text, profile)
        if self.source_type == "mobilede":
            listings = self.parse_mobilede_listings(response.text, profile)
            if not listings:
                raise ValueError(
                    "mobile.de returned HTML without embedded public vehicle results. "
                    "Use a concrete mobile.de search result URL copied from the browser."
                )
            return listings
        if self.source_type == "marktplaats":
            listings = self.parse_marktplaats_listings(response.text, profile)
            if not listings:
                raise ValueError(
                    "Marktplaats.nl returned HTML without public listing cards. "
                    "Use a concrete Marktplaats search result URL copied from the browser."
                )
            return listings
        return self.parse_listings(response.text, profile)

    async def fetch_paginated_kleinanzeigen(
        self,
        client: httpx.AsyncClient,
        profile: dict,
        first_html: str,
        first_url: str,
    ) -> list[ListingCandidate]:
        candidates: list[ListingCandidate] = []
        seen: set[str] = set()
        visited = {first_url}
        html = first_html
        current_url = first_url
        for _ in range(12):
            page_candidates = self.parse_kleinanzeigen_listings(html, profile)
            await self.fill_missing_kleinanzeigen_posted_dates(client, page_candidates)
            for candidate in page_candidates:
                if candidate.content_hash in seen:
                    continue
                seen.add(candidate.content_hash)
                candidates.append(candidate)
            next_url = self.next_page_url(html, current_url)
            if not next_url or next_url in visited or len(candidates) >= 500:
                break
            visited.add(next_url)
            response = await client.get(next_url)
            response.raise_for_status()
            html = response.text
            current_url = str(response.url)
        return candidates[:500]

    async def fill_missing_kleinanzeigen_posted_dates(
        self,
        client: httpx.AsyncClient,
        candidates: list[ListingCandidate],
    ) -> None:
        missing = [candidate for candidate in candidates if not candidate.posted_at_text]
        for candidate in missing[:24]:
            try:
                response = await client.get(candidate.listing_url)
                response.raise_for_status()
            except (httpx.HTTPError, KeyError):
                continue
            candidate.posted_at_text = parse_kleinanzeigen_detail_posted_at(response.text)

    def parse_facebook_listings(self, html: str, profile: dict) -> list[ListingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        anchors = [
            node
            for node in soup.select("a[href*='/marketplace/item/']")
            if isinstance(node, Tag) and node.get("href")
        ]
        candidates: list[ListingCandidate] = []
        seen_urls: set[str] = set()
        for anchor in anchors[:250]:
            listing_url = urljoin("https://www.facebook.com", str(anchor.get("href") or ""))
            listing_url = canonical_facebook_item_url(listing_url)
            if listing_url in seen_urls:
                continue
            seen_urls.add(listing_url)
            card = facebook_listing_card(anchor)
            candidate = self.normalize_facebook_listing(card, anchor, listing_url)
            if candidate:
                candidates.append(candidate)
        return candidates[:200]

    def normalize_facebook_listing(self, card: Tag, anchor: Tag, listing_url: str) -> ListingCandidate | None:
        lines = facebook_text_lines(card)
        anchor_label = clean_text(str(anchor.get("aria-label") or anchor.get("title") or ""))
        if anchor_label and anchor_label not in lines:
            lines.insert(0, anchor_label)
        price_text = next((line for line in lines if looks_like_price(line)), "")
        title = next((line for line in lines if line != price_text and not looks_like_location(line)), "")
        if not title:
            title = clean_text(anchor.get_text(" ", strip=True))
        if not title or len(title) < 3:
            return None
        location_text = next((line for line in lines if line not in {title, price_text} and looks_like_location(line)), "")
        snippet = " · ".join(line for line in lines if line not in {title, price_text, location_text})[:400]
        image = card.find("img") or anchor.find("img")
        thumbnail_url = ""
        if isinstance(image, Tag):
            thumbnail_url = str(image.get("src") or image.get("data-src") or "")
        source_listing_id = extract_facebook_item_id(listing_url)
        hash_input = "|".join([source_listing_id, title, price_text, location_text])
        return ListingCandidate(
            source_type=self.source_type,
            source_listing_id=source_listing_id,
            title=title,
            price_text=price_text,
            price_value=parse_price(price_text),
            location_text=location_text,
            category_text="",
            posted_at_text="",
            description_snippet=snippet,
            listing_url=listing_url,
            thumbnail_url=thumbnail_url,
            content_hash=hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
        )

    def parse_kleinanzeigen_listings(self, html: str, profile: dict) -> list[ListingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        cards = [node for node in soup.select("#srchrslt-adtable .ad-listitem, .aditem") if isinstance(node, Tag)]
        if not cards:
            return []

        candidates: list[ListingCandidate] = []
        seen: set[str] = set()
        for card in cards[:200]:
            candidate = self.normalize_kleinanzeigen_listing(card, profile["search_url"])
            if not candidate or candidate.content_hash in seen:
                continue
            seen.add(candidate.content_hash)
            candidates.append(candidate)
        return candidates

    def normalize_kleinanzeigen_listing(self, card: Tag, base_url: str) -> ListingCandidate | None:
        ad_node = card.select_one(".aditem") if "aditem" not in (card.get("class") or []) else card
        if not isinstance(ad_node, Tag):
            ad_node = card
        link = str(ad_node.get("data-href") or "")
        anchor = card.select_one("a[href*='/s-anzeige/']")
        if not link and isinstance(anchor, Tag):
            link = str(anchor.get("href") or "")
        if not link or not is_kleinanzeigen_listing_url(link):
            return None
        listing_url = urljoin("https://www.kleinanzeigen.de", link) if link else ""
        title = clean_text(first_text(card, [".aditem-main .text-module-begin", ".ellipsis", "h2", "h3", "a"]))
        if not title or not listing_url or is_non_listing_artifact(self.source_type, title, listing_url):
            return None
        price_text = clean_text(first_text(card, [".aditem-main--middle--price-shipping--price", "[class*=price]"]))
        location_text = clean_text(first_text(card, [".aditem-main--top--left", "[class*=location]"]))
        posted_at_text = parse_kleinanzeigen_card_posted_at(card)
        tags = clean_text(first_text(card, [".aditem-main--middle--tags"]))
        snippet = clean_text(first_text(card, [".aditem-main--middle--description", "[class*=description]", "p"]))
        image = card.find("img")
        thumbnail_url = ""
        if isinstance(image, Tag):
            thumbnail_url = urljoin(base_url, str(image.get("src") or image.get("data-src") or image.get("data-imgsrc") or ""))
        source_listing_id = str(ad_node.get("data-adid") or extract_listing_id(listing_url))
        hash_input = "|".join([source_listing_id, title, price_text, location_text])
        return ListingCandidate(
            source_type=self.source_type,
            source_listing_id=source_listing_id,
            title=title,
            price_text=price_text,
            price_value=parse_price(price_text),
            location_text=location_text,
            category_text=tags,
            posted_at_text=posted_at_text,
            description_snippet=snippet[:400],
            listing_url=listing_url,
            thumbnail_url=thumbnail_url,
            content_hash=hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
        )

    def next_page_url(self, html: str, base_url: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "a[rel=next]",
            "a.pagination-next",
            ".pagination-next a",
            "a[aria-label*=Weiter]",
            "a[aria-label*=Next]",
        ]
        for selector in selectors:
            link = soup.select_one(selector)
            if isinstance(link, Tag) and link.get("href"):
                return urljoin(base_url, str(link["href"]))
        for link in soup.find_all("a", href=True):
            if not isinstance(link, Tag):
                continue
            label = clean_text(link.get_text(" ", strip=True)).lower()
            href = str(link.get("href") or "")
            if label in {"weiter", "next", ">"} or "seite:" in href or "pageNum=" in href:
                return urljoin(base_url, href)
        return ""

    def parse_mobilede_listings(self, html: str, profile: dict) -> list[ListingCandidate]:
        state = extract_mobilede_initial_state(html)
        items = (
            state.get("search", {})
            .get("srp", {})
            .get("data", {})
            .get("searchResults", {})
            .get("items", [])
        )
        candidates: list[ListingCandidate] = []
        seen: set[str] = set()
        for item in items[:200]:
            if not isinstance(item, dict):
                continue
            candidate = self.normalize_mobilede_listing(item, profile["search_url"])
            if not candidate or candidate.content_hash in seen:
                continue
            seen.add(candidate.content_hash)
            candidates.append(candidate)
        return candidates

    def normalize_mobilede_listing(self, item: dict, base_url: str) -> ListingCandidate | None:
        listing_id = str(item.get("id") or "")
        title = clean_text(item.get("title") or " ".join([str(item.get("shortTitle") or ""), str(item.get("subTitle") or "")]))
        if not listing_id or not title:
            return None
        price = item.get("price") if isinstance(item.get("price"), dict) else {}
        attributes = item.get("attr") if isinstance(item.get("attr"), dict) else {}
        contact = item.get("contactInfo") if isinstance(item.get("contactInfo"), dict) else {}
        image = item.get("previewImage") if isinstance(item.get("previewImage"), dict) else {}
        price_text = clean_text(str(price.get("gross") or price.get("net") or ""))
        relative_url = str(item.get("relativeUrl") or f"/fahrzeuge/details.html?id={listing_id}")
        listing_url = urljoin("https://suchen.mobile.de/", relative_url)
        location_text = clean_text(contact.get("location") or " ".join([str(attributes.get("z") or ""), str(attributes.get("loc") or "")]))
        category_text = clean_text(item.get("category") or attributes.get("c") or "")
        snippet = clean_text(
            " · ".join(
                str(value)
                for value in [
                    attributes.get("fr"),
                    attributes.get("ml"),
                    attributes.get("pw"),
                    attributes.get("ft"),
                    attributes.get("tr"),
                    contact.get("typeLocalized"),
                    contact.get("name"),
                ]
                if value
            )
        )
        thumbnail_url = urljoin(base_url, str(image.get("src") or ""))
        hash_input = "|".join([listing_id, title, price_text, location_text])
        return ListingCandidate(
            source_type=self.source_type,
            source_listing_id=listing_id,
            title=title,
            price_text=price_text,
            price_value=float(price["grossAmount"]) if isinstance(price.get("grossAmount"), int | float) else parse_price(price_text),
            location_text=location_text,
            category_text=category_text,
            posted_at_text=clean_text(attributes.get("fr") or ""),
            description_snippet=snippet[:400],
            listing_url=listing_url,
            thumbnail_url=thumbnail_url,
            content_hash=hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
        )

    def parse_marktplaats_listings(self, html: str, profile: dict) -> list[ListingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        cards = [node for node in soup.select("li.hz-Listing, article.hz-Listing, .hz-Listing") if isinstance(node, Tag)]
        if not cards:
            cards = [
                node
                for node in soup.select("li, article")
                if isinstance(node, Tag) and node.select_one("a[href^='/v/'], a[href*='marktplaats.nl/v/']")
            ]
        candidates: list[ListingCandidate] = []
        seen: set[str] = set()
        for card in cards[:200]:
            candidate = self.normalize_marktplaats_listing(card, profile["search_url"])
            if not candidate or candidate.content_hash in seen:
                continue
            seen.add(candidate.content_hash)
            candidates.append(candidate)
        return candidates

    def normalize_marktplaats_listing(self, card: Tag, base_url: str) -> ListingCandidate | None:
        anchor = card.select_one("a[href^='/v/'], a[href*='marktplaats.nl/v/']")
        if not isinstance(anchor, Tag):
            return None
        listing_url = urljoin("https://www.marktplaats.nl", str(anchor.get("href") or ""))
        if not is_marktplaats_listing_url(listing_url):
            return None
        title = clean_text(
            first_text_by_class_pattern(card, [r"\bListingTitle_hz-Listing-title-new"])
            or first_text(
                card,
                [
                    "[class*=listing-title]",
                    "[class*=title-new]",
                    "h2",
                    "h3",
                    "a[title]",
                    "a",
                ],
            )
        )
        if not title:
            title = clean_text(str(anchor.get("title") or anchor.get("aria-label") or ""))
        if not title or len(title) < 3:
            return None
        price_text = clean_text(
            first_text_by_class_pattern(card, [r"\bListingPrice_hz-Listing-price"])
            or first_text(card, ["[class*=price]", "[data-testid*=price]"])
        )
        location_text = clean_text(
            first_text_by_class_pattern(card, [r"\bListingLocationDetails_hz-Listing-location-label"])
            or first_text(card, ["[class*=location]", "[data-testid*=location]"])
        )
        posted_at_text = clean_text(
            first_text_by_class_pattern(card, [r"\bListingDate_hz-Listing-date"])
            or first_text(card, ["[class*=date]", "time"])
        )
        category_text = marktplaats_category_from_url(listing_url)
        snippet = clean_text(
            first_text_by_class_pattern(card, [r"\bListingDescription_hz-Listing-description"])
            or first_text(card, ["[class*=Description]", "[class*=description]", "p"])
        )
        image = card.find("img")
        thumbnail_url = ""
        if isinstance(image, Tag):
            thumbnail_url = urljoin(base_url, str(image.get("src") or image.get("data-src") or ""))
        source_listing_id = extract_marktplaats_listing_id(listing_url)
        hash_input = "|".join([source_listing_id, title, price_text, location_text])
        return ListingCandidate(
            source_type=self.source_type,
            source_listing_id=source_listing_id,
            title=title,
            price_text=price_text,
            price_value=parse_price(price_text),
            location_text=location_text,
            category_text=category_text,
            posted_at_text=posted_at_text,
            description_snippet=snippet[:400],
            listing_url=listing_url,
            thumbnail_url=thumbnail_url,
            content_hash=hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
        )

    def parse_listings(self, html: str, profile: dict) -> list[ListingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "article",
            "[data-adid]",
            "[data-listing-id]",
            ".aditem",
            ".listing",
            ".result",
            "li",
        ]
        cards: list[Tag] = []
        for selector in selectors:
            cards = [node for node in soup.select(selector) if isinstance(node, Tag) and node.find("a", href=True)]
            if len(cards) >= 2:
                break
        if not cards:
            cards = [a.parent for a in soup.select("a[href]") if isinstance(a.parent, Tag)]

        candidates: list[ListingCandidate] = []
        seen: set[str] = set()
        for card in cards[:200]:
            candidate = self.normalize_listing(card, profile["search_url"])
            if not candidate or candidate.content_hash in seen:
                continue
            seen.add(candidate.content_hash)
            candidates.append(candidate)
        return candidates

    def normalize_listing(self, card: Tag, base_url: str) -> ListingCandidate | None:
        anchor = card.find("a", href=True)
        if not isinstance(anchor, Tag):
            return None
        listing_url = urljoin(base_url, str(anchor.get("href", "")))
        title = clean_text(
            first_text(
                card,
                [
                    "[data-testid*=title]",
                    ".title",
                    ".aditem-main--middle--title",
                    "h1",
                    "h2",
                    "h3",
                    "a",
                ],
            )
        )
        if not title or len(title) < 3 or is_non_listing_artifact(self.source_type, title, listing_url):
            return None
        price_text = clean_text(first_text(card, ["[class*=price]", "[data-testid*=price]", ".aditem-main--middle--price-shipping--price"]))
        location_text = clean_text(first_text(card, ["[class*=location]", "[data-testid*=location]", ".aditem-main--top--left"]))
        category_text = clean_text(first_text(card, ["[class*=category]", "[data-testid*=category]"]))
        posted_at_text = clean_text(first_text(card, ["time", "[class*=date]", "[data-testid*=date]"]))
        snippet = clean_text(first_text(card, ["[class*=description]", "[class*=snippet]", "p"]))
        image = card.find("img")
        thumbnail_url = ""
        if isinstance(image, Tag):
            thumbnail_url = urljoin(base_url, str(image.get("src") or image.get("data-src") or ""))
        source_listing_id = str(
            card.get("data-adid")
            or card.get("data-listing-id")
            or extract_listing_id(listing_url)
        )
        hash_input = "|".join([title, price_text, location_text, listing_url])
        content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        return ListingCandidate(
            source_type=self.source_type,
            source_listing_id=source_listing_id,
            title=title,
            price_text=price_text,
            price_value=parse_price(price_text),
            location_text=location_text,
            category_text=category_text,
            posted_at_text=posted_at_text,
            description_snippet=snippet[:400],
            listing_url=listing_url,
            thumbnail_url=thumbnail_url,
            content_hash=content_hash,
        )


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_kleinanzeigen_card_posted_at(card: Tag) -> str:
    date_node = card.select_one(".aditem-main--top--right, time, [class*=date]")
    if not isinstance(date_node, Tag):
        return ""
    candidates = [
        str(date_node.get("datetime") or ""),
        str(date_node.get("title") or ""),
        date_node.get_text(" ", strip=True),
    ]
    return next((clean_text(value) for value in candidates if clean_text(value)), "")


def parse_kleinanzeigen_detail_posted_at(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        "#viewad-extra-info .icon-calendar-gray-simple + span",
        "#viewad-extra-info span",
        "time[datetime]",
        ".aditem-main--top--right",
    ]
    for selector in selectors:
        for node in soup.select(selector):
            if not isinstance(node, Tag):
                continue
            candidates = [
                str(node.get("datetime") or ""),
                str(node.get("title") or ""),
                node.get_text(" ", strip=True),
            ]
            for candidate in candidates:
                text = clean_text(candidate)
                if re.search(r"\b(\d{1,2}\.\d{1,2}\.(?:\d{2}|\d{4})|heute|gestern)\b", text, re.IGNORECASE):
                    return text
    return ""


def parse_listing_availability(source_type: str, status_code: int, html: str, final_url: str) -> str:
    if status_code in {404, 410}:
        return "deleted"
    text = clean_text(BeautifulSoup(html, "html.parser").get_text(" ", strip=True)).lower()
    if source_type == "kleinanzeigen":
        if any(
            phrase in text
            for phrase in (
                "anzeige ist nicht mehr verfügbar",
                "anzeige wurde gelöscht",
                "anzeige nicht mehr verfügbar",
                "nicht mehr verfügbar",
                "seite wurde nicht gefunden",
            )
        ):
            return "deleted"
        if re.search(r"\breserviert\b", text):
            return "reserved"
        if "kleinanzeigen.de/s-anzeige/" not in final_url and "/s-anzeige/" not in final_url:
            return "unknown"
    if source_type == "facebook":
        if any(phrase in text for phrase in ("listing is not available", "this content isn't available", "inserat ist nicht verfügbar")):
            return "deleted"
        if any(phrase in text for phrase in ("sold", "verkauft", "reserved", "reserviert")):
            return "reserved"
        if "login" in final_url:
            return "unknown"
    if source_type == "marktplaats":
        if any(
            phrase in text
            for phrase in (
                "advertentie is niet beschikbaar",
                "advertentie bestaat niet meer",
                "deze advertentie is verwijderd",
                "deze advertentie is niet meer beschikbaar",
            )
        ):
            return "deleted"
        if any(phrase in text for phrase in ("gereserveerd", "verkocht", "reserved", "sold")):
            return "reserved"
        if "/v/" not in urlparse(final_url).path:
            return "unknown"
    return "active"


def first_text(card: Tag, selectors: list[str]) -> str:
    for selector in selectors:
        node = card.select_one(selector)
        if node:
            return node.get_text(" ", strip=True)
    return ""


def first_text_by_class_pattern(card: Tag, patterns: list[str]) -> str:
    compiled = [re.compile(pattern) for pattern in patterns]
    for node in card.find_all(True):
        if not isinstance(node, Tag):
            continue
        classes = " ".join(str(item) for item in (node.get("class") or []))
        if classes and any(pattern.search(classes) for pattern in compiled):
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return ""


def is_kleinanzeigen_listing_url(url: str) -> bool:
    parsed = urlparse(urljoin("https://www.kleinanzeigen.de", url))
    return "kleinanzeigen.de" in parsed.netloc.lower() and "/s-anzeige/" in parsed.path


def is_marktplaats_listing_url(url: str) -> bool:
    parsed = urlparse(urljoin("https://www.marktplaats.nl", url))
    return parsed.netloc.lower() in {"marktplaats.nl", "www.marktplaats.nl"} and parsed.path.startswith("/v/")


def is_non_listing_artifact(source_type: str, title: str, listing_url: str) -> bool:
    normalized_title = clean_text(title).lower()
    parsed = urlparse(urljoin("https://www.kleinanzeigen.de", listing_url))
    path = parsed.path.lower()
    if source_type == "kleinanzeigen":
        if "passwort vergessen" in normalized_title or "passwort-vergessen" in path:
            return True
        if (
            "erstelle ein konto" in normalized_title
            or "konto erstellen" in normalized_title
            or "registrieren" in normalized_title
            or "konto-erstellen" in path
            or "registrieren" in path
            or "/m-benutzer-anmeldung" in path
        ):
            return True
        if "kleinanzeigen.de" in parsed.netloc.lower() and "/s-anzeige/" not in path:
            return True
    return False


def extract_listing_id(url: str) -> str:
    parsed = urlparse(url)
    tail = parsed.path.rstrip("/").split("/")[-1]
    return tail or hashlib.sha1(url.encode("utf-8")).hexdigest()


def extract_marktplaats_listing_id(url: str) -> str:
    parsed = urlparse(url)
    match = re.search(r"/([am]\d{7,})(?:-|/|$)", parsed.path)
    return match.group(1) if match else extract_listing_id(url)


def marktplaats_category_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] != "v":
        return ""
    return clean_text(parts[1].replace("-", " "))


def canonical_facebook_item_url(url: str) -> str:
    parsed = urlparse(url)
    path_match = re.search(r"(/marketplace/item/\d+)", parsed.path)
    path = path_match.group(1) + "/" if path_match else parsed.path
    return urlunparse(("https", "www.facebook.com", path, "", "", ""))


def normalize_facebook_marketplace_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host not in {"facebook.com", "www.facebook.com", "m.facebook.com"}:
        return url
    path = parsed.path
    np_search = re.match(r"^/marketplace/np/([^/]+)/search/?$", path, re.IGNORECASE)
    if np_search:
        path = f"/marketplace/{np_search.group(1)}/search/"
    return urlunparse(("https", "www.facebook.com", path, "", parsed.query, ""))


def extract_facebook_item_id(url: str) -> str:
    match = re.search(r"/marketplace/item/(\d+)", url)
    return match.group(1) if match else extract_listing_id(url)


def facebook_listing_card(anchor: Tag) -> Tag:
    card = anchor
    current: Tag | None = anchor
    for _ in range(5):
        parent = current.parent if current else None
        if not isinstance(parent, Tag):
            break
        text = clean_text(parent.get_text(" ", strip=True))
        if len(text) > 25 and parent.find("img"):
            card = parent
        current = parent
    return card


def facebook_text_lines(card: Tag) -> list[str]:
    lines: list[str] = []
    for raw in card.stripped_strings:
        text = clean_text(str(raw))
        if not text or text in lines:
            continue
        if text.lower() in {"sponsored", "gesponsert"}:
            continue
        lines.append(text)
    return lines


def looks_like_price(value: str) -> bool:
    text = value.strip().lower()
    return bool(re.search(r"(€|eur|\$|£|\bfree\b|kostenlos|zu verschenken|\bvb\b|\bvhb\b)", text))


def looks_like_location(value: str) -> bool:
    text = value.strip()
    return bool(re.search(r"\b\d{5}\b", text) or re.search(r"\bkm\b", text, re.IGNORECASE))


def apply_kleinanzeigen_location_to_url(url: str, location_hint: str) -> str:
    location, radius = parse_location_hint(location_hint)
    if not location:
        return url
    parsed = urlparse(url)
    if "kleinanzeigen.de" not in parsed.netloc.lower():
        return url
    query = parse_qs(parsed.query, keep_blank_values=True)
    if query.get("locationStr") or re.search(r"l\d+(?:r\d+)?(?:\D|$)", parsed.path):
        return url
    query["locationStr"] = [location]
    if radius:
        query["radius"] = [radius]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def parse_location_hint(value: str) -> tuple[str, str]:
    normalized = value.replace("·", ",").strip()
    location = ""
    radius = ""
    for part in normalized.split(","):
        cleaned = part.strip()
        if not cleaned or cleaned.lower() in {"whole place", "ganzer ort"}:
            continue
        cleaned = re.sub(r"^(?:map point|kartenpunkt)\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
        if not cleaned:
            continue
        radius_match = re.search(r"\+?\s*(\d+)\s*km\b", cleaned, re.IGNORECASE)
        if radius_match:
            radius = radius_match.group(1)
            continue
        if re.fullmatch(r"-?\d+\.\d+", cleaned):
            continue
        if not location:
            location = cleaned
    return location, radius


def facebook_requires_login(html: str, final_url: str) -> bool:
    lowered = html.lower()
    parsed = urlparse(final_url)
    return (
        "/login" in parsed.path
        or "/checkpoint" in parsed.path
        or "loggedinlandingupselleligible" in lowered
        or "marketplace_logged_out_content" in lowered
        or "loginbutton" in lowered
        or "login_form" in lowered
        or "facebook.com/login" in lowered
        or 'href="/login' in lowered
        or "/login/device-based/" in lowered
    )


def facebook_browser_headers() -> dict[str, str]:
    return {
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }


def safe_cookie_header(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    cookie = extract_cookie_header_value(raw)
    if not cookie or "\n" in cookie or "\r" in cookie:
        return ""
    if ":" in cookie.split(";", 1)[0]:
        return ""
    return cookie


def facebook_cookie_has_login_session(cookie: str) -> bool:
    names = {part.split("=", 1)[0].strip() for part in cookie.split(";") if "=" in part}
    return {"c_user", "xs"}.issubset(names)


def extract_cookie_header_value(value: str) -> str:
    for line in value.splitlines():
        name, separator, rest = line.partition(":")
        if separator and name.strip().lower() == "cookie":
            return rest.strip()
    if value.lower().startswith("cookie:"):
        return value.split(":", 1)[1].strip()
    return value


def parse_price(value: str) -> float | None:
    lowered = value.lower()
    if "kostenlos" in lowered or "free" in lowered or "zu verschenken" in lowered:
        return 0.0
    match = re.search(r"(\d+(?:[.,]\d{1,2})?)", lowered.replace(".", ""))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def extract_mobilede_initial_state(html: str) -> dict:
    marker = "window.__INITIAL_STATE__"
    marker_index = html.find(marker)
    if marker_index < 0:
        return {}
    start = html.find("{", marker_index)
    if start < 0:
        return {}
    in_string = False
    escaped = False
    depth = 0
    for index, char in enumerate(html[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(html[start : index + 1])
                except json.JSONDecodeError:
                    return {}
                return data if isinstance(data, dict) else {}
    return {}


def get_connector(source_type: str) -> MarketplaceConnector:
    if source_type in {"html", "kleinanzeigen", "facebook", "mobilede", "marktplaats"}:
        return HtmlListingConnector(source_type)
    raise ValueError(f"Unsupported source type: {source_type}")
