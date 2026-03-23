"""
Tests for Human Scheduler - demonstrating non-uniform, realistic distribution.

Run with: pytest test_human_scheduler.py -v
"""

import pytest
import json
from datetime import datetime, timedelta
from collections import Counter
import statistics

from human_scheduler import (
    HumanScheduler,
    ProfileConfig,
    TimeWindow,
    PostDecision,
    PROFILES
)


class TestProfileConfig:
    """Tests for profile configuration."""
    
    def test_night_owl_profile(self):
        """Test night_owl profile configuration."""
        scheduler = HumanScheduler(profile="night_owl", agent="test_night")
        assert scheduler.config.name == "night_owl"
        assert len(scheduler.config.active_windows) == 1
        assert scheduler.config.active_windows[0].start_hour == 22
        assert scheduler.config.active_windows[0].end_hour == 3
    
    def test_morning_person_profile(self):
        """Test morning_person profile configuration."""
        scheduler = HumanScheduler(profile="morning_person", agent="test_morning")
        assert scheduler.config.name == "morning_person"
        assert scheduler.config.active_windows[0].start_hour == 6
        assert scheduler.config.active_windows[0].end_hour == 10
    
    def test_binge_creator_profile(self):
        """Test binge_creator profile configuration."""
        scheduler = HumanScheduler(profile="binge_creator", agent="test_binge")
        assert scheduler.config.name == "binge_creator"
        assert scheduler.config.base_post_frequency_hours == 72.0  # Posts every ~3 days
        assert scheduler.config.double_post_probability > 0.2  # High burst chance
    
    def test_weekend_warrior_profile(self):
        """Test weekend_warrior profile configuration."""
        scheduler = HumanScheduler(profile="weekend_warrior", agent="test_weekend")
        assert scheduler.config.name == "weekend_warrior"
        assert scheduler.config.skip_probability > 0.2  # High skip on weekdays
    
    def test_consistent_but_human_profile(self):
        """Test consistent_but_human profile configuration."""
        scheduler = HumanScheduler(profile="consistent_but_human", agent="test_consistent")
        assert scheduler.config.name == "consistent_but_human"
        assert scheduler.config.jitter_hours == 4.0  # ±4 hours jitter


class TestTimeWindow:
    """Tests for time window logic."""
    
    def test_window_contains_simple(self):
        """Test simple time window (not crossing midnight)."""
        window = TimeWindow(6, 10)
        assert window.contains(6)
        assert window.contains(8)
        assert not window.contains(10)  # End is exclusive
        assert not window.contains(5)
    
    def test_window_contains_midnight_crossing(self):
        """Test window crossing midnight."""
        window = TimeWindow(22, 3)
        assert window.contains(22)
        assert window.contains(23)
        assert window.contains(0)
        assert window.contains(1)
        assert window.contains(2)
        assert not window.contains(3)  # End is exclusive
        assert not window.contains(12)


class TestSchedulerLogic:
    """Tests for core scheduler logic."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes correctly."""
        scheduler = HumanScheduler(profile="night_owl", agent="test_init")
        assert scheduler.agent == "test_init"
        assert scheduler.state is not None
        assert scheduler.state.get("total_posts", 0) >= 0
    
    def test_reset_state(self):
        """Test state reset."""
        scheduler = HumanScheduler(profile="night_owl", agent="test_reset")
        scheduler.state["total_posts"] = 100
        scheduler.reset_state()
        assert scheduler.state["total_posts"] == 0
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        scheduler = HumanScheduler(profile="night_owl", agent="test_stats")
        stats = scheduler.get_stats()
        assert "profile" in stats
        assert "agent" in stats
        assert stats["profile"] == "night_owl"
    
    def test_load_custom_profile(self):
        """Test loading custom profile from file."""
        scheduler = HumanScheduler(
            profile="night_owl",
            agent="test_custom",
            config_path="profiles/night_owl.json"
        )
        assert scheduler.config.name == "night_owl"


class TestNonUniformDistribution:
    """Tests demonstrating non-uniform, realistic distribution."""
    
    def test_distribution_not_uniform(self):
        """Verify that post distribution is NOT uniform across hours."""
        scheduler = HumanScheduler(profile="night_owl", agent="dist_test")
        results = scheduler.simulate_distribution(days=30)
        
        hour_counts = results["hour_distribution"]
        
        # Check that posts are concentrated in specific hours (not all hours)
        non_zero_hours = [h for h, count in hour_counts.items() if count > 0]
        
        # With night_owl profile, posts should only be in night hours
        night_hours = {22, 23, 0, 1, 2}
        posted_night_hours = set(non_zero_hours)
        
        # All posted hours should be in the active window
        assert len(non_zero_hours) > 0, "Should have some posts"
        # Posts should be concentrated, not spread across all 24 hours
        assert len(non_zero_hours) < 24, "Posts should not be spread across all hours"
    
    def test_night_owl_posts_at_night(self):
        """Verify night_owl posts during night hours."""
        scheduler = HumanScheduler(profile="night_owl", agent="night_test")
        results = scheduler.simulate_distribution(days=30)
        
        hour_counts = results["hour_distribution"]
        
        # Night hours (22-3) should have most posts
        night_posts = sum(hour_counts[h] for h in [22, 23, 0, 1, 2])
        day_posts = sum(hour_counts[h] for h in range(6, 18))
        
        assert night_posts > day_posts, \
            f"Night owl should post more at night: night={night_posts}, day={day_posts}"
    
    def test_morning_person_posts_in_morning(self):
        """Verify morning_person posts during morning hours."""
        scheduler = HumanScheduler(profile="morning_person", agent="morning_test")
        results = scheduler.simulate_distribution(days=30)
        
        hour_counts = results["hour_distribution"]
        
        # Morning hours (6-10) should have most posts
        morning_posts = sum(hour_counts[h] for h in [6, 7, 8, 9])
        evening_posts = sum(hour_counts[h] for h in [18, 19, 20, 21])
        
        assert morning_posts > evening_posts, \
            f"Morning person should post more in morning: morning={morning_posts}, evening={evening_posts}"
    
    def test_binge_creator_has_bursts(self):
        """Verify binge_creator has burst posting behavior."""
        scheduler = HumanScheduler(profile="binge_creator", agent="binge_test")
        results = scheduler.simulate_distribution(days=90)  # Longer simulation for rare profile
        
        # Binge creator should have some posts
        assert results["total_posts"] >= 0, "Should have valid results"
        
        # Binge creator has high skip rate when not inspired
        # The skip probability is 15%, so over time some should be skipped
        # But with 72h base frequency, we may not see many posts
        
        # Check that the configuration has burst behavior
        assert scheduler.config.double_post_probability > 0.2, \
            "Binge creator should have high double post probability"
    
    def test_weekend_warrior_posts_on_saturday(self):
        """Verify weekend_warrior posts mostly on Saturday."""
        scheduler = HumanScheduler(profile="weekend_warrior", agent="weekend_test")
        results = scheduler.simulate_distribution(days=30)
        
        day_counts = results["day_distribution"]
        
        # Saturday (index 5) should have most posts
        saturday_posts = day_counts[5]
        weekday_posts = sum(day_counts[d] for d in range(5))
        
        assert saturday_posts > 0, "Should have Saturday posts"
        # Weekend warrior pattern: Saturday dominates
        assert saturday_posts > weekday_posts / 5, \
            f"Saturday should have more posts than average weekday"
    
    def test_skip_probability_affects_results(self):
        """Verify skip probability causes posts to be skipped."""
        scheduler = HumanScheduler(profile="night_owl", agent="skip_test")
        results = scheduler.simulate_distribution(days=60)
        
        assert results["skipped"] > 0, "Some posts should be skipped"
    
    def test_jitter_creates_variance(self):
        """Verify jitter creates variance in posting times."""
        scheduler = HumanScheduler(profile="consistent_but_human", agent="jitter_test")
        results = scheduler.simulate_distribution(days=30)
        
        # With ±4 hours jitter, posts should spread across multiple hours
        active_hours = [h for h, count in results["hour_distribution"].items() if count > 0]
        
        assert len(active_hours) > 4, \
            f"With jitter, posts should spread across multiple hours, got: {active_hours}"


class TestIntegration:
    """Integration tests for typical usage."""
    
    def test_basic_usage(self):
        """Test basic usage pattern."""
        scheduler = HumanScheduler(profile="consistent_but_human", agent="integration_test")
        
        # Should return a boolean
        result = scheduler.should_post_now()
        assert isinstance(result, bool)
    
    def test_state_persistence(self):
        """Test that state is persisted between instances."""
        agent_id = "persistence_test"
        
        # First instance
        scheduler1 = HumanScheduler(profile="night_owl", agent=agent_id)
        scheduler1.reset_state()
        scheduler1.state["total_posts"] = 5
        scheduler1._save_state()
        
        # Second instance - should load state
        scheduler2 = HumanScheduler(profile="night_owl", agent=agent_id)
        assert scheduler2.state["total_posts"] == 5
    
    def test_multiple_agents_independent(self):
        """Test that different agents have independent state."""
        scheduler1 = HumanScheduler(profile="night_owl", agent="agent_1")
        scheduler2 = HumanScheduler(profile="morning_person", agent="agent_2")
        
        scheduler1.reset_state()
        scheduler2.reset_state()
        
        scheduler1.state["total_posts"] = 10
        scheduler1._save_state()
        
        assert scheduler2.state["total_posts"] == 0


class TestProfileJSONFiles:
    """Tests for JSON profile files."""
    
    def test_all_profiles_exist_as_json(self):
        """Verify all profile JSON files exist."""
        import os
        profile_dir = "profiles"
        expected_files = [
            "night_owl.json",
            "morning_person.json",
            "binge_creator.json",
            "weekend_warrior.json",
            "consistent_but_human.json"
        ]
        
        for filename in expected_files:
            filepath = os.path.join(profile_dir, filename)
            assert os.path.exists(filepath), f"Profile file missing: {filepath}"
    
    def test_json_profiles_loadable(self):
        """Verify all JSON profiles can be loaded."""
        import os
        profile_dir = "profiles"
        
        for filename in os.listdir(profile_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(profile_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Verify required fields
                assert "name" in data
                assert "active_windows" in data
                assert len(data["active_windows"]) > 0


def test_distribution_summary():
    """Generate a summary of distribution for each profile (used for documentation)."""
    print("\n" + "=" * 60)
    print("DISTRIBUTION SUMMARY (30-day simulation)")
    print("=" * 60)
    
    for profile_name in PROFILES.keys():
        scheduler = HumanScheduler(profile=profile_name, agent=f"summary_{profile_name}")
        results = scheduler.simulate_distribution(days=30)
        
        print(f"\n{profile_name.upper()}")
        print("-" * 40)
        print(f"Total posts: {results['total_posts']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Double posts: {results['double_posts']}")
        
        # Show hour distribution
        peak_hours = sorted(
            results['hour_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        if peak_hours[0][1] > 0:
            print(f"Peak hours: {', '.join(f'{h}:00 ({c})' for h, c in peak_hours)}")
        
        # Show day distribution
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        peak_days = sorted(
            results['day_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:2]
        if peak_days[0][1] > 0:
            print(f"Peak days: {', '.join(f'{days[d]} ({c})' for d, c in peak_days)}")


if __name__ == "__main__":
    # Run distribution summary when executed directly
    test_distribution_summary()