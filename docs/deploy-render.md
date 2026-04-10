# Deploy Backseat DJ Beta on Render

## What this gives you
- a hosted URL for the passenger page
- a hosted admin page
- a clean path to generating a QR code once the URL is live

## Steps

1. Push the latest repo to GitHub
2. In Render, create a new Web Service from the repo
3. Render should detect `render.yaml`
4. Set these secret env vars in Render:
   - `BACKSEAT_DJ_ADMIN_PIN`
   - `SPOTIFY_USERNAME` and `SPOTIFY_PASSWORD`
     or
   - `SPOTIFY_USER` and `SPOTIFY_PASS`
5. Deploy

## After deploy
- passenger page: `https://<your-render-url>/`
- admin page: `https://<your-render-url>/admin`
- health: `https://<your-render-url>/health`

## Notes
- Current queue/settings storage is file-backed, so this hosted beta is okay for early testing but not durable production infrastructure.
- For a stronger hosted version later, move queue/settings into a real database or managed store.
- Keep the admin PIN enabled before sharing the passenger URL widely.
