from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.spotapi_wrapper import SpotAPIHandler
from app.queue import request_queue
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize SpotAPI handler
spotify = SpotAPIHandler(username=os.getenv("SPOTIFY_USER"), password=os.getenv("SPOTIFY_PASS"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/request")
async def add_song(song: str = Form(...), artist: str = Form("")):
    request_queue.append((song, artist))
    return RedirectResponse(url="/queue", status_code=303)

@app.get("/queue", response_class=HTMLResponse)
async def show_queue(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "queue": list(request_queue)
    })

@app.post("/play-next")
async def play_next():
    if request_queue:
        song, artist = request_queue.pop(0)
        full_query = f"{song} {artist}" if artist else song
        spotify.search_and_play(full_query)
    return {"status": "ok"}

