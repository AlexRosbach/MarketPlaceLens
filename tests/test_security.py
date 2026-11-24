import asyncio
import socket
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

import httpx

from app import auth, database
from app.connectors import HtmlListingConnector, resolve_public_addresses, validate_public_request


class OutboundTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_public_dns_response_is_rejected(self):
        loop = asyncio.get_running_loop()
        with patch.object(loop, "getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ]):
            with self.assertRaises(ValueError):
                await resolve_public_addresses("example.test", 443)

    async def test_facebook_cookie_is_not_forwarded_to_unrelated_host(self):
        request = httpx.Request("GET", "https://example.test/", headers={"Cookie": "example=value"})
        await validate_public_request(request)
        self.assertNotIn("cookie", request.headers)

    async def test_current_cards_outside_legacy_wrapper_are_supported(self):
        html = '<article data-adid="123" data-href="/s-anzeige/example/123-1-2"><h3>Example</h3><p class="text-title3">15 EUR</p></article>'
        entries = HtmlListingConnector("kleinanzeigen").parse_kleinanzeigen_listings(
            html, {"search_url": "https://www.kleinanzeigen.de/s-example/k0"})
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].source_listing_id, "123")


class SessionTests(unittest.TestCase):
    def test_logout_and_password_change_invalidate_sessions(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = replace(database.settings, db_path=folder + "/test.db", admin_password="example-test-password")
            with patch.object(database, "settings", settings), patch.object(auth, "settings", settings):
                database.init_db()
                token = auth.create_session(settings.admin_username)
                self.assertIsNotNone(auth.current_user_from_session(token))
                auth.revoke_session(token)
                self.assertIsNone(auth.current_user_from_session(token))
                token = auth.create_session(settings.admin_username)
                with database.connect() as db:
                    db.execute("UPDATE users SET password_hash = ?", (auth.hash_password("different-example-password"),))
                self.assertIsNone(auth.current_user_from_session(token))
