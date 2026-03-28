"""Chat pattern analysis for roast personalization.

Extracts behavioral patterns from a user's message history to give the AI
engine richer context for generating targeted, personalized roasts.
"""

from __future__ import annotations

import re
from datetime import datetime

# Pre-compiled regex for URL detection
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def analyze_chat_patterns(messages: list[dict]) -> dict:
    """Analyze a user's messages for behavioral patterns.

    Takes messages as dicts (each with ``"content"``, ``"channel_id"``, and
    ``"created_at"`` keys — sourced from the database) and returns a dict of
    detected patterns with boolean flags plus basic stats.

    Detected patterns
    -----------------
    *Existing* (ported from ``ai_engine.py``):
        emoji_heavy, repetitive, one_word_warrior, caps_lock_fan, question_asker

    *New*:
        late_night_poster, burst_sender, link_sharer

    Args:
        messages: List of message dicts.  Each dict is expected to contain at
            least a ``"content"`` key.  ``"created_at"`` is used for
            time-based detections and ``"channel_id"`` is reserved for
            future use.

    Returns:
        A dict containing boolean pattern flags and basic numeric stats
        (``message_count``, ``avg_length``, ``total_chars``).
    """
    if not messages:
        return {
            "message_count": 0,
            "avg_length": 0,
            "total_chars": 0,
            "emoji_heavy": False,
            "repetitive": False,
            "one_word_warrior": False,
            "caps_lock_fan": False,
            "question_asker": False,
            "late_night_poster": False,
            "burst_sender": False,
            "link_sharer": False,
        }

    contents: list[str] = [m.get("content", "") for m in messages]
    count = len(contents)

    # --- Basic stats ---
    total_chars = sum(len(c) for c in contents)
    avg_length = total_chars / count

    analysis: dict = {
        "message_count": count,
        "avg_length": avg_length,
        "total_chars": total_chars,
    }

    # --- Existing detections (preserved from ai_engine.py) ---

    # Emoji usage — characters above the common emoji Unicode range
    combined_text = " ".join(contents).lower()
    emoji_count = sum(1 for char in combined_text if ord(char) > 127000)
    analysis["emoji_heavy"] = emoji_count > count * 2

    # Repetitive messages
    unique_ratio = len(set(contents)) / count
    analysis["repetitive"] = unique_ratio < 0.3

    # Short / one-word messages
    analysis["one_word_warrior"] = avg_length < 10

    # ALL-CAPS messages (only count messages longer than 3 chars)
    caps_count = sum(1 for c in contents if c.isupper() and len(c) > 3)
    analysis["caps_lock_fan"] = caps_count > count * 0.3

    # Question marks
    question_count = sum(c.count("?") for c in contents)
    analysis["question_asker"] = question_count > count * 0.5

    # --- New detections ---

    # Late-night posting (midnight–5 AM)
    analysis["late_night_poster"] = _detect_late_night(messages)

    # Burst sending (5+ messages within 2 minutes)
    analysis["burst_sender"] = _detect_bursts(messages)

    # Link / URL sharing frequency
    link_count = sum(len(_URL_PATTERN.findall(c)) for c in contents)
    analysis["link_sharer"] = link_count > count * 0.3

    return analysis


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(raw: str) -> datetime | None:
    """Best-effort ISO-8601 timestamp parse. Returns *None* on failure."""
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def _detect_late_night(messages: list[dict]) -> bool:
    """Return *True* if >25 % of messages were sent between midnight and 5 AM."""
    late_count = 0
    parsed_count = 0
    for m in messages:
        ts = _parse_timestamp(m.get("created_at", ""))
        if ts is None:
            continue
        parsed_count += 1
        if 0 <= ts.hour < 5:
            late_count += 1

    if parsed_count == 0:
        return False
    return late_count > parsed_count * 0.25


def _detect_bursts(messages: list[dict]) -> bool:
    """Return *True* if there is any window of 5+ messages within 2 minutes."""
    timestamps: list[datetime] = []
    for m in messages:
        ts = _parse_timestamp(m.get("created_at", ""))
        if ts is not None:
            timestamps.append(ts)

    if len(timestamps) < 5:
        return False

    timestamps.sort()

    # Sliding window: check if any 5 consecutive messages fit in 2 minutes
    for i in range(len(timestamps) - 4):
        delta = (timestamps[i + 4] - timestamps[i]).total_seconds()
        if delta <= 120:
            return True

    return False
