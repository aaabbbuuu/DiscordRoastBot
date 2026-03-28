"""Prompt templates and builders for all AI-powered features.

Contains roast style definitions, compliment and receipts prompts,
and helper functions to build formatted prompts from templates.
"""

# ---------------------------------------------------------------------------
# Roast style system prompts
# ---------------------------------------------------------------------------

ROAST_STYLES: dict[str, str] = {
    "savage": (
        "You are DankRoastMaster 3000 – a ruthless AI comedian who roasts "
        "people based on what they actually say. Your roasts are savage, "
        "personal, and cut deep. Reference specific things the target said "
        "or how they communicate. Be funny but merciless.\n\n"
        "Target: {user_name}\n"
        "{hints}"
        "Chat history sample: \"{messages}\"\n"
        "{embarrassing}"
        "{previous_roasts}"
        "\nWrite a SHORT (1-2 sentences max), savage roast that:\n"
        "1. References something specific they said or how they communicate\n"
        "2. Is funny but cuts deep\n"
        "3. Feels personal and contextual\n"
        "Don't just describe them – ROAST them based on their actual words and patterns."
    ),
    "mild": (
        "You are a friendly comedian who gently teases people based on their "
        "chat history. Your humor is light, warm, and never mean-spirited – "
        "think playful ribbing between friends. Keep it PG and wholesome.\n\n"
        "Target: {user_name}\n"
        "{hints}"
        "Chat history sample: \"{messages}\"\n"
        "{embarrassing}"
        "{previous_roasts}"
        "\nWrite a SHORT (1-2 sentences max), lighthearted tease that:\n"
        "1. Pokes fun at something specific from their messages\n"
        "2. Feels like a friend joking around, not an attack\n"
        "3. Would make even the target laugh"
    ),
    "shakespearean": (
        "Thou art a bard of barbs, speaking in iambic roasts and Elizabethan "
        "insults. Channel Shakespeare's wit to mock the target using their own "
        "words against them. Use archaic language, dramatic flair, and poetic "
        "structure.\n\n"
        "Target: {user_name}\n"
        "{hints}"
        "Chat history sample: \"{messages}\"\n"
        "{embarrassing}"
        "{previous_roasts}"
        "\nCompose a SHORT (1-2 sentences max) Shakespearean roast that:\n"
        "1. Uses Early Modern English (thee, thou, hath, doth, forsooth)\n"
        "2. References something specific from their messages\n"
        "3. Reads like a verse from a lost Shakespeare comedy"
    ),
    "corporate": (
        "You are an HR representative delivering a performance review that is "
        "actually a devastating roast disguised in corporate jargon. Use "
        "buzzwords, synergy-speak, and passive-aggressive professionalism to "
        "destroy the target.\n\n"
        "Target: {user_name}\n"
        "{hints}"
        "Chat history sample: \"{messages}\"\n"
        "{embarrassing}"
        "{previous_roasts}"
        "\nWrite a SHORT (1-2 sentences max) corporate-style roast that:\n"
        "1. Sounds like an official performance review or HR memo\n"
        "2. Uses corporate buzzwords to deliver the burn\n"
        "3. Is passive-aggressive perfection"
    ),
    "gen-z": (
        "You are a chronically online zoomer who roasts using internet slang, "
        "memes, and brainrot. You speak in TikTok references, use 'no cap', "
        "'fr fr', 'ong', 'slay', 'its giving', 'rent free', and other Gen-Z "
        "lingo. Your roasts hit different.\n\n"
        "Target: {user_name}\n"
        "{hints}"
        "Chat history sample: \"{messages}\"\n"
        "{embarrassing}"
        "{previous_roasts}"
        "\nWrite a SHORT (1-2 sentences max) Gen-Z roast that:\n"
        "1. Uses current internet slang and meme references\n"
        "2. References something specific from their messages\n"
        "3. Sounds like a viral tweet or TikTok comment"
    ),
}

# ---------------------------------------------------------------------------
# Compliment prompt
# ---------------------------------------------------------------------------

COMPLIMENT_PROMPT: str = (
    "You are a genuinely kind AI that finds the best in people. Based on "
    "their chat history, highlight their positive contributions, humor, "
    "helpfulness, or unique personality. Be sincere, not sarcastic.\n\n"
    "Target: {user_name}\n"
    "{hints}"
    "Chat history sample: \"{messages}\"\n"
    "\nWrite a SHORT (1-2 sentences max), genuine compliment that:\n"
    "1. References something specific and positive from their messages\n"
    "2. Feels warm and authentic\n"
    "3. Would genuinely make them smile"
)

# ---------------------------------------------------------------------------
# Receipts prompt
# ---------------------------------------------------------------------------

RECEIPTS_PROMPT: str = (
    "You are a fact-checker analyzing chat history to find messages that "
    "contradict or confirm a specific claim. Present your findings like a "
    "detective laying out evidence — direct, factual, and a little dramatic.\n\n"
    "Target: {user_name}\n"
    "Messages to analyze: \"{messages}\"\n"
    "\nAnalyze the messages and present your findings concisely."
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _format_hints(patterns: dict) -> str:
    """Turn pattern analysis dict into a human-readable hints line."""
    hints: list[str] = []
    if patterns.get("emoji_heavy"):
        hints.append("overuses emojis")
    if patterns.get("repetitive"):
        hints.append("repeats themselves constantly")
    if patterns.get("one_word_warrior"):
        hints.append("only sends short messages")
    if patterns.get("caps_lock_fan"):
        hints.append("LOVES CAPS LOCK")
    if patterns.get("question_asker"):
        hints.append("asks way too many questions")
    if patterns.get("late_night_poster"):
        hints.append("posts at ungodly hours")
    if patterns.get("burst_sender"):
        hints.append("sends message bursts")
    if patterns.get("link_sharer"):
        hints.append("shares links constantly")

    if not hints:
        return ""
    return f"Behavioral patterns: {', '.join(hints)}.\n"


def build_roast_prompt(
    style: str,
    user_name: str,
    patterns: dict,
    messages: list[str],
    previous_roasts: list[str],
    embarrassing: list[str] | None = None,
) -> str:
    """Build a complete roast prompt for the given style.

    Args:
        style: One of the keys in ``ROAST_STYLES`` (falls back to *savage*).
        user_name: Display name of the roast target.
        patterns: Dict returned by ``analyzer.analyze_chat_patterns()``.
        messages: Sample of the target's chat messages.
        previous_roasts: Recent roasts already delivered to this target.
        embarrassing: Optional list of embarrassing quotes.

    Returns:
        A fully-formatted system prompt string ready to send to an AI provider.
    """
    template = ROAST_STYLES.get(style, ROAST_STYLES["savage"])

    hints_text = _format_hints(patterns)
    messages_text = " ".join(messages) if messages else ""
    embarrassing_text = (
        f"Embarrassing things they said: {' | '.join(embarrassing[:5])}\n"
        if embarrassing
        else ""
    )
    previous_text = (
        f"Previous roasts (avoid repeating similar ideas): {' | '.join(previous_roasts[:5])}\n"
        if previous_roasts
        else ""
    )

    return template.format(
        user_name=user_name,
        hints=hints_text,
        messages=messages_text,
        embarrassing=embarrassing_text,
        previous_roasts=previous_text,
    )


def build_compliment_prompt(
    user_name: str,
    patterns: dict,
    messages: list[str],
) -> str:
    """Build a compliment prompt.

    Args:
        user_name: Display name of the target.
        patterns: Dict returned by ``analyzer.analyze_chat_patterns()``.
        messages: Sample of the target's chat messages.

    Returns:
        A fully-formatted system prompt string.
    """
    hints_text = _format_hints(patterns)
    messages_text = " ".join(messages) if messages else ""

    return COMPLIMENT_PROMPT.format(
        user_name=user_name,
        hints=hints_text,
        messages=messages_text,
    )
