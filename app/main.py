import os
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

    try:
        return SpotAPIHandler(username=username, password=password)
    except Exception:
        return None


spotify = build_spotify_handler()
ADMIN_PIN = os.getenv("BACKSEAT_DJ_ADMIN_PIN")
selected_device_id = os.getenv("BACKSEAT_DJ_DEVICE_ID", "").strip()
last_playback_status = "Spotify playback has not been used yet."


def is_admin(pin: Optional[str]) -> bool:
    if not ADMIN_PIN:
        return True
    return bool(pin) and pin == ADMIN_PIN


def admin_query(pin: Optional[str]) -> str:
    if not pin:
        return ""
    return f"?{urlencode({'pin': pin})}"


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


def current_devices():
    if spotify is None:
        return []
    return spotify.devices()


def selected_device_name(devices) -> Optional[str]:
    if not selected_device_id:
        return None
    for device in devices:
        device_id = str(device.get("id", "") or "")
        if device_id == selected_device_id:
            return str(device.get("name", "Selected device"))
    return None


def render_admin(request: Request, pin: Optional[str], message: Optional[str] = None) -> HTMLResponse:
    authorized = is_admin(pin)
    devices = current_devices()
    active_device_name = selected_device_name(devices)
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "queue": list(enumerate(request_queue.list())),
            "spotify_ready": spotify is not None,
            "message": message,
            "admin_configured": bool(ADMIN_PIN),
            "authorized": authorized,
            "pin": pin or "",
            "admin_action": f"/play-next{admin_query(pin)}",
            "clear_action": f"/admin/clear{admin_query(pin)}",
            "remove_base": "/admin/remove",
            "skip_action": f"/admin/skip-next{admin_query(pin)}",
            "device_action": f"/admin/device{admin_query(pin)}",
            "devices": devices,
            "selected_device_id": selected_device_id,
            "selected_device_name": active_device_name,
            "last_playback_status": last_playback_status,
        },
        status_code=200 if authorized else 403,
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render_home(request)


@app.get("/queue", response_class=HTMLResponse)
async def show_queue(request: Request):
    return render_home(request)


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, pin: Optional[str] = Query(default=None)):
    return render_admin(request, pin)


@app.post("/request", response_class=HTMLResponse)
async def add_song(request: Request, song: str = Form(...), artist: str = Form("")):
    added, error_message = request_queue.add(song, artist)
    if not added:
        return render_home(request, error_message)

    return render_home(request, f'Added "{song.strip()}" to the queue.')


@app.post("/play-next")
async def play_next(pin: Optional[str] = Query(default=None)):
    global last_playback_status

    if not is_admin(pin):
        destination = "/admin"
        if pin:
            destination = f"{destination}{admin_query(pin)}"
        return RedirectResponse(url=destination, status_code=303)

    next_song = request_queue.next()
    message = ""
    if not next_song:
        message = "Queue is empty."
        last_playback_status = message
    else:
        song, artist = next_song
        full_query = f"{song} {artist}" if artist else song

        if spotify is None:
            request_queue.add(song, artist)
            message = "Spotify credentials are not configured yet."
            last_playback_status = message
        else:
            played = spotify.search_and_play(full_query, device_id=selected_device_id or None)
            if not played:
                request_queue.add(song, artist)
                message = f'Could not play "{full_query}". The request was returned to the queue.'
                last_playback_status = message
            else:
                device_label = selected_device_name(current_devices()) or "default Spotify device"
                message = f'Now playing "{full_query}" on {device_label}.'
                last_playback_status = message

    destination = f"/admin/refresh{admin_query(pin)}"
    if message:
        joiner = "&" if "?" in destination else "?"
        destination = f"{destination}{joiner}{urlencode({'message': message})}"
    return RedirectResponse(url=destination, status_code=303)


@app.post("/admin/skip-next")
async def skip_next(pin: Optional[str] = Query(default=None)):
    if not is_admin(pin):
        destination = "/admin"
        if pin:
            destination = f"{destination}{admin_query(pin)}"
        return RedirectResponse(url=destination, status_code=303)

    removed = request_queue.next()
    if removed is None:
        message = "Queue is empty, nothing to skip."
    else:
        song, artist = removed
        full_query = f"{song} {artist}" if artist else song
        message = f'Skipped "{full_query}".'

    destination = f"/admin/refresh{admin_query(pin)}"
    joiner = "&" if "?" in destination else "?"
    destination = f"{destination}{joiner}{urlencode({'message': message})}"
    return RedirectResponse(url=destination, status_code=303)


@app.post("/admin/remove")
async def remove_song(index: int = Form(...), pin: Optional[str] = Query(default=None)):
    if not is_admin(pin):
        destination = "/admin"
        if pin:
            destination = f"{destination}{admin_query(pin)}"
        return RedirectResponse(url=destination, status_code=303)

    removed = request_queue.remove(index)
    if removed is None:
        message = "Could not remove that queue item."
    else:
        song, artist = removed
        full_query = f"{song} {artist}" if artist else song
        message = f'Removed "{full_query}" from the queue.'

    destination = f"/admin/refresh{admin_query(pin)}"
    joiner = "&" if "?" in destination else "?"
    destination = f"{destination}{joiner}{urlencode({'message': message})}"
    return RedirectResponse(url=destination, status_code=303)


@app.post("/admin/device")
async def set_device(device_id: str = Form(""), pin: Optional[str] = Query(default=None)):
    global selected_device_id, last_playback_status

    if not is_admin(pin):
        destination = "/admin"
        if pin:
            destination = f"{destination}{admin_query(pin)}"
        return RedirectResponse(url=destination, status_code=303)

    cleaned_device_id = device_id.strip()
    devices = current_devices()
    valid_ids = {str(device.get('id', '') or '') for device in devices}

    if cleaned_device_id and cleaned_device_id not in valid_ids:
        message = "That Spotify device is no longer available."
    else:
        selected_device_id = cleaned_device_id
        if selected_device_id:
            device_name = selected_device_name(devices) or "selected device"
            message = f"Playback device set to {device_name}."
            last_playback_status = message
        else:
            message = "Playback device reset to Spotify default."
            last_playback_status = message

    destination = f"/admin/refresh{admin_query(pin)}"
    joiner = "&" if "?" in destination else "?"
    destination = f"{destination}{joiner}{urlencode({'message': message})}"
    return RedirectResponse(url=destination, status_code=303)


@app.post("/admin/clear")
async def clear_queue(pin: Optional[str] = Query(default=None)):
    if not is_admin(pin):
        destination = "/admin"
        if pin:
            destination = f"{destination}{admin_query(pin)}"
        return RedirectResponse(url=destination, status_code=303)

    removed_count = request_queue.clear()
    if removed_count:
        message = f"Cleared {removed_count} queued request(s)."
    else:
        message = "Queue was already empty."

    destination = f"/admin/refresh{admin_query(pin)}"
    joiner = "&" if "?" in destination else "?"
    destination = f"{destination}{joiner}{urlencode({'message': message})}"
    return RedirectResponse(url=destination, status_code=303)


@app.get("/admin/refresh", response_class=HTMLResponse)
async def admin_refresh(
    request: Request,
    pin: Optional[str] = Query(default=None),
    message: Optional[str] = Query(default=None),
):
    return render_admin(request, pin, message)


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "queue_length": len(request_queue),
        "spotify_ready": spotify is not None,
        "admin_pin_configured": bool(ADMIN_PIN),
        "selected_device_id": selected_device_id or None,
        "last_playback_status": last_playback_status,
    }
