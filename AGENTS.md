# AGENTS.md

## Project goal
This project only automates **requesting** a ChatGPT data export from the ChatGPT web UI.

## Hard scope limits
Do not add:
- email reading
- IMAP integration
- archive downloading
- OpenAI API integration
- mailbox credentials
- export parsing

## Existing assumptions
- The user has a valid ChatGPT subscription/session
- A persistent Chromium profile is mounted at `/app/profile`
- The profile is logged into ChatGPT
- The app runs in a container

## Key files
- `scripts/request_export.py` — main export requester
- `scripts/bootstrap_profile.py` — interactive profile bootstrap
- `scripts/run_export.sh` — wrapper for normal runs
- `scripts/bootstrap_profile.sh` — wrapper for initial login bootstrap
- `chatgpt-export-requester-context.md` — project context and future-phase planning

## Runtime behavior expectations
- Save screenshots before and after major UI actions
- Log success/failure to `/app/logs`
- Exit nonzero on failure
- Keep selectors readable and easy to update

## Debugging approach
1. Inspect latest screenshot in `screenshots/`
2. Run `bootstrap` mode non-headless
3. Verify the profile is still logged in
4. Adjust selectors if the UI moved

## Future work
A separate project may later parse `conversations.json` and generate infra documentation, but that is out of scope here.
