from __future__ import annotations

import asyncio
import unittest

from app.connectors import (
    HtmlListingConnector,
    apply_kleinanzeigen_location_to_url,
    extract_marktplaats_listing_id,
    facebook_cookie_has_login_session,
    facebook_browser_headers,
    facebook_requires_login,
    normalize_facebook_marketplace_url,
    parse_kleinanzeigen_detail_posted_at,
    parse_listing_availability,
    safe_cookie_header,
    validate_public_fetch_host,
)


class FakeResponse:
    def __init__(self, html: str, url: str) -> None:
        self.text = html
        self.url = url

    def raise_for_status(self) -> None:
        return None


class FakeClient:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.requested: list[str] = []

    async def get(self, url: str) -> FakeResponse:
        self.requested.append(url)
        return FakeResponse(self.pages[url], url)


def article(title: str, href: str, price: str = "10 EUR") -> str:
    return f"""
    <article class="aditem" data-adid="{href.rsplit('/', 1)[-1]}">
      <div class="aditem-main--top--right">Heute</div>
      <a href="{href}"><h2>{title}</h2></a>
      <p class="aditem-main--middle--price-shipping--price">{price}</p>
    </article>
    """


class ConnectorTests(unittest.TestCase):
    def test_safe_cookie_header_rejects_multiline_values(self) -> None:
        self.assertEqual(safe_cookie_header(" c_user=1; xs=2; "), "c_user=1; xs=2;")
        self.assertEqual(safe_cookie_header("Cookie: c_user=1; xs=2;"), "c_user=1; xs=2;")
        self.assertEqual(safe_cookie_header("host: www.facebook.com\ncookie: c_user=1; xs=2;\naccept: text/html"), "c_user=1; xs=2;")
        self.assertEqual(safe_cookie_header("c_user=1\nX-Bad: yes"), "")
        self.assertEqual(safe_cookie_header("X-Bad: yes"), "")

    def test_facebook_browser_headers_include_navigation_context(self) -> None:
        headers = facebook_browser_headers()

        self.assertEqual(headers["Sec-Fetch-Dest"], "document")
        self.assertEqual(headers["Sec-Fetch-Mode"], "navigate")
        self.assertEqual(headers["Upgrade-Insecure-Requests"], "1")

    def test_facebook_cookie_requires_logged_in_session_pair(self) -> None:
        self.assertTrue(facebook_cookie_has_login_session("c_user=1; xs=token; wd=1280x720"))
        self.assertFalse(facebook_cookie_has_login_session("c_user=1; presence=C; wd=1280x720"))

    def test_facebook_np_search_url_is_normalized(self) -> None:
        url = normalize_facebook_marketplace_url(
            "https://www.facebook.com/marketplace/np/105483586153093/search?query=porsche%20cayenne&radius=60"
        )

        self.assertEqual(
            url,
            "https://www.facebook.com/marketplace/105483586153093/search/?query=porsche%20cayenne&radius=60",
        )

    def test_facebook_marketplace_item_links_are_parsed(self) -> None:
        html = """
        <html><body>
          <div>
            <a href="/marketplace/item/123456789/?ref=browse_tab">
              <img src="https://example.test/photo.jpg" />
              <span>120 €</span>
              <span>Vintage Stuhl</span>
              <span>10115 Berlin</span>
            </a>
          </div>
        </body></html>
        """
        connector = HtmlListingConnector("facebook")
        listings = connector.parse_facebook_listings(html, {"search_url": "https://www.facebook.com/marketplace/"})
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].source_listing_id, "123456789")
        self.assertEqual(listings[0].listing_url, "https://www.facebook.com/marketplace/item/123456789/")
        self.assertEqual(listings[0].title, "Vintage Stuhl")
        self.assertEqual(listings[0].price_text, "120 €")
        self.assertEqual(listings[0].location_text, "10115 Berlin")

    def test_marktplaats_search_url_validation_accepts_marktplaats_only(self) -> None:
        connector = HtmlListingConnector("marktplaats")

        connector.validate_search_url("https://www.marktplaats.nl/q/fiets/")
        with self.assertRaises(ValueError):
            connector.validate_search_url("https://www.example.test/q/fiets/")

    def test_marktplaats_parser_reads_listing_cards(self) -> None:
        html = """
        <ul>
          <li class="hz-Listing hz-Listing--list-item">
            <a href="/v/fietsen-en-brommers/fietsen/a1511355607-bakfiets">
              <img src="https://images.example.test/bakfiets.jpg" alt="Bakfiets">
            </a>
            <span class="ListingTitle_hz-Listing-title-new__YIv8B">Bakfiets Urban Arrow</span>
            <h5 class="ListingPrice_hz-Listing-price__tlzf6">€ 1.250,00</h5>
            <span class="ListingLocationDetails_hz-Listing-location-label__GfAXl">Amsterdam</span>
            <span class="ListingDate_hz-Listing-date__cX8M_">Vandaag</span>
            <p class="ListingDescription_hz-Listing-description__x">Goed onderhouden bakfiets.</p>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("marktplaats").parse_marktplaats_listings(
            html,
            {"search_url": "https://www.marktplaats.nl/q/bakfiets/"},
        )

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.source_type, "marktplaats")
        self.assertEqual(listing.source_listing_id, "a1511355607")
        self.assertEqual(listing.title, "Bakfiets Urban Arrow")
        self.assertEqual(listing.price_text, "€ 1.250,00")
        self.assertEqual(listing.price_value, 1250.0)
        self.assertEqual(listing.location_text, "Amsterdam")
        self.assertEqual(listing.category_text, "fietsen en brommers")
        self.assertEqual(listing.posted_at_text, "Vandaag")
        self.assertEqual(listing.description_snippet, "Goed onderhouden bakfiets.")
        self.assertEqual(
            listing.listing_url,
            "https://www.marktplaats.nl/v/fietsen-en-brommers/fietsen/a1511355607-bakfiets",
        )

    def test_marktplaats_listing_id_supports_m_and_a_ids(self) -> None:
        self.assertEqual(
            extract_marktplaats_listing_id("https://www.marktplaats.nl/v/audio-tv-en-foto/m1234567890-speakers"),
            "m1234567890",
        )
        self.assertEqual(
            extract_marktplaats_listing_id("https://www.marktplaats.nl/v/fietsen-en-brommers/a1511355607-fiets"),
            "a1511355607",
        )

    def test_search_url_validation_rejects_local_fetch_hosts(self) -> None:
        for host in ["localhost", "host.docker.internal", "127.0.0.1", "10.0.0.8", "192.168.1.10", "fd00::1"]:
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    validate_public_fetch_host(host)

        validate_public_fetch_host("www.kleinanzeigen.de")

    def test_kleinanzeigen_location_hint_is_added_to_search_url(self) -> None:
        url = apply_kleinanzeigen_location_to_url(
            "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl",
            "10115 · +50 km",
        )

        self.assertEqual(
            url,
            "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl&locationStr=10115&radius=50",
        )

    def test_kleinanzeigen_map_location_hint_uses_resolved_place(self) -> None:
        url = apply_kleinanzeigen_location_to_url(
            "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl",
            "Kartenpunkt: 52.5200, 13.4050 · 10115 Berlin · +50 km",
        )

        self.assertEqual(
            url,
            "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl&locationStr=10115+Berlin&radius=50",
        )

    def test_existing_kleinanzeigen_location_url_is_not_rewritten(self) -> None:
        url = "https://www.kleinanzeigen.de/s-immobilien/duesseldorf/anzeige:angebote/wohnung/k0c195l2068r5"

        self.assertEqual(apply_kleinanzeigen_location_to_url(url, "10115 · +50 km"), url)

    def test_kleinanzeigen_dedicated_parser_reads_aditem_fields(self) -> None:
        html = """
        <ul id="srchrslt-adtable">
          <li class="ad-listitem">
            <article class="aditem" data-adid="12345" data-href="/s-anzeige/eiche-stuhl/12345-86-1">
              <div class="aditem-main--top--left">10115 Mitte</div>
              <div class="aditem-main--top--right">Heute</div>
              <div class="aditem-main">
                <a class="text-module-begin" href="/s-anzeige/eiche-stuhl/12345-86-1">Eiche Stuhl</a>
                <p class="aditem-main--middle--price-shipping--price">25 EUR VB</p>
                <p class="aditem-main--middle--tags">Haus & Garten</p>
                <p class="aditem-main--middle--description">Massiver Stuhl.</p>
              </div>
              <img src="/image.jpg">
            </article>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html,
            {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl"},
        )

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.source_listing_id, "12345")
        self.assertEqual(listing.title, "Eiche Stuhl")
        self.assertEqual(listing.price_text, "25 EUR VB")
        self.assertEqual(listing.price_value, 25.0)
        self.assertEqual(listing.location_text, "10115 Mitte")
        self.assertEqual(listing.category_text, "Haus & Garten")
        self.assertEqual(listing.posted_at_text, "Heute")
        self.assertEqual(listing.listing_url, "https://www.kleinanzeigen.de/s-anzeige/eiche-stuhl/12345-86-1")

    def test_kleinanzeigen_parser_reads_time_datetime_when_visible_text_is_empty(self) -> None:
        html = """
        <ul id="srchrslt-adtable">
          <li class="ad-listitem">
            <article class="aditem" data-adid="12345" data-href="/s-anzeige/eiche-stuhl/12345-86-1">
              <time class="date" datetime="12.06.2026"></time>
              <a href="/s-anzeige/eiche-stuhl/12345-86-1">Eiche Stuhl</a>
              <p class="aditem-main--middle--price-shipping--price">25 EUR VB</p>
            </article>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html,
            {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl"},
        )

        self.assertEqual(listings[0].posted_at_text, "12.06.2026")

    def test_kleinanzeigen_detail_posted_at_is_read_from_extra_info(self) -> None:
        html = """
        <div id="viewad-extra-info" class="boxedarticle--details--full">
          <div><i class="icon icon-small icon-calendar-gray-simple"></i><span>07.06.2026</span></div>
        </div>
        """

        self.assertEqual(parse_kleinanzeigen_detail_posted_at(html), "07.06.2026")

    def test_kleinanzeigen_availability_detects_reserved_and_deleted(self) -> None:
        self.assertEqual(
            parse_listing_availability("kleinanzeigen", 200, "<html>Reserviert</html>", "https://www.kleinanzeigen.de/s-anzeige/a/1"),
            "reserved",
        )
        self.assertEqual(
            parse_listing_availability(
                "kleinanzeigen",
                200,
                "<html>Diese Anzeige ist nicht mehr verfügbar</html>",
                "https://www.kleinanzeigen.de/s-anzeige/a/1",
            ),
            "deleted",
        )
        self.assertEqual(
            parse_listing_availability("kleinanzeigen", 200, "<html>Normale Anzeige</html>", "https://www.kleinanzeigen.de/s-anzeige/a/1"),
            "active",
        )

    def test_marktplaats_availability_detects_reserved_and_deleted(self) -> None:
        self.assertEqual(
            parse_listing_availability(
                "marktplaats",
                200,
                "<html>Deze advertentie is niet meer beschikbaar</html>",
                "https://www.marktplaats.nl/v/fietsen-en-brommers/a1511355607-fiets",
            ),
            "deleted",
        )
        self.assertEqual(
            parse_listing_availability(
                "marktplaats",
                200,
                "<html>Gereserveerd</html>",
                "https://www.marktplaats.nl/v/fietsen-en-brommers/a1511355607-fiets",
            ),
            "reserved",
        )

    def test_kleinanzeigen_parser_ignores_footer_links_when_no_listing_cards(self) -> None:
        connector = HtmlListingConnector("kleinanzeigen")
        html = """
        <html><body>
          <footer>
            <a href="https://www.facebook.com/Kleinanzeigen/">Facebook</a>
            <a href="https://www.adevinta.com/brands">Adevinta</a>
          </footer>
        </body></html>
        """

        listings = connector.parse_kleinanzeigen_listings(html, {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=macbook"})

        self.assertEqual(listings, [])

    def test_kleinanzeigen_parser_ignores_account_links(self) -> None:
        html = """
        <ul id="srchrslt-adtable">
          <li class="ad-listitem">
            <article class="aditem" data-href="/m-passwort-vergessen.html">
              <a href="/m-passwort-vergessen.html">Passwort vergessen?</a>
            </article>
          </li>
          <li class="ad-listitem">
            <article class="aditem" data-href="/m-benutzer-anmeldung.html">
              <a href="/m-benutzer-anmeldung.html">Erstelle ein Konto</a>
            </article>
          </li>
          <li class="ad-listitem">
            <article class="aditem" data-href="/s-anzeige/echte-anzeige/12345-172-1">
              <a href="/s-anzeige/echte-anzeige/12345-172-1">Echte Anzeige</a>
              <p class="aditem-main--middle--price-shipping--price">15 € VB</p>
            </article>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html,
            {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=defekt"},
        )

        self.assertEqual([listing.title for listing in listings], ["Echte Anzeige"])
        self.assertEqual(listings[0].price_text, "15 € VB")

    def test_kleinanzeigen_parser_ignores_password_reset_artifact_with_listing_url(self) -> None:
        html = """
        <ul id="srchrslt-adtable">
          <li class="ad-listitem">
            <article class="aditem" data-href="/s-anzeige/passwort-vergessen/99999-172-1">
              <a href="/s-anzeige/passwort-vergessen/99999-172-1">Passwort vergessen?</a>
              <p class="aditem-main--middle--price-shipping--price">kein Preis</p>
            </article>
          </li>
          <li class="ad-listitem">
            <article class="aditem" data-href="/s-anzeige/echte-anzeige/12345-172-1">
              <a href="/s-anzeige/echte-anzeige/12345-172-1">Echte Anzeige</a>
              <p class="aditem-main--middle--price-shipping--price">15 € VB</p>
            </article>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html,
            {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=defekt"},
        )

        self.assertEqual([listing.title for listing in listings], ["Echte Anzeige"])

    def test_kleinanzeigen_parser_ignores_account_artifact_with_listing_url(self) -> None:
        html = """
        <ul id="srchrslt-adtable">
          <li class="ad-listitem">
            <article class="aditem" data-href="/s-anzeige/konto-erstellen/99999-172-1">
              <a href="/s-anzeige/konto-erstellen/99999-172-1">Erstelle ein Konto</a>
              <p class="aditem-main--middle--price-shipping--price">kein Preis</p>
            </article>
          </li>
          <li class="ad-listitem">
            <article class="aditem" data-href="/s-anzeige/echte-anzeige/12345-172-1">
              <a href="/s-anzeige/echte-anzeige/12345-172-1">Echte Anzeige</a>
              <p class="aditem-main--middle--price-shipping--price">15 € VB</p>
            </article>
          </li>
        </ul>
        """

        listings = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html,
            {"search_url": "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=defekt"},
        )

        self.assertEqual([listing.title for listing in listings], ["Echte Anzeige"])

    def test_kleinanzeigen_pagination_keeps_client_available(self) -> None:
        first_url = "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl"
        second_url = "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=stuhl&pageNum=2"
        first_html = f"""
        {article("Erster Stuhl", "/s-anzeige/erster-stuhl/1")}
        <a rel="next" href="{second_url}">Weiter</a>
        """
        second_html = article("Zweiter Stuhl", "/s-anzeige/zweiter-stuhl/2", "20 EUR")
        client = FakeClient({second_url: second_html})

        listings = asyncio.run(
            HtmlListingConnector("kleinanzeigen").fetch_paginated_kleinanzeigen(
                client,
                {"search_url": first_url},
                first_html,
                first_url,
            )
        )

        self.assertEqual([item.title for item in listings], ["Erster Stuhl", "Zweiter Stuhl"])
        self.assertEqual(client.requested, [second_url])

    def test_facebook_login_and_upsell_pages_are_detected(self) -> None:
        self.assertTrue(facebook_requires_login("<form id='login_form'></form>", "https://www.facebook.com/login.php"))
        self.assertTrue(
            facebook_requires_login(
                "<html>LoggedInLandingUpsellEligible marketplace_logged_out_content</html>",
                "https://www.facebook.com/marketplace/search/?query=stuhl",
            )
        )
        self.assertFalse(
            facebook_requires_login(
                '<a href="/marketplace/item/123456789/">Stuhl</a>',
                "https://www.facebook.com/marketplace/search/?query=stuhl",
            )
        )


if __name__ == "__main__":
    unittest.main()
