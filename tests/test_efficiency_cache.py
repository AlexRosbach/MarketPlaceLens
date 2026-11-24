from app.efficiency import BoundedCache, search_key

def test_cache_isolation_and_budget():
    cache = BoundedCache(60, 2, 4)
    cache.put("a", [1], 2)
    value = cache.get("a")
    value.append(2)
    assert cache.get("a") == [1]
    cache.put("b", [2], 3)
    assert cache.get("a") is None
    assert cache.get("b") == [2]
    assert search_key({"user_id": 1, "search_url": "https://example.test"}) != search_key({"user_id": 2, "search_url": "https://example.test"})
