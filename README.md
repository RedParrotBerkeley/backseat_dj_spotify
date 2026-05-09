# Backseat DJ

**Backseat DJ** is a rideshare music request app that lets passengers submit songs from a simple web page while the driver controls playback from a separate admin view.

The core idea is straightforward:
make it easy for riders to request music without turning the driver into a DJ taking verbal requests all night.

## What it does

Backseat DJ gives a driver a lightweight system for:
- collecting song requests from passengers
- managing a live queue
- controlling playback from a separate admin screen
- keeping the rider experience fun without making the workflow chaotic

This is aimed at real-world use in environments like:
- Uber
- Lyft
- private rides
- event or shuttle environments where a shared queue makes sense

## Why this exists

Music requests are a real part of the rideshare experience, but the normal workflow is messy.

Passengers ask out loud.
The driver has to stop what they are doing, search manually, and manage the social friction of yes/no requests while also driving safely.

Backseat DJ turns that into a cleaner system:
- passengers request from their phones
- requests land in a queue
- the driver reviews and plays them when safe

It is a small product, but it solves a real interaction problem.

## Current MVP

The current version is a FastAPI app with:
- a passenger request page
- a driver/admin page
- a file-backed request queue
- optional admin PIN protection
- playback provider abstraction
- official Spotify OAuth/Web API playback support
- queue persistence across restarts
- device selection and saved playback settings

## Current architecture

- `app/main.py` - FastAPI routes and primary app flow
- `app/queue.py` - file-backed queue persisted to `data/queue.json`
- `app/playback.py` - playback provider interface
- `app/spotify_oauth_provider.py` - official Spotify OAuth/Web API playback provider
- `app/spotapi_provider.py` - legacy SpotAPI fallback provider
- `templates/index.html` - passenger request UI
- `templates/admin.html` - driver/admin controls
- `static/style.css` - shared styling

## What works today

- passengers can submit song requests from a simple web form
- the current queue is visible on the passenger page
- queue data persists across app restarts
- the driver has a separate admin page for playback controls
- admin actions can be protected with a shared PIN
- playback failures can re-queue the song automatically
- queued songs can be skipped or removed from the admin view
- playback status and visible devices can be inspected from the admin page
- a preferred playback device can be selected and saved

## Product direction

Backseat DJ is interesting because it is more than a toy playlist app.

It sits in a useful middle ground between:
- rider experience
- driver workflow
- lightweight consumer product design
- operational simplicity

The long-term opportunity is not just “request a song.”
It is creating a cleaner rider-to-driver interaction loop around music, mood, and experience.

## MVP gaps worth tackling next

- improve anti-spam / rate limiting for public-facing usage
- strengthen auth if the app moves beyond personal-use beta
- improve deployment and public-beta ergonomics
- add better UX polish for drivers under real-world conditions

## Setup

### 1. Create a virtual environment and install dependencies

Python 3.11+ is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_app_client_id
SPOTIFY_CLIENT_SECRET=***
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/spotify/callback
BACKSEAT_DJ_ADMIN_PIN=1234
BACKSEAT_DJ_DEVICE_ID=spotify_device_id_here
```

Notes:
- `SPOTIFY_REDIRECT_URI` must exactly match a Redirect URI in the Spotify Developer Dashboard
- local development should use `http://127.0.0.1:8000/auth/spotify/callback`
- after the app starts, open `/admin` and use **Connect Spotify** to complete OAuth
- Spotify playback control requires a Spotify Premium account and an active playback device
- `BACKSEAT_DJ_ADMIN_PIN` is optional, but recommended if anyone else can reach `/admin`
- once a playback device is selected in the admin UI, the app saves it in `data/settings.json`
- OAuth tokens are stored in `data/spotify_tokens.json` by default; set `SPOTIFY_TOKEN_PATH` to override
- `BACKSEAT_DJ_DEVICE_ID` is mainly a startup fallback

### 3. Launch the app

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

### 4. Verify health

```bash
curl http://localhost:8000/health
```

### 5. Use it

- open `http://localhost:8000` for the passenger page
- open `http://localhost:8000/admin` for driver controls
- choose a playback device if Spotify devices are visible

## Deployment notes

This repo already includes pieces to support a hosted beta path:
- `render.yaml`
- `Dockerfile`
- deployment notes in `docs/`
- an Apple beta shell under `apple/BackseatDJBeta/`

That makes it a useful product prototype rather than just a local hack.

## Important caveats

- Spotify playback control requires Spotify Premium and an active device
- OAuth token storage is file-backed for beta; use managed storage before production/multi-user use
- the admin PIN is an MVP safeguard, not production-grade auth
- the current app should be treated as a prototype / beta, not production software

## Status

Backseat DJ is an **active MVP / prototype**.

It already demonstrates the request workflow and now uses official Spotify OAuth/Web API plumbing for playback.
The next step is a hosted beta smoke test with a Premium account and active device.


## Portfolio snapshot

- **Problem:** In-car music requests are socially noisy and operationally awkward for rideshare drivers.
- **Core capability:** Passenger request flow with separate driver queue/playback controls.
- **Primary stack:** Python FastAPI web app with rider/driver views.
- **Status:** Functional MVP oriented around real rideshare usage.
