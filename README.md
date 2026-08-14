# ChatGPT & Claude Export Requester

A containerized Playwright project that **only initiates** data exports from the ChatGPT and Claude web UIs.

It does **not**:
- read email
- download the export archive
- parse the export
- use the OpenAI or Anthropic APIs

It uses **persisted browser profiles** that are already logged into each service.

## What it does

1. Launch Chromium with the persisted profile
2. Open the target service (ChatGPT or Claude)
3. Navigate to the export settings
4. Click the export button
5. Save screenshots and a log entry
6. Exit

## Quick start

### 1. Build
```bash
docker compose build
```

### Development checks
Run:

```bash
make lint
make test
```

`make lint` runs `ruff` and `mypy`. `make test` runs pytest and writes
`coverage.xml` for Codecov; coverage remains informational until it reaches 80%.

### 2. Bootstrap the browser profiles
Run once per service, non-headless, and log in manually:

**ChatGPT:**
```bash
docker compose run --rm exporter bootstrap
```

**Claude:**
```bash
docker compose run --rm exporter claude-bootstrap
```

A Chromium window should open. Log into the service, verify you can reach the app, then close the browser.

Sessions will be stored in `./profile` (ChatGPT) and `./claude-profile` (Claude).

### 3. Request an export

**Both platforms (default):**
```bash
docker compose run --rm exporter
```

**ChatGPT only:**
```bash
docker compose run --rm exporter request
```

**Claude only:**
```bash
docker compose run --rm exporter claude-request
```

Artifacts will land in:
- `./logs`
- `./screenshots`

## Scheduled monthly run

Example cron entry (requests both exports):

```cron
15 3 1 * * cd /opt/docker-ai-export-requester && docker compose run --rm exporter >> logs/cron.log 2>&1
```

## Notes

- The `profile/` and `claude-profile/` directories contain session cookies. Treat them like credentials.
- UI selectors may drift over time. If a run fails, start with the screenshots.
- This project intentionally avoids email handling and download automation.
- GitHub Actions runs `make lint` on pushes to `master` and pull requests, and publishes a GHCR image on pushes to `master` or tags.

## Using a .env file

Rather than embedding credentials in your `docker-compose.yml`, you can store them in a `.env` file and bind-mount it into the container:

```bash
cp .env.example .env
# edit .env with your values
```

```yaml
services:
  app:
    image: ghcr.io/jasmeralia/docker-ai-export-requester:latest
    volumes:
      - /path/to/your/.env:/app/.env:ro
```

The app loads `/app/.env` automatically on startup. Any value in `.env` can still be overridden by an explicit `environment:` entry in your Compose file.
