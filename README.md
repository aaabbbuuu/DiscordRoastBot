# Smart Roast Discord Bot v3 🤖🔥

A Discord bot that delivers witty, personalized roasts based on chat history and behavioral patterns.
Features deep history indexing, embarrassing moment detection, roast styles, compliment mode, receipts, scheduled roasts, and dual AI engine support with automatic fallback.

---

## 🚀 Features

### Core Roasting
- **Context-Aware Roasts** — Analyzes actual chat history, not just usernames
- **Roast Styles** — Choose your flavor: savage, mild, shakespearean, corporate, or gen-z
- **Pattern Recognition** — Detects emoji abuse, caps lock, repetitiveness, late-night posting, message bursts, and more
- **Embarrassing Moments** — Automatically finds and roasts based on self-deprecating messages
- **Compliment Mode** — Flip the script and generate genuine compliments based on positive contributions
- **Deep History** — Index weeks or months of chat history for devastating contextual roasts
- **Dual AI Engine** — OpenAI (gpt-4o-mini) as primary, Groq (llama-3.3-70b) as automatic fallback

### Social Features
- **Roast Battles** — Head-to-head roast competitions with reaction voting
- **Receipts** — Search a user's message history to prove (or disprove) their claims
- **Hall of Shame** — Server-wide leaderboard of the most embarrassing moments
- **Scheduled Roasts** — Automatic daily roast-of-the-day targeting a random active user
- **Leaderboards** — Track most active chatters
- **Stats & Memory** — View message stats and stored message counts per user

### Admin Tools
- **Channel Indexing** — Fetch and analyze messages from before the bot joined
- **Server-Wide Indexing** — Index entire servers across all channels
- **User Deep Dive** — Target specific users for comprehensive history analysis

### Smart Detection
- Emoji overuse 🔥🔥🔥
- CAPS LOCK ABUSE
- One-word warriors
- Question spam
- Repetitive messages
- Late-night posting (midnight–5am)
- Message frequency bursts
- Link/URL sharing patterns
- Embarrassing admissions

---

## 📋 Commands

All commands use Discord slash commands (`/`).

### Everyone Can Use
| Command | Description | Example |
|---------|-------------|---------|
| `/roast @user [style]` | Roast someone based on their chat history | `/roast @Alice style:shakespearean` |
| `/roastme` | Roast yourself | `/roastme` |
| `/embarrass @user` | Find embarrassing moments and roast | `/embarrass @Alice` |
| `/compliment @user` | Generate a genuine compliment | `/compliment @Alice` |
| `/battle @user1 @user2` | Epic roast battle with reaction voting | `/battle @Alice @Bob` |
| `/stats @user` | View message statistics | `/stats @Alice` |
| `/leaderboard` | Top 10 most active chatters | `/leaderboard` |
| `/memory @user` | Check stored message count | `/memory @Alice` |
| `/receipts @user "claim"` | Search message history for a claim | `/receipts @Alice "I never said that"` |
| `/hallofshame` | Server-wide embarrassment leaderboard | `/hallofshame` |

### Admin Commands (Require Administrator)
| Command | Description | Example |
|---------|-------------|---------|
| `/index [channel] [days]` | Index channel message history | `/index #general 60` |
| `/indexserver [days]` | Index entire server history | `/indexserver 30` |
| `/deepdive @user [days]` | Deep dive into user's full history | `/deepdive @Alice 90` |
| `/scheduleroast channel enabled [hour] [minute]` | Configure daily roast-of-the-day | `/scheduleroast #roasts true 12 0` |

### Roast Styles
| Style | Vibe |
|-------|------|
| `savage` | Ruthless, no-holds-barred (default) |
| `mild` | Friendly teasing, light-hearted |
| `shakespearean` | Iambic roasts, thou art roasted |
| `corporate` | HR performance review... that's actually a roast |
| `gen-z` | Chronically online, brainrot, meme-speak |

---

## 🛠 Installation & Setup

### Prerequisites

- Python 3.10+
- Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))
- OpenAI API key (from [OpenAI Platform](https://platform.openai.com/api-keys))
- Groq API key (from [Groq Console](https://console.groq.com/keys)) — optional but recommended

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SmartRoastBot.git
   cd SmartRoastBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your API keys:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

   > **Note:** The bot also supports `data/config.json` as a fallback for backward compatibility. Environment variables and `.env` take priority.

4. **Enable Discord Intents**

   In [Discord Developer Portal](https://discord.com/developers/applications):
   - Go to your application → Bot → Privileged Gateway Intents
   - ✅ Enable **Message Content Intent**
   - ✅ Enable **Server Members Intent**
   - Save changes

5. **Run the bot**
   ```bash
   python main.py
   ```

   You should see:
   ```
   ✅ Logged in as Smart Roast Bot#0478
   📊 Loaded 0 users with message history
   📋 Commands registered: roast, stats, leaderboard, ...
   🔥 Bot is ready to roast!
   ```

6. **Invite bot to your server**

   Required permissions:
   - Read Messages/View Channels
   - Send Messages
   - Read Message History
   - Add Reactions
   - Use External Emojis
   - Use Slash Commands

### Initial Setup (Recommended)

After the bot joins your server:

```bash
# Let the bot collect messages naturally for a day, then:

# Option A: Index specific channel
/index #general 30

# Option B: Index entire server (recommended)
/indexserver 30

# Option C: Target specific users
/deepdive @ActiveUser 90
```

---

## 🏗 Architecture

```
├── main.py                          # Entry point — init config, logging, DB, start bot
├── requirements.txt                 # All dependencies
├── .env.example                     # Template for environment variables
├── README.md                        # Documentation
├── data/
│   ├── config.json                  # Legacy config (backward compat, gitignored)
│   └── roastbot.db                  # SQLite database (gitignored)
├── logs/
│   └── bot.log                      # Rotating log file
└── roast_master/
    ├── __init__.py                  # Package init, version 3.0.0
    ├── config.py                    # Centralized config loader (env → .env → config.json)
    ├── database.py                  # Async SQLite database (aiosqlite)
    ├── logging_setup.py             # Logging configuration
    ├── bot.py                       # Bot setup, event handlers, cog loading
    ├── ai/                          # AI provider system
    │   ├── __init__.py
    │   ├── base.py                  # AIProvider abstract base class
    │   ├── openai_provider.py       # OpenAI implementation
    │   ├── groq_provider.py         # Groq implementation (70B → 8B fallback)
    │   ├── engine.py                # AIEngine — provider chain + generation logic
    │   ├── prompts.py               # Prompt templates and roast style definitions
    │   └── analyzer.py              # Chat pattern analysis
    └── cogs/                        # Discord command cogs
        ├── __init__.py
        ├── roast.py                 # /roast, /roastme, /embarrass, /compliment
        ├── battle.py                # /battle
        ├── stats.py                 # /stats, /leaderboard, /memory
        ├── history.py               # /index, /indexserver, /deepdive (admin)
        ├── receipts.py              # /receipts
        ├── hallofshame.py           # /hallofshame
        └── scheduler.py             # Scheduled roast-of-the-day (admin config)
```

---

## 🧠 How It Works

### Message Collection
1. Bot passively monitors all non-command messages in channels it can see
2. Stores messages in an async SQLite database (`data/roastbot.db`)
3. Tracks metadata: user, guild, channel, timestamp, first seen, last seen, total count

### Historical Indexing
When admins run `/index` or `/indexserver`:
1. Bot fetches historical messages via Discord API (up to 365 days)
2. Processes messages in batches of 100 (Discord API limit)
3. Stores messages while filtering out commands and bot messages
4. Provides progress updates and statistics

### Pattern Analysis
Before generating roasts, the bot analyzes:
- **Emoji usage** — Flags users who spam emojis
- **Repetitiveness** — Detects copy-paste behavior
- **Message length** — Identifies one-word warriors
- **CAPS usage** — Tracks excessive capitalization
- **Question frequency** — Notes excessive question marks
- **Late-night posting** — Messages between midnight and 5am
- **Message bursts** — Many messages in short time windows
- **Link sharing** — URL sharing frequency

### AI Roast Generation
1. **Fetches messages** — Pulls user messages from the database
2. **Analyzes patterns** — Runs behavioral pattern detection
3. **Checks history** — Reviews past roasts to avoid repeats
4. **Builds prompt** — Selects style template and assembles context
5. **Generates roast** — Sends to OpenAI (gpt-4o-mini) with creative prompt
6. **Fallback** — Automatically switches to Groq if OpenAI fails
7. **Logs roast** — Records the roast in history for dedup
8. **Returns roast** — Posts to Discord with provider attribution

### Embarrassing Moment Detection
Searches for keywords in message history:
- Self-deprecating: "cringe", "embarrassing", "oops", "my bad"
- Mistakes: "wrong", "fail", "mistake", "stupid"
- Confusion: "forgot", "confused", "help", "i don't know"

---

## 📊 Storage & Privacy

### What Gets Stored
- Messages per user in SQLite (configurable limit, default 500)
- Message content only (no attachments, images, or embeds)
- Timestamps, channel, and guild metadata
- Roast history (for dedup and stats)
- Scheduled roast configuration per guild

### What Doesn't Get Stored
- Direct messages (DMs)
- Messages in private channels bot can't access
- Messages from other bots
- Commands (anything starting with the prefix)
- Deleted messages are kept if captured during indexing

### GDPR Considerations
- Bot only stores what's necessary for functionality
- Users can check their data via `/memory`
- Message history respects configurable limits
- Admins can implement data deletion (feature can be added)

---

## ⚙️ Configuration

Configuration is loaded with this priority: **environment variables → `.env` file → `data/config.json`**.

### Environment Variables

Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | *(required)* | Discord bot token |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GROQ_API_KEY` | — | Groq API key |
| `AI_PROVIDERS` | `openai,groq` | Comma-separated provider priority list |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Primary Groq model |
| `GROQ_FALLBACK_MODEL` | `llama-3.1-8b-instant` | Groq fallback model |
| `COMMAND_PREFIX` | `!` | Legacy prefix command character |
| `ROAST_COOLDOWN` | `30` | Seconds between roasts for same target |
| `MAX_MESSAGES_PER_USER` | `500` | Max stored messages per user |
| `MAX_INDEX_DAYS` | `365` | Max days for historical indexing |
| `SCHEDULED_ROAST_ENABLED` | `false` | Enable scheduled roasts |
| `SCHEDULED_ROAST_CHANNEL_ID` | — | Channel ID for scheduled roasts |
| `SCHEDULED_ROAST_CRON` | `0 12 * * *` | Cron expression for schedule |

### Legacy Config (Fallback)

If you prefer, you can still use `data/config.json`:
```json
{
  "DISCORD_TOKEN": "your_discord_bot_token",
  "OPENAI_API_KEY": "sk-proj-...",
  "GROQ_API_KEY": "gsk_..."
}
```

Environment variables and `.env` always take priority over `config.json`.

---

## ⚠️ Limitations & Safety

### Content Warnings
- Bot generates edgy/savage humor — use discretion in professional environments
- Roasts are AI-generated and may occasionally miss context
- Consider the culture of your server before deploying

### Rate Limits
- OpenAI: Subject to API tier limits (bot auto-switches to Groq)
- Groq: Free tier has rate limits (bot tries 70B model, then 8B fallback)
- Discord: Bot respects Discord API rate limits during indexing

### Permissions
- Bot needs `Read Message History` to index historical messages
- Some private channels may be inaccessible (this is normal)
- Admin commands require Administrator role

### Performance
- `/indexserver` can take several minutes on large servers
- Recommended to run during low-traffic hours
- Consider indexing specific channels instead of entire server

---

## 🐛 Troubleshooting

### Bot doesn't respond to slash commands
- ✅ Check Message Content Intent is enabled in the Developer Portal
- ✅ Verify bot has Send Messages and Use Slash Commands permissions
- ✅ Re-invite the bot with the `applications.commands` scope if slash commands don't appear
- ✅ Wait a few minutes — Discord can take time to register slash commands globally

### Slash commands not showing up
- ✅ Make sure the bot was invited with the `applications.commands` OAuth2 scope
- ✅ Try restarting the bot — commands sync on startup
- ✅ Check the bot logs for any sync errors

### Import errors or missing modules
- ✅ Verify project structure matches the architecture section above
- ✅ Check Python version is 3.10+
- ✅ Reinstall dependencies: `pip install -r requirements.txt`
- ✅ Ensure all `__init__.py` files exist in `roast_master/`, `roast_master/ai/`, and `roast_master/cogs/`

### "No permission to read channel"
- ✅ Check bot role has Read Message History permission
- ✅ Verify channel isn't private/hidden from bot
- ✅ Some channels being inaccessible is normal — use `/index` on specific channels

### Rate limit issues
- ✅ Automatic fallback to Groq should handle OpenAI rate limits
- ✅ Verify both API keys are set in `.env`
- ✅ Wait a few minutes if both services are rate-limited

### Database issues
- ✅ The SQLite database is created automatically at `data/roastbot.db`
- ✅ If migrating from v2, the bot auto-migrates `data/messages.json` on first run
- ✅ Delete `data/roastbot.db` to reset (you'll lose stored data)

---

## 🤝 Contributing

Contributions are welcome! Areas where help is appreciated:

- New roast generation strategies
- Additional pattern detection algorithms
- Performance optimizations for large servers
- Multi-language support
- Bug fixes and testing

Please submit pull requests with clear descriptions of changes.

---

## 📄 License

This project is provided under the **MIT License**

---

## ✍️ Author

**Abu Hassan**

---

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check the troubleshooting section above first

---

## 🔗 Resources & References

- [OpenAI Python SDK Documentation](https://platform.openai.com/docs)
- [Groq API Documentation](https://console.groq.com/docs)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Bot Best Practices](https://discord.com/developers/docs/topics/community-resources)

---
