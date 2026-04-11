# Backseat DJ (SpotAPI Edition)

Backseat DJ is a small FastAPI app for car rides: passengers submit song requests from a simple web page, and the driver can play the next request from a separate admin page when it is safe.

This repo is still an MVP and currently uses SpotAPI, an unofficial Spotify wrapper.

Important April 2026 note: Spotify appears to be intermittently blocking or hiding new app creation for some developer accounts with a "new integrations are on hold" restriction. This repo is now seeded for an official OAuth migration path, but that final step may remain blocked until Spotify re-enables app creation for the account.

## Current architecture

- `app/main.py`: FastAPI routes, passenger page, admin page, and staged Spotify OAuth routes
- `app/queue.py`: file-backed queue persisted to `data/queue.json`, now storing future-ready match metadata
- `app/playback.py`: provider interface and provider status structures
- `app/provider_registry.py`: central provider selection and fallback logic
- `app/spotapi_provider.py`: current SpotAPI-backed playback provider
- `app/official_spotify_provider.py`: staged official Spotify OAuth provider stub
- `templates/index.html`: passenger request page
- `templates/admin.html`: driver/admin controls and provider status visibility
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
- See playback status, provider mode, last attempted request, and available playback devices
- Choose a preferred Spotify playback device when one is visible
- Store future-ready queue metadata for matched Spotify title, artist, URI, album art URL, and match status
- Show lightweight matched-track previews in the queue UI when the active provider can resolve them

## MVP gaps still worth tackling next

- Finish the staged official Spotify OAuth provider implementation once app creation is available
- Switch provider selection by config once the OAuth path is ready
- Add stronger rate limiting if passengers start spamming the queue
- Add lightweight auth or session controls if this ever leaves personal-use mode

## Spotify auth and app creation issue

Current live research suggests the missing Create App button is often not a browser bug. Multiple Spotify community threads in 2026 report the dashboard showing variants of:
- "New integrations are currently on hold"
- disabled or missing Create App button
- app creation blocked for new developer setups

This has two separate implications:

### 1. Spotify developer app creation may be blocked
- the dashboard may not let Mike create a new Spotify app right now
- direct create URLs do not appear to reliably bypass the restriction
- this seems to be a Spotify-side platform restriction, not just mobile Safari being broken

### 2. Official OAuth wiring is staged, but not complete
The repo is now prepared for official Spotify auth, but the full path is intentionally unfinished until app creation is actually possible.

Current staged pieces:
- `app/official_spotify_provider.py`
- `app/provider_registry.py`
- `/spotify/login`
- `/spotify/callback`
- provider status surfaced in admin UI
- queue metadata ready for exact Spotify match storage

Practical implication for this project:
- we can keep building product and data flow now
- we may not be able to finish the final credential wiring until Spotify allows app creation on the target account again
- if Mike already had an older Spotify developer app, that would likely unblock us immediately

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

# Staged official Spotify OAuth config
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/spotify/callback
```

The app also accepts `SPOTIFY_USER` and `SPOTIFY_PASS`.

Notes:
- `BACKSEAT_DJ_ADMIN_PIN` is optional, but recommended if anyone besides you can reach `/admin`.
- After you choose a playback device in the admin UI, the app persists it in `data/settings.json` across restarts.
- The environment variable `BACKSEAT_DJ_DEVICE_ID` is now just a startup fallback.
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI` are staged for the official provider path, but do not complete OAuth playback by themselves yet.

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

## OAuth migration seed status

The codebase is being prepared around this target future state:
- official Spotify OAuth app with server-side token handling
- queue stores real Spotify track matches instead of only raw request strings
- playback device selection still lives in the admin UI
- SpotAPI remains the fallback while official app creation is blocked
- `app/official_spotify_provider.py` now exists as the interface-compatible stub for that handoff
- queue items can already carry matched metadata and display match-ready status in the UI

Recommended implementation order once Spotify app creation is available again:
1. create Spotify app in dashboard
2. add redirect URI(s)
3. add server routes for `/login` and `/callback`
4. persist refresh token securely
5. refresh access tokens automatically
6. use official search endpoint to resolve requests into track URIs
7. play exact track URIs instead of free-text search when possible

## Dev push readiness notes

This repo is now in a cleaner intermediate state for another push to `dev`:
- provider selection is centralized
- official Spotify provider stub is in place
- queue model is future-ready for exact Spotify matches
- UI surfaces provider/auth state and match-ready queue items
- README now documents the Spotify app creation blocker and staged OAuth path

What is still intentionally incomplete before full official Spotify support:
- token exchange and refresh flow
- real OAuth callback handling
- official provider search/device/playback implementation
- final persistence flow for resolved match metadata beyond lightweight preview hydration

## Beta and migration notes

- `docs/beta-plan.md` outlines the recommended beta path: hosted web beta first, then SwiftUI/TestFlight wrapper, then deeper native work.
- `docs/deploy-render.md` documents the fastest hosted-beta path.
- `render.yaml` and `Dockerfile` were added so the app is easier to deploy to a public beta URL.
- `apple/BackseatDJBeta/README.md` is the starting point for the Apple app beta shell.
- Playback now sits behind a provider abstraction so we can add an official Spotify OAuth provider without rewriting the whole app again.
- SpotAPI is still the active provider today, and it remains unofficial.
- Device visibility depends on what the active playback provider can see from the authenticated Spotify account.
- The app stores queue state in `data/queue.json` and saved playback settings in `data/settings.json`.
- The current admin PIN flow is a lightweight MVP safeguard, not strong production auth.
- This should be treated as a personal-use prototype, not a production app.
