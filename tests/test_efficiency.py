from app.connectors import parse_price

def test_international_price_formats():
    for text, expected in [("1.299,99 €", 1299.99), ("1,299.99 EUR", 1299.99), ("19.99 EUR", 19.99), ("19,99 €", 19.99), ("1.299 €", 1299), ("zu verschenken", 0)]:
        assert parse_price(text) == expected
