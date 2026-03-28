"""Centralized configuration loader.

Loads config with priority: environment variables → .env file → data/config.json.
Validates required fields at startup and provides sensible defaults.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file if present (does not override existing env vars)
load_dotenv()

_DEFAULT_CONFIG_PATH = Path("data/config.json")


def _load_json_config(path: Path) -> dict:
    """Load legacy JSON config file, returning empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return {}


def _get(key: str, json_cfg: dict, default: object = None) -> object:
    """Resolve a config value: env var → JSON fallback → default."""
    return os.environ.get(key) or json_cfg.get(key) or default


@dataclass
class Config:
    """Bot configuration with env → .env → JSON loading and validation."""

    # Required
    discord_token: str = ""

    # API keys (optional — at least one AI provider key recommended)
    openai_api_key: str | None = None
    groq_api_key: str | None = None

    # AI settings
    ai_providers: list[str] = field(default_factory=lambda: ["openai", "groq"])
    openai_model: str = "gpt-4o-mini"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"

    # Bot settings
    command_prefix: str = "!"
    roast_cooldown: int = 30
    max_messages_per_user: int = 500
    max_index_days: int = 365

    # Scheduler
    scheduled_roast_enabled: bool = False
    scheduled_roast_channel_id: int | None = None
    scheduled_roast_cron: str = "0 12 * * *"

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, config_path: Path | str = _DEFAULT_CONFIG_PATH) -> Config:
        """Load configuration from env vars, .env, and JSON fallback.

        Raises:
            SystemExit: If ``discord_token`` is missing after all sources
                are checked.
        """
        json_cfg = _load_json_config(Path(config_path))

        # Parse ai_providers from env (comma-separated) or JSON
        raw_providers = _get("AI_PROVIDERS", json_cfg)
        if isinstance(raw_providers, str):
            providers = [p.strip() for p in raw_providers.split(",") if p.strip()]
        elif isinstance(raw_providers, list):
            providers = raw_providers
        else:
            providers = ["openai", "groq"]

        # Parse scheduled_roast_channel_id
        raw_channel = _get("SCHEDULED_ROAST_CHANNEL_ID", json_cfg)
        channel_id = int(raw_channel) if raw_channel else None

        config = cls(
            discord_token=str(_get("DISCORD_TOKEN", json_cfg, "") or ""),
            openai_api_key=_get("OPENAI_API_KEY", json_cfg) or None,
            groq_api_key=_get("GROQ_API_KEY", json_cfg) or None,
            ai_providers=providers,
            openai_model=str(_get("OPENAI_MODEL", json_cfg, "gpt-4o-mini")),
            groq_model=str(_get("GROQ_MODEL", json_cfg, "llama-3.3-70b-versatile")),
            groq_fallback_model=str(
                _get("GROQ_FALLBACK_MODEL", json_cfg, "llama-3.1-8b-instant")
            ),
            command_prefix=str(_get("COMMAND_PREFIX", json_cfg, "!")),
            roast_cooldown=int(_get("ROAST_COOLDOWN", json_cfg, 30)),
            max_messages_per_user=int(
                _get("MAX_MESSAGES_PER_USER", json_cfg, 500)
            ),
            max_index_days=int(_get("MAX_INDEX_DAYS", json_cfg, 365)),
            scheduled_roast_enabled=str(
                _get("SCHEDULED_ROAST_ENABLED", json_cfg, "false")
            ).lower() in ("true", "1", "yes"),
            scheduled_roast_channel_id=channel_id,
            scheduled_roast_cron=str(
                _get("SCHEDULED_ROAST_CRON", json_cfg, "0 12 * * *")
            ),
        )

        config.validate()
        return config

    def validate(self) -> None:
        """Validate required configuration values. Fail fast on errors."""
        if not self.discord_token:
            raise SystemExit(
                "DISCORD_TOKEN is required. Set it via environment variable, "
                ".env file, or data/config.json."
            )
        logger.info("Configuration loaded and validated successfully.")
