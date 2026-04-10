# Backseat DJ (SpotAPI Edition)

Backseat DJ is a small FastAPI app for car rides: passengers submit song requests from a simple web page, and the driver can play the next request from a separate admin page when it is safe.

This repo is still an MVP and currently uses SpotAPI, an unofficial Spotify wrapper.

## Current architecture

- `app/main.py`: FastAPI routes, passenger page, and admin page
- `app/queue.py`: file-backed queue persisted to `data/queue.json`
- `app/spotapi_wrapper.py`: Spotify search-and-play adapter
- `templates/index.html`: passenger request page
- `templates/admin.html`: driver/admin controls
- `static/style.css`: shared styling

## What works now

- Add song requests from the passenger web form
- View the current queue on the passenger page
- Keep queue data across app restarts
- Run even when Spotify credentials are missing
- Use a separate `/admin` page for driver playback controls
- Optionally protect admin playback actions with a shared PIN
- Re-queue the song automatically if playback fails
- Skip or remove queued requests from the admin page
- See playback status, last attempted request, and available playback devices
- Choose a preferred Spotify playback device when one is visible

## MVP gaps still worth tackling next

- Replace SpotAPI with official Spotify OAuth when ready
- Add better live playback confirmation from Spotify, not just best-effort status messages
- Add stronger rate limiting if passengers start spamming the queue
- Add lightweight auth or session controls if this ever leaves personal-use mode

## Setup

### 1. Create a virtual environment and install dependencies

Python 3.11+ is recommended. The current `spotapi` dependency is not reliable on Python 3.9.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you only have Python 3.9 available, the app can still run in queue-only mode, but Spotify playback support may stay disabled until you upgrade Python.

### 2. Configure environment

Create a `.env` file in the project root:

```env
SPOTIFY_USERNAME=your_email
SPOTIFY_PASSWORD=your_password
BACKSEAT_DJ_ADMIN_PIN=1234
# Optional one-time default before the app saves your selection:
BACKSEAT_DJ_DEVICE_ID=spotify_device_id_here
```

The app also accepts `SPOTIFY_USER` and `SPOTIFY_PASS`.

Notes:
- `BACKSEAT_DJ_ADMIN_PIN` is optional, but recommended if anyone besides you can reach `/admin`.
- After you choose a playback device in the admin UI, the app persists it in `data/settings.json` across restarts.
- The environment variable `BACKSEAT_DJ_DEVICE_ID` is now just a startup fallback.

### 3. Launch the app

From the repo root:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

### 4. Verify it started cleanly

In another terminal:

```bash
curl http://localhost:8000/health
```

You should see JSON showing the queue length plus playback/admin status.

### 5. Use it

- Open <http://localhost:8000> for the passenger request page
- Open <http://localhost:8000/admin> for driver controls
- In `/admin`, choose a playback device once if Spotify devices are visible
- That selected device will now persist across restarts in `data/settings.json`

## Notes

- SpotAPI is unofficial and may break without warning.
- Device visibility depends on what SpotAPI can see from the authenticated Spotify account.
- The app stores queue state in `data/queue.json` and saved playback settings in `data/settings.json`.
- The current admin PIN flow is a lightweight MVP safeguard, not strong production auth.
- This should be treated as a personal-use prototype, not a production app.
