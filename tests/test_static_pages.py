from __future__ import annotations

import unittest
from pathlib import Path

from app.main import static_page_response


class StaticPageTests(unittest.TestCase):
    def test_index_assets_are_versioned(self) -> None:
        response = static_page_response("index.html")
        html = response.body.decode("utf-8")

        self.assertNotIn("__ASSET_VERSION__", html)
        self.assertIn("/static/app.js?v=", html)
        self.assertIn("/static/styles.css?v=", html)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_setup_includes_scraping_notice_before_form(self) -> None:
        response = static_page_response("setup.html")
        html = response.body.decode("utf-8")

        notice_index = html.index("Hinweis zu Scraping und Plattformregeln")
        form_index = html.index('id="setup-form"')
        self.assertLess(notice_index, form_index)
        self.assertIn("Kleinanzeigen", html)
        self.assertIn("Nutzungsbedingungen", html)

    def test_index_includes_facebook_setup_guide(self) -> None:
        response = static_page_response("index.html")
        html = response.body.decode("utf-8")

        self.assertIn('data-i18n="settings.facebookGuideTitle"', html)
        self.assertIn("https://www.facebook.com/marketplace/", html)

    def test_app_uses_browser_language_when_unset(self) -> None:
        app_js = (Path(__file__).resolve().parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn("detectBrowserLanguage", app_js)
        self.assertIn("navigator.languages", app_js)
        self.assertIn('savedLanguage || detectBrowserLanguage()', app_js)

    def test_quick_job_has_kleinanzeigen_notebook_category(self) -> None:
        app_js = (Path(__file__).resolve().parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('"Elektronik > Notebooks"', app_js)
        self.assertIn('"notebooks"', app_js)
        self.assertIn('"278"', app_js)

    def test_index_exposes_marktplaats_source_option(self) -> None:
        response = static_page_response("index.html")
        html = response.body.decode("utf-8")
        app_js = (Path(__file__).resolve().parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('value="marktplaats"', html)
        self.assertIn('data-source-option="marktplaats"', html)
        self.assertIn("https://www.marktplaats.nl/q/", app_js)


if __name__ == "__main__":
    unittest.main()
