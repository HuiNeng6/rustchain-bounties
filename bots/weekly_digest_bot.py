#!/usr/bin/env python3
"""
BoTTube Weekly Digest Bot
=========================

Automated weekly digest video generator for BoTTube platform.

Every Monday at 00:00 UTC, this bot:
1. Queries BoTTube API for past 7 days:
   - Top 5 most-viewed videos
   - Top 3 most-commented videos
   - New agents that joined
   - Total views/comments for the week
2. Generates a digest image (1280x720) using Pillow
3. Converts static image to 15s video via ffmpeg
4. Uploads to BoTTube with descriptive title and tags

Bounty: #2279 - 25 RTC
Wallet: 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT

Usage:
    python weekly_digest_bot.py [--dry-run] [--output-dir ./output]

Crontab (Monday 00:00 UTC):
    0 0 * * 1 cd /path/to/rustchain-bounties/bots && python weekly_digest_bot.py
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import httpx

# Optional imports with fallback
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Install with: pip install Pillow")

# Configuration
BOTTUBE_URL = os.environ.get("BOTTUBE_URL", "https://bottube.ai")
BOTTUBE_API_KEY = os.environ.get("BOTTUBE_API_KEY", "")
WALLET_ADDRESS = "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT"
OUTPUT_DIR = Path(os.environ.get("DIGEST_OUTPUT_DIR", "./output"))

# Image settings
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
BACKGROUND_COLOR = "#0f0f23"
HEADER_COLOR = "#1a1a3e"
ACCENT_COLOR = "#00d4ff"
TEXT_COLOR = "#ffffff"
SECONDARY_TEXT = "#a0a0b0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class VideoStats:
    """Video statistics data"""
    id: str
    title: str
    views: int
    comments: int
    likes: int
    agent_name: str
    thumbnail_url: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class AgentStats:
    """New agent data"""
    name: str
    created_at: str
    video_count: int = 0
    bio: str = ""


@dataclass
class WeeklyStats:
    """Weekly digest statistics"""
    total_views: int
    total_comments: int
    total_likes: int
    new_agents_count: int
    top_viewed: List[VideoStats]
    top_commented: List[VideoStats]
    new_agents: List[AgentStats]
    week_start: str
    week_end: str


class BoTTubeClient:
    """BoTTube API client"""

    def __init__(self, base_url: str = BOTTUBE_URL, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(timeout=30, verify=False)

    def _headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_weekly_stats(self) -> WeeklyStats:
        """Get weekly statistics from BoTTube API"""
        logger.info("Fetching weekly statistics from BoTTube...")

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        # Fetch data from multiple endpoints
        top_viewed = self._get_top_videos("views", 5)
        top_commented = self._get_top_videos("comments", 3)
        new_agents = self._get_new_agents()
        platform_stats = self._get_platform_stats()

        # Aggregate totals from API or estimate
        total_views = platform_stats.get("total_views", sum(v.views for v in top_viewed))
        total_comments = platform_stats.get("total_comments", sum(v.comments for v in top_commented))

        return WeeklyStats(
            total_views=total_views,
            total_comments=total_comments,
            total_likes=platform_stats.get("total_likes", 0),
            new_agents_count=len(new_agents),
            top_viewed=top_viewed,
            top_commented=top_commented,
            new_agents=new_agents,
            week_start=start_date.strftime("%Y-%m-%d"),
            week_end=end_date.strftime("%Y-%m-%d")
        )

    def _get_top_videos(self, sort_by: str, limit: int) -> List[VideoStats]:
        """Get top videos by criteria"""
        try:
            # Use the correct BoTTube API endpoint
            response = self.client.get(
                f"{self.base_url}/api/videos",
                params={"sort": sort_by, "period": "week", "per_page": limit},
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()

            videos = data.get("videos", []) if isinstance(data, dict) else data
            return [self._parse_video(v) for v in videos[:limit]]

        except Exception as e:
            logger.warning(f"Primary API endpoint failed: {e}, trying fallback...")

        # Fallback: get all videos and sort locally
        try:
            response = self.client.get(
                f"{self.base_url}/api/videos",
                params={"per_page": 50},
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()

            videos = data.get("videos", []) if isinstance(data, dict) else data
            
            # Filter to past 7 days
            now = datetime.now(timezone.utc).timestamp()
            week_ago = now - (7 * 24 * 60 * 60)
            
            recent_videos = [
                v for v in videos 
                if v.get("created_at", 0) > week_ago
            ]
            
            # Sort by requested criteria
            if sort_by == "views":
                recent_videos.sort(key=lambda x: x.get("views", 0), reverse=True)
            elif sort_by == "comments":
                recent_videos.sort(key=lambda x: x.get("comments", 0), reverse=True)
            
            return [self._parse_video(v) for v in recent_videos[:limit]]

        except Exception as e:
            logger.error(f"Failed to fetch videos: {e}")
            return []

    def _parse_video(self, data: Dict[str, Any]) -> VideoStats:
        """Parse video data from API response"""
        return VideoStats(
            id=str(data.get("id", data.get("video_id", ""))),
            title=data.get("title", "Untitled"),
            views=data.get("views", data.get("view_count", 0)),
            comments=data.get("comments", data.get("comment_count", 0)),
            likes=data.get("likes", data.get("like_count", 0)),
            agent_name=data.get("agent_name", data.get("display_name", "Unknown")),
            thumbnail_url=data.get("thumbnail_url", data.get("thumbnail")),
            created_at=str(data.get("created_at", "")) if data.get("created_at") else None
        )

    def _get_new_agents(self) -> List[AgentStats]:
        """Get new agents from past week"""
        try:
            # Get all agents from stats API
            response = self.client.get(
                f"{self.base_url}/api/stats",
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()

            # Extract recent agents from stats
            agents = data.get("recent_agents", data.get("agents", []))
            if isinstance(agents, list):
                return [self._parse_agent(a) for a in agents[:5]]
            
            return []

        except Exception as e:
            logger.warning(f"Failed to fetch new agents: {e}")
            return []

    def _parse_agent(self, data: Dict[str, Any]) -> AgentStats:
        """Parse agent data from API response"""
        return AgentStats(
            name=data.get("name", "Unknown"),
            created_at=data.get("created_at", ""),
            video_count=data.get("video_count", 0),
            bio=data.get("bio", data.get("description", ""))[:100]
        )

    def _get_platform_stats(self) -> Dict[str, int]:
        """Get platform-wide statistics"""
        try:
            response = self.client.get(
                f"{self.base_url}/api/stats",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.warning(f"Failed to fetch platform stats: {e}")
            return {}

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Upload video to BoTTube"""
        if not self.api_key:
            raise ValueError("BOTTUBE_API_KEY is required for uploads")

        tags = tags or ["weekly-digest", "bottube", "ai-generated", "community"]

        try:
            # Try multipart upload
            with open(video_path, "rb") as f:
                files = {"video": (Path(video_path).name, f, "video/mp4")}
                data = {
                    "title": title,
                    "description": description,
                    "tags": ",".join(tags)
                }

                response = self.client.post(
                    f"{self.base_url}/api/videos/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise


class DigestImageGenerator:
    """Generate digest image using Pillow"""

    def __init__(self, width: int = IMAGE_WIDTH, height: int = IMAGE_HEIGHT):
        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required. Install with: pip install Pillow")

        self.width = width
        self.height = height
        self._fonts = {}

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font at specified size"""
        cache_key = (size, bold)
        if cache_key in self._fonts:
            return self._fonts[cache_key]

        # Try common font paths
        font_paths = [
            "arial.ttf",
            "Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSMono.ttf",
        ]

        for path in font_paths:
            try:
                font = ImageFont.truetype(path, size)
                self._fonts[cache_key] = font
                return font
            except (OSError, IOError):
                continue

        # Fallback to default
        font = ImageFont.load_default()
        self._fonts[cache_key] = font
        return font

    def generate(self, stats: WeeklyStats, output_path: str) -> str:
        """Generate digest image"""
        logger.info(f"Generating digest image: {output_path}")

        # Create base image
        img = Image.new("RGB", (self.width, self.height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        # Draw header background
        draw.rectangle([0, 0, self.width, 100], fill=HEADER_COLOR)

        # Draw title
        title_font = self._get_font(36, bold=True)
        title = f"BoTTube Weekly Digest"
        draw.text((40, 30), title, fill=ACCENT_COLOR, font=title_font)

        # Draw date range
        date_font = self._get_font(18)
        date_text = f"Week of {stats.week_start} to {stats.week_end}"
        draw.text((40, 70), date_text, fill=SECONDARY_TEXT, font=date_font)

        # Draw stats summary section
        self._draw_stats_section(draw, stats, y_offset=120)

        # Draw top viewed videos section
        self._draw_videos_section(
            draw, stats.top_viewed, "Top Viewed Videos",
            y_offset=280, max_videos=5
        )

        # Draw new creators section
        self._draw_new_creators_section(draw, stats, y_offset=520)

        # Draw footer
        self._draw_footer(draw)

        # Save image
        img.save(output_path, "PNG", quality=95)
        logger.info(f"Image saved to: {output_path}")
        return output_path

    def _draw_stats_section(self, draw: ImageDraw, stats: WeeklyStats, y_offset: int):
        """Draw statistics summary section"""
        font = self._get_font(16, bold=True)
        value_font = self._get_font(28, bold=True)

        # Stats boxes
        box_width = 200
        box_height = 80
        gap = 40
        start_x = 40

        stat_items = [
            ("Total Views", stats.total_views, "👁"),
            ("Comments", stats.total_comments, "💬"),
            ("New Agents", stats.new_agents_count, "🤖"),
            ("Top Videos", len(stats.top_viewed), "🔥"),
        ]

        for i, (label, value, icon) in enumerate(stat_items):
            x = start_x + i * (box_width + gap)

            # Draw box background
            draw.rectangle(
                [x, y_offset, x + box_width, y_offset + box_height],
                fill=HEADER_COLOR,
                outline=ACCENT_COLOR,
                width=2
            )

            # Draw icon and value
            draw.text((x + 15, y_offset + 10), f"{icon} {self._format_number(value)}", fill=TEXT_COLOR, font=value_font)
            draw.text((x + 15, y_offset + 50), label, fill=SECONDARY_TEXT, font=font)

    def _draw_videos_section(
        self,
        draw: ImageDraw,
        videos: List[VideoStats],
        title: str,
        y_offset: int,
        max_videos: int = 5
    ):
        """Draw videos list section"""
        title_font = self._get_font(20, bold=True)
        item_font = self._get_font(14)
        stats_font = self._get_font(12)

        # Section title
        draw.text((40, y_offset), f"🏆 {title}", fill=TEXT_COLOR, font=title_font)

        # Video items
        for i, video in enumerate(videos[:max_videos]):
            y = y_offset + 35 + i * 38

            # Rank badge
            badge_color = ["#FFD700", "#C0C0C0", "#CD7F32", "#808080", "#808080"][i]
            draw.ellipse([45, y + 2, 65, y + 22], fill=badge_color)
            draw.text((50, y + 3), str(i + 1), fill="#000000", font=stats_font)

            # Video title
            title_text = video.title[:50] + "..." if len(video.title) > 50 else video.title
            draw.text((75, y), title_text, fill=TEXT_COLOR, font=item_font)

            # Stats
            stats_text = f"👁 {self._format_number(video.views)}  💬 {self._format_number(video.comments)}"
            draw.text((75, y + 18), stats_text, fill=SECONDARY_TEXT, font=stats_font)

            # Agent name
            draw.text((400, y + 8), f"by {video.agent_name}", fill=ACCENT_COLOR, font=stats_font)

    def _draw_new_creators_section(self, draw: ImageDraw, stats: WeeklyStats, y_offset: int):
        """Draw new creators section"""
        title_font = self._get_font(20, bold=True)
        item_font = self._get_font(14)
        bio_font = self._get_font(12)

        # Section title
        draw.text((700, y_offset), "✨ New Creators", fill=TEXT_COLOR, font=title_font)

        if not stats.new_agents:
            draw.text((700, y_offset + 35), "No new agents this week", fill=SECONDARY_TEXT, font=item_font)
            return

        # Agent items
        for i, agent in enumerate(stats.new_agents[:4]):
            y = y_offset + 35 + i * 45

            # Agent icon
            draw.ellipse([705, y, 735, y + 30], fill=ACCENT_COLOR)
            draw.text((715, y + 5), "🤖", fill=TEXT_COLOR, font=item_font)

            # Agent name
            draw.text((745, y), agent.name, fill=TEXT_COLOR, font=item_font)

            # Bio snippet
            if agent.bio:
                bio_text = agent.bio[:40] + "..." if len(agent.bio) > 40 else agent.bio
                draw.text((745, y + 18), bio_text, fill=SECONDARY_TEXT, font=bio_font)

    def _draw_footer(self, draw: ImageDraw):
        """Draw footer with branding"""
        font = self._get_font(12)

        # Footer background
        draw.rectangle([0, self.height - 40, self.width, self.height], fill=HEADER_COLOR)

        # Footer text
        footer_text = f"Generated by BoTTube Weekly Digest Bot | Wallet: {WALLET_ADDRESS[:20]}..."
        draw.text((40, self.height - 25), footer_text, fill=SECONDARY_TEXT, font=font)

        # Logo/brand
        draw.text((self.width - 200, self.height - 25), "BoTTube.ai", fill=ACCENT_COLOR, font=font)

    def _format_number(self, n: int) -> str:
        """Format large numbers with suffixes"""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)


class VideoCreator:
    """Create video from static image using ffmpeg"""

    def __init__(self, duration: int = 15, fps: int = 30):
        self.duration = duration
        self.fps = fps

    def create(self, image_path: str, output_path: str) -> str:
        """Convert image to video with ffmpeg"""
        logger.info(f"Creating video from image: {image_path}")

        # Check ffmpeg availability
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loop", "1",  # Loop input image
            "-i", image_path,
            "-c:v", "libx264",
            "-t", str(self.duration),
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}",
            "-r", str(self.fps),
            output_path
        ]

        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        logger.info(f"Video created: {output_path}")
        return output_path

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False


class WeeklyDigestBot:
    """Main bot orchestrator"""

    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        api_key: str = "",
        dry_run: bool = False
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client = BoTTubeClient(api_key=api_key)
        self.image_gen = DigestImageGenerator()
        self.video_creator = VideoCreator()
        self.dry_run = dry_run

    def run(self) -> Dict[str, Any]:
        """Execute weekly digest workflow"""
        logger.info("=" * 60)
        logger.info("BoTTube Weekly Digest Bot Starting")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)

        results = {
            "success": False,
            "stats": None,
            "image_path": None,
            "video_path": None,
            "upload_result": None,
            "error": None
        }

        try:
            # Step 1: Fetch weekly stats
            stats = self.client.get_weekly_stats()
            results["stats"] = {
                "total_views": stats.total_views,
                "total_comments": stats.total_comments,
                "new_agents": stats.new_agents_count,
                "top_viewed": len(stats.top_viewed),
                "top_commented": len(stats.top_commented),
                "week_start": stats.week_start,
                "week_end": stats.week_end
            }
            logger.info(f"Weekly stats: {results['stats']}")

            # Step 2: Generate digest image
            image_path = str(self.output_dir / f"digest_{stats.week_end}.png")
            self.image_gen.generate(stats, image_path)
            results["image_path"] = image_path

            # Step 3: Create video from image
            video_path = str(self.output_dir / f"digest_{stats.week_end}.mp4")
            self.video_creator.create(image_path, video_path)
            results["video_path"] = video_path

            # Step 4: Upload to BoTTube (if not dry run)
            if not self.dry_run:
                title = f"BoTTube Weekly Digest — Week of {stats.week_start}"
                description = self._generate_description(stats)

                upload_result = self.client.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=["weekly-digest", "bottube", "ai-generated", "community", "stats"]
                )
                results["upload_result"] = upload_result
                logger.info(f"Upload successful: {upload_result}")
            else:
                logger.info("Dry run: skipping upload")
                results["upload_result"] = {"dry_run": True, "video_path": video_path}

            results["success"] = True

        except Exception as e:
            logger.error(f"Error: {e}")
            results["error"] = str(e)

        return results

    def _generate_description(self, stats: WeeklyStats) -> str:
        """Generate video description"""
        lines = [
            f"🎬 BoTTube Weekly Digest — Week of {stats.week_start}",
            "",
            "📊 This Week's Highlights:",
            f"• Total Views: {stats.total_views:,}",
            f"• Total Comments: {stats.total_comments:,}",
            f"• New Agents: {stats.new_agents_count}",
            "",
            "🔥 Top Videos:",
        ]

        for i, v in enumerate(stats.top_viewed[:5], 1):
            lines.append(f"  {i}. {v.title} by {v.agent_name} ({v.views:,} views)")

        if stats.new_agents:
            lines.append("")
            lines.append("✨ New Creators:")
            for agent in stats.new_agents[:3]:
                lines.append(f"  • {agent.name}")

        lines.extend([
            "",
            "---",
            "Generated by BoTTube Weekly Digest Bot",
            f"Wallet: {WALLET_ADDRESS}",
            "#BoTTube #WeeklyDigest #AI"
        ])

        return "\n".join(lines)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="BoTTube Weekly Digest Bot"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate content without uploading"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="",
        help="BoTTube API key (or set BOTTUBE_API_KEY env)"
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Generate image only, skip video creation"
    )

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("BOTTUBE_API_KEY", "")

    # Run bot
    bot = WeeklyDigestBot(
        output_dir=Path(args.output_dir),
        api_key=api_key,
        dry_run=args.dry_run
    )

    results = bot.run()

    # Print results
    print("\n" + "=" * 60)
    print("DIGEST BOT RESULTS")
    print("=" * 60)
    print(json.dumps(results, indent=2, default=str))

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()