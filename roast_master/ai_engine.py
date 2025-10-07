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


# === Core Roast Generation ===
async def generate_roast(user_name: str, user_data: dict) -> str:
    """
    Generate a dank, witty, and hilarious roast about a given user *based on recent chat history.
    Uses OpenAI as the primary model and Groq as an automatic fallback.
    """

    recent_msgs = " ".join(user_data.get("messages", [])[-20:])
    prompt = f"""
    You are DankRoastMaster 3000 — a witty AI comedian that crafts roasts *based on what people say*, not just their name.
    The target's name is {user_name}.
    Their recent chat history: {recent_msgs}
    Write a hilarious, and offensive roast that's personal and **in context** - refer to something from their history above. they said, Avoid focusing on just their name.
    Keep it short (1–2 sentences).
    """

    # --- Primary: OpenAI ---
    if client:
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=60,
                temperature=0.9,
            )
            print("✅ Roast generated using OpenAI (gpt-4o-mini)")
            return response.choices[0].message.content.strip() + " 🤖 (Powered by OpenAI)"
        except (RateLimitError, APIError) as e:
            print("⚠️ OpenAI unavailable, switching to Groq:", e)
        except Exception as e:
            print("❌ Unexpected OpenAI error:", e)

    # --- Fallback: Groq ---
    if groq_client:
        try:
            groq_response = await asyncio.to_thread(
                groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",  # ✅ current Groq model
                messages=[{"role": "system", "content": prompt}],
                max_tokens=60,
                temperature=0.9,
            )
            print("✅ Roast generated using Groq (llama-3.3-70b-versatile)")
            return groq_response.choices[0].message.content.strip() + " 🤖 (Powered by Groq)"
        except Exception as g_err:
            print("⚠️ Groq 70B failed, switching to 8B:", g_err)
            try:
                groq_response = await asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model="llama-3.1-8b-instant",  # secondary backup
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=60,
                    temperature=0.9,
                )
                print("✅ Roast generated using Groq (llama-3.1-8b-instant)")
                return groq_response.choices[0].message.content.strip() + " 🤖 (Powered by Groq 8B)"
            except Exception as g_err2:
                print("❌ Both Groq models failed:", g_err2)
                return "Both roast engines are out of jokes! Try again soon."

    # --- If both fail ---
    return "⚠️ Could not generate a roast right now. Try again later!"
