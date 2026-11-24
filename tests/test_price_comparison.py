from app.price_comparison import match_score, select_ebay_offers

def test_variant_mismatch_rejected():
    assert match_score("Example Phone 256GB", "Example Phone 128GB") == 0

def test_new_eur_offer_only():
    item = {"title": "Example Phone 256GB", "conditionId": "1000", "price": {"value": "299", "currency": "EUR"}, "itemWebUrl": "https://www.ebay.de/itm/123"}
    assert select_ebay_offers("Example Phone 256GB", [item])[0]["price"] == 299
    assert not select_ebay_offers("Example Phone 256GB", [{**item, "conditionId": "3000"}])
