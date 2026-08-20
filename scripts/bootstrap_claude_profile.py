import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from settings import settings


def main() -> int:
    base_url = settings.claude_base_url
    profile_path = settings.claude_profile_path
    screenshot_dir = Path(settings.screenshot_dir)

    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile_path,
            headless=False,
            viewport={"width": 1600, "height": 1200},
        )
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        page.screenshot(path=str(screenshot_dir / "claude-bootstrap-opened.png"), full_page=True)

        print("")
        print("Bootstrap mode is running.")
        print("Log into Claude in the opened browser window if needed.")
        print("Once you can access the app normally, close the browser window.")
        print("The persisted profile will remain in /app/claude-profile.")
        print("")

        page.wait_for_timeout(60000 * 30)
        context.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
