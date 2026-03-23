"""
Human Scheduler - A human-like upload scheduler for bot creators.

Breaks the cron job feel by introducing natural irregularities in posting patterns.

Usage:
    from human_scheduler import HumanScheduler
    
    scheduler = HumanScheduler(profile="night_owl", agent="my_bot")
    if scheduler.should_post_now():
        upload_video(...)
"""

from .human_scheduler import (
    HumanScheduler,
    ProfileConfig,
    TimeWindow,
    PostDecision,
    PROFILES
)

__version__ = "1.0.0"
__all__ = [
    "HumanScheduler",
    "ProfileConfig",
    "TimeWindow",
    "PostDecision",
    "PROFILES"
]