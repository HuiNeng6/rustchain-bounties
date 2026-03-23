#!/usr/bin/env python3
"""
BoTTube Telegram Bot - Browse & Watch BoTTube Videos via Telegram
Bounty #2299 - 30 RTC

Features:
- /latest — 5 most recent videos with thumbnails
- /trending — top videos by views
- /watch <id> — video embed + thumbnail preview
- /search <query> — search by title/description
- /agent <name> — agent profile + recent uploads
- /tip <video_id> <amount> — tip video creator in RTC
- /link <wallet> — link RTC wallet for tipping
- Inline mode: @bottube_bot <query> in any chat

Tech:
- python-telegram-bot v22+
- BoTTubeClient SDK
- httpx for async HTTP

Wallet: 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQueryResultPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from bottube import BoTTubeClient, BoTTubeError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
BOTTUBE_API_URL = os.environ.get('BOTTUBE_API_URL', 'https://50.28.86.153:8097')
WALLET_ADDRESS = '9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT'

# In-memory storage for user wallets (in production, use a database)
user_wallets: Dict[int, str] = {}


@dataclass
class Video:
    """Video data structure"""
    id: str
    title: str
    description: str
    thumbnail_url: str
    video_url: str
    views: int
    likes: int
    agent_name: str
    duration: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Video':
        return cls(
            id=str(data.get('id', '')),
            title=data.get('title', 'Untitled'),
            description=data.get('description', '')[:200] + '...' if len(data.get('description', '')) > 200 else data.get('description', ''),
            thumbnail_url=data.get('thumbnail_url', data.get('thumbnail', '')),
            video_url=data.get('video_url', data.get('url', '')),
            views=data.get('views', data.get('view_count', 0)),
            likes=data.get('likes', data.get('like_count', 0)),
            agent_name=data.get('agent_name', data.get('agent', {}).get('name', 'Unknown')),
            duration=data.get('duration')
        )


class BoTTubeAPI:
    """Wrapper for BoTTube API"""

    def __init__(self):
        self.client = BoTTubeClient(
            base_url=BOTTUBE_API_URL,
            verify_ssl=False,
            timeout=30
        )

    async def get_latest_videos(self, limit: int = 5) -> List[Video]:
        """Get latest videos"""
        try:
            result = self.client.list_videos(limit=limit)
            videos = result if isinstance(result, list) else result.get('videos', [])
            return [Video.from_dict(v) for v in videos[:limit]]
        except BoTTubeError as e:
            logger.error(f"Error fetching latest videos: {e}")
            return []

    async def get_trending_videos(self, limit: int = 5) -> List[Video]:
        """Get trending videos"""
        try:
            result = self.client.trending(limit=limit)
            videos = result if isinstance(result, list) else result.get('videos', [])
            return [Video.from_dict(v) for v in videos[:limit]]
        except BoTTubeError as e:
            logger.error(f"Error fetching trending videos: {e}")
            return []

    async def search_videos(self, query: str, limit: int = 5) -> List[Video]:
        """Search videos by title/description"""
        try:
            result = self.client.search(query=query, limit=limit)
            videos = result if isinstance(result, list) else result.get('videos', [])
            return [Video.from_dict(v) for v in videos[:limit]]
        except BoTTubeError as e:
            logger.error(f"Error searching videos: {e}")
            return []

    async def get_video(self, video_id: str) -> Optional[Video]:
        """Get a single video by ID"""
        try:
            result = self.client.get_video(video_id)
            return Video.from_dict(result)
        except BoTTubeError as e:
            logger.error(f"Error fetching video {video_id}: {e}")
            return None

    async def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent profile"""
        try:
            return self.client.get_agent(agent_name)
        except BoTTubeError as e:
            logger.error(f"Error fetching agent {agent_name}: {e}")
            return None

    async def tip_video(self, video_id: str, amount: float, wallet_address: str) -> bool:
        """Tip a video"""
        try:
            self.client.tip(video_id=video_id, amount=amount)
            return True
        except BoTTubeError as e:
            logger.error(f"Error tipping video {video_id}: {e}")
            return False


# Global API instance
api = BoTTubeAPI()


def format_video_caption(video: Video) -> str:
    """Format video caption for display"""
    duration_str = f"Duration: {video.duration}s\n" if video.duration else ""
    return (
        f"🎬 *{video.title}*\n\n"
        f"👤 Agent: {video.agent_name}\n"
        f"👁 Views: {video.views:,}\n"
        f"❤️ Likes: {video.likes:,}\n"
        f"{duration_str}"
        f"\n📝 {video.description}"
    )


def create_video_keyboard(video_id: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for video actions"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Watch", callback_data=f"watch_{video_id}"),
            InlineKeyboardButton("💰 Tip", callback_data=f"tip_{video_id}")
        ],
        [
            InlineKeyboardButton("👤 Agent", callback_data=f"agent_video_{video_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "🤖 *Welcome to BoTTube Bot!*\n\n"
        "Browse and watch BoTTube videos directly in Telegram.\n\n"
        "📋 *Commands:*\n"
        "/latest — Show 5 most recent videos\n"
        "/trending — Show trending videos\n"
        "/watch `<id>` — Watch a specific video\n"
        "/search `<query>` — Search videos\n"
        "/agent `<name>` — View agent profile\n"
        "/tip `<video_id>` `<amount>` — Tip a video\n"
        "/link `<wallet>` — Link your RTC wallet\n\n"
        "💡 *Inline Mode:* Type `@bottube_bot <query>` in any chat to search!\n\n"
        f"💼 Developer Wallet: `{WALLET_ADDRESS}`"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await start_command(update, context)


async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /latest command - show 5 most recent videos"""
    await update.message.reply_text("🔄 Fetching latest videos...")

    videos = await api.get_latest_videos(5)

    if not videos:
        await update.message.reply_text("❌ No videos found or API unavailable.")
        return

    for video in videos:
        try:
            if video.thumbnail_url:
                await update.message.reply_photo(
                    photo=video.thumbnail_url,
                    caption=format_video_caption(video),
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
            else:
                await update.message.reply_text(
                    format_video_caption(video),
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
        except Exception as e:
            logger.error(f"Error sending video {video.id}: {e}")
            await update.message.reply_text(
                f"🎬 {video.title} (ID: {video.id})\n"
                f"Error displaying full details. Use /watch {video.id}",
                reply_markup=create_video_keyboard(video.id)
            )


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - show top videos by views"""
    await update.message.reply_text("🔥 Fetching trending videos...")

    videos = await api.get_trending_videos(5)

    if not videos:
        await update.message.reply_text("❌ No trending videos found or API unavailable.")
        return

    for idx, video in enumerate(videos, 1):
        caption = f"🔥 #{idx} - " + format_video_caption(video)
        try:
            if video.thumbnail_url:
                await update.message.reply_photo(
                    photo=video.thumbnail_url,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
            else:
                await update.message.reply_text(
                    caption,
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
        except Exception as e:
            logger.error(f"Error sending trending video {video.id}: {e}")
            await update.message.reply_text(
                f"🔥 #{idx} - {video.title} (ID: {video.id})",
                reply_markup=create_video_keyboard(video.id)
            )


async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watch command - show specific video"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a video ID.\n"
            "Usage: /watch <video_id>"
        )
        return

    video_id = context.args[0]
    await update.message.reply_text(f"🔄 Loading video {video_id}...")

    video = await api.get_video(video_id)

    if not video:
        await update.message.reply_text(f"❌ Video {video_id} not found.")
        return

    # Send video with thumbnail and link
    caption = format_video_caption(video) + f"\n\n🎬 [Watch on BoTTube]({video.video_url})"

    try:
        if video.thumbnail_url:
            await update.message.reply_photo(
                photo=video.thumbnail_url,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=create_video_keyboard(video.id)
            )
        else:
            await update.message.reply_text(
                caption,
                parse_mode='Markdown',
                reply_markup=create_video_keyboard(video.id)
            )

        # Try to send video file if available
        if video.video_url and video.video_url.endswith(('.mp4', '.webm')):
            await update.message.reply_text(
                f"📥 [Download Video]({video.video_url})",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        await update.message.reply_text(
            f"🎬 {video.title}\n"
            f"Video ID: {video.id}\n"
            f"Link: {video.video_url}"
        )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - search videos"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search query.\n"
            "Usage: /search <query>"
        )
        return

    query = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    videos = await api.search_videos(query, 5)

    if not videos:
        await update.message.reply_text(f"❌ No videos found for: {query}")
        return

    await update.message.reply_text(f"✅ Found {len(videos)} videos for: {query}")

    for video in videos:
        try:
            if video.thumbnail_url:
                await update.message.reply_photo(
                    photo=video.thumbnail_url,
                    caption=format_video_caption(video),
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
            else:
                await update.message.reply_text(
                    format_video_caption(video),
                    parse_mode='Markdown',
                    reply_markup=create_video_keyboard(video.id)
                )
        except Exception as e:
            logger.error(f"Error sending search result: {e}")
            await update.message.reply_text(
                f"🎬 {video.title} (ID: {video.id})"
            )


async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /agent command - show agent profile"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an agent name.\n"
            "Usage: /agent <name>"
        )
        return

    agent_name = ' '.join(context.args)
    await update.message.reply_text(f"👤 Fetching profile for: {agent_name}...")

    agent = await api.get_agent(agent_name)

    if not agent:
        await update.message.reply_text(f"❌ Agent not found: {agent_name}")
        return

    # Format agent profile
    profile = (
        f"👤 *{agent.get('name', 'Unknown')}*\n\n"
        f"📝 {agent.get('bio', agent.get('description', 'No description available.'))}\n\n"
        f"📊 *Stats:*\n"
        f"🎬 Videos: {agent.get('video_count', agent.get('videos', 0)):,}\n"
        f"👁 Total Views: {agent.get('total_views', 0):,}\n"
        f"❤️ Total Likes: {agent.get('total_likes', 0):,}\n"
        f"👥 Subscribers: {agent.get('subscriber_count', agent.get('subscribers', 0)):,}\n"
    )

    # Add avatar if available
    avatar_url = agent.get('avatar_url', agent.get('avatar', ''))
    if avatar_url:
        try:
            await update.message.reply_photo(
                photo=avatar_url,
                caption=profile,
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text(profile, parse_mode='Markdown')
    else:
        await update.message.reply_text(profile, parse_mode='Markdown')

    # Show recent videos
    recent_videos = agent.get('recent_videos', agent.get('videos', []))[:3]
    if recent_videos:
        await update.message.reply_text("🎬 *Recent Uploads:*", parse_mode='Markdown')
        for video_data in recent_videos:
            video = Video.from_dict(video_data) if isinstance(video_data, dict) else None
            if video:
                await update.message.reply_text(
                    f"• {video.title} (ID: {video.id})\n"
                    f"  👁 {video.views:,} views",
                    reply_markup=create_video_keyboard(video.id)
                )


async def tip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tip command - tip a video"""
    user_id = update.effective_user.id

    # Check if user has linked wallet
    if user_id not in user_wallets:
        await update.message.reply_text(
            "❌ You need to link your wallet first!\n"
            "Use /link <wallet_address> to link your RTC wallet."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Please provide video ID and amount.\n"
            "Usage: /tip <video_id> <amount>"
        )
        return

    try:
        video_id = context.args[0]
        amount = float(context.args[1])

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive.")
            return

        await update.message.reply_text(
            f"💰 Tipping {amount} RTC to video {video_id}...\n"
            f"From wallet: {user_wallets[user_id]}"
        )

        success = await api.tip_video(video_id, amount, user_wallets[user_id])

        if success:
            await update.message.reply_text(
                f"✅ Successfully tipped {amount} RTC to video {video_id}!\n"
                f"Thank you for supporting the creator! 🙏"
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to tip video {video_id}. Please try again later."
            )
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please use a number.")


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link command - link RTC wallet"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide your wallet address.\n"
            "Usage: /link <wallet_address>"
        )
        return

    wallet_address = context.args[0]
    user_id = update.effective_user.id

    # Validate wallet address (basic check)
    if len(wallet_address) < 20:
        await update.message.reply_text(
            "❌ Invalid wallet address. Please check and try again."
        )
        return

    user_wallets[user_id] = wallet_address

    await update.message.reply_text(
        f"✅ Wallet linked successfully!\n"
        f"💼 Wallet: `{wallet_address}`\n\n"
        f"You can now use /tip to tip videos.",
        parse_mode='Markdown'
    )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline query - search videos in any chat"""
    query = update.inline_query.query.strip()

    if not query:
        # Show trending videos if no query
        videos = await api.get_trending_videos(5)
    else:
        videos = await api.search_videos(query, 5)

    results = []
    for video in videos:
        results.append(
            InlineQueryResultArticle(
                id=video.id,
                title=video.title,
                description=f"👤 {video.agent_name} | 👁 {video.views:,} views",
                thumbnail_url=video.thumbnail_url if video.thumbnail_url else None,
                input_message_content=InputTextMessageContent(
                    message_text=format_video_caption(video),
                    parse_mode='Markdown'
                ),
                reply_markup=create_video_keyboard(video.id)
            )
        )

    await update.inline_query.answer(results[:50], cache_time=30)


async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('watch_'):
        video_id = data.split('_')[1]
        video = await api.get_video(video_id)
        if video:
            await query.edit_message_caption(
                caption=format_video_caption(video) + f"\n\n🎬 [Watch]({video.video_url})",
                parse_mode='Markdown',
                reply_markup=create_video_keyboard(video_id)
            )

    elif data.startswith('tip_'):
        video_id = data.split('_')[1]
        await query.message.reply_text(
            f"💰 To tip this video, use:\n"
            f"/tip {video_id} <amount>\n\n"
            f"Example: /tip {video_id} 1"
        )

    elif data.startswith('agent_video_'):
        video_id = data.split('_')[2]
        video = await api.get_video(video_id)
        if video:
            # Simulate agent command
            context.args = [video.agent_name]
            await agent_command(update, context)


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN environment variable not set!")
        print("Please set it: export BOT_TOKEN='your_token_here'")
        print("\nTo get a token, talk to @BotFather on Telegram.")
        return

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("latest", latest_command))
    application.add_handler(CommandHandler("trending", trending_command))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("agent", agent_command))
    application.add_handler(CommandHandler("tip", tip_command))
    application.add_handler(CommandHandler("link", link_command))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(callback_query))

    # Start bot
    print("🤖 BoTTube Bot starting...")
    print(f"💼 Developer Wallet: {WALLET_ADDRESS}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()