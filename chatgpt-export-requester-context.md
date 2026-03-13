# ChatGPT Export Requester Context

## Scope

This project exists to **initiate only** a ChatGPT account export from the ChatGPT web interface.

It should:

1. Run in a container
2. Reuse a persisted Chromium profile that is already logged into ChatGPT
3. Navigate to the ChatGPT UI
4. Open **Settings → Data Controls**
5. Click **Export Data**
6. Save screenshots and logs
7. Exit

It should **not**:

- read email
- poll IMAP
- download the export archive
- parse `conversations.json`
- use the OpenAI API
- require API keys

## Why this project exists

The user wants a low-friction way to periodically request a ChatGPT export without manually clicking through the UI each time.

The export email and archive handling remain manual for now.

## Architecture

```text
host cron / manual run
        ↓
docker compose run --rm exporter request
        ↓
Playwright launches Chromium with persistent profile
        ↓
ChatGPT session already authenticated
        ↓
navigate to Settings → Data Controls
        ↓
click Export Data
        ↓
write screenshots + logs
        ↓
exit
```

## Repository layout

```text
chatgpt-export-requester/
├── README.md
├── AGENTS.md
├── chatgpt-export-requester-context.md
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── scripts/
│   ├── request_export.py
│   ├── bootstrap_profile.py
│   ├── run_export.sh
│   └── bootstrap_profile.sh
├── logs/
├── profile/
└── screenshots/
```

## Implementation notes

### Persistent browser profile
Use a mounted profile directory. The first run should be interactive so the user can log in manually and persist cookies.

### Headless vs non-headless
- Bootstrap: non-headless
- Steady-state request mode: headless by default, but configurable

### Selector philosophy
Prefer selectors that are easy to adjust and well-commented.

### Proof of action
Each run should save:
- a timestamped log line
- a before screenshot
- an after screenshot
- an error screenshot on failure

## Security notes

The `profile/` directory effectively contains authenticated session material. Protect it like credentials:
- do not commit it
- restrict permissions
- keep it off casual backups if possible

## Later phase plan

After a human downloads the archive manually, a separate project can:
1. unpack `conversations.json`
2. normalize thread/message structures
3. extract commands, config paths, services, fixes, and root causes
4. generate:
   - `SERVER_NOTES.md`
   - `AGENTS.md`
   - `KNOWN_ISSUES.md`
   - runbooks and helper scripts for `rin-city-infra`

That later parser/documentation project is intentionally out of scope here, but this repo should keep enough context to make that future phase straightforward.

## Suggested next iteration ideas
- add a dry-run mode that stops before clicking Export Data
- add a healthcheck mode that verifies the session is still logged in
- add selector fallback logic if the settings UI changes
- add structured JSON logging
