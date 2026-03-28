"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class all AI providers must implement."""

    name: str

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> str | None:
        """Generate text from the given prompt.

        Returns generated text, or None on failure.
        """
        ...
