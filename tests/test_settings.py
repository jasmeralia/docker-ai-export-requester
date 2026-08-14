from scripts.settings import Settings


def test_default_settings() -> None:
    config = Settings(_env_file=None)

    assert config.chatgpt_base_url == "https://chatgpt.com"
    assert config.claude_base_url == "https://claude.ai"
    assert config.headless is True


def test_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setenv("REQUEST_TIMEOUT_MS", "1234")

    config = Settings(_env_file=None)

    assert config.headless is False
    assert config.request_timeout_ms == 1234
