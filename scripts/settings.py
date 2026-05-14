from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "/app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude
    claude_base_url: str = "https://claude.ai"
    claude_profile_path: str = "/app/claude-profile"

    # ChatGPT
    chatgpt_base_url: str = "https://chatgpt.com"
    chatgpt_profile_path: str = "/app/profile"

    # Shared
    log_dir: str = "/app/logs"
    screenshot_dir: str = "/app/screenshots"
    headless: bool = True
    request_timeout_ms: int = 30000


settings = Settings()
