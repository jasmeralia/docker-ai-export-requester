from unittest.mock import MagicMock, patch

import bootstrap_claude_profile


def test_bootstrap_claude_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bootstrap_claude_profile.settings, "claude_base_url", "https://claude.test")
    monkeypatch.setattr(
        bootstrap_claude_profile.settings, "claude_profile_path", str(tmp_path / "profile")
    )
    monkeypatch.setattr(
        bootstrap_claude_profile.settings, "screenshot_dir", str(tmp_path / "shots")
    )
    manager = MagicMock()
    playwright = manager.__enter__.return_value
    context = playwright.chromium.launch_persistent_context.return_value
    page = context.new_page.return_value

    with patch.object(bootstrap_claude_profile, "sync_playwright", return_value=manager):
        result = bootstrap_claude_profile.main()

    assert result == 0
    page.wait_for_timeout.assert_called_once_with(60000 * 30)
    page.screenshot.assert_called_once_with(
        path=str(tmp_path / "shots" / "claude-bootstrap-opened.png"), full_page=True
    )
    context.close.assert_called_once_with()
