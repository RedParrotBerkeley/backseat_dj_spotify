# Backseat DJ (SpotAPI Edition)

Backseat DJ is a tiny FastAPI app for car rides: passengers submit song requests from a simple web page, and the driver can play the next request from the queue when it is safe.

This repo is still an MVP and currently uses SpotAPI, an unofficial Spotify wrapper.

## Current architecture

- `app/main.py`: FastAPI routes and page rendering
- `app/queue.py`: small file-backed queue persisted to `data/queue.json`
- `app/spotapi_wrapper.py`: Spotify search-and-play adapter
- `templates/index.html`: single-page passenger and driver UI
- `static/style.css`: app styling

## What works now

- Add song requests from the web form
- View the current queue on the same page
- Persist the queue across restarts
- Gracefully run even when Spotify credentials are missing
- Trigger "play next" from the browser
- Re-queue the song if playback fails

## MVP gaps still worth tackling next

- Split passenger UI from driver/admin controls
- Add duplicate / spam protection
- Add lightweight auth for driver actions
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

### 3. Run the app

From the repo root:

```bash
uvicorn app.main:app --reload
```

Then open <http://localhost:8000>.

## Notes

- SpotAPI is unofficial and may break without warning.
- This should be treated as a personal-use prototype, not a production app.
