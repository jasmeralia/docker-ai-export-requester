import json
from unittest.mock import MagicMock, patch

import request_export


def configure_settings(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(request_export.settings, "chatgpt_base_url", "https://chatgpt.test")
    monkeypatch.setattr(request_export.settings, "chatgpt_profile_path", str(tmp_path / "profile"))
    monkeypatch.setattr(request_export.settings, "log_dir", str(tmp_path))
    monkeypatch.setattr(request_export.settings, "screenshot_dir", str(tmp_path / "shots"))
    monkeypatch.setattr(request_export.settings, "headless", True)
    monkeypatch.setattr(request_export.settings, "request_timeout_ms", 1234)


def browser_mocks(page: MagicMock) -> tuple[MagicMock, MagicMock]:
    manager = MagicMock()
    playwright = manager.__enter__.return_value
    context = playwright.chromium.launch_persistent_context.return_value
    context.new_page.return_value = page
    return manager, context


def read_payload(tmp_path) -> dict:
    run_logs = list(tmp_path.glob("export-request-*.json"))
    assert len(run_logs) == 1
    return json.loads(run_logs[0].read_text(encoding="utf-8"))


def test_happy_path(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://chatgpt.test/"
    manager, context = browser_mocks(page)

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 0
    assert payload["status"] == "success"
    assert len(payload["screenshots"]) == 4
    assert all(path.startswith(str(tmp_path / "shots")) for path in payload["screenshots"])
    context.close.assert_called_once_with()
    page.set_default_timeout.assert_called_once_with(1234)
    assert page.screenshot.call_count == 4


def test_login_redirect(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://chatgpt.test/auth/login"
    manager, context = browser_mocks(page)

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 1
    assert payload["status"] == "failed"
    assert payload["notes"] == ["Profile does not appear to be logged in to ChatGPT."]
    assert len(payload["screenshots"]) == 1
    page.locator.assert_not_called()
    page.get_by_text.assert_not_called()
    context.close.assert_called_once_with()


def test_export_button_never_found(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://chatgpt.test/"

    def locator(selector: str) -> MagicMock:
        element = MagicMock()
        if "Export Data" in selector:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    def get_by_text(text: str, *, exact: bool) -> MagicMock:
        element = MagicMock()
        if text == "Export Data" and exact:
            element.click.side_effect = RuntimeError("missing")
        return element

    page.locator.side_effect = locator
    page.get_by_text.side_effect = get_by_text
    manager, context = browser_mocks(page)

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 2
    assert payload["status"] == "failed"
    assert payload["notes"][-1] == "Could not find or click Export Data."
    assert len(payload["screenshots"]) == 4
    context.close.assert_called_once_with()


def test_playwright_timeout(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    manager, _ = browser_mocks(page)
    playwright = manager.__enter__.return_value
    playwright.chromium.launch_persistent_context.side_effect = (
        request_export.PlaywrightTimeoutError("browser timed out")
    )

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 3
    assert payload["status"] == "failed"
    assert "Timeout" in payload["notes"][0]


def test_generic_exception(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    manager, _ = browser_mocks(page)
    playwright = manager.__enter__.return_value
    playwright.chromium.launch_persistent_context.side_effect = ValueError("broken browser")

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 4
    assert payload["status"] == "failed"
    assert "ValueError" in payload["notes"][0]


def test_selector_fallbacks(monkeypatch, tmp_path) -> None:
    configure_settings(monkeypatch, tmp_path)
    page = MagicMock()
    page.url = "https://chatgpt.test/"
    menu_selectors = {
        'button[aria-label*="Settings"]',
        'button[aria-label*="Account"]',
        'button[aria-haspopup="menu"]',
    }

    def locator(selector: str) -> MagicMock:
        element = MagicMock()
        if selector in menu_selectors:
            element.last.click.side_effect = RuntimeError("missing")
        if "Export Data" in selector:
            element.first.click.side_effect = RuntimeError("missing")
        return element

    page.locator.side_effect = locator
    page.goto.side_effect = [None, RuntimeError("missing"), RuntimeError("missing")]
    manager, _ = browser_mocks(page)

    with patch.object(request_export, "sync_playwright", return_value=manager):
        result = request_export.main()

    payload = read_payload(tmp_path)
    assert result == 0
    assert payload["status"] == "success"
    assert "Opened Settings directly from visible text." in payload["notes"]
    assert (
        "Direct navigation paths were not reachable; falling back to visible UI."
        in payload["notes"]
    )
    assert "Clicked Export Data using exact visible text." in payload["notes"]
