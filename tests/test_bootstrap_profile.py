from unittest.mock import MagicMock, patch

import bootstrap_profile


def test_bootstrap_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bootstrap_profile.settings, "chatgpt_base_url", "https://chatgpt.test")
    monkeypatch.setattr(
        bootstrap_profile.settings, "chatgpt_profile_path", str(tmp_path / "profile")
    )
    monkeypatch.setattr(bootstrap_profile.settings, "screenshot_dir", str(tmp_path / "shots"))
    manager = MagicMock()
    playwright = manager.__enter__.return_value
    context = playwright.chromium.launch_persistent_context.return_value
    page = context.new_page.return_value

    with patch.object(bootstrap_profile, "sync_playwright", return_value=manager):
        result = bootstrap_profile.main()

    assert result == 0
    page.wait_for_timeout.assert_called_once_with(60000 * 30)
    page.screenshot.assert_called_once_with(
        path=str(tmp_path / "shots" / "bootstrap-opened.png"), full_page=True
    )
    context.close.assert_called_once_with()
