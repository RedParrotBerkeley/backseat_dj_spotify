# Spotify OAuth Seed Notes

This file captures the official Spotify integration target while Spotify app creation is currently blocked for some accounts by the developer dashboard.

## Current blocker

Observed behavior in April 2026:
- Spotify developer dashboard may hide or disable app creation
- users report the message: "New integrations are currently on hold"
- direct create URLs do not reliably bypass the restriction

This appears to be a Spotify-side restriction, not just a mobile Safari issue.

## What Backseat DJ needs from official Spotify

Minimum capabilities:
- user login and consent
- search tracks
- list playback devices
- start playback on chosen device
- skip to next track
- inspect current playback state

Useful endpoints:
- `GET /v1/search`
- `GET /v1/me/player/devices`
- `PUT /v1/me/player/play`
- `POST /v1/me/player/next`
- `GET /v1/me/player`

Useful scopes:
- `user-read-playback-state`
- `user-modify-playback-state`
- `user-read-currently-playing`
- `user-read-private`

## Proposed app flow

### Driver auth

Only the driver account needs Spotify auth.

Planned server routes:
- `GET /spotify/login`
- `GET /spotify/callback`
- optional `POST /spotify/disconnect`

### Request flow

1. Passenger submits song and optional artist.
2. App stores the original request.
3. Official Spotify search resolves the best track.
4. Queue item can later store:
   - raw song title
   - raw artist
   - matched track name
   - matched artist name
   - Spotify track URI
   - album art URL
   - confidence or match status
5. Driver presses play next.
6. App plays exact URI on selected device.

## Why this is better than SpotAPI

- official auth instead of username/password automation
- less fragile
- better alignment with long-term hosted deployment
- easier to debug and reason about
- better path to richer search results and album art

## What can be built before the blocker clears

- queue model updates for matched track metadata
- provider abstraction improvements
- admin UI copy for OAuth readiness
- health/status surfacing for provider mode
- search-result display model
- graceful fallback when official app credentials are unavailable

## Unblock paths

1. Spotify restores app creation for Mike's account
2. Mike already has another Spotify developer account or older app with valid credentials
3. Spotify support/community provides an account-specific fix

## Recommendation

Do not block product progress on Spotify dashboard access.
Seed the code and UX now, then finish the final OAuth wiring as soon as app creation is available.
