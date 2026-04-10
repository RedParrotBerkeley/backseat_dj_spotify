import json
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.playback import PlaybackDevice, PlaybackProvider
from app.queue import request_queue
from app.spotapi_provider import SpotAPIPlaybackProvider

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
APP_DATA_DIR = BASE_DIR / "data"
SETTINGS_PATH = APP_DATA_DIR / "settings.json"

app = FastAPI(title="Backseat DJ")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


playback_provider: Optional[PlaybackProvider] = SpotAPIPlaybackProvider.from_env()
ADMIN_PIN = os.getenv("BACKSEAT_DJ_ADMIN_PIN")
last_playback_status = "Spotify playback has not been used yet."
last_selected_query = ""


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        raw = json.loads(SETTINGS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}

    return raw if isinstance(raw, dict) else {}


def save_settings(settings: dict) -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))


_runtime_settings = load_settings()
selected_device_id = str(
    _runtime_settings.get("selected_device_id")
    or os.getenv("BACKSEAT_DJ_DEVICE_ID", "")
).strip()


def is_admin(pin: Optional[str]) -> bool:
    if not ADMIN_PIN:
        return True
    return bool(pin) and pin == ADMIN_PIN


def admin_query(pin: Optional[str]) -> str:
    if not pin:
        return ""
    return f"?{urlencode({'pin': pin})}"


def public_queue_items() -> list[dict]:
    return [
        {"song": song, "artist": artist}
        for song, artist in request_queue.list()
    ]


def admin_queue_items() -> list[dict]:
    return [
        {"index": index, "song": song, "artist": artist}
        for index, (song, artist) in enumerate(request_queue.list())
    ]


def render_home(request: Request, message: Optional[str] = None) -> HTMLResponse:
    queue = public_queue_items()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "queue": queue,
            "queue_count": len(queue),
            "spotify_ready": playback_provider is not None and playback_provider.is_ready(),
            "message": message,
        },
    )


def current_devices():
    if playback_provider is None:
        return []
    return playback_provider.devices()


def normalized_devices():
    return current_devices()


def template_devices() -> list[dict]:
    devices = []
    for device in normalized_devices():
        label = device.name or "Unknown device"
        if device.type:
            label = f"{label} · {device.type}"
        if device.is_active:
            label = f"{label} (active)"
        devices.append({"id": device.id, "label": label})
    return devices


def selected_device_name(devices) -> Optional[str]:
    if not selected_device_id:
        return None
    for device in devices:
        if device.id == selected_device_id:
            return device.name or "Selected device"
    return None


def active_device_name(devices) -> Optional[str]:
    for device in devices:
        if device.is_active:
            return device.name or "Active device"
    return None


def render_admin(request: Request, pin: Optional[str], message: Optional[str] = None) -> HTMLResponse:
    authorized = is_admin(pin)
    raw_devices = normalized_devices()
    queue = admin_queue_items()
    configured_device_name = selected_device_name(raw_devices)
    current_active_device = active_device_name(raw_devices)
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "queue": queue,
            "queue_count": len(queue),
            "spotify_ready": playback_provider is not None and playback_provider.is_ready(),
            "message": message,
            "admin_configured": bool(ADMIN_PIN),
            "authorized": authorized,
            "pin": pin or "",
            "admin_action": f"/play-next{admin_query(pin)}",
            "clear_action": f"/admin/clear{admin_query(pin)}",
            "remove_base": "/admin/remove",
            "skip_action": f"/admin/skip-next{admin_query(pin)}",
            "device_action": f"/admin/device{admin_query(pin)}",
            "devices": template_devices(),
            "device_count": len(raw_devices),
            "selected_device_id": selected_device_id,
            "selected_device_name": configured_device_name,
            "active_device_name": current_active_device,
            "last_playback_status": last_playback_status,
            "last_selected_query": last_selected_query,
            "playback_provider_name": playback_provider.provider_name() if playback_provider else None,
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
    global last_playback_status, last_selected_query

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

        if playback_provider is None:
            request_queue.add(song, artist)
            message = "Spotify credentials are not configured yet."
            last_playback_status = message
            last_selected_query = full_query
        else:
            last_selected_query = full_query
            playback_result = playback_provider.search_and_play(full_query, device_id=selected_device_id or None)
            if not playback_result.ok:
                request_queue.add(song, artist)
                if playback_result.error:
                    message = f'Could not play "{full_query}". {playback_result.error}. The request was returned to the queue.'
                else:
                    message = f'Could not play "{full_query}". The request was returned to the queue.'
                last_playback_status = message
            else:
                provider_label = playback_provider.provider_name() if playback_provider else "spotify"
                device_label = selected_device_name(normalized_devices()) or active_device_name(normalized_devices()) or f"default {provider_label} device"
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
    devices = normalized_devices()
    valid_ids = {device.id for device in devices}

    if cleaned_device_id and cleaned_device_id not in valid_ids:
        message = "That Spotify device is no longer available."
    else:
        selected_device_id = cleaned_device_id
        save_settings({"selected_device_id": selected_device_id})
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
        "spotify_ready": playback_provider is not None and playback_provider.is_ready(),
        "playback_provider": playback_provider.provider_name() if playback_provider else None,
        "admin_pin_configured": bool(ADMIN_PIN),
        "selected_device_id": selected_device_id or None,
        "last_playback_status": last_playback_status,
        "last_selected_query": last_selected_query or None,
        "active_device_name": active_device_name(normalized_devices()),
    }
