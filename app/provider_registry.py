from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from app.official_spotify_provider import OfficialSpotifyPlaybackProvider
from app.playback import PlaybackProvider, PlaybackProviderStatus
from app.spotapi_provider import SpotAPIPlaybackProvider


@dataclass
class ProviderSelection:
    provider: Optional[PlaybackProvider]
    status: PlaybackProviderStatus


def select_playback_provider() -> ProviderSelection:
    oauth_configured = bool(os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"))
    official_provider = OfficialSpotifyPlaybackProvider.from_env()

    if official_provider is not None:
        if official_provider.is_ready():
            return ProviderSelection(
                provider=official_provider,
                status=PlaybackProviderStatus(
                    active_provider=official_provider.provider_name(),
                    spotify_ready=True,
                    oauth_configured=True,
                    using_official_oauth=True,
                    blocked_reason=None,
                ),
            )

        fallback_provider = SpotAPIPlaybackProvider.from_env()
        if fallback_provider is not None:
            return ProviderSelection(
                provider=fallback_provider,
                status=PlaybackProviderStatus(
                    active_provider=fallback_provider.provider_name(),
                    spotify_ready=True,
                    oauth_configured=True,
                    using_official_oauth=False,
                    blocked_reason="Official Spotify OAuth provider is staged but not implemented yet.",
                ),
            )

        return ProviderSelection(
            provider=official_provider,
            status=PlaybackProviderStatus(
                active_provider=official_provider.provider_name(),
                spotify_ready=False,
                oauth_configured=True,
                using_official_oauth=False,
                blocked_reason="Official Spotify OAuth provider is staged but not implemented yet.",
            ),
        )

    spotapi_provider = SpotAPIPlaybackProvider.from_env()
    if spotapi_provider is not None:
        return ProviderSelection(
            provider=spotapi_provider,
            status=PlaybackProviderStatus(
                active_provider=spotapi_provider.provider_name(),
                spotify_ready=True,
                oauth_configured=False,
                using_official_oauth=False,
                blocked_reason=None,
            ),
        )

    return ProviderSelection(
        provider=None,
        status=PlaybackProviderStatus(
            active_provider=None,
            spotify_ready=False,
            oauth_configured=oauth_configured,
            using_official_oauth=False,
            blocked_reason="Spotify credentials are not configured yet." if not oauth_configured else "Official Spotify OAuth provider is staged but not implemented yet.",
        ),
    )
