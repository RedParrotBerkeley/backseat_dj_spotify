import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.queue import request_queue
from app.spotapi_wrapper import SpotAPIHandler

app = FastAPI(title="Backseat DJ")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def build_spotify_handler() -> Optional[SpotAPIHandler]:
    username = os.getenv("SPOTIFY_USER") or os.getenv("SPOTIFY_USERNAME")
    password = os.getenv("SPOTIFY_PASS") or os.getenv("SPOTIFY_PASSWORD")
    if not username or not password:
        return None
    return SpotAPIHandler(username=username, password=password)


spotify = build_spotify_handler()


def render_home(request: Request, message: Optional[str] = None) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "queue": request_queue.list(),
            "spotify_ready": spotify is not None,
            "message": message,
        },
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render_home(request)


@app.get("/queue", response_class=HTMLResponse)
async def show_queue(request: Request):
    return render_home(request)


@app.post("/request", response_class=HTMLResponse)
async def add_song(request: Request, song: str = Form(...), artist: str = Form("")):
    added = request_queue.add(song, artist)
    if not added:
        return render_home(request, "Please enter a song title before submitting.")

    return render_home(request, f'Added "{song.strip()}" to the queue.')


@app.post("/play-next", response_class=HTMLResponse)
async def play_next(request: Request):
    next_song = request_queue.next()
    if not next_song:
        return render_home(request, "Queue is empty.")

    song, artist = next_song
    full_query = f"{song} {artist}" if artist else song

    if spotify is None:
        request_queue.add(song, artist)
        return render_home(request, "Spotify credentials are not configured yet.")

    played = spotify.search_and_play(full_query)
    if not played:
        request_queue.add(song, artist)
        return render_home(request, f'Could not play "{full_query}". The request was returned to the queue.')

    return render_home(request, f'Now playing "{full_query}".')
