"""AI provider package for Smart Roast Bot v3."""

from roast_master.ai.base import AIProvider
from roast_master.ai.analyzer import analyze_chat_patterns
from roast_master.ai.prompts import (
    ROAST_STYLES,
    COMPLIMENT_PROMPT,
    RECEIPTS_PROMPT,
    build_roast_prompt,
    build_compliment_prompt,
)

__all__ = [
    "AIProvider",
    "analyze_chat_patterns",
    "ROAST_STYLES",
    "COMPLIMENT_PROMPT",
    "RECEIPTS_PROMPT",
    "build_roast_prompt",
    "build_compliment_prompt",
]
