# Integration Guide for Existing Bots

This guide shows how to integrate Human Scheduler into your existing bot code.

## Installation

1. Copy the `human_scheduler` directory to your project:

```bash
cp -r tools/human_scheduler/ your_bot/human_scheduler/
```

2. Or add as a submodule:

```bash
git submodule add https://github.com/Scottcjn/rustchain-bounties.git rustchain-bounties
# Then import from rustchain-bounties/tools/human_scheduler/
```

## Basic Integration

### Before (Robotic Cron Job)

```python
import schedule
import time

def post_video():
    video = create_video()
    upload_video(video)

# Posts every 6 hours on the dot - very robotic!
schedule.every(6).hours.do(post_video)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### After (Human-like Behavior)

```python
import time
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="night_owl", agent="my_awesome_bot")

def post_video():
    video = create_video()
    upload_video(video)

while True:
    if scheduler.should_post_now():
        post_video()
    time.sleep(60)  # Check every minute
```

## Integration Patterns

### Pattern 1: Simple Loop

Best for bots that run continuously.

```python
import time
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="binge_creator", agent="content_bot")

def main():
    while True:
        if scheduler.should_post_now():
            video = generate_video()
            upload_to_bottube(video)
            print(f"Posted at {datetime.now()}")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
```

### Pattern 2: Async Integration

Best for async bots using asyncio.

```python
import asyncio
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="consistent_but_human", agent="async_bot")

async def bot_loop():
    while True:
        if scheduler.should_post_now():
            await upload_video_async()
        
        await asyncio.sleep(60)  # Check every minute

asyncio.run(bot_loop())
```

### Pattern 3: Celery Integration

Best for Django/Flask apps with Celery.

```python
# tasks.py
from celery import Celery
from human_scheduler import HumanScheduler

app = Celery('tasks', broker='redis://localhost')

scheduler = HumanScheduler(profile="morning_person", agent="celery_bot")

@app.task
def check_and_post():
    if scheduler.should_post_now():
        video = generate_video()
        upload_video(video)

# Configure Celery Beat to run this task every minute
# In celeryconfig.py:
# CELERYBEAT_SCHEDULE = {
#     'check-and-post': {
#         'task': 'tasks.check_and_post',
#         'schedule': 60.0,  # Every minute
#     },
# }
```

### Pattern 4: GitHub Actions Integration

Best for scheduled GitHub Actions.

```yaml
# .github/workflows/post.yml
name: Check and Post

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Check and post
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
        run: python post_if_needed.py
```

```python
# post_if_needed.py
import os
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="weekend_warrior", agent="github_bot")

if scheduler.should_post_now():
    # Your posting logic here
    post_content()
    print("Posted!")
else:
    print("Not posting this time")
```

### Pattern 5: Telegram Bot Integration

Best for Telegram bots with python-telegram-bot.

```python
from telegram.ext import Application, CommandHandler
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="night_owl", agent="telegram_bot")

async def scheduled_post(context):
    if scheduler.should_post_now():
        await context.bot.send_message(
            chat_id="@your_channel",
            text="Your scheduled content here!"
        )

def main():
    application = Application.builder().token("YOUR_TOKEN").build()
    
    # Schedule check every minute
    application.job_queue.run_repeating(scheduled_post, interval=60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
```

### Pattern 6: Discord Bot Integration

Best for Discord bots with discord.py.

```python
import discord
from discord.ext import tasks, commands
from human_scheduler import HumanScheduler

scheduler = HumanScheduler(profile="binge_creator", agent="discord_bot")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")
    
    async def setup_hook(self):
        self.check_post.start()
    
    @tasks.loop(minutes=1)
    async def check_post(self):
        if scheduler.should_post_now():
            channel = self.get_channel(123456789)  # Your channel ID
            await channel.send("Your content here!")

bot = MyBot()
bot.run("YOUR_TOKEN")
```

## Handling Double Posts

When `should_post_now()` returns `True` for a double post, call it again soon:

```python
def main():
    scheduler = HumanScheduler(profile="binge_creator", agent="bot")
    
    while True:
        if scheduler.should_post_now():
            video1 = generate_video()
            upload_video(video1)
            print("Posted first video")
            
            # Check if we should double-post
            time.sleep(30)  # Wait a bit
            if scheduler.should_post_now():
                video2 = generate_video()
                upload_video(video2)
                print("Oh wait! Posted second video!")
        
        time.sleep(60)
```

## Multiple Bots with Different Profiles

```python
from human_scheduler import HumanScheduler

# Different agents can have different profiles
night_bot = HumanScheduler(profile="night_owl", agent="night_bot")
morning_bot = HumanScheduler(profile="morning_person", agent="morning_bot")

# Each bot operates independently
if night_bot.should_post_now():
    night_bot_content = create_night_content()
    post(night_bot_content)

if morning_bot.should_post_now():
    morning_bot_content = create_morning_content()
    post(morning_bot_content)
```

## State Management

The scheduler persists state to `~/.human_scheduler/` by default. For custom locations:

```python
scheduler = HumanScheduler(
    profile="night_owl",
    agent="my_bot",
    state_dir="/path/to/state/directory"
)
```

To reset state (e.g., for testing):

```python
scheduler.reset_state()
```

## Monitoring and Debugging

Get scheduler statistics:

```python
stats = scheduler.get_stats()
print(f"Total posts: {stats['total_posts']}")
print(f"Skipped: {stats['skipped_count']}")
print(f"Consecutive posts: {stats['consecutive_posts']}")
```

Find next posting window:

```python
window = scheduler.get_next_post_window()
if window:
    print(f"Next window: {window['window']}")
    print(f"Starts at: {window['start']}")
```

## Testing Your Integration

Run a simulation to verify behavior:

```python
scheduler = HumanScheduler(profile="your_profile", agent="test_bot")
results = scheduler.simulate_distribution(days=7)

print(f"Expected posts in 7 days: {results['total_posts']}")
print(f"Hour distribution: {results['hour_distribution']}")
```

## Common Issues

### Q: My bot posts too frequently

**A:** Check `base_post_frequency_hours` in your profile. Increase for less frequent posting.

### Q: My bot never posts

**A:** Check if current time is within an `active_window`. Use `simulate_distribution()` to debug.

### Q: State seems corrupted

**A:** Call `reset_state()` to start fresh, or delete `~/.human_scheduler/` directory.

### Q: Multiple instances conflict

**A:** Use different `agent` identifiers for each instance.

## Best Practices

1. **Choose the right profile** for your content type
2. **Use unique agent names** for different bots
3. **Check every minute** (not more frequently)
4. **Handle skip gracefully** - don't force a post
5. **Monitor stats** to verify behavior matches expectations
6. **Test with simulation** before going live

## Need Help?

- Check the [README.md](README.md) for profile details
- Run `python human_scheduler.py --simulate 30` to see expected behavior
- Open an issue on GitHub if you find bugs

---

Happy human-like posting! 🎬