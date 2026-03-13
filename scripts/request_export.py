import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = os.environ.get("CHATGPT_BASE_URL", "https://chatgpt.com")
PROFILE_PATH = os.environ.get("PROFILE_PATH", "/app/profile")
LOG_DIR = Path(os.environ.get("LOG_DIR", "/app/logs"))
SCREENSHOT_DIR = Path(os.environ.get("SCREENSHOT_DIR", "/app/screenshots"))
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
REQUEST_TIMEOUT_MS = int(os.environ.get("REQUEST_TIMEOUT_MS", "30000"))

LOG_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
run_log = LOG_DIR / f"export-request-{ts}.json"

def write_log(payload):
    run_log.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def save_shot(page, name):
    path = SCREENSHOT_DIR / f"{ts}-{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)

def main():
    payload = {
        "timestamp_utc": ts,
        "base_url": BASE_URL,
        "headless": HEADLESS,
        "status": "started",
        "screenshots": [],
        "notes": [],
    }

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                PROFILE_PATH,
                headless=HEADLESS,
                viewport={"width": 1600, "height": 1200},
            )
            page = context.new_page()
            page.set_default_timeout(REQUEST_TIMEOUT_MS)

            page.goto(BASE_URL, wait_until="domcontentloaded")
            payload["screenshots"].append(save_shot(page, "01-home"))

            if "login" in page.url.lower() or "auth" in page.url.lower():
                payload["status"] = "failed"
                payload["notes"].append("Profile does not appear to be logged in to ChatGPT.")
                write_log(payload)
                context.close()
                return 1

            # Open account/settings menu if needed.
            # The exact UI can drift, so these fallbacks are intentionally broad.
            menu_opened = False
            menu_selectors = [
                'button[aria-label*="Settings"]',
                'button[aria-label*="Account"]',
                'button[aria-haspopup="menu"]',
            ]
            for sel in menu_selectors:
                try:
                    page.locator(sel).last.click(timeout=5000)
                    menu_opened = True
                    payload["notes"].append(f"Opened menu using selector: {sel}")
                    break
                except Exception:
                    continue

            if not menu_opened:
                # Some UIs expose Settings in the sidebar or user menu text
                try:
                    page.get_by_text("Settings", exact=True).click(timeout=5000)
                    menu_opened = True
                    payload["notes"].append("Opened Settings directly from visible text.")
                except Exception:
                    pass

            payload["screenshots"].append(save_shot(page, "02-menu-or-home"))

            # Try to open Data Controls directly if reachable.
            tried_direct = False
            for path in ("/#settings/DataControls", "/settings/data-controls"):
                try:
                    page.goto(f"{BASE_URL.rstrip('/')}{path}", wait_until="domcontentloaded", timeout=10000)
                    tried_direct = True
                    payload["notes"].append(f"Tried direct navigation: {path}")
                    break
                except Exception:
                    continue

            if not tried_direct:
                payload["notes"].append("Direct navigation paths were not reachable; falling back to visible UI.")

            # Fallback through visible UI.
            text_clicks = [
                ("Settings", True),
                ("Data Controls", False),
            ]
            for label, exact in text_clicks:
                try:
                    page.get_by_text(label, exact=exact).click(timeout=7000)
                    payload["notes"].append(f"Clicked visible text: {label}")
                except Exception:
                    payload["notes"].append(f"Could not click visible text: {label}")

            payload["screenshots"].append(save_shot(page, "03-data-controls"))

            # Final action: click Export Data
            clicked = False
            export_selectors = [
                ('text="Export Data"', "text selector"),
                ('button:has-text("Export Data")', "button selector"),
                ('[role="button"]:has-text("Export Data")', "role button selector"),
            ]
            for sel, label in export_selectors:
                try:
                    page.locator(sel).first.click(timeout=7000)
                    clicked = True
                    payload["notes"].append(f"Clicked Export Data using {label}.")
                    break
                except Exception:
                    continue

            if not clicked:
                try:
                    page.get_by_text("Export Data", exact=True).click(timeout=7000)
                    clicked = True
                    payload["notes"].append("Clicked Export Data using exact visible text.")
                except Exception:
                    pass

            payload["screenshots"].append(save_shot(page, "04-post-click"))

            if not clicked:
                payload["status"] = "failed"
                payload["notes"].append("Could not find or click Export Data.")
                write_log(payload)
                context.close()
                return 2

            payload["status"] = "success"
            payload["notes"].append("Export request click issued.")
            write_log(payload)
            context.close()
            return 0

    except PlaywrightTimeoutError as exc:
        payload["status"] = "failed"
        payload["notes"].append(f"Timeout: {exc}")
        write_log(payload)
        return 3
    except Exception as exc:
        payload["status"] = "failed"
        payload["notes"].append(f"Unhandled exception: {type(exc).__name__}: {exc}")
        write_log(payload)
        return 4

if __name__ == "__main__":
    sys.exit(main())
