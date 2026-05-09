from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.playback import PlaybackDevice, PlaybackProvider, PlaybackResult

logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_SCOPES = ("user-read-playback-state", "user-modify-playback-state")
EXPIRY_SAFETY_SECONDS = 60


class FileTokenStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        return raw if isinstance(raw, dict) else {}

    def save(self, token: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(json.dumps(token, indent=2))
        temporary_path.chmod(0o600)
        temporary_path.replace(self.path)
        self.path.chmod(0o600)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return


class SpotifyOAuthPlaybackProvider(PlaybackProvider):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_store: FileTokenStore,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_store = token_store

    @classmethod
    def from_env(cls, data_dir: Path) -> Optional["SpotifyOAuthPlaybackProvider"]:
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()
        if not client_id or not client_secret or not redirect_uri:
            return None

        token_path = Path(os.getenv("SPOTIFY_TOKEN_PATH", data_dir / "spotify_tokens.json"))
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_store=FileTokenStore(token_path),
        )

    def provider_name(self) -> str:
        return "spotify-web-api"

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def is_ready(self) -> bool:
        token = self.token_store.load()
        expires_at = float(token.get("expires_at") or 0)
        has_valid_access_token = bool(token.get("access_token")) and expires_at > time.time() + EXPIRY_SAFETY_SECONDS
        return bool(token.get("refresh_token") or has_valid_access_token)

    def authorization_url(self, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "scope": " ".join(SPOTIFY_SCOPES),
                "redirect_uri": self.redirect_uri,
                "state": state,
            }
        )
        return f"{AUTHORIZE_URL}?{query}"

    def exchange_code(self, code: str) -> None:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        response.raise_for_status()
        self._save_token_response(response.json())

    def access_token(self) -> Optional[str]:
        token = self.token_store.load()
        access_token = token.get("access_token")
        expires_at = float(token.get("expires_at") or 0)
        if access_token and expires_at > time.time() + EXPIRY_SAFETY_SECONDS:
            return str(access_token)
        return self.refresh_access_token()

    def refresh_access_token(self) -> Optional[str]:
        existing = self.token_store.load()
        refresh_token = existing.get("refresh_token")
        if not refresh_token:
            return None

        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if "refresh_token" not in data:
            data["refresh_token"] = refresh_token
        self._save_token_response(data)
        return str(data.get("access_token") or "") or None

    def disconnect(self) -> None:
        self.token_store.clear()

    def _save_token_response(self, data: Dict[str, Any]) -> None:
        token = dict(self.token_store.load())
        token.update(data)
        expires_in = int(data.get("expires_in") or 3600)
        token["expires_at"] = time.time() + expires_in
        self.token_store.save(token)

    def _headers(self) -> Optional[Dict[str, str]]:
        token = self.access_token()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    def _not_connected_error(self) -> str:
        return "Spotify is not connected. Use Connect Spotify in admin first."

    def _api_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        headers = self._headers()
        if headers is None:
            return None
        response = httpx.get(f"{API_BASE_URL}{path}", headers=headers, params=params or {}, timeout=15)
        response.raise_for_status()
        raw = response.json()
        return raw if isinstance(raw, dict) else {}

    def _api_put(self, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> None:
        headers = self._headers()
        if headers is None:
            raise RuntimeError(self._not_connected_error())
        response = httpx.put(f"{API_BASE_URL}{path}", headers=headers, params=params or {}, json=json_body or {}, timeout=15)
        response.raise_for_status()

    def devices(self) -> List[PlaybackDevice]:
        try:
            raw = self._api_get("/me/player/devices")
        except Exception as exc:
            logger.warning("Could not fetch Spotify devices: %s", exc)
            return []
        raw_devices = raw.get("devices", []) if raw else []
        if not isinstance(raw_devices, list):
            return []
        return [
            PlaybackDevice(
                id=str(device.get("id", "") or ""),
                name=str(device.get("name", "Unknown device") or "Unknown device"),
                type=str(device.get("type", "") or ""),
                is_active=bool(device.get("is_active")),
            )
            for device in raw_devices
            if isinstance(device, dict)
        ]

    def best_track_uri(self, query: str) -> tuple[Optional[str], Optional[str]]:
        try:
            raw = self._api_get("/search", params={"q": query, "type": "track", "limit": 1})
        except Exception as exc:
            logger.warning("Spotify search failed for %s: %s", query, exc)
            return None, f"Spotify search failed: {exc}"
        tracks = ((raw or {}).get("tracks") or {}).get("items", [])
        if not tracks:
            return None, "No matching Spotify track was found."
        uri = tracks[0].get("uri") if isinstance(tracks[0], dict) else None
        if not uri:
            return None, "Spotify found a result, but it had no playable URI."
        return str(uri), None

    def play_uri(self, uri: str, device_id: Optional[str] = None) -> PlaybackResult:
        try:
            params = {"device_id": device_id} if device_id else {}
            self._api_put("/me/player/play", params=params, json_body={"uris": [uri]})
            return PlaybackResult(ok=True)
        except Exception as exc:
            logger.warning("Spotify playback failed for %s: %s", uri, exc)
            return PlaybackResult(ok=False, error=str(exc))

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> PlaybackResult:
        if not self.is_ready():
            return PlaybackResult(ok=False, error=self._not_connected_error())
        uri, error = self.best_track_uri(query)
        if not uri:
            return PlaybackResult(ok=False, error=error)
        return self.play_uri(uri, device_id=device_id)
