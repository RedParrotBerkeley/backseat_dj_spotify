from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SongRequest(BaseModel):
    song: str
    artist: str = ""


class SongQueueEntry(BaseModel):
    song: str
    artist: str = ""
    matched_title: Optional[str] = None
    matched_artist: Optional[str] = None
    spotify_uri: Optional[str] = None
    album_art_url: Optional[str] = None
    match_status: str = Field(default="unmatched")
