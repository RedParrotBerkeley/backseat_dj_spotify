import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse


class SpotifyOAuthProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.token_path = Path(self.temp_dir.name) / "tokens.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_authorization_url_uses_official_scopes_and_redirect_uri(self):
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        provider = SpotifyOAuthPlaybackProvider(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
            token_store=FileTokenStore(self.token_path),
        )

        url = provider.authorization_url(state="state-123")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.netloc, "accounts.spotify.com")
        self.assertEqual(parsed.path, "/authorize")
        self.assertEqual(params["response_type"], ["code"])
        self.assertEqual(params["client_id"], ["client-id"])
        self.assertEqual(params["redirect_uri"], ["http://127.0.0.1:8000/auth/spotify/callback"])
        self.assertEqual(params["state"], ["state-123"])
        self.assertIn("user-read-playback-state", params["scope"][0])
        self.assertIn("user-modify-playback-state", params["scope"][0])

    def test_exchange_code_persists_token_without_exposing_secret(self):
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        provider = SpotifyOAuthPlaybackProvider(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
            token_store=FileTokenStore(self.token_path),
        )
        response = Mock()
        response.json.return_value = {
            "access_token": "access-1",
            "refresh_token": "refresh-1",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        response.raise_for_status.return_value = None

        with patch("app.spotify_oauth_provider.httpx.post", return_value=response) as post:
            provider.exchange_code("auth-code")

        post.assert_called_once()
        _, kwargs = post.call_args
        self.assertEqual(kwargs["data"]["grant_type"], "authorization_code")
        self.assertEqual(kwargs["data"]["code"], "auth-code")
        self.assertEqual(kwargs["auth"], ("client-id", "client-secret"))
        persisted = json.loads(self.token_path.read_text())
        self.assertEqual(persisted["access_token"], "access-1")
        self.assertEqual(persisted["refresh_token"], "refresh-1")
        self.assertNotIn("client-secret", self.token_path.read_text())

    def test_refresh_uses_refresh_token_and_preserves_it_when_response_omits_refresh_token(self):
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        store = FileTokenStore(self.token_path)
        store.save({
            "access_token": "expired-access",
            "refresh_token": "refresh-1",
            "expires_at": time.time() - 60,
        })
        provider = SpotifyOAuthPlaybackProvider(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
            token_store=store,
        )
        response = Mock()
        response.json.return_value = {
            "access_token": "access-2",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        response.raise_for_status.return_value = None

        with patch("app.spotify_oauth_provider.httpx.post", return_value=response):
            token = provider.access_token()

        self.assertEqual(token, "access-2")
        persisted = store.load()
        self.assertEqual(persisted["access_token"], "access-2")
        self.assertEqual(persisted["refresh_token"], "refresh-1")

    def test_search_and_play_calls_spotify_search_and_playback_endpoints(self):
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        store = FileTokenStore(self.token_path)
        store.save({
            "access_token": "access-1",
            "refresh_token": "refresh-1",
            "expires_at": time.time() + 3600,
        })
        provider = SpotifyOAuthPlaybackProvider(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
            token_store=store,
        )
        search_response = Mock()
        search_response.json.return_value = {"tracks": {"items": [{"uri": "spotify:track:123"}]}}
        search_response.raise_for_status.return_value = None
        play_response = Mock()
        play_response.raise_for_status.return_value = None

        with patch("app.spotify_oauth_provider.httpx.get", return_value=search_response) as get, \
             patch("app.spotify_oauth_provider.httpx.put", return_value=play_response) as put:
            result = provider.search_and_play("Dreams Fleetwood Mac", device_id="device-1")

        self.assertTrue(result.ok)
        self.assertEqual(get.call_args.kwargs["params"]["q"], "Dreams Fleetwood Mac")
        self.assertEqual(get.call_args.kwargs["params"]["type"], "track")
        self.assertEqual(put.call_args.kwargs["params"], {"device_id": "device-1"})
        self.assertEqual(put.call_args.kwargs["json"], {"uris": ["spotify:track:123"]})

    def test_search_and_play_reports_not_connected_before_searching(self):
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        provider = SpotifyOAuthPlaybackProvider(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
            token_store=FileTokenStore(self.token_path),
        )

        with patch("app.spotify_oauth_provider.httpx.get") as get:
            result = provider.search_and_play("Dreams Fleetwood Mac")

        self.assertFalse(result.ok)
        self.assertIn("Spotify is not connected", result.error)
        get.assert_not_called()

    def test_token_store_writes_private_file_permissions(self):
        from app.spotify_oauth_provider import FileTokenStore

        store = FileTokenStore(self.token_path)
        store.save({"access_token": "access-1"})

        self.assertEqual(self.token_path.stat().st_mode & 0o777, 0o600)


class SpotifyOAuthRouteTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "SPOTIFY_CLIENT_ID": "client-id",
            "SPOTIFY_CLIENT_SECRET": "client-secret",
            "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8000/auth/spotify/callback",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_admin_page_shows_connect_link_when_oauth_configured_but_not_connected(self):
        from fastapi.testclient import TestClient
        import app.main as main
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        with tempfile.TemporaryDirectory() as tmp:
            original_provider = main.playback_provider
            try:
                main.playback_provider = SpotifyOAuthPlaybackProvider(
                    client_id="client-id",
                    client_secret="client-secret",
                    redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
                    token_store=FileTokenStore(Path(tmp) / "tokens.json"),
                )
                response = TestClient(main.app).get("/admin")
            finally:
                main.playback_provider = original_provider

        self.assertEqual(response.status_code, 200)
        self.assertIn("Connect Spotify", response.text)
        self.assertIn("/auth/spotify/start", response.text)

    def test_start_route_redirects_to_spotify_and_persists_state(self):
        from fastapi.testclient import TestClient
        import app.main as main
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_provider = main.playback_provider
            original_settings_path = main.SETTINGS_PATH
            try:
                main.SETTINGS_PATH = tmp_path / "settings.json"
                main.playback_provider = SpotifyOAuthPlaybackProvider(
                    client_id="client-id",
                    client_secret="client-secret",
                    redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
                    token_store=FileTokenStore(tmp_path / "tokens.json"),
                )
                response = TestClient(main.app).get("/auth/spotify/start", follow_redirects=False)
            finally:
                main.playback_provider = original_provider
                main.SETTINGS_PATH = original_settings_path

            settings = json.loads((tmp_path / "settings.json").read_text())

        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["location"].startswith("https://accounts.spotify.com/authorize?"))
        self.assertEqual(len(settings["spotify_oauth_state"]), 32)

    def test_callback_exchanges_code_when_state_matches(self):
        from fastapi.testclient import TestClient
        import app.main as main
        from app.spotify_oauth_provider import SpotifyOAuthPlaybackProvider, FileTokenStore

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_provider = main.playback_provider
            original_settings_path = main.SETTINGS_PATH
            provider = SpotifyOAuthPlaybackProvider(
                client_id="client-id",
                client_secret="client-secret",
                redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
                token_store=FileTokenStore(tmp_path / "tokens.json"),
            )
            provider.exchange_code = Mock()
            try:
                main.SETTINGS_PATH = tmp_path / "settings.json"
                main.save_settings({"spotify_oauth_state": "state-123", "spotify_oauth_pin": ""})
                main.playback_provider = provider
                response = TestClient(main.app).get(
                    "/auth/spotify/callback?code=auth-code&state=state-123",
                    follow_redirects=False,
                )
            finally:
                main.playback_provider = original_provider
                main.SETTINGS_PATH = original_settings_path

        provider.exchange_code.assert_called_once_with("auth-code")
        self.assertEqual(response.status_code, 303)
        self.assertIn("Spotify+connected+successfully", response.headers["location"])

    def test_locked_admin_page_does_not_fetch_spotify_devices(self):
        from fastapi.testclient import TestClient
        import app.main as main

        class CountingProvider:
            def __init__(self):
                self.device_calls = 0

            def is_ready(self):
                return True

            def devices(self):
                self.device_calls += 1
                return []

            def search_and_play(self, query, device_id=None):
                raise AssertionError("not expected")

            def provider_name(self):
                return "counting"

        provider = CountingProvider()
        original_provider = main.playback_provider
        original_admin_pin = main.ADMIN_PIN
        try:
            main.playback_provider = provider
            main.ADMIN_PIN = "secret-pin"
            response = TestClient(main.app).get("/admin?pin=wrong")
        finally:
            main.playback_provider = original_provider
            main.ADMIN_PIN = original_admin_pin

        self.assertEqual(response.status_code, 403)
        self.assertEqual(provider.device_calls, 0)


if __name__ == "__main__":
    unittest.main()
