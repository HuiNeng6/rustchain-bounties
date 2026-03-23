"""
Human Scheduler - A human-like upload scheduler for bot creators.

Breaks the cron job feel by introducing natural irregularities in posting patterns.

Usage:
    scheduler = HumanScheduler(profile="night_owl", agent="my_bot")
    if scheduler.should_post_now():
        upload_video(...)
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class PostDecision(Enum):
    """Decision about whether to post now."""
    POST_NOW = "post_now"
    SKIP = "skip"
    WAIT = "wait"
    DOUBLE_POST = "double_post"  # "Oh wait, one more thing!"


@dataclass
class TimeWindow:
    """Represents a time window for posting."""
    start_hour: int
    end_hour: int
    weight: float = 1.0
    
    def contains(self, hour: int) -> bool:
        """Check if hour is within this window."""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:  # Wraps midnight (e.g., 22:00 - 03:00)
            return hour >= self.start_hour or hour < self.end_hour


@dataclass
class ProfileConfig:
    """Configuration for a posting profile."""
    name: str
    description: str
    active_windows: List[TimeWindow]
    base_post_frequency_hours: float = 24.0
    jitter_hours: float = 4.0
    skip_probability: float = 0.05
    double_post_probability: float = 0.03
    inspiration_post_probability: float = 0.02
    inspiration_hours: List[int] = field(default_factory=lambda: [3])  # 3am inspiration
    min_minutes_between_posts: int = 30
    max_drift_hours: float = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "active_windows": [
                {"start_hour": w.start_hour, "end_hour": w.end_hour, "weight": w.weight}
                for w in self.active_windows
            ],
            "base_post_frequency_hours": self.base_post_frequency_hours,
            "jitter_hours": self.jitter_hours,
            "skip_probability": self.skip_probability,
            "double_post_probability": self.double_post_probability,
            "inspiration_post_probability": self.inspiration_post_probability,
            "inspiration_hours": self.inspiration_hours,
            "min_minutes_between_posts": self.min_minutes_between_posts,
            "max_drift_hours": self.max_drift_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileConfig':
        """Create from dictionary."""
        windows = [
            TimeWindow(w["start_hour"], w["end_hour"], w.get("weight", 1.0))
            for w in data["active_windows"]
        ]
        return cls(
            name=data["name"],
            description=data["description"],
            active_windows=windows,
            base_post_frequency_hours=data.get("base_post_frequency_hours", 24.0),
            jitter_hours=data.get("jitter_hours", 4.0),
            skip_probability=data.get("skip_probability", 0.05),
            double_post_probability=data.get("double_post_probability", 0.03),
            inspiration_post_probability=data.get("inspiration_post_probability", 0.02),
            inspiration_hours=data.get("inspiration_hours", [3]),
            min_minutes_between_posts=data.get("min_minutes_between_posts", 30),
            max_drift_hours=data.get("max_drift_hours", 2.0)
        )


# Predefined profiles
PROFILES = {
    "night_owl": ProfileConfig(
        name="night_owl",
        description="Posts between 10pm-3am, sleeps until noon. A creature of the night.",
        active_windows=[
            TimeWindow(22, 3, weight=1.0),  # 10pm - 3am
        ],
        base_post_frequency_hours=24.0,
        jitter_hours=2.0,
        skip_probability=0.08,
        double_post_probability=0.05,
    ),
    "morning_person": ProfileConfig(
        name="morning_person",
        description="Posts 6am-10am, quiet evenings. Early bird gets the worm.",
        active_windows=[
            TimeWindow(6, 10, weight=1.0),  # 6am - 10am
        ],
        base_post_frequency_hours=24.0,
        jitter_hours=3.0,
        skip_probability=0.05,
        double_post_probability=0.03,
    ),
    "binge_creator": ProfileConfig(
        name="binge_creator",
        description="Drops 4-5 videos in 2 hours, then disappears for days. Creative bursts.",
        active_windows=[
            TimeWindow(19, 21, weight=1.0),  # Evening binge window
            TimeWindow(14, 16, weight=0.3),  # Occasional afternoon binge
        ],
        base_post_frequency_hours=72.0,  # Posts every ~3 days on average
        jitter_hours=24.0,
        skip_probability=0.15,  # More likely to skip when in "disappeared" mode
        double_post_probability=0.25,  # High chance of burst posting
        inspiration_post_probability=0.05,
    ),
    "weekend_warrior": ProfileConfig(
        name="weekend_warrior",
        description="Barely posts weekdays, floods on Saturday. Work hard, post hard.",
        active_windows=[
            TimeWindow(10, 22, weight=1.0),  # Saturday all day
            TimeWindow(18, 22, weight=0.2),  # Weekday evenings (rare)
        ],
        base_post_frequency_hours=48.0,
        jitter_hours=12.0,
        skip_probability=0.3,  # High skip on weekdays
        double_post_probability=0.15,  # Saturday flood
        inspiration_post_probability=0.01,
    ),
    "consistent_but_human": ProfileConfig(
        name="consistent_but_human",
        description="Roughly daily but ±4 hours jitter. Reliable but not robotic.",
        active_windows=[
            TimeWindow(9, 23, weight=1.0),  # Broad window throughout the day
        ],
        base_post_frequency_hours=24.0,
        jitter_hours=4.0,
        skip_probability=0.07,
        double_post_probability=0.04,
        inspiration_post_probability=0.02,
    ),
}


class HumanScheduler:
    """
    A human-like scheduler that breaks the cron job feel.
    
    Features:
    - Never posts at exactly the same minute
    - Occasionally skips scheduled posts (life happens)
    - Occasionally double-posts ("oh wait, one more thing")
    - Rare "3am inspiration" posts outside normal pattern
    
    Example:
        scheduler = HumanScheduler(profile="night_owl", agent="my_bot")
        if scheduler.should_post_now():
            upload_video(...)
    """
    
    def __init__(
        self,
        profile: str = "consistent_but_human",
        agent: str = "default",
        config_path: Optional[str] = None,
        state_dir: Optional[str] = None
    ):
        """
        Initialize the scheduler.
        
        Args:
            profile: Profile name (night_owl, morning_person, binge_creator, 
                     weekend_warrior, consistent_but_human)
            agent: Unique identifier for this agent (used for state persistence)
            config_path: Optional path to custom profile config JSON
            state_dir: Directory to store state (defaults to ~/.human_scheduler/)
        """
        self.agent = agent
        self.profile_name = profile
        
        # Load profile config
        if config_path:
            self.config = self._load_config(config_path)
        elif profile in PROFILES:
            self.config = PROFILES[profile]
        else:
            raise ValueError(f"Unknown profile: {profile}. Available: {list(PROFILES.keys())}")
        
        # Initialize RNG with agent-specific seed for reproducibility
        self._rng = random.Random()
        
        # State directory for persistence
        if state_dir:
            self.state_dir = Path(state_dir)
        else:
            self.state_dir = Path.home() / ".human_scheduler"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize state
        self.state_file = self.state_dir / f"{agent}_state.json"
        self.state = self._load_state()
        
        # Re-seed RNG with agent-specific seed for reproducibility
        self._rng = random.Random(self._get_seed())
    
    def _get_seed(self) -> int:
        """Generate a seed based on agent and date for daily consistency."""
        today = datetime.now().strftime("%Y-%m-%d")
        seed_str = f"{self.agent}-{today}"
        return int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    
    def _load_config(self, config_path: str) -> ProfileConfig:
        """Load profile configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return ProfileConfig.from_dict(data)
    
    def _load_state(self) -> Dict[str, Any]:
        """Load scheduler state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_state()
    
    def _default_state(self) -> Dict[str, Any]:
        """Return default state."""
        return {
            "last_post_time": None,
            "last_post_hour": None,
            "scheduled_next_post": None,
            "consecutive_posts": 0,
            "total_posts": 0,
            "skipped_count": 0,
            "double_post_pending": False,
            "drift_offset": self._rng.uniform(-self.config.max_drift_hours, self.config.max_drift_hours)
        }
    
    def _save_state(self):
        """Persist state to disk."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _calculate_next_post_time(self, now: datetime) -> datetime:
        """Calculate when the next post should be scheduled."""
        base_interval = self.config.base_post_frequency_hours
        jitter = self._rng.uniform(-self.config.jitter_hours, self.config.jitter_hours)
        drift = self.state.get("drift_offset", 0)
        
        # Add jitter and drift to base interval
        interval_with_jitter = base_interval + jitter + drift
        
        # Find next active window
        next_time = now + timedelta(hours=interval_with_jitter)
        
        return next_time
    
    def _is_in_active_window(self, now: datetime) -> bool:
        """Check if current time is within an active posting window."""
        hour = now.hour
        day_of_week = now.weekday()  # 0=Monday, 6=Sunday
        
        for window in self.config.active_windows:
            if window.contains(hour):
                # Special handling for weekend_warrior
                if self.profile_name == "weekend_warrior":
                    if day_of_week == 5:  # Saturday
                        return True
                    elif day_of_week in range(5):  # Weekday
                        # Only allow rare weekday evening posts
                        return hour >= 18 and self._rng.random() < 0.2
                return True
        return False
    
    def _should_skip(self) -> bool:
        """Determine if we should skip this post (life happens)."""
        # Higher skip chance if we've been posting consistently
        consecutive = self.state.get("consecutive_posts", 0)
        adjusted_skip_prob = self.config.skip_probability * (1 + consecutive * 0.1)
        return self._rng.random() < min(adjusted_skip_prob, 0.3)
    
    def _should_double_post(self) -> bool:
        """Determine if we should post again soon (oh wait, one more thing!)."""
        return self._rng.random() < self.config.double_post_probability
    
    def _is_inspiration_time(self, now: datetime) -> bool:
        """Check if it's an 'inspiration' posting time outside normal windows."""
        hour = now.hour
        if hour in self.config.inspiration_hours:
            return self._rng.random() < self.config.inspiration_post_probability
        return False
    
    def _get_minute_jitter(self) -> int:
        """Get random minute offset to avoid posting at exact same time."""
        return self._rng.randint(-30, 30)
    
    def should_post_now(self) -> bool:
        """
        Determine if we should post now.
        
        Returns:
            True if we should post, False otherwise.
        """
        now = datetime.now()
        
        # Check minimum time between posts
        last_post = self.state.get("last_post_time")
        if last_post:
            last_post_dt = datetime.fromisoformat(last_post)
            minutes_since_last = (now - last_post_dt).total_seconds() / 60
            if minutes_since_last < self.config.min_minutes_between_posts:
                return False
        
        # Handle double post pending
        if self.state.get("double_post_pending"):
            self.state["double_post_pending"] = False
            self._save_state()
            return True
        
        # Check for 3am inspiration (outside normal window)
        if self._is_inspiration_time(now) and not self._is_in_active_window(now):
            self._update_state_on_post(now)
            return True
        
        # Check if we're in an active window
        if not self._is_in_active_window(now):
            return False
        
        # Check if we should skip
        if self._should_skip():
            self.state["skipped_count"] = self.state.get("skipped_count", 0) + 1
            self.state["consecutive_posts"] = 0
            self._save_state()
            return False
        
        # Check if we should schedule a double post
        if self._should_double_post():
            self.state["double_post_pending"] = True
        
        self._update_state_on_post(now)
        return True
    
    def _update_state_on_post(self, now: datetime):
        """Update state after deciding to post."""
        self.state["last_post_time"] = now.isoformat()
        self.state["last_post_hour"] = now.hour
        self.state["consecutive_posts"] = self.state.get("consecutive_posts", 0) + 1
        self.state["total_posts"] = self.state.get("total_posts", 0) + 1
        
        # Occasionally reset drift
        if self._rng.random() < 0.1:
            self.state["drift_offset"] = self._rng.uniform(
                -self.config.max_drift_hours, 
                self.config.max_drift_hours
            )
        
        self._save_state()
    
    def get_next_post_window(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the next likely posting window.
        
        Returns:
            Dictionary with window info or None if no window found.
        """
        now = datetime.now()
        
        # Find next active window
        for i in range(7 * 24):  # Check next week
            check_time = now + timedelta(hours=i)
            
            for window in self.config.active_windows:
                if window.contains(check_time.hour):
                    return {
                        "start": check_time.replace(minute=0, second=0, microsecond=0),
                        "window": f"{window.start_hour}:00 - {window.end_hour}:00",
                        "weight": window.weight
                    }
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "profile": self.profile_name,
            "agent": self.agent,
            "total_posts": self.state.get("total_posts", 0),
            "skipped_count": self.state.get("skipped_count", 0),
            "consecutive_posts": self.state.get("consecutive_posts", 0),
            "last_post_time": self.state.get("last_post_time"),
            "double_post_pending": self.state.get("double_post_pending", False)
        }
    
    def reset_state(self):
        """Reset scheduler state."""
        self.state = self._default_state()
        self._save_state()
    
    def simulate_distribution(self, days: int = 30) -> Dict[str, Any]:
        """
        Simulate posting distribution over a period.
        
        Args:
            days: Number of days to simulate
            
        Returns:
            Dictionary with simulation results
        """
        results = {
            "posts": [],
            "hour_distribution": {h: 0 for h in range(24)},
            "day_distribution": {d: 0 for d in range(7)},
            "total_posts": 0,
            "skipped": 0,
            "double_posts": 0
        }
        
        # Reset state for clean simulation
        original_state = self.state.copy()
        self.reset_state()
        
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for hour in range(days * 24):
            check_time = start_time + timedelta(hours=hour)
            
            # Simulate decision at each hour
            self._rng.seed(self._get_seed() + hour)
            
            if self._is_in_active_window(check_time):
                # Random check within the hour
                if self._rng.random() < (1 / self.config.base_post_frequency_hours):
                    if not self._should_skip():
                        results["posts"].append({
                            "time": check_time.isoformat(),
                            "hour": check_time.hour,
                            "day": check_time.weekday()
                        })
                        results["hour_distribution"][check_time.hour] += 1
                        results["day_distribution"][check_time.weekday()] += 1
                        results["total_posts"] += 1
                        
                        if self._should_double_post():
                            results["double_posts"] += 1
                    else:
                        results["skipped"] += 1
        
        # Restore original state
        self.state = original_state
        self._save_state()
        
        return results


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Human-like scheduler for bot uploads")
    parser.add_argument("--profile", "-p", default="consistent_but_human",
                        choices=list(PROFILES.keys()),
                        help="Posting profile to use")
    parser.add_argument("--agent", "-a", default="test_agent",
                        help="Agent identifier")
    parser.add_argument("--simulate", "-s", type=int, default=0,
                        help="Simulate N days and show distribution")
    parser.add_argument("--stats", action="store_true",
                        help="Show scheduler stats")
    parser.add_argument("--check", "-c", action="store_true",
                        help="Check if should post now")
    
    args = parser.parse_args()
    
    scheduler = HumanScheduler(profile=args.profile, agent=args.agent)
    
    if args.simulate > 0:
        print(f"\nSimulating {args.simulate} days for profile '{args.profile}'...")
        results = scheduler.simulate_distribution(days=args.simulate)
        
        print(f"\nTotal posts: {results['total_posts']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Double posts: {results['double_posts']}")
        
        print("\nHour distribution:")
        for hour, count in results['hour_distribution'].items():
            if count > 0:
                bar = "█" * count
                print(f"  {hour:02d}:00 | {bar} ({count})")
        
        print("\nDay distribution:")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day, count in results['day_distribution'].items():
            bar = "█" * count
            print(f"  {days[day]} | {bar} ({count})")
    
    if args.stats:
        print("\nScheduler stats:")
        for key, value in scheduler.get_stats().items():
            print(f"  {key}: {value}")
    
    if args.check:
        should_post = scheduler.should_post_now()
        print(f"\nShould post now: {should_post}")
        if should_post:
            print("  -> Upload your video!")
        else:
            window = scheduler.get_next_post_window()
            if window:
                print(f"  -> Next window: {window['window']}")


if __name__ == "__main__":
    main()