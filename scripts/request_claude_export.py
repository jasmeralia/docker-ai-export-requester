import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import (
    Page,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from settings import settings

BASE_URL = settings.claude_base_url
PROFILE_PATH = settings.claude_profile_path
LOG_DIR = Path(settings.log_dir)
SCREENSHOT_DIR = Path(settings.screenshot_dir)
HEADLESS = settings.headless
REQUEST_TIMEOUT_MS = settings.request_timeout_ms

LOG_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
run_log = LOG_DIR / f"claude-export-request-{ts}.json"


class RunPayload(TypedDict):
    timestamp_utc: str
    base_url: str
    headless: bool
    status: str
    screenshots: list[str]
    notes: list[str]


def write_log(payload: RunPayload) -> None:
    run_log.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_shot(page: Page, name: str) -> str:
    path = SCREENSHOT_DIR / f"{ts}-claude-{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def main() -> int:
    payload: RunPayload = {
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
                payload["notes"].append("Profile does not appear to be logged in to Claude.")
                write_log(payload)
                context.close()
                return 1

            # Navigate to Settings.
            # Claude's UI typically has a user/profile menu or a direct Settings link.
            settings_opened = False
            settings_selectors = [
                'button[aria-label*="Settings"]',
                'button[aria-label*="User menu"]',
                'button[aria-label*="Profile"]',
                'button[aria-label*="Account"]',
                'a[href*="/settings"]',
            ]
            for sel in settings_selectors:
                try:
                    page.locator(sel).last.click(timeout=5000)
                    settings_opened = True
                    payload["notes"].append(f"Opened settings using selector: {sel}")
                    break
                except Exception:
                    continue

            if not settings_opened:
                # Try clicking visible text links
                for label in ("Settings", "Account"):
                    try:
                        page.get_by_text(label, exact=True).first.click(timeout=5000)
                        settings_opened = True
                        payload["notes"].append(f"Opened settings using visible text: {label}")
                        break
                    except Exception:
                        continue

            if not settings_opened:
                # Try the initials avatar button (common Claude UI pattern)
                try:
                    page.locator('button[data-testid="user-menu-button"]').click(timeout=5000)
                    settings_opened = True
                    payload["notes"].append("Opened user menu via data-testid.")
                except Exception:
                    payload["notes"].append("Could not open settings or user menu.")

            payload["screenshots"].append(save_shot(page, "02-menu-or-settings"))

            # Try direct navigation to settings page.
            tried_direct = False
            for path in ("/settings", "/settings/account"):
                try:
                    page.goto(
                        f"{BASE_URL.rstrip('/')}{path}",
                        wait_until="domcontentloaded",
                        timeout=10000,
                    )
                    tried_direct = True
                    payload["notes"].append(f"Navigated directly to: {path}")
                    break
                except Exception:
                    continue

            if not tried_direct:
                payload["notes"].append(
                    "Direct navigation paths were not reachable; falling back to visible UI."
                )

            # If a menu opened, try clicking through to Settings/Account
            for label in ("Settings", "Account"):
                try:
                    page.get_by_text(label, exact=True).first.click(timeout=5000)
                    payload["notes"].append(f"Clicked visible text: {label}")
                except Exception:
                    pass

            payload["screenshots"].append(save_shot(page, "03-settings"))

            # Final action: click Export Data (or similar)
            clicked = False
            export_selectors = [
                ('text="Export Data"', "text selector"),
                ('button:has-text("Export Data")', "button selector"),
                ('[role="button"]:has-text("Export Data")', "role button selector"),
                ('text="Export"', "short text selector"),
                ('button:has-text("Export")', "short button selector"),
                ('text="Request export"', "request export text"),
                ('button:has-text("Request export")', "request export button"),
                ('text="Request Export"', "request Export text"),
                ('button:has-text("Request Export")', "request Export button"),
            ]
            for sel, label in export_selectors:
                try:
                    page.locator(sel).first.click(timeout=7000)
                    clicked = True
                    payload["notes"].append(f"Clicked export using {label}.")
                    break
                except Exception:
                    continue

            if not clicked:
                for text in ("Export Data", "Export", "Request export", "Request Export"):
                    try:
                        page.get_by_text(text, exact=True).first.click(timeout=5000)
                        clicked = True
                        payload["notes"].append(
                            f"Clicked export using exact visible text: {text}"
                        )
                        break
                    except Exception:
                        continue

            # Some export flows show a confirmation dialog
            if clicked:
                for confirm_text in ("Confirm", "Yes", "Request"):
                    try:
                        page.get_by_text(confirm_text, exact=True).first.click(timeout=5000)
                        payload["notes"].append(f"Clicked confirmation: {confirm_text}")
                        break
                    except Exception:
                        continue

            payload["screenshots"].append(save_shot(page, "04-post-click"))

            if not clicked:
                payload["status"] = "failed"
                payload["notes"].append("Could not find or click export button.")
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
