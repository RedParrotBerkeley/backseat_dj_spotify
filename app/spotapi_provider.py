import logging
import os
from typing import Any, Dict, List, Optional

from app.playback import PlaybackDevice, PlaybackProvider, PlaybackResult

logger = logging.getLogger(__name__)

try:
    from spotapi import Client
except Exception:  # pragma: no cover, optional dependency may be missing or incompatible
    Client = None  # type: ignore[assignment]


class SpotAPIPlaybackProvider(PlaybackProvider):
    def __init__(self, username: str, password: str):
        if Client is None:
            raise RuntimeError("spotapi is not installed")

        self.client: Any = Client(username=username, password=password)
        logger.info("SpotAPI client initialized")

    @classmethod
    def from_env(cls) -> Optional["SpotAPIPlaybackProvider"]:
        username = os.getenv("SPOTIFY_USER") or os.getenv("SPOTIFY_USERNAME")
        password = os.getenv("SPOTIFY_PASS") or os.getenv("SPOTIFY_PASSWORD")
        if not username or not password:
            return None

        try:
            return cls(username=username, password=password)
        except Exception as exc:
            logger.warning("Could not initialize SpotAPI provider: %s", exc)
            return None

    def is_ready(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "spotapi"

    def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        results = self.client.search(query)
        tracks = (results or {}).get("tracks", {}).get("items", [])
        return tracks if isinstance(tracks, list) else []

    def best_track_uri(self, query: str):
        try:
            tracks = self.search_tracks(query)
            if not tracks:
                logger.warning("No results found for: %s", query)
                return None, "No matching Spotify track was found."

            uri: Optional[str] = tracks[0].get("uri")
            if not uri:
                logger.warning("Top search result had no URI for: %s", query)
                return None, "Spotify found a result, but it had no playable URI."

            return uri, None
        except Exception as exc:
            logger.error("Failed to search for %s: %s", query, exc)
            return None, f"Spotify search failed: {exc}"

    def play_uri(self, uri: str, device_id: Optional[str] = None) -> PlaybackResult:
        try:
            if device_id:
                try:
                    self.client.play(uri, device_id=device_id)
                except TypeError:
                    self.client.play(uri)
            else:
                self.client.play(uri)
            return PlaybackResult(ok=True)
        except Exception as exc:
            logger.error("Failed to play URI %s: %s", uri, exc)
            return PlaybackResult(ok=False, error=str(exc))

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> PlaybackResult:
        uri, error = self.best_track_uri(query)
        if not uri:
            return PlaybackResult(ok=False, error=error)
        return self.play_uri(uri, device_id=device_id)

    def devices(self) -> List[PlaybackDevice]:
        try:
            devices = self.client.devices()
        except Exception as exc:
            logger.error("Failed to fetch devices: %s", exc)
            return []

        raw_devices: List[Dict[str, Any]] = []
        if isinstance(devices, dict):
            if isinstance(devices.get("devices"), list):
                raw_devices = devices.get("devices", [])
            elif isinstance(devices.get("items"), list):
                raw_devices = devices.get("items", [])
        elif isinstance(devices, list):
            raw_devices = devices

        normalized: List[PlaybackDevice] = []
        for device in raw_devices:
            normalized.append(
                PlaybackDevice(
                    id=str(device.get("id", "") or ""),
                    name=str(device.get("name", "Unknown device") or "Unknown device"),
                    type=str(device.get("type", "") or ""),
                    is_active=bool(device.get("is_active") or device.get("active")),
                )
            )
        return normalized
