from pydantic import BaseModel

class SongRequest(BaseModel):
    song: str
    artist: str = ""
