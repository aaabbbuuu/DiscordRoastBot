
# Smart Roast Discord Bot 🤖🔥

A Discord bot that delivers witty, personalized roasts based on chat content.  
Uses OpenAI as the primary model and falls back to Groq when OpenAI’s quota is exhausted.

---

## 🚀 Features

- Generate roasts using recent chat history  
- Automatic fallback: Groq model takes over when OpenAI rate limits  
- Easily extendable for compliments, daily roasts, etc.

---

## 🛠 Installation & Setup

### Prerequisites

- Python 3.10+  
- Discord bot token (from Discord Developer Portal)  
- OpenAI API key  
- Groq API key (optional, used as fallback)  

### Steps

1. Clone the repo  
   ```bash
   git clone https://github.com/yourusername/SmartRoastBot.git
   cd SmartRoastBot
   ```

2. Create a config file  
   ```bash
   cp data/config.example.json data/config.json
   ```  
   Fill in your `DISCORD_TOKEN`, `OPENAI_API_KEY`, and (optionally) `GROQ_API_KEY`.

3. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

4. Run the bot  
   ```bash
   python main.py
   ```

5. Invite the bot to your server (with permissions: Read Messages, Send Messages, Read Message History, etc.)

---

## 🎯 Usage

In a Discord server where the bot is present (especially in a `#general` or chat channel), use:

```
!roast @username
```

The bot will reply with a roast, using OpenAI or Groq backend depending on quota.  
Future additions might include `!compliment`, scheduled daily roasts, etc.

---

## ⚙️ Config Example (`data/config.example.json`)

```json
{
  "DISCORD_TOKEN": "your_discord_token_here",
  "OPENAI_API_KEY": "sk-xxxxx",
  "GROQ_API_KEY": "gsk-xxxxx"
}
```

## 🧠 How It Works (Overview)

1. The bot scans messages in a designated public channel (e.g. `#general`) and stores recent messages per user in `messages.json`.  
2. When `!roast` is invoked, the `ai_engine.py` builds a prompt combining recent messages and a roast style template.  
3. It first tries using OpenAI (`gpt-4o-mini`). If that fails (rate limit or quota), it falls back to Groq with `llama-3.3-70b-versatile` (or the latest supported model).  
4. The API’s response is returned in a Discord message, annotated with which engine powered it.

---

## ⚠️ Limitations & Safety

- The roast generator may occasionally produce mild or edgy jokes; use discretion in sensitive environments.  
- If both OpenAI and Groq fail, the bot returns a fallback message ("could not generate roast").  
- The bot only reads public channels where it has permission... it doesn’t access DMs or private channels.

---

## 📦 Future Ideas

- Add `!compliment @username` mode  
- Roasts based on voice channel behavior or other server events  
- Adjust roast “intensity” (mild / savage) via commands or config  
- Logging and analytics (e.g. which user gets roasted most)  

---

## 📄 License

This project is provided under the **MIT License**
---

## 🔗 Resources & References

- [OpenAI Python SDK docs](https://platform.openai.com/docs)  
- [Groq model & API docs](https://console.groq.com/docs)  
- [Discord Developer Portal & Bot Intents](https://discord.com/developers/docs)
