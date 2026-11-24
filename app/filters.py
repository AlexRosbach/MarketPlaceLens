from __future__ import annotations

import re
from dataclasses import dataclass

from .connectors import ListingCandidate


@dataclass
class FilterResult:
    status: str
    score: int
    reason: str
    matched_reason: str


def apply_filters(candidate: ListingCandidate, profile: dict) -> FilterResult:
    haystack = " ".join(
        [
            candidate.title,
            candidate.description_snippet,
            candidate.category_text,
            candidate.location_text,
            candidate.price_text,
        ]
    ).lower()
    category = candidate.category_text.lower()

    if profile.get("min_price") is not None and candidate.price_value is not None:
        if candidate.price_value < float(profile["min_price"]):
            return FilterResult("hidden", 0, "below_min_price", "price below minimum")
    if profile.get("max_price") is not None and candidate.price_value is not None:
        if candidate.price_value > float(profile["max_price"]):
            return FilterResult("hidden", 0, "above_max_price", "price above maximum")

    location_hint = profile.get("location_hint", "")
    # Radius filtering requires provider-supported coordinates; unsupported sources
    # must not silently claim that distance has been verified.
    if has_radius_hint(location_hint) and candidate.source_type != "kleinanzeigen":
        return FilterResult("hidden", 0, "radius_unverified", "radius cannot be verified for this source")
    location_terms = location_filter_terms(location_hint)
    if location_terms and not any(term in candidate.location_text.lower() for term in location_terms):
        return FilterResult("hidden", 0, "location_mismatch", "location does not match profile")

    for excluded in profile.get("excluded_categories", []):
        if excluded and excluded.lower() in category:
            return FilterResult("hidden", 0, f"excluded_category:{excluded}", "excluded category")

    missing = [word for word in profile.get("required_keywords", []) if word and word.lower() not in haystack]
    if missing:
        return FilterResult("hidden", 0, f"missing_required:{', '.join(missing)}", "required keyword missing")

    for word in profile.get("exclude_keywords", []):
        if word and word.lower() in haystack:
            return FilterResult("hidden", 0, f"excluded_keyword:{word}", "excluded keyword")

    include_hits = [word for word in profile.get("include_keywords", []) if word and word.lower() in haystack]
    required_hits = [word for word in profile.get("required_keywords", []) if word and word.lower() in haystack]
    score = 10 + (len(include_hits) * 10) + (len(required_hits) * 15)
    if candidate.price_value == 0:
        score += 5
    matched = ", ".join(include_hits or required_hits) or "new listing matched profile"
    return FilterResult("new", score, "", matched)


def location_filter_terms(value: str) -> list[str]:
    terms: list[str] = []
    normalized = value.replace("·", ",").replace("/", ",")
    if normalized.lower().startswith(("map point:", "kartenpunkt:")):
        return []
    if has_radius_hint(normalized):
        return []
    for part in normalized.split(","):
        cleaned = part.strip().lower()
        if (
            not cleaned
            or cleaned.endswith("km")
            or cleaned.startswith("+")
            or (cleaned.isdigit() and len(cleaned) != 5)
            or cleaned in {"whole place", "ganzer ort"}
        ):
            continue
        terms.append(cleaned)
    return terms


def has_radius_hint(value: str) -> bool:
    return bool(re.search(r"\+?\s*\d+\s*km\b", value, re.IGNORECASE))
