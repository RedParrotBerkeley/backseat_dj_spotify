import json
import logging
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional, Tuple

SongQueueItem = Tuple[str, str]

logger = logging.getLogger(__name__)
DEFAULT_QUEUE_PATH = Path(__file__).resolve().parent.parent / "data" / "queue.json"


class SongRequestQueue:
    def __init__(self, storage_path: Path = DEFAULT_QUEUE_PATH) -> None:
        self._items: Deque[SongQueueItem] = deque()
        self.storage_path = storage_path
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return

        try:
            raw_items = json.loads(self.storage_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load queue from %s: %s", self.storage_path, exc)
            return

        if not isinstance(raw_items, list):
            logger.warning("Queue file %s did not contain a list", self.storage_path)
            return

        for item in raw_items:
            if not isinstance(item, dict):
                continue
            song = str(item.get("song", "")).strip()
            artist = str(item.get("artist", "")).strip()
            if song:
                self._items.append((song, artist))

    def _save(self) -> None:
        payload = [{"song": song, "artist": artist} for song, artist in self._items]
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(payload, indent=2))

    def add(self, song: str, artist: str = "") -> bool:
        cleaned_song = song.strip()
        cleaned_artist = artist.strip()
        if not cleaned_song:
            return False

        self._items.append((cleaned_song, cleaned_artist))
        self._save()
        return True

    def next(self) -> Optional[SongQueueItem]:
        if not self._items:
            return None
        item = self._items.popleft()
        self._save()
        return item

    def list(self) -> List[SongQueueItem]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


request_queue = SongRequestQueue()
