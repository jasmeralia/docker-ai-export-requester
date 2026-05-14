# AGENTS.md

## Project goal
This project automates **requesting** data exports from the ChatGPT and Claude web UIs.

## Hard scope limits
Do not add:
- email reading
- IMAP integration
- archive downloading
- OpenAI or Anthropic API integration
- mailbox credentials
- export parsing

## Existing assumptions
- The user has valid ChatGPT and/or Claude subscriptions/sessions
- Persistent Chromium profiles are mounted at `/app/profile` (ChatGPT) and `/app/claude-profile` (Claude)
- The profiles are logged into their respective services
- The app runs in a container

## Key files
- `scripts/request_export.py` — ChatGPT export requester
- `scripts/request_claude_export.py` — Claude export requester
- `scripts/bootstrap_profile.py` — ChatGPT interactive profile bootstrap
- `scripts/bootstrap_claude_profile.py` — Claude interactive profile bootstrap
- `scripts/run_export.sh` — wrapper for ChatGPT runs
- `scripts/run_claude_export.sh` — wrapper for Claude runs
- `scripts/bootstrap_profile.sh` — wrapper for ChatGPT login bootstrap
- `scripts/bootstrap_claude_profile.sh` — wrapper for Claude login bootstrap
- `docker-ai-export-requester-context.md` — project context and future-phase planning

## Runtime behavior expectations
- Save screenshots before and after major UI actions
- Log success/failure to `/app/logs`
- Exit nonzero on failure
- Keep selectors readable and easy to update

## After Any Code Change

```bash
make lint-fix && make lint
```

Resolve all reported issues before committing.

## Git Workflow

- Never push commits directly to `master`. Always open a pull request from a feature/fix branch.
- Use squash merge strategy when merging pull requests.

## Debugging approach
1. Inspect latest screenshot in `screenshots/`
2. Run `bootstrap` or `claude-bootstrap` mode non-headless
3. Verify the profile is still logged in
4. Adjust selectors if the UI moved

## Future work
A separate project may later parse `conversations.json` and generate infra documentation, but that is out of scope here.
