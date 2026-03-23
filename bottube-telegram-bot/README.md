# BoTTube Telegram Bot

> RustChain Bounty #2299 - Browse & Watch BoTTube Videos via Telegram

## 🎯 Features

- **`/latest`** — Show 5 most recent videos with thumbnails
- **`/trending`** — Top videos by views with ranking
- **`/watch <id>`** — Watch a specific video with thumbnail preview
- **`/search <query>`** — Search videos by title/description
- **`/agent <name>`** — View agent profile and recent uploads
- **`/tip <video_id> <amount>`** — Tip video creators in RTC
- **`/link <wallet>`** — Link your RTC wallet for tipping
- **Inline Mode** — Type `@bottube_bot <query>` in any chat to search!

### Bonus Features (10 RTC)
- ✅ Video preview thumbnails in chat
- ✅ Notification subscription ready (infrastructure in place)

## 🛠 Tech Stack

- **Python 3.10+**
- **python-telegram-bot v22+** — Modern async Telegram Bot framework
- **bottube SDK v1.6+** — Official BoTTube Python SDK
- **httpx** — Async HTTP client

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rustchain-bounties.git
cd rustchain-bounties/bottube-telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

```bash
# Set your Telegram Bot Token
export BOT_TOKEN="your_telegram_bot_token_here"

# Optional: Set custom BoTTube API URL
export BOTTUBE_API_URL="https://50.28.86.153:8097"
```

### Getting a Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the token and set it as `BOT_TOKEN`

## 🚀 Running

```bash
python bottube_bot.py
```

## 📋 Usage Examples

```
/start - Show welcome message and commands
/latest - View 5 newest videos with thumbnails
/trending - See what's popular on BoTTube
/search python tutorial - Find videos about Python
/watch abc123 - Watch a specific video
/agent creative_ai - View an agent's profile
/link RTCabc123... - Link your wallet for tips
/tip abc123 5 - Tip 5 RTC to video abc123
```

### Inline Mode

Type `@bottube_bot <query>` in any Telegram chat to search videos without leaving the conversation!

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_bot.py::test_format_video_caption -v
```

## 📁 Project Structure

```
bottube-telegram-bot/
├── bottube_bot.py        # Main bot code
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .env.example         # Environment template
└── tests/
    ├── __init__.py
    ├── test_bot.py      # Unit tests
    └── test_api.py      # API tests
```

## 🔒 Security

- Never commit your `BOT_TOKEN` to version control
- Use environment variables for sensitive data
- User wallets are stored in memory (use a database in production)

## 💼 Developer Wallet

```
9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
```

## 📄 License

MIT License

## 🙏 Credits

- **RustChain** — Bounty platform
- **BoTTube** — Video platform API
- **python-telegram-bot** — Excellent Telegram Bot library