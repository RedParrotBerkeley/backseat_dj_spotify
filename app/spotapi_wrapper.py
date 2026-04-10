import logging
from typing import Any, Optional

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

    def search_and_play(self, query: str) -> bool:
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

            self.client.play(uri)
            logger.info("Playing: %s", query)
            return True
        except Exception as exc:
            logger.error("Failed to play %s: %s", query, exc)
            return False
