import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from settings import settings

BASE_URL = settings.chatgpt_base_url
PROFILE_PATH = settings.chatgpt_profile_path
SCREENSHOT_DIR = Path(settings.screenshot_dir)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            PROFILE_PATH,
            headless=False,
            viewport={"width": 1600, "height": 1200},
        )
        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.screenshot(path=str(SCREENSHOT_DIR / "bootstrap-opened.png"), full_page=True)

        print("")
        print("Bootstrap mode is running.")
        print("Log into ChatGPT in the opened browser window if needed.")
        print("Once you can access the app normally, close the browser window.")
        print("The persisted profile will remain in /app/profile.")
        print("")

        page.wait_for_timeout(60000 * 30)
        context.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
