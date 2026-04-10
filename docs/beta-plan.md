# Backseat DJ Beta Plan

## Goal
Ship a beta that works in the car with the least friction:
- passenger page opens from a QR code or URL
- driver/admin page is separate and protected
- Mike can test quickly on iPhone without waiting for a fully native app first

## Recommended rollout

### Phase 1: Hosted web beta
- Deploy the FastAPI app to a reachable host
- Keep `/` as the passenger page
- Keep `/admin` as the driver page
- Protect `/admin` with `BACKSEAT_DJ_ADMIN_PIN`
- Generate a QR code for the passenger URL

### Phase 2: Apple wrapper beta
- Create a SwiftUI iPhone app
- First version can be a lightweight app shell around the hosted product
- Support two modes:
  - Passenger
  - Driver/Admin
- Distribute via TestFlight

### Phase 3: Native expansion
- Replace web-wrapper pieces with native queue/admin views
- Add camera QR scanning inside the app
- Add richer playback/admin state when the backend stabilizes

## Hosting options

### Fastest
- Render
- Railway
- Fly.io

### Good long-term
- Small VPS or container host once auth and deployment are more mature

## Immediate next steps
1. Introduce provider abstraction so Spotify migration does not destabilize the app
2. Add deployment config for a hosted beta
3. Generate a QR code once the first public beta URL exists
4. Start a SwiftUI app shell for TestFlight
