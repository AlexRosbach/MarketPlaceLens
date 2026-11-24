from app.duplicates import duplicate_score

def test_duplicate_candidates_are_conservative():
    left = {"title":"Example Phone 256GB","source_type":"a","location_text":"Example City","price_value":200}
    assert duplicate_score(left,{**left,"source_type":"b"}) == 1
    assert duplicate_score(left,{**left,"source_type":"b","title":"Example Phone 128GB"}) == 0
    assert duplicate_score(left,{**left,"source_type":"b","location_text":"Another city"}) == 0
