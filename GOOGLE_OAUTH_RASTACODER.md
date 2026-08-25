# RastaCoder Google OAuth / Gmail / Calendar

The app already contains working Gmail read/list and Google Calendar list/create tools. The remaining external requirement is a Google OAuth Android client which trusts this exact Android application identity.

## Android application identity

- Package name: `ai.navixmind`
- Stable RastaCoder development certificate SHA-1: `74:5D:97:54:87:32:A9:DE:D0:96:6E:A5:58:8E:78:68:8F:85:31:B6`
- Stable RastaCoder development certificate SHA-256: `87:D5:60:A2:D8:F7:A7:C7:FB:8F:D6:6B:40:AC:6A:40:FB:8F:21:0A:4F:43:6F:A4:68:EC:BB:AA:5B:61:70:B8`

The package ID intentionally remains `ai.navixmind` in v2 so the RastaCoder-signed v2 APK can update the already-tested RastaCoder v1 package in place.

## Google Cloud requirements

A Google Cloud project must have:

1. An Android OAuth 2.0 client registered for package `ai.navixmind` and the SHA-1 above.
2. Gmail API enabled.
3. Google Calendar API enabled.
4. OAuth consent configured for the account(s) which will test the app.
5. The requested scopes permitted:
   - `email`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.events`

The v2 source removes the original developer's hard-coded Web OAuth client ID. The app only needs a Google access token for direct Gmail/Calendar REST calls, so it does not request an ID token or backend server auth code.

## Current tool capability

- Gmail: list/search messages and read full messages.
- Gmail send: intentionally disabled by current tool schema and implementation.
- Calendar: list events and create events.

The access token obtained by Flutter is injected into the Python agent context for every query, so once Google Sign-In succeeds these tools can be called by the local agent without an additional login layer.

## Android release-build compatibility

The pinned Flutter 3.22 / `flutter_inappwebview_android` 1.0.13 combination has a known release-only R8 failure involving `android.window.BackEvent`. RastaCoder v2 disables minification only for that WebView library module while retaining the normal release build for the application. The override is attached through the Android Library plugin's `buildTypes.configureEach` lifecycle so it also works when Flutter has already evaluated Android subprojects. This workaround does not modify the MLC runtime, Qwen3 model registration, or agent/tool execution path.
