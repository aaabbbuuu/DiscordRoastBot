# Smart Roast Discord Bot 🤖🔥

A Discord bot that delivers witty, personalized roasts based on chat history and behavioral patterns.  
Features deep history indexing, embarrassing moment detection, and dual AI engine support with automatic fallback.

---

## 🚀 Features

### Core Roasting
- **Context-Aware Roasts** - Analyzes actual chat history, not just usernames
- **Pattern Recognition** - Detects emoji abuse, caps lock, repetitiveness, and more
- **Embarrassing Moments** - Automatically finds and roasts based on self-deprecating messages
- **Deep History** - Index weeks or months of chat history for devastating contextual roasts
- **Dual AI Engine** - OpenAI (gpt-4o-mini) as primary, Groq (llama-3.3-70b) as automatic fallback

### Advanced Features
- **Historical Indexing** - Fetch and analyze messages from before the bot joined
- **Server-Wide Search** - Index entire servers across all channels
- **User Deep Dive** - Target specific users for comprehensive history analysis
- **Roast Battles** - Head-to-head roast competitions with voting
- **Leaderboards** - Track most active chatters
- **Anti-Spam Protection** - Cooldown system prevents roast spam

### Smart Detection
- Emoji overuse 🔥🔥🔥
- CAPS LOCK ABUSE
- One-word warriors
- Question spam
- Repetitive messages
- Embarrassing admissions

---

## 📋 Commands

### Everyone Can Use
| Command | Description | Example |
|---------|-------------|---------|
| `!roast @user` | Roast someone based on their chat history | `!roast @Alice` |
| `!roast` | Roast yourself | `!roast` |
| `!roastme` | Explicitly request self-roast | `!roastme` |
| `!battle @user1 @user2` | Epic roast battle with voting | `!battle @Alice @Bob` |
| `!stats [@user]` | View message statistics | `!stats @Alice` |
| `!leaderboard` | Top 10 most active chatters | `!leaderboard` |
| `!embarrass @user` | Roast based on embarrassing messages | `!embarrass @Alice` |
| `!memory [@user]` | Check stored message count | `!memory @Alice` |

### Admin Commands (Require Administrator)
| Command | Description | Example |
|---------|-------------|---------|
| `!index [days]` | Index current channel history | `!index 60` |
| `!indexserver [days]` | Index entire server history | `!indexserver 30` |
| `!deepdive @user [days]` | Deep dive into user's full history | `!deepdive @Alice 90` |

---

## 🛠 Installation & Setup

### Prerequisites

- Python 3.10+
- Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))
- OpenAI API key (from [OpenAI Platform](https://platform.openai.com/api-keys))
- Groq API key (from [Groq Console](https://console.groq.com/keys)) - optional but recommended

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

3. **Create config file**
   ```bash
   mkdir -p data
   ```
   
   Create `data/config.json`:
   ```json
   {
     "DISCORD_TOKEN": "your_discord_bot_token",
     "OPENAI_API_KEY": "sk-proj-...",
     "GROQ_API_KEY": "gsk_..."
   }
   ```

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

### Initial Setup (Recommended)

After bot joins your server:

```bash
# Let bot collect messages naturally for a day, then:

# Option A: Index specific channel
!index 30

# Option B: Index entire server (recommended)
!indexserver 30

# Option C: Target specific users
!deepdive @ActiveUser 90
```

---

## 🧠 How It Works

### Message Collection
1. Bot passively monitors all non-command messages in channels it can see
2. Stores up to 500 messages per user in `data/messages.json`
3. Tracks metadata: first seen, last seen, total message count

### Historical Indexing
When admins run `!index` or `!indexserver`:
1. Bot fetches historical messages via Discord API (up to 365 days)
2. Processes messages in batches of 100 (Discord API limit)
3. Stores messages while filtering out commands and bot messages
4. Provides progress updates and statistics

### Pattern Analysis
Before generating roasts, the bot analyzes:
- **Emoji usage** - Flags users who spam emojis
- **Repetitiveness** - Detects copy-paste behavior
- **Message length** - Identifies one-word warriors
- **CAPS usage** - Tracks excessive capitalization
- **Question frequency** - Notes excessive question marks

### AI Roast Generation
1. **Samples messages** - Uses mix of recent (20) + random older (30) messages
2. **Adds context** - Includes behavioral patterns and embarrassing moments
3. **Generates roast** - Sends to OpenAI (gpt-4o-mini) with creative prompt
4. **Fallback** - Automatically switches to Groq if OpenAI fails
5. **Returns roast** - Posts to Discord with attribution

### Embarrassing Moment Detection
Searches for keywords in message history:
- Self-deprecating: "cringe", "embarrassing", "oops", "my bad"
- Mistakes: "wrong", "fail", "mistake", "stupid"
- Confusion: "forgot", "confused", "help", "i don't know"

---

## 📊 Storage & Privacy

### What Gets Stored
- Last 500 messages per user (configurable)
- Message content only (no attachments, images, or embeds)
- First seen and last seen timestamps
- Total message count (lifetime)

### What Doesn't Get Stored
- Direct messages (DMs)
- Messages in private channels bot can't access
- Messages from other bots
- Commands (anything starting with `!`)
- Deleted messages are kept if captured during indexing

### GDPR Considerations
- Bot only stores what's necessary for functionality
- Users can request their data via `!memory`
- Admins can implement data deletion (feature can be added)
- Message history automatically rotates (keeps only last 500)

---

## ⚙️ Configuration

### Adjust Message Storage Limit
Edit `roast_master/data_manager.py`:
```python
if len(self.data[user_id]["messages"]) > 500:  # Change to 200, 1000, etc.
```

### Adjust Cooldown Time
Edit `roast_master/bot.py`:
```python
time_left = 30 - (...)  # Change 30 to desired seconds
```

### Change AI Model
Edit `roast_master/ai_engine.py`:
```python
model="gpt-4o-mini",  # Options: gpt-4o, gpt-3.5-turbo, etc.
```

### Adjust Index Limits
Edit the max days in `roast_master/bot.py`:
```python
if days > 365:  # Change to 180, 90, etc.
```

---

## ⚠️ Limitations & Safety

### Content Warnings
- Bot generates edgy/savage humor - use discretion in professional environments
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
- `!indexserver` can take several minutes on large servers
- Recommended to run during low-traffic hours
- Consider indexing specific channels instead of entire server

---

## 🔮 Future Ideas

### Planned Features
- **Receipts Command** - Search for specific claims users made
  ```
  !receipts @Alice "I never said that"
  # Bot finds 3 times they said exactly that
  ```

- **Hall of Shame** - Server-wide leaderboard of most embarrassing messages
  ```
  !hallofshame
  # Display top 10 most cringe-worthy moments across all users
  ```

- **Compliment Mode** - Flip the script and generate genuine compliments
  ```
  !compliment @Alice
  # AI analyzes positive contributions and communication style
  ```

- **Custom Roast Styles** - Let users choose roast intensity
  ```
  !roast @Bob --style savage
  !roast @Alice --style mild
  !roast @Charlie --style shakespearean
  ```

## 🐛 Troubleshooting

### Bot doesn't respond to commands
- ✅ Check Message Content Intent is enabled
- ✅ Verify bot has Send Messages permission
- ✅ Ensure commands start with `!` (exclamation mark)
- ✅ Try `!ping` to test if bot is responsive

### "Command not found" errors
- ✅ Make sure all files exist: `bot.py`, `ai_engine.py`, `data_manager.py`, `history_fetcher.py`
- ✅ Check `__init__.py` exists in `roast_master` folder
- ✅ Restart the bot after any file changes

### Import errors
- ✅ Verify project structure matches documentation
- ✅ Check Python version is 3.10+
- ✅ Reinstall dependencies: `pip install -r requirements.txt`

### "No permission to read channel"
- ✅ Check bot role has Read Message History permission
- ✅ Verify channel isn't private/hidden from bot
- ✅ Some channels being inaccessible is normal - use `!index` on specific channels

### Rate limit issues
- ✅ Automatic fallback to Groq should work
- ✅ Verify both API keys are in config.json
- ✅ Wait a few minutes if both services are rate-limited

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

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check TROUBLESHOOTING.md first

---

## 🔗 Resources & References

- [OpenAI Python SDK Documentation](https://platform.openai.com/docs)
- [Groq API Documentation](https://console.groq.com/docs)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Bot Best Practices](https://discord.com/developers/docs/topics/community-resources)

---