"""Application configuration loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the NotesApp backend.

    All values are loaded from a `.env` file located in the backend root
    directory or from real environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notesapp"

    # --- Auth (Passkey/WebAuthn) ---
    JWT_SECRET: str = "change-me-in-production-use-64-char-random-string"
    JWT_EXPIRY_DAYS: int = 7
    WEBAUTHN_RP_ID: str = "localhost"
    WEBAUTHN_RP_NAME: str = "NotesApp"
    WEBAUTHN_ORIGIN: str = "http://localhost:3000"

    # --- Telegram (optional) ---
    TELEGRAM_BOT_TOKEN: str | None = None

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Rate Limiting ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"  # Default for authenticated endpoints
    RATE_LIMIT_AUTH: str = "5/minute"  # Stricter for auth endpoints (login, signup)
    RATE_LIMIT_WEBHOOK: str = "30/minute"  # For telegram webhook

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list, split on commas."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()


def get_settings() -> Settings:
    """Return the global settings instance."""
    return settings
