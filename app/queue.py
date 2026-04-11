import json
import logging
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional

from app.models import SongQueueEntry

logger = logging.getLogger(__name__)
DEFAULT_QUEUE_PATH = Path(__file__).resolve().parent.parent / "data" / "queue.json"


class SongRequestQueue:
    def __init__(self, storage_path: Path = DEFAULT_QUEUE_PATH) -> None:
        self._items: Deque[SongQueueEntry] = deque()
        self.storage_path = storage_path
        self._load()

    @staticmethod
    def _normalize(song: str, artist: str = "") -> tuple[str, str]:
        normalized_song = " ".join(song.casefold().split())
        normalized_artist = " ".join(artist.casefold().split())
        return normalized_song, normalized_artist

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
            if not song:
                continue

            entry = SongQueueEntry(
                song=song,
                artist=artist,
                matched_title=item.get("matched_title"),
                matched_artist=item.get("matched_artist"),
                spotify_uri=item.get("spotify_uri"),
                album_art_url=item.get("album_art_url"),
                match_status=str(item.get("match_status") or "unmatched"),
            )
            self._items.append(entry)

    def _save(self) -> None:
        payload = [item.model_dump() for item in self._items]
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(payload, indent=2))

    def add(self, song: str, artist: str = "") -> tuple[bool, Optional[str]]:
        cleaned_song = song.strip()
        cleaned_artist = artist.strip()
        if not cleaned_song:
            return False, "Please enter a song title before submitting."

        normalized_new = self._normalize(cleaned_song, cleaned_artist)
        duplicate_count = 0
        same_title_count = 0
        for queued_item in self._items:
            normalized_existing = self._normalize(queued_item.song, queued_item.artist)
            if normalized_existing == normalized_new:
                return False, f'"{cleaned_song}" is already in the queue.'
            if normalized_existing[0] == normalized_new[0]:
                same_title_count += 1
            if cleaned_artist and normalized_existing[1] == normalized_new[1]:
                duplicate_count += 1

        if same_title_count >= 2:
            return False, f'Too many versions of "{cleaned_song}" are already queued.'

        if cleaned_artist and duplicate_count >= 3:
            return False, f'There are already several requests from {cleaned_artist} in the queue.'

        self._items.append(SongQueueEntry(song=cleaned_song, artist=cleaned_artist))
        self._save()
        return True, None

    def requeue(self, item: SongQueueEntry) -> None:
        self._items.append(item)
        self._save()

    def update(self, index: int, item: SongQueueEntry) -> bool:
        if index < 0 or index >= len(self._items):
            return False

        items = list(self._items)
        items[index] = item
        self._items = deque(items)
        self._save()
        return True

    def next(self) -> Optional[SongQueueEntry]:
        if not self._items:
            return None
        item = self._items.popleft()
        self._save()
        return item

    def remove(self, index: int) -> Optional[SongQueueEntry]:
        if index < 0 or index >= len(self._items):
            return None

        items = list(self._items)
        removed = items.pop(index)
        self._items = deque(items)
        self._save()
        return removed

    def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        self._save()
        return count

    def list(self) -> List[SongQueueEntry]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


request_queue = SongRequestQueue()
