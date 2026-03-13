# ChatGPT Export Requester

A containerized Playwright project that **only initiates** a ChatGPT data export from the web UI.

It does **not**:
- read email
- download the export archive
- parse the export
- use the OpenAI API

It uses a **persisted browser profile** that is already logged into ChatGPT.

## What it does

1. Launch Chromium with the persisted profile
2. Open ChatGPT
3. Navigate to **Settings → Data Controls**
4. Click **Export Data**
5. Save screenshots and a log entry
6. Exit

## Quick start

### 1. Build
```bash
docker compose build
```

### 2. Bootstrap the browser profile
Run once, non-headless, and log in manually:

```bash
docker compose run --rm exporter bootstrap
```

A Chromium window should open. Log into ChatGPT, verify you can reach the app, then close the browser.

Your session will be stored in `./profile`.

### 3. Request an export
```bash
docker compose run --rm exporter request
```

Artifacts will land in:
- `./logs`
- `./screenshots`

## Scheduled monthly run

Example cron entry:

```cron
15 3 1 * * cd /opt/chatgpt-export-requester && docker compose run --rm exporter request >> /opt/chatgpt-export-requester/logs/cron.log 2>&1
```

## Notes

- The `profile/` directory contains your ChatGPT session cookies. Treat it like a credential.
- UI selectors may drift over time. If a run fails, start with the screenshots.
- This project intentionally avoids email handling and download automation.
