#!/usr/bin/env python3
"""Smart Roast Bot v3 — async entry point.

Loads configuration, initialises logging and the database, auto-migrates
legacy JSON data, builds the AI provider chain, and starts the Discord bot.
"""

from __future__ import annotations

import asyncio
import logging
import os

from roast_master.ai.base import AIProvider
from roast_master.ai.engine import AIEngine
from roast_master.ai.groq_provider import GroqProvider
from roast_master.ai.openai_provider import OpenAIProvider
from roast_master.bot import create_bot
from roast_master.config import Config
from roast_master.database import Database
from roast_master.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def build_providers(config: Config) -> list[AIProvider]:
    """Build an ordered list of AI providers from *config*.

    Iterates through ``config.ai_providers`` and instantiates each provider
    whose API key is present.  Logs which providers were configured and warns
    if the resulting list is empty.
    """
    providers: list[AIProvider] = []

    for name in config.ai_providers:
        if name == "openai" and config.openai_api_key:
            providers.append(OpenAIProvider(api_key=config.openai_api_key, model=config.openai_model))
            logger.info("Configured AI provider: OpenAI (%s)", config.openai_model)
        elif name == "groq" and config.groq_api_key:
            providers.append(
                GroqProvider(
                    api_key=config.groq_api_key,
                    model=config.groq_model,
                    fallback_model=config.groq_fallback_model,
                )
            )
            logger.info("Configured AI provider: Groq (%s)", config.groq_model)
        else:
            logger.debug("Skipping provider '%s' — no API key set.", name)

    if not providers:
        logger.warning("No AI providers configured. Roast generation will use fallback messages.")

    return providers


async def main() -> None:
    """Async entry point — wire everything up and start the bot."""
    config = Config.load()
    setup_logging()

    db = Database("data/roastbot.db")
    await db.init()

    try:
        # Auto-migrate from legacy JSON if the file exists
        if os.path.exists("data/messages.json"):
            count = await db.migrate_from_json("data/messages.json")
            logger.info("Migrated %d messages from JSON", count)

        # Build AI provider chain from config
        providers = build_providers(config)
        engine = AIEngine(providers, db)

        # Create and run bot
        bot = create_bot(config, db, engine)
        await bot.start(config.discord_token)
    finally:
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
