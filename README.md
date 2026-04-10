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

- Persist the selected playback device across restarts
- Replace SpotAPI with official Spotify OAuth when ready
- Add better live playback confirmation from Spotify, not just best-effort status messages
- Add stronger rate limiting if passengers start spamming the queue

## Setup

### 1. Create a virtual environment and install dependencies

Python 3.11+ is recommended. The current `spotapi` dependency is not reliable on Python 3.9.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you only have Python 3.9 available, the app can still run in queue-only mode, but Spotify playback support may stay disabled until you upgrade Python.

### 2. Configure Spotify credentials

Create a `.env` file in the project root:

```env
SPOTIFY_USERNAME=your_email
SPOTIFY_PASSWORD=your_password
```

The app also accepts `SPOTIFY_USER` and `SPOTIFY_PASS`.

Optional admin protection:

```env
BACKSEAT_DJ_ADMIN_PIN=1234
```

If `BACKSEAT_DJ_ADMIN_PIN` is set, `/admin` requires that PIN before playback controls are shown.

Optional default playback device:

```env
BACKSEAT_DJ_DEVICE_ID=spotify_device_id_here
```

### 3. Run the app

From the repo root:

```bash
uvicorn app.main:app --reload
```

You can verify the app boots even without Spotify credentials by checking:

```bash
curl http://localhost:8000/health
```

Then open <http://localhost:8000> for passengers and <http://localhost:8000/admin> for driver controls.

## Notes

- SpotAPI is unofficial and may break without warning.
- Device visibility depends on what SpotAPI can see from the authenticated Spotify account.
- The current admin PIN flow is a lightweight MVP safeguard, not strong production auth.
- This should be treated as a personal-use prototype, not a production app.
