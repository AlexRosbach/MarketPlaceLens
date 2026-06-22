from __future__ import annotations

import unittest

from app.main import ai_token_limit_payload, listing_assessment_prompt, normalize_inquiry_text, normalize_search_draft


class AiDraftTests(unittest.TestCase):
    def test_normalize_search_draft_accepts_json_block(self) -> None:
        draft = normalize_search_draft(
            """
            ```json
            {
              "name": "Defekte Elektronik bis 100 Euro",
              "source_type": "kleinanzeigen",
              "query": "defekte elektronik",
              "category_hint": "Elektronik",
              "location": "10115",
              "radius_km": 50,
              "max_price": 100,
              "max_listing_age_days": 14,
              "required_keywords": ["defekt"],
              "exclude_keywords": ["gesuch"]
            }
            ```
            """
        )

        self.assertEqual(draft["source_type"], "kleinanzeigen")
        self.assertEqual(draft["query"], "defekte elektronik")
        self.assertEqual(draft["radius_km"], 50)
        self.assertEqual(draft["max_price"], 100.0)
        self.assertEqual(draft["required_keywords"], ["defekt"])

    def test_normalize_search_draft_defaults_unknown_source(self) -> None:
        draft = normalize_search_draft('{"source_type":"unknown","query":"stuhl"}')

        self.assertEqual(draft["source_type"], "kleinanzeigen")
        self.assertEqual(draft["max_listing_age_days"], 365)

    def test_normalize_search_draft_accepts_marktplaats_source(self) -> None:
        draft = normalize_search_draft('{"source_type":"marktplaats","query":"bakfiets marktplaats.nl"}')

        self.assertEqual(draft["source_type"], "marktplaats")
        self.assertEqual(draft["query"], "bakfiets")

    def test_normalize_search_draft_cleans_price_from_query_and_infers_notebooks(self) -> None:
        draft = normalize_search_draft(
            """
            {
              "name": "Macbook air M2 unter 600€",
              "source_type": "kleinanzeigen",
              "query": "Macbook air M2 unter 600€",
              "category_hint": "",
              "location": "",
              "radius_km": null,
              "max_price": null,
              "required_keywords": ["Macbook", "Air", "M2"],
              "exclude_keywords": []
            }
            """
        )

        self.assertEqual(draft["query"], "Macbook air M2")
        self.assertEqual(draft["name"], "Macbook air M2")
        self.assertEqual(draft["max_price"], 600.0)
        self.assertEqual(draft["category_hint"], "Elektronik > Notebooks")

    def test_ollama_uses_completion_token_limit(self) -> None:
        self.assertEqual(ai_token_limit_payload("ollama", 20), {"max_completion_tokens": 20})

    def test_openai_uses_chat_token_limit(self) -> None:
        self.assertEqual(ai_token_limit_payload("openai", 20), {"max_tokens": 20})

    def test_listing_assessment_prompt_focuses_search_value_and_market_price(self) -> None:
        prompt = listing_assessment_prompt(
            {
                "title": "MacBook Air M2 256 GB",
                "price_text": "590 EUR",
                "profile_name": "MacBook Air M2 bis 600",
                "description_snippet": "Guter Zustand, Akku 91%",
            }
        )
        joined = "\n".join(message["content"] for message in prompt)

        self.assertIn("useful for the saved search", joined)
        self.assertIn("currently usual market-price range", joined)
        self.assertIn("Search job: MacBook Air M2 bis 600", joined)

    def test_normalize_inquiry_text_removes_buyer_name_from_greeting(self) -> None:
        text = normalize_inquiry_text(
            "Hallo Mia,\nist der Artikel noch verfügbar?\n\nViele Grüße, Mia",
            {"display_name": "Mia"},
        )

        self.assertEqual(text, "Hallo,\nist der Artikel noch verfügbar?\n\nViele Grüße, Mia")

    def test_normalize_inquiry_text_keeps_signature_name(self) -> None:
        text = normalize_inquiry_text(
            "Guten Tag Mia, ich könnte heute abholen.\nViele Grüße, Mia",
            {"display_name": "Mia"},
        )

        self.assertEqual(text, "Guten Tag, ich könnte heute abholen.\nViele Grüße, Mia")


if __name__ == "__main__":
    unittest.main()
