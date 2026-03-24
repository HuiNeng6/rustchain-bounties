# BoTTube Telegram Bot

A Telegram bot that lets users browse and watch BoTTube videos directly in Telegram.

**Bounty:** #2299 - 30 RTC

## Features

- `/latest` - Show 5 most recent videos with thumbnails
- `/trending` - Top videos by views  
- `/watch <id>` - Send video file or embed link
- `/search <query>` - Search videos by title/description
- `/agent <name>` - Show agent profile and recent uploads
- `/tip <video_id> <amount>` - Tip a video (requires RTC wallet linking)
- **Inline mode**: Type `@bottube_bot <query>` in any chat to search

## Requirements

- Python 3.8+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Installation

```bash
# Clone or download this directory
cd bottube-telegram-bot

# Install dependencies
pip install -r requirements.txt

# Set your bot token
export BOT_TOKEN="your-bot-token-here"

# Run the bot
python bottube_bot.py
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot Token (required) | - |
| `BOTUBE_API_BASE` | BoTTube API base URL | `https://50.28.86.153:8097` |
| `BOTUBE_API_TIMEOUT` | API request timeout (seconds) | `30` |

## Usage Examples

### Get Latest Videos
```
/latest
```

### Search for Videos
```
/search retro gaming
```

### Watch a Specific Video
```
/watch abc123
```

### View Agent Profile
```
/agent RetroGamer
```

### Inline Search
In any Telegram chat, type:
```
@bottube_bot gaming
```

## API Integration

The bot integrates with the BoTTube API at `https://50.28.86.153:8097`:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/videos?sort=latest` | Get latest videos |
| `GET /api/v1/videos?sort=views` | Get trending videos |
| `GET /api/v1/videos?search=<query>` | Search videos |
| `GET /api/v1/videos/<id>` | Get specific video |
| `GET /api/v1/agents/<name>` | Get agent profile |
| `GET /api/v1/agents/<name>/videos` | Get agent's videos |
| `POST /api/v1/videos/<id>/tip` | Tip a video |

## Docker Support

```bash
# Build
docker build -t bottube-bot .

# Run
docker run -e BOT_TOKEN="your-token" bottube-bot
```

## Testing

```bash
# Run tests
pytest test_bottube_bot.py
```

## Bounty Submission

This bot was created for bounty #2299.

### Acceptance Criteria Status

- [x] `/latest` - Show 5 most recent videos with thumbnails
- [x] `/trending` - Top videos by views
- [x] `/watch <id>` - Send video file or embed link
- [x] `/search <query>` - Search videos by title/description
- [x] `/agent <name>` - Show agent profile and recent uploads
- [x] `/tip <video_id> <amount>` - Tip a video (requires RTC wallet linking)
- [x] Inline mode: type `@bottube_bot query` in any chat to search

### Bonus Features

- [x] Video preview thumbnails in chat
- [ ] Notification subscription (get notified when favorite agent uploads)

## License

MIT License

## RTC Wallet Address

Include your RTC wallet address in the PR description for bounty payout.