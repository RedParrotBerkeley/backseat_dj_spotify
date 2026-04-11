from __future__ import annotations

import os
from typing import Optional

from app.playback import PlaybackDevice, PlaybackProvider, PlaybackResult


class OfficialSpotifyPlaybackProvider(PlaybackProvider):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @classmethod
    def from_env(cls) -> Optional["OfficialSpotifyPlaybackProvider"]:
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

        if not client_id or not client_secret:
            return None

        if not redirect_uri:
            redirect_uri = "http://127.0.0.1:8000/spotify/callback"

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    def is_ready(self) -> bool:
        return False

    def provider_name(self) -> str:
        return "spotify_oauth"

    def devices(self) -> list[PlaybackDevice]:
        return []

    def preview_track(self, query: str) -> Optional[dict]:
        return None

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> PlaybackResult:
        return PlaybackResult(
            ok=False,
            error="Official Spotify OAuth provider is staged but not implemented yet.",
        )
