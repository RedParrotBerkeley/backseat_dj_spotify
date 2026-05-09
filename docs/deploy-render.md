# Deploy Backseat DJ Beta on Render

## What this gives you
- a hosted URL for the passenger page
- a hosted admin page
- official Spotify OAuth callback handling
- a clean path to generating a QR code once the URL is live

## Spotify dashboard setup

Add the deployed callback URL to the Spotify Developer Dashboard **Redirect URIs** list before connecting from the hosted admin page:

```text
https://<your-render-url>/auth/spotify/callback
```

The value must exactly match the deployed `SPOTIFY_REDIRECT_URI`, including protocol, host, and path.

## Steps

1. Push the latest repo to GitHub.
2. In Render, create a new Web Service from the repo.
3. Render should detect `render.yaml`.
4. Set these secret env vars in Render:
   - `BACKSEAT_DJ_ADMIN_PIN`
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `SPOTIFY_REDIRECT_URI=https://<your-render-url>/auth/spotify/callback`
5. Add a persistent disk or other durable storage if you want file-backed queue/settings/token state to survive service rebuilds.
6. Deploy.
7. Open `/admin`, unlock with the admin PIN, and use **Connect Spotify** to complete OAuth.

## After deploy
- passenger page: `https://<your-render-url>/`
- admin page: `https://<your-render-url>/admin`
- OAuth callback: `https://<your-render-url>/auth/spotify/callback`
- health: `https://<your-render-url>/health`

## Notes
- Current queue/settings/token storage is file-backed, so this hosted beta is okay for early testing but not durable production infrastructure unless backed by persistent disk.
- OAuth tokens default to `data/spotify_tokens.json`; set `SPOTIFY_TOKEN_PATH` if Render disk mounts somewhere else.
- Spotify playback control requires a Premium account and an active Spotify playback device.
- For a stronger hosted version later, move queue/settings/tokens into a real database or managed store.
- Keep the admin PIN enabled before sharing the passenger URL widely.
