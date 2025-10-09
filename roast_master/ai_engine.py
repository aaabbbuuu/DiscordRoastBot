import os
import json
import asyncio
from openai import OpenAI, RateLimitError, APIError
from groq import Groq

# === Load configuration ===
CONFIG_PATH = "data/config.json"
config = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

# === Initialize Clients ===
openai_key = os.getenv("OPENAI_API_KEY") or config.get("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY") or config.get("GROQ_API_KEY")

client = OpenAI(api_key=openai_key) if openai_key else None
groq_client = Groq(api_key=groq_key) if groq_key else None


def analyze_chat_patterns(messages: list) -> dict:
    """
    Analyze chat patterns to give AI more context for personalized roasts
    """
    if not messages:
        return {"pattern": "silent", "details": "No messages"}
    
    analysis = {
        "message_count": len(messages),
        "avg_length": sum(len(m) for m in messages) / len(messages),
        "total_chars": sum(len(m) for m in messages),
    }
    
    # Detect patterns
    text = " ".join(messages).lower()
    
    # Emoji usage
    emoji_count = sum(1 for char in text if ord(char) > 127000)
    analysis["emoji_heavy"] = emoji_count > len(messages) * 2
    
    # Check for repeated phrases/spam
    unique_ratio = len(set(messages)) / len(messages)
    analysis["repetitive"] = unique_ratio < 0.3
    
    # Short messages
    analysis["one_word_warrior"] = analysis["avg_length"] < 10
    
    # All caps usage
    caps_count = sum(1 for m in messages if m.isupper() and len(m) > 3)
    analysis["caps_lock_fan"] = caps_count > len(messages) * 0.3
    
    # Question marks (curious/confused person)
    question_count = sum(m.count("?") for m in messages)
    analysis["question_asker"] = question_count > len(messages) * 0.5
    
    return analysis


async def generate_roast(user_name: str, user_data: dict) -> str:
    """
    Generate a dank, witty, and hilarious roast about a given user based on chat history.
    Uses OpenAI as primary and Groq as automatic fallback.
    """
    
    messages = user_data.get("messages", [])
    recent_msgs = " ".join(messages[-20:])  # Last 20 messages
    
    # ✅ ENHANCEMENT: Handle users with no message history
    if not recent_msgs.strip():
        prompt = f"""
You are DankRoastMaster 3000 – a savage AI comedian.

Target: {user_name}
Status: GHOST MODE - They've been lurking without saying a word.

Write a SHORT (1-2 sentences max), hilarious roast about them being a silent lurker/ghost in the chat. 
Make it punchy and funny. No need to explain they have no history - just roast the silence itself.
"""
    else:
        # ✅ ENHANCEMENT: Add chat pattern analysis for better roasts
        analysis = analyze_chat_patterns(messages)
        
        # Build context hints for the AI
        context_hints = []
        if analysis.get("emoji_heavy"):
            context_hints.append("overuses emojis")
        if analysis.get("repetitive"):
            context_hints.append("repeats themselves constantly")
        if analysis.get("one_word_warrior"):
            context_hints.append("only sends short messages")
        if analysis.get("caps_lock_fan"):
            context_hints.append("LOVES CAPS LOCK")
        if analysis.get("question_asker"):
            context_hints.append("asks way too many questions")
        
        hints_text = f"Behavioral patterns: {', '.join(context_hints)}. " if context_hints else ""
        
        prompt = f"""
You are DankRoastMaster 3000 – a ruthless AI comedian who roasts people based on what they actually say.

Target: {user_name}
{hints_text}
Recent chat history: "{recent_msgs}"

Write a SHORT (1-2 sentences max), savage roast that:
1. References something specific they said or how they communicate
2. Is funny but cuts deep
3. Feels personal and contextual

Don't just describe them - ROAST them based on their actual words and patterns.
"""

    # --- Primary: OpenAI ---
    if client:
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=80,  # Slightly more room for better roasts
                temperature=0.95,  # Higher creativity
            )
            print("✅ Roast generated using OpenAI (gpt-4o-mini)")
            return response.choices[0].message.content.strip()
        except (RateLimitError, APIError) as e:
            print("⚠️ OpenAI unavailable, switching to Groq:", e)
        except Exception as e:
            print("❌ Unexpected OpenAI error:", e)

    # --- Fallback: Groq ---
    if groq_client:
        try:
            groq_response = await asyncio.to_thread(
                groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=80,
                temperature=0.95,
            )
            print("✅ Roast generated using Groq (llama-3.3-70b-versatile)")
            return groq_response.choices[0].message.content.strip()
        except Exception as g_err:
            print("⚠️ Groq 70B failed, switching to 8B:", g_err)
            try:
                groq_response = await asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=80,
                    temperature=0.95,
                )
                print("✅ Roast generated using Groq (llama-3.1-8b-instant)")
                return groq_response.choices[0].message.content.strip()
            except Exception as g_err2:
                print("❌ Both Groq models failed:", g_err2)
                return "Both roast engines are taking a break. Even they need rest after dealing with you people."

    # --- If both fail ---
    return "⚠️ Could not generate a roast right now. The AI is probably recovering from the last person it roasted."