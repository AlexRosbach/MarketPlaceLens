from app.price_comparison import select_amazon_offers

def test_amazon_new_used_and_map():
    item = {"itemInfo":{"title":{"displayValue":"Example Phone 256GB"}},"detailPageURL":"https://www.amazon.de/dp/EXAMPLE",
            "offersV2":{"listings":[{"condition":{"value":"New"},"availability":{"type":"IN_STOCK"},"price":{"money":{"amount":299,"currency":"EUR"}}},
              {"condition":{"value":"Used"},"availability":{"type":"IN_STOCK"},"price":{"money":{"amount":199,"currency":"EUR"}}},
              {"condition":{"value":"New"},"availability":{"type":"IN_STOCK"},"violatesMAP":True,"price":{"money":{"amount":99,"currency":"EUR"}}}]}}
    offers = select_amazon_offers("Example Phone 256GB",[item])
    assert [(o["condition"],o["price"]) for o in offers] == [("new",299),("used",199)]
