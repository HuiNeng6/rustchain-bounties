# Human Scheduler

> Break the cron job feel. Make your bot post like a real human.

A human-like upload scheduler that introduces natural irregularities in posting patterns, making automated uploads feel more authentic and less robotic.

## Why?

Agents that post every 6 hours on the dot feel like cron jobs, not creators. Real humans:
- Post irregularly — bursts of content, then silence
- Never post at exactly the same minute twice
- Occasionally skip posts (life happens)
- Sometimes double-post ("oh wait, one more thing!")
- Have rare "3am inspiration" moments

## Features

✅ **5 Pre-built Profiles** - night_owl, morning_person, binge_creator, weekend_warrior, consistent_but_human

✅ **Natural Jitter** - Never posts at the exact same time

✅ **Skip Behavior** - Occasionally skips scheduled posts (life happens)

✅ **Double Posting** - "Oh wait, one more thing!" behavior

✅ **Inspiration Posts** - Rare posts outside normal patterns (3am inspiration)

✅ **State Persistence** - Remembers history across restarts

## Quick Start

```python
from human_scheduler import HumanScheduler

# Initialize scheduler
scheduler = HumanScheduler(profile="night_owl", agent="my_bot")

# Check if should post now
if scheduler.should_post_now():
    upload_video(...)
```

## Profiles

### 🦉 night_owl
Posts between 10pm-3am, sleeps until noon. A creature of the night.

**Best for:** Creative content that feels more authentic late at night

**Characteristics:**
- Active window: 22:00 - 03:00
- ~24 hours between posts
- 8% skip chance
- 5% double-post chance

### 🌅 morning_person
Posts 6am-10am, quiet evenings. Early bird gets the worm.

**Best for:** News, daily updates, professional content

**Characteristics:**
- Active window: 06:00 - 10:00
- ~24 hours between posts
- 5% skip chance
- Reliable morning presence

### 🎬 binge_creator
Drops 4-5 videos in 2 hours, then disappears for days. Creative bursts.

**Best for:** Artists, vloggers with irregular creative flow

**Characteristics:**
- Active windows: 19:00-21:00 (primary), 14:00-16:00 (secondary)
- ~72 hours between posting sessions
- 25% double-post chance during binges
- 15% skip chance (when not inspired)

### 🏋️ weekend_warrior
Barely posts weekdays, floods on Saturday. Work hard, post hard.

**Best for:** Hobbyist creators with day jobs

**Characteristics:**
- Active window: 10:00-22:00 on Saturday
- Rare weekday evening posts
- 30% skip chance on weekdays
- 15% double-post chance on weekends

### 📅 consistent_but_human
Roughly daily but ±4 hours jitter. Reliable but not robotic.

**Best for:** Brands, automated channels that need consistency

**Characteristics:**
- Broad active window: 09:00 - 23:00
- ±4 hours jitter around scheduled time
- 7% skip chance
- 4% double-post chance

## Custom Profiles

Create your own profile by defining a JSON file:

```json
{
    "name": "my_custom_profile",
    "description": "My custom posting behavior",
    "active_windows": [
        {"start_hour": 18, "end_hour": 22, "weight": 1.0}
    ],
    "base_post_frequency_hours": 24.0,
    "jitter_hours": 3.0,
    "skip_probability": 0.1,
    "double_post_probability": 0.05,
    "inspiration_post_probability": 0.02,
    "inspiration_hours": [2, 3],
    "min_minutes_between_posts": 30,
    "max_drift_hours": 2.0
}
```

Load it:

```python
scheduler = HumanScheduler(
    profile="custom",
    agent="my_bot",
    config_path="profiles/my_custom_profile.json"
)
```

## API Reference

### `HumanScheduler(profile, agent, config_path=None, state_dir=None)`

Initialize the scheduler.

**Parameters:**
- `profile` (str): Profile name (night_owl, morning_person, binge_creator, weekend_warrior, consistent_but_human)
- `agent` (str): Unique identifier for this bot
- `config_path` (str, optional): Path to custom profile JSON
- `state_dir` (str, optional): Directory to store state

### `should_post_now() -> bool`

Check if we should post now.

**Returns:** `True` if you should upload, `False` otherwise

### `get_stats() -> dict`

Get scheduler statistics.

**Returns:** Dictionary with total_posts, skipped_count, etc.

### `get_next_post_window() -> dict`

Get information about the next posting window.

### `simulate_distribution(days=30) -> dict`

Simulate posting distribution over a period.

**Parameters:**
- `days` (int): Number of days to simulate

**Returns:** Dictionary with hour_distribution, day_distribution, etc.

### `reset_state()`

Reset scheduler state.

## CLI Usage

```bash
# Check if should post now
python human_scheduler.py --profile night_owl --agent my_bot --check

# Simulate 30 days
python human_scheduler.py --profile binge_creator --simulate 30

# View stats
python human_scheduler.py --profile night_owl --agent my_bot --stats
```

## Testing

```bash
# Run all tests
pytest test_human_scheduler.py -v

# Run specific test
pytest test_human_scheduler.py::TestNonUniformDistribution -v

# Run distribution simulation
python test_human_scheduler.py
```

## Files

```
tools/human_scheduler/
├── human_scheduler.py       # Main scheduler engine
├── test_human_scheduler.py  # Tests demonstrating non-uniform distribution
├── README.md                # This file
├── INTEGRATION.md           # Integration guide for existing bots
└── profiles/
    ├── night_owl.json
    ├── morning_person.json
    ├── binge_creator.json
    ├── weekend_warrior.json
    └── consistent_but_human.json
```

## Example Output

```
NIGHT_OWL (30-day simulation)
----------------------------------------
Total posts: 28
Skipped: 3
Double posts: 2
Peak hours: 22:00 (8), 23:00 (7), 0:00 (6)
Peak days: Sat (5), Fri (4)

MORNING_PERSON (30-day simulation)
----------------------------------------
Total posts: 29
Skipped: 2
Double posts: 1
Peak hours: 7:00 (9), 8:00 (8), 6:00 (6)
Peak days: Tue (5), Thu (5)
```

## License

Apache 2.0

---

Built for RustChain Bounty #2284 | Creator: 慧能 | Wallet: `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`