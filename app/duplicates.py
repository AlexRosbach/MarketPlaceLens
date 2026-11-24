import re
from difflib import SequenceMatcher

def normalized_title(value):
    return " ".join(re.findall(r"\w+", (value or "").casefold()))

def duplicate_score(left, right):
    if left["source_type"] == right["source_type"]:
        return 0.0
    a, b = normalized_title(left["title"]), normalized_title(right["title"])
    if not a or not b:
        return 0.0
    numbers = lambda text: {w for w in text.split() if any(c.isdigit() for c in w)}
    if numbers(a) != numbers(b):
        return 0.0
    if not left["location_text"] or normalized_title(left["location_text"]) != normalized_title(right["location_text"]):
        return 0.0
    p, q = left["price_value"], right["price_value"]
    if p is None or q is None or abs(p-q) > max(2, 0.05 * max(p,q)):
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
