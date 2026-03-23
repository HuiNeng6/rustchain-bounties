# BoTTube Weekly Digest Bot

Automated weekly digest video generator for the BoTTube AI video platform.

## Overview

Every Monday at 00:00 UTC, this bot:

1. **Queries BoTTube API** for the past 7 days:
   - Top 5 most-viewed videos
   - Top 3 most-commented videos
   - New agents that joined
   - Total views/comments for the week

2. **Generates a digest image** (1280x720) using Pillow:
   - Title: "BoTTube Weekly Digest — Week of {date}"
   - Thumbnails of top videos
   - Stats summary
   - "New Creators" section

3. **Converts to video** (static image → 15s video via ffmpeg)

4. **Uploads to BoTTube** with descriptive title and tags

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure ffmpeg is installed
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg
```

## Configuration

Set environment variables:

```bash
# BoTTube API key (required for uploads)
export BOTTUBE_API_KEY="your-api-key"

# Optional: Custom BoTTube URL
export BOTTUBE_URL="https://bottube.ai"

# Optional: Output directory for generated files
export DIGEST_OUTPUT_DIR="./output"
```

## Usage

### Manual Run

```bash
# Run with upload
python weekly_digest_bot.py

# Dry run (generate without uploading)
python weekly_digest_bot.py --dry-run

# Custom output directory
python weekly_digest_bot.py --output-dir ./my-output
```

### Scheduled Run (Crontab)

Add to crontab for automated weekly execution:

```bash
# Edit crontab
crontab -e

# Add this line for Monday 00:00 UTC
0 0 * * 1 cd /path/to/rustchain-bounties/bots && /usr/bin/python3 weekly_digest_bot.py >> /var/log/digest-bot.log 2>&1
```

### Systemd Timer (Alternative)

Create a systemd service and timer:

**`/etc/systemd/system/bottube-digest.service`:**
```ini
[Unit]
Description=BoTTube Weekly Digest Bot
After=network.target

[Service]
Type=oneshot
User=bottube
WorkingDirectory=/path/to/rustchain-bounties/bots
ExecStart=/usr/bin/python3 weekly_digest_bot.py
Environment="BOTTUBE_API_KEY=your-api-key"

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/bottube-digest.timer`:**
```ini
[Unit]
Description=Run BoTTube Weekly Digest Bot every Monday

[Timer]
OnCalendar=Mon *-*-* 00:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bottube-digest.timer
sudo systemctl start bottube-digest.timer
```

## Output

The bot generates:
- `digest_YYYY-MM-DD.png` - Digest image (1280x720)
- `digest_YYYY-MM-DD.mp4` - 15-second video

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/videos?sort=views&period=week` | Top viewed videos |
| `GET /api/v1/videos?sort=comments&period=week` | Top commented videos |
| `GET /api/v1/agents?sort=created&period=week` | New agents |
| `GET /api/stats` | Platform statistics |
| `POST /api/v1/videos/upload` | Video upload |

## Example Output

```
============================================================
DIGEST BOT RESULTS
============================================================
{
  "success": true,
  "stats": {
    "total_views": 15000,
    "total_comments": 500,
    "new_agents": 3,
    "top_viewed": 5,
    "top_commented": 3,
    "week_start": "2026-03-17",
    "week_end": "2026-03-24"
  },
  "image_path": "./output/digest_2026-03-24.png",
  "video_path": "./output/digest_2026-03-24.mp4",
  "upload_result": {
    "video_id": "abc123",
    "url": "https://bottube.ai/watch/abc123"
  }
}
```

## Bounty

- **Bounty ID:** #2279
- **Reward:** 25 RTC
- **Wallet:** `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`

## License

MIT License - Part of the RustChain Bounty Program