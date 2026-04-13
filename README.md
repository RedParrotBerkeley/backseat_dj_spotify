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
- Spotify-oriented playback support through SpotAPI
- queue persistence across restarts
- device selection and saved playback settings

## Current architecture

- `app/main.py` - FastAPI routes and primary app flow
- `app/queue.py` - file-backed queue persisted to `data/queue.json`
- `app/playback.py` - playback provider interface
- `app/spotapi_provider.py` - current SpotAPI-backed playback provider
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

- add an official Spotify OAuth playback provider
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
SPOTIFY_USERNAME=your_email
SPOTIFY_PASSWORD=your_password
BACKSEAT_DJ_ADMIN_PIN=1234
BACKSEAT_DJ_DEVICE_ID=spotify_device_id_here
```

Notes:
- `BACKSEAT_DJ_ADMIN_PIN` is optional, but recommended if anyone else can reach `/admin`
- once a playback device is selected in the admin UI, the app saves it in `data/settings.json`
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

- the current playback provider is SpotAPI, which is unofficial
- the admin PIN is an MVP safeguard, not production-grade auth
- the current app should be treated as a prototype / beta, not production software

## Status

Backseat DJ is an **active MVP / prototype**.

It already demonstrates the workflow clearly.
The next step is not proving the idea exists, it is tightening the product and choosing the best beta path.
