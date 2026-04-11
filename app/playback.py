from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class PlaybackDevice:
    id: str
    name: str
    type: str = ""
    is_active: bool = False


@dataclass
class PlaybackResult:
    ok: bool
    error: Optional[str] = None
    detail: Optional[str] = None


@dataclass
class PlaybackProviderStatus:
    active_provider: Optional[str]
    spotify_ready: bool
    oauth_configured: bool
    using_official_oauth: bool
    blocked_reason: Optional[str] = None


class PlaybackProvider(Protocol):
    def is_ready(self) -> bool: ...

    def devices(self) -> List[PlaybackDevice]: ...

    def search_and_play(self, query: str, device_id: Optional[str] = None) -> PlaybackResult: ...

    def preview_track(self, query: str) -> Optional[dict]: ...

    def provider_name(self) -> str: ...
