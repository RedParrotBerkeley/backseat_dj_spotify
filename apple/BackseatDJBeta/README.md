# Backseat DJ Apple Beta Shell

This directory is the starting point for the Apple app beta track.

## Goal
Ship a simple iPhone app that can become a TestFlight beta while the hosted web product keeps moving.

## Recommended first version
- SwiftUI app
- Two entry points:
  - Passenger mode
  - Driver/Admin mode
- Start as a lightweight wrapper around the hosted beta URL
- Later replace web-wrapper screens with native views as the backend stabilizes

## Suggested first screens
1. Welcome / mode picker
2. Passenger web view
3. Driver/Admin web view
4. Settings screen for base URL and optional admin PIN convenience

## Why this approach
- fastest path to an actual beta on iPhone
- easy to distribute through TestFlight
- does not block product iteration on native UI work first

## Immediate next engineering tasks
1. Create Xcode SwiftUI project in this folder
2. Add WKWebView wrapper views
3. Add configurable base URL
4. Add QR scanner later if needed
