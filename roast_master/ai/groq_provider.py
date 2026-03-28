"""Groq provider implementation for Smart Roast Bot v3.

Wraps the synchronous ``groq.Groq`` client and provides automatic
model fallback (70B → 8B) when the primary model fails.
"""

import asyncio
import logging

from groq import Groq

from roast_master.ai.base import AIProvider

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """AI provider backed by the Groq API with internal model fallback.

    When the primary model (default: ``llama-3.3-70b-versatile``) fails,
    the provider automatically retries with the fallback model (default:
    ``llama-3.1-8b-instant``) before giving up.

    Uses ``asyncio.to_thread()`` to run the synchronous Groq client
    without blocking the event loop.
    """

    name: str = "groq"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        fallback_model: str = "llama-3.1-8b-instant",
    ) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model
        self._fallback_model = fallback_model

    async def _call_model(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str | None:
        """Make a single chat completion request against *model*."""
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=model,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content
        return text.strip() if text else None

    async def generate(self, prompt: str, max_tokens: int = 80, temperature: float = 0.95) -> str | None:
        """Generate text from *prompt* via the Groq chat completions API.

        Tries the primary model first; on any failure falls back to the
        secondary model.  Returns ``None`` only when both models fail.
        """
        # --- Primary model ---
        try:
            result = await self._call_model(self._model, prompt, max_tokens, temperature)
            logger.info("Generated response using Groq (%s)", self._model)
            return result
        except Exception as exc:
            logger.warning("Groq primary model (%s) failed: %s", self._model, exc)

        # --- Fallback model ---
        try:
            result = await self._call_model(self._fallback_model, prompt, max_tokens, temperature)
            logger.info("Generated response using Groq fallback (%s)", self._fallback_model)
            return result
        except Exception as exc:
            logger.error("Groq fallback model (%s) also failed: %s", self._fallback_model, exc)
            return None
