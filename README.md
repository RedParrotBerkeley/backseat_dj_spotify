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

## MVP gaps still worth tackling next

- Add duplicate / spam protection
- Add skip/remove moderation controls for the driver
- Add device selection and better playback status
- Replace SpotAPI with official Spotify OAuth when ready

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

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

### 3. Run the app

From the repo root:

```bash
uvicorn app.main:app --reload
```

Then open <http://localhost:8000> for passengers and <http://localhost:8000/admin> for driver controls.

## Notes

- SpotAPI is unofficial and may break without warning.
- The current admin PIN flow is a lightweight MVP safeguard, not strong production auth.
- This should be treated as a personal-use prototype, not a production app.
