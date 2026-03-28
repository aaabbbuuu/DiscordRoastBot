"""OpenAI provider implementation for Smart Roast Bot v3."""

import asyncio
import logging

from openai import APIError, OpenAI, RateLimitError

from roast_master.ai.base import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """AI provider backed by the OpenAI API.

    Uses ``asyncio.to_thread()`` to run the synchronous OpenAI client
    without blocking the event loop.
    """

    name: str = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    async def generate(self, prompt: str, max_tokens: int = 80, temperature: float = 0.95) -> str | None:
        """Generate text from *prompt* via the OpenAI chat completions API.

        Returns the generated string, or ``None`` when the request fails.
        """
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content
            logger.info("Generated response using OpenAI (%s)", self._model)
            return text.strip() if text else None
        except RateLimitError as exc:
            logger.warning("OpenAI rate-limited: %s", exc)
            return None
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            return None
        except Exception as exc:
            logger.error("Unexpected OpenAI error: %s", exc)
            return None
