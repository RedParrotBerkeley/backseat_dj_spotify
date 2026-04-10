import logging
from typing import Any, Dict, List, Optional

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

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> bool:
        try:
            results = self.client.search(query)
            tracks = (results or {}).get("tracks", {}).get("items", [])
            if not tracks:
                logger.warning("No results found for: %s", query)
                return False

            uri: Optional[str] = tracks[0].get("uri")
            if not uri:
                logger.warning("Top search result had no URI for: %s", query)
                return False

            if device_id:
                try:
                    self.client.play(uri, device_id=device_id)
                except TypeError:
                    self.client.play(uri)
            else:
                self.client.play(uri)
            logger.info("Playing: %s", query)
            return True
        except Exception as exc:
            logger.error("Failed to play %s: %s", query, exc)
            return False

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
