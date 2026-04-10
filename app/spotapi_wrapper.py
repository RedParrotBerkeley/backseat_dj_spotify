import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from spotapi import Client
except Exception:  # pragma: no cover, optional dependency may be missing or incompatible
    Client = None  # type: ignore[assignment]


class SpotAPIHandler:
    def __init__(self, username: str, password: str):
        if Client is None:
            raise RuntimeError("spotapi is not installed")

        self.client: Any = Client(username=username, password=password)
        logger.info("SpotAPI client initialized")

    def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        results = self.client.search(query)
        tracks = (results or {}).get("tracks", {}).get("items", [])
        return tracks if isinstance(tracks, list) else []

    def best_track_uri(self, query: str) -> Tuple[Optional[str], Optional[str]]:
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

    def play_uri(self, uri: str, device_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        try:
            if device_id:
                try:
                    self.client.play(uri, device_id=device_id)
                except TypeError:
                    self.client.play(uri)
            else:
                self.client.play(uri)
            return True, None
        except Exception as exc:
            logger.error("Failed to play URI %s: %s", uri, exc)
            return False, str(exc)

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        uri, error = self.best_track_uri(query)
        if not uri:
            return False, error
        return self.play_uri(uri, device_id=device_id)

    def devices(self) -> List[Dict[str, Any]]:
        try:
            devices = self.client.devices()
        except Exception as exc:
            logger.error("Failed to fetch devices: %s", exc)
            return []

        if isinstance(devices, dict):
            if isinstance(devices.get("devices"), list):
                return devices.get("devices", [])
            if isinstance(devices.get("items"), list):
                return devices.get("items", [])

        if isinstance(devices, list):
            return devices

        return []
