"""AI Engine — manages provider chain and roast/compliment generation.

Orchestrates the full generation pipeline: message fetching, pattern analysis,
prompt building, provider iteration with fallback, history dedup, and logging.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from roast_master.ai.analyzer import analyze_chat_patterns
from roast_master.ai.prompts import build_compliment_prompt, build_roast_prompt

if TYPE_CHECKING:
    from roast_master.ai.base import AIProvider
    from roast_master.database import Database

logger = logging.getLogger(__name__)

# Fallback messages when every provider fails
_ROAST_FALLBACK = (
    "Both roast engines are taking a break. "
    "Even they need rest after dealing with you people."
)
_COMPLIMENT_FALLBACK = (
    "I wanted to say something nice, but the AI is speechless right now. "
    "That probably says more about you than it does about the AI."
)

# Ghost/lurker prompt used when a user has zero indexed messages
_GHOST_ROAST_STYLE = (
    "You are DankRoastMaster 3000 – a savage AI comedian.\n\n"
    "Target: {user_name}\n"
    "Status: GHOST MODE — They've been lurking without saying a word.\n\n"
    "Write a SHORT (1-2 sentences max), hilarious roast about them being "
    "a silent lurker/ghost in the chat. Make it punchy and funny. "
    "No need to explain they have no history — just roast the silence itself."
)
_GHOST_COMPLIMENT = (
    "You are a genuinely kind AI.\n\n"
    "Target: {user_name}\n"
    "Status: They haven't said much yet, but that's okay.\n\n"
    "Write a SHORT (1-2 sentences max), warm compliment encouraging them "
    "to participate more. Be sincere and welcoming."
)


class AIEngine:
    """Manages the AI provider chain and generation pipeline.

    The engine fetches user messages from the database, analyses chat patterns,
    builds a prompt (roast or compliment), iterates through providers until one
    succeeds, logs the result, and returns the generated text with the provider
    name.
    """

    def __init__(self, providers: list[AIProvider], db: Database) -> None:
        self.providers = providers
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_roast(
        self,
        user_name: str,
        user_id: str,
        guild_id: str,
        style: str = "savage",
        embarrassing: list[str] | None = None,
    ) -> tuple[str, str]:
        """Generate a personalised roast for *user_name*.

        Returns:
            A ``(roast_text, provider_name)`` tuple.  If every provider fails
            a static fallback message is returned with ``"fallback"`` as the
            provider name.
        """
        messages = await self.db.get_user_messages(user_id, guild_id)

        # --- Ghost / lurker path ---
        if not messages:
            logger.info("No messages for user %s — using ghost prompt.", user_id)
            prompt = _GHOST_ROAST_STYLE.format(user_name=user_name)
            return await self._generate_with_providers(
                prompt=prompt,
                user_id=user_id,
                guild_id=guild_id,
                style=style,
                fallback=_ROAST_FALLBACK,
            )

        # --- Normal path ---
        patterns = analyze_chat_patterns(messages)
        sample_texts = self._sample_message_texts(messages)
        previous_roasts = await self._get_previous_roast_texts(user_id, guild_id)

        prompt = build_roast_prompt(
            style=style,
            user_name=user_name,
            patterns=patterns,
            messages=sample_texts,
            previous_roasts=previous_roasts,
            embarrassing=embarrassing,
        )

        return await self._generate_with_providers(
            prompt=prompt,
            user_id=user_id,
            guild_id=guild_id,
            style=style,
            fallback=_ROAST_FALLBACK,
        )

    async def generate_compliment(
        self,
        user_name: str,
        user_id: str,
        guild_id: str,
    ) -> tuple[str, str]:
        """Generate a genuine compliment for *user_name*.

        Returns:
            A ``(compliment_text, provider_name)`` tuple.
        """
        messages = await self.db.get_user_messages(user_id, guild_id)

        # --- Ghost / lurker path ---
        if not messages:
            logger.info("No messages for user %s — using ghost compliment.", user_id)
            prompt = _GHOST_COMPLIMENT.format(user_name=user_name)
            return await self._generate_with_providers(
                prompt=prompt,
                user_id=user_id,
                guild_id=guild_id,
                style="compliment",
                fallback=_COMPLIMENT_FALLBACK,
            )

        # --- Normal path ---
        patterns = analyze_chat_patterns(messages)
        sample_texts = self._sample_message_texts(messages)

        prompt = build_compliment_prompt(
            user_name=user_name,
            patterns=patterns,
            messages=sample_texts,
        )

        return await self._generate_with_providers(
            prompt=prompt,
            user_id=user_id,
            guild_id=guild_id,
            style="compliment",
            fallback=_COMPLIMENT_FALLBACK,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _generate_with_providers(
        self,
        prompt: str,
        user_id: str,
        guild_id: str,
        style: str,
        fallback: str,
    ) -> tuple[str, str]:
        """Iterate through providers until one returns a result.

        On success the roast/compliment is logged to ``roast_history`` via the
        database.  If every provider returns ``None`` or raises, the *fallback*
        string is returned with ``"fallback"`` as the provider name.
        """
        for provider in self.providers:
            try:
                logger.debug("Trying provider %s …", provider.name)
                result = await provider.generate(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=1.0,
                )
                if result is not None:
                    logger.info("Generated text via %s.", provider.name)
                    await self.db.add_roast(
                        target_id=user_id,
                        roaster_id="bot",
                        guild_id=guild_id,
                        text=result,
                        style=style,
                        provider=provider.name,
                    )
                    return result, provider.name
                logger.warning("Provider %s returned None.", provider.name)
            except Exception:
                logger.exception("Provider %s failed.", provider.name)

        logger.error("All providers failed for user %s — returning fallback.", user_id)
        return fallback, "fallback"

    async def _get_previous_roast_texts(
        self, user_id: str, guild_id: str
    ) -> list[str]:
        """Fetch recent roast texts for dedup context."""
        rows = await self.db.get_recent_roasts(user_id, guild_id)
        return [r["roast_text"] for r in rows]

    @staticmethod
    def _sample_message_texts(messages: list[dict], max_total: int = 50) -> list[str]:
        """Return a mixed sample of message content strings.

        Weights recent messages higher while still including older context.
        """
        contents = [m.get("content", "") for m in messages if m.get("content")]
        if len(contents) <= max_total:
            return contents

        recent = contents[:20]  # messages are ordered DESC from DB
        older = contents[20:]
        sample_size = min(max_total - len(recent), len(older))
        older_sample = random.sample(older, sample_size) if older else []
        return older_sample + recent
