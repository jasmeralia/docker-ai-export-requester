import json
from unittest.mock import MagicMock, patch

import request_claude_export


def configure_settings(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(request_claude_export.settings, "claude_base_url", "https://claude.test")
    monkeypatch.setattr(
        request_claude_export.settings, "claude_profile_path", str(tmp_path / "profile")
    )
    monkeypatch.setattr(request_claude_export.settings, "log_dir", str(tmp_path))
    monkeypatch.setattr(request_claude_export.settings, "screenshot_dir", str(tmp_path / "shots"))
    monkeypatch.setattr(request_claude_export.settings, "headless", True)
    monkeypatch.setattr(request_claude_export.settings, "request_timeout_ms", 4321)


def browser_mocks(page: MagicMock) -> tuple[MagicMock, MagicMock]:
    manager = MagicMock()
    playwright = manager.__enter__.return_value
    context = playwright.chromium.launch_persistent_context.return_value
    context.new_page.return_value = page
    return manager, context


def read_payload(tmp_path) -> dict:
    run_logs = list(tmp_path.glob("claude-export-request-*.json"))
    assert len(run_logs) == 1
    return json.loads(run_logs[0].read_text(encoding="utf-8"))


def test_happy_path(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://claude.test/"
    manager, context = browser_mocks(page)

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 0
    assert payload["status"] == "success"
    assert len(payload["screenshots"]) == 4
    assert all(path.startswith(str(tmp_path / "shots")) for path in payload["screenshots"])
    context.close.assert_called_once_with()
    page.set_default_timeout.assert_called_once_with(4321)
    assert page.screenshot.call_count == 4


def test_login_redirect(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://claude.test/login"
    manager, context = browser_mocks(page)

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 1
    assert payload["status"] == "failed"
    assert payload["notes"] == ["Profile does not appear to be logged in to Claude."]
    assert len(payload["screenshots"]) == 1
    page.locator.assert_not_called()
    page.get_by_text.assert_not_called()
    context.close.assert_called_once_with()


def test_export_button_never_found(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://claude.test/"
    export_text = {"Export Data", "Export", "Request export", "Request Export"}

    def locator(selector: str) -> MagicMock:
        element = MagicMock()
        if "Export" in selector or "export" in selector:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    def get_by_text(text: str, *, exact: bool) -> MagicMock:
        element = MagicMock()
        if text in export_text and exact:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    page.locator.side_effect = locator
    page.get_by_text.side_effect = get_by_text
    manager, context = browser_mocks(page)

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 2
    assert payload["status"] == "failed"
    assert payload["notes"][-1] == "Could not find or click export button."
    assert len(payload["screenshots"]) == 4
    context.close.assert_called_once_with()


def test_playwright_timeout(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    manager, _ = browser_mocks(page)
    playwright = manager.__enter__.return_value
    playwright.chromium.launch_persistent_context.side_effect = (
        request_claude_export.PlaywrightTimeoutError("browser timed out")
    )

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 3
    assert payload["status"] == "failed"
    assert "Timeout" in payload["notes"][0]


def test_generic_exception(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    manager, _ = browser_mocks(page)
    playwright = manager.__enter__.return_value
    playwright.chromium.launch_persistent_context.side_effect = OSError("broken browser")

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 4
    assert payload["status"] == "failed"
    assert "OSError" in payload["notes"][0]


def test_selector_fallbacks(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://claude.test/"
    settings_selectors = {
        'button[aria-label*="Settings"]',
        'button[aria-label*="User menu"]',
        'button[aria-label*="Profile"]',
        'button[aria-label*="Account"]',
        'a[href*="/settings"]',
    }
    export_selectors = {
        'text="Export Data"',
        'button:has-text("Export Data")',
        '[role="button"]:has-text("Export Data")',
        'text="Export"',
        'button:has-text("Export")',
        'text="Request export"',
        'button:has-text("Request export")',
        'text="Request Export"',
        'button:has-text("Request Export")',
    }

    def locator(selector: str) -> MagicMock:
        element = MagicMock()
        if selector in settings_selectors:
            element.last.click.side_effect = RuntimeError("missing")
        if selector in export_selectors:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    def get_by_text(text: str, *, exact: bool) -> MagicMock:
        element = MagicMock()
        if text in {"Settings", "Account", "Export Data", "Confirm"} and exact:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    page.locator.side_effect = locator
    page.get_by_text.side_effect = get_by_text
    page.goto.side_effect = [None, RuntimeError("missing"), None]
    manager, _ = browser_mocks(page)

    with patch.object(request_claude_export, "sync_playwright", return_value=manager):
        result = request_claude_export.main()

    payload = read_payload(tmp_path)
    assert result == 0
    assert payload["status"] == "success"
    assert "Opened user menu via data-testid." in payload["notes"]
    assert "Navigated directly to: /settings/account" in payload["notes"]
    assert "Clicked export using exact visible text: Export" in payload["notes"]
    assert "Clicked confirmation: Yes" in payload["notes"]
