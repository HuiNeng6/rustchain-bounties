#!/usr/bin/env python3
"""
BoTTube Telegram Bot - Watch & Interact via Telegram

A Telegram bot that lets users browse and watch BoTTube videos directly in Telegram.

Bounty: #2299 - 30 RTC

Features:
- /latest - Show 5 most recent videos with thumbnails
- /trending - Top videos by views
- /watch <id> - Send video file or embed link
- /search <query> - Search videos by title/description
- /agent <name> - Show agent profile and recent uploads
- /tip <video_id> <amount> - Tip a video (requires RTC wallet linking)
- Inline mode: type @bottube_bot query in any chat to search

Requirements:
- pip install python-telegram-bot requests
- Set BOT_TOKEN environment variable

Usage:
    export BOT_TOKEN="your-bot-token"
    python bottube_bot.py
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote

import requests
from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
    CallbackContext,
    CallbackQueryHandler,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# BoTTube API Configuration
BOTUBE_API_BASE = os.environ.get("BOTUBE_API_BASE", "https://50.28.86.153:8097")
BOTUBE_API_TIMEOUT = int(os.environ.get("BOTUBE_API_TIMEOUT", 30))


class BoTTubeAPI:
    """Client for BoTTube API."""

    def __init__(self, base_url: str = BOTUBE_API_BASE):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # Disable SSL verification for self-signed certs (development only)
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make a request to the BoTTube API."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", BOTUBE_API_TIMEOUT)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def get_latest_videos(self, limit: int = 5) -> List[Dict]:
        """Get the latest videos."""
        data = self._request("GET", f"/api/v1/videos?sort=latest&limit={limit}")
        return data.get("videos", []) if data else []

    def get_trending_videos(self, limit: int = 5) -> List[Dict]:
        """Get trending videos by views."""
        data = self._request("GET", f"/api/v1/videos?sort=views&limit={limit}")
        return data.get("videos", []) if data else []

    def search_videos(self, query: str, limit: int = 10) -> List[Dict]:
        """Search videos by title/description."""
        encoded_query = quote(query)
        data = self._request("GET", f"/api/v1/videos?search={encoded_query}&limit={limit}")
        return data.get("videos", []) if data else []

    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get a specific video by ID."""
        return self._request("GET", f"/api/v1/videos/{video_id}")

    def get_agent(self, name: str) -> Optional[Dict]:
        """Get agent profile."""
        return self._request("GET", f"/api/v1/agents/{name}")

    def get_agent_videos(self, name: str, limit: int = 5) -> List[Dict]:
        """Get recent videos from an agent."""
        data = self._request("GET", f"/api/v1/agents/{name}/videos?limit={limit}")
        return data.get("videos", []) if data else []

    def tip_video(self, video_id: str, amount: float, wallet_address: str) -> Optional[Dict]:
        """Tip a video."""
        return self._request(
            "POST",
            f"/api/v1/videos/{video_id}/tip",
            json={"amount": amount, "wallet": wallet_address}
        )


# Initialize API client
api = BoTTubeAPI()


def format_video_message(video: Dict) -> str:
    """Format a video for display in Telegram."""
    title = video.get("title", "Untitled")
    agent = video.get("agent_name", "Unknown")
    views = video.get("views", 0)
    video_id = video.get("id", "")
    duration = video.get("duration", "0:00")
    tags = video.get("tags", [])

    tags_str = " ".join(f"#{tag}" for tag in tags[:3]) if tags else ""

    return (
        f"🎬 *{title}*\n"
        f"👤 {agent}\n"
        f"👁 {views:,} views · ⏱ {duration}\n"
        f"🆔 `{video_id}`\n"
        f"{tags_str}"
    )


async def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command."""
    welcome_message = (
        "🎬 *Welcome to BoTTube Bot!*\n\n"
        "I help you discover and watch AI-generated videos from BoTTube.\n\n"
        "Commands:\n"
        "/latest - Show recent videos\n"
        "/trending - Show popular videos\n"
        "/search <query> - Search videos\n"
        "/watch <id> - Watch a specific video\n"
        "/agent <name> - Show agent profile\n"
        "/tip <video_id> <amount> - Tip a video\n\n"
        "Inline: Type `@bottube_bot <query>` in any chat to search!"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)


async def latest_command(update: Update, context: CallbackContext) -> None:
    """Handle /latest command."""
    await update.message.reply_text("🔍 Fetching latest videos...")

    videos = api.get_latest_videos(limit=5)

    if not videos:
        await update.message.reply_text("❌ No videos found. BoTTube API may be unavailable.")
        return

    for video in videos:
        message = format_video_message(video)
        keyboard = [
            [
                InlineKeyboardButton("▶️ Watch", callback_data=f"watch_{video.get('id')}"),
                InlineKeyboardButton("👤 Agent", callback_data=f"agent_{video.get('agent_name')}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Try to send thumbnail if available
        thumbnail_url = video.get("thumbnail_url")
        if thumbnail_url:
            try:
                await update.message.reply_photo(
                    photo=thumbnail_url,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )


async def trending_command(update: Update, context: CallbackContext) -> None:
    """Handle /trending command."""
    await update.message.reply_text("🔥 Fetching trending videos...")

    videos = api.get_trending_videos(limit=5)

    if not videos:
        await update.message.reply_text("❌ No trending videos found.")
        return

    for video in videos:
        message = format_video_message(video)
        keyboard = [
            [
                InlineKeyboardButton("▶️ Watch", callback_data=f"watch_{video.get('id')}"),
                InlineKeyboardButton("👤 Agent", callback_data=f"agent_{video.get('agent_name')}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        thumbnail_url = video.get("thumbnail_url")
        if thumbnail_url:
            try:
                await update.message.reply_photo(
                    photo=thumbnail_url,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )


async def search_command(update: Update, context: CallbackContext) -> None:
    """Handle /search command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/search <query>`\nExample: `/search gaming`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}")

    videos = api.search_videos(query, limit=10)

    if not videos:
        await update.message.reply_text("❌ No videos found matching your query.")
        return

    for video in videos[:5]:  # Limit to 5 results
        message = format_video_message(video)
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def watch_command(update: Update, context: CallbackContext) -> None:
    """Handle /watch command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/watch <video_id>`\nExample: `/watch abc123`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    video_id = context.args[0]
    video = api.get_video(video_id)

    if not video:
        await update.message.reply_text("❌ Video not found.")
        return

    message = format_video_message(video)

    # Try to send the video file
    video_url = video.get("video_url")
    if video_url:
        try:
            await update.message.reply_video(
                video=video_url,
                caption=message,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True
            )
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
            # Fallback: send link
            await update.message.reply_text(
                f"{message}\n\n🔗 [Watch on BoTTube]({video_url})",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def agent_command(update: Update, context: CallbackContext) -> None:
    """Handle /agent command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/agent <name>`\nExample: `/agent RetroGamer`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    agent_name = context.args[0]
    agent = api.get_agent(agent_name)

    if not agent:
        await update.message.reply_text("❌ Agent not found.")
        return

    name = agent.get("name", agent_name)
    bio = agent.get("bio", "No bio available.")
    video_count = agent.get("video_count", 0)
    total_views = agent.get("total_views", 0)
    joined = agent.get("created_at", "Unknown")

    message = (
        f"👤 *{name}*\n\n"
        f"📝 {bio}\n\n"
        f"📊 *Stats:*\n"
        f"• Videos: {video_count:,}\n"
        f"• Total views: {total_views:,}\n"
        f"• Joined: {joined}\n"
    )

    # Get recent videos
    recent_videos = api.get_agent_videos(agent_name, limit=3)
    if recent_videos:
        message += "\n🎬 *Recent Videos:*\n"
        for v in recent_videos:
            message += f"• {v.get('title', 'Untitled')} ({v.get('views', 0)} views)\n"

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def tip_command(update: Update, context: CallbackContext) -> None:
    """Handle /tip command."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/tip <video_id> <amount>`\n"
            "Example: `/tip abc123 0.5`\n\n"
            "Note: You need to link your RTC wallet first.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    video_id = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a number.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive.")
        return

    # Check if user has linked wallet
    user_id = str(update.effective_user.id)
    # In a real implementation, we'd check a database for linked wallets

    await update.message.reply_text(
        f"💰 *Tipping {amount} RTC to video `{video_id}`*\n\n"
        "To complete this tip, you need to link your RTC wallet.\n"
        "Use /linkwallet <address> to link your wallet.",
        parse_mode=ParseMode.MARKDOWN
    )


async def inline_query(update: Update, context: CallbackContext) -> None:
    """Handle inline queries."""
    query = update.inline_query.query

    if not query or len(query) < 2:
        return

    videos = api.search_videos(query, limit=10)

    results = []
    for video in videos:
        video_id = video.get("id", "")
        title = video.get("title", "Untitled")
        agent = video.get("agent_name", "Unknown")
        views = video.get("views", 0)
        video_url = video.get("video_url")
        thumbnail_url = video.get("thumbnail_url")

        if video_url:
            results.append(
                InlineQueryResultVideo(
                    id=video_id,
                    video_url=video_url,
                    mime_type="video/mp4",
                    thumbnail_url=thumbnail_url or "",
                    title=title,
                    description=f"{agent} · {views:,} views",
                )
            )
        else:
            results.append(
                InlineQueryResultArticle(
                    id=video_id,
                    title=title,
                    description=f"{agent} · {views:,} views",
                    input_message_content=InputTextMessageContent(
                        format_video_message(video),
                        parse_mode=ParseMode.MARKDOWN
                    )
                )
            )

    await update.inline_query.answer(results[:50], cache_time=30)


async def callback_query(update: Update, context: CallbackContext) -> None:
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    data = query.data

    if data.startswith("watch_"):
        video_id = data.replace("watch_", "")
        video = api.get_video(video_id)

        if video:
            message = format_video_message(video)
            await query.answer()
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("agent_"):
        agent_name = data.replace("agent_", "")
        agent = api.get_agent(agent_name)

        if agent:
            name = agent.get("name", agent_name)
            bio = agent.get("bio", "No bio available.")
            await query.answer()
            await query.edit_message_text(
                f"👤 *{name}*\n\n{bio}",
                parse_mode=ParseMode.MARKDOWN
            )


def main() -> None:
    """Start the bot."""
    # Get bot token from environment
    token = os.environ.get("BOT_TOKEN")

    if not token:
        logger.error("BOT_TOKEN environment variable not set!")
        print("Error: Set BOT_TOKEN environment variable")
        print("Example: export BOT_TOKEN='your-token-here'")
        return

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("latest", latest_command))
    application.add_handler(CommandHandler("trending", trending_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("agent", agent_command))
    application.add_handler(CommandHandler("tip", tip_command))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(callback_query))

    # Run the bot
    logger.info("Starting BoTTube Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()