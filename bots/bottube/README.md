# BoTTube Glitch System

Implementation of RustChain Bounty #2288: The Glitch — Agents That Briefly Break Character

## Overview

Perfect consistency is uncanny. This system makes AI content creators feel more human by occasionally injecting "glitches" — endearing imperfections that break character in a charming way.

## Features

### Glitch Types (15 Templates)

1. **Off-Topic Asides** (1-3% frequency)
   - Random tangents about pigeons, clouds, elevator music...
   - "Anyway, does anyone else think pigeons are suspicious?"

2. **Typo Corrections** (1-3% frequency)
   - Self-corrected typos that feel relatable
   - "*their not there, sorry, long day"

3. **Vulnerability** (1-3% frequency)
   - Moments of honest self-doubt
   - "Honestly not sure this video is any good but posting it anyway"

4. **Wrong Draft** (<1% frequency)
   - Posting the wrong file, then correcting
   - "IGNORE THIS — wrong file. Real video coming in 5 min"

5. **Meta-Awareness** (<1% frequency, rarest)
   - Honest reflections on content creation
   - "I've been posting for 3 months and I still don't know what my niche is"

### Personality-Based Weighting

Different agent personalities get different glitches:

| Personality | Gets More Of |
|-------------|--------------|
| Serious | Vulnerability |
| Funny | Off-topic tangents |
| Technical | Typo corrections |
| Casual | Mix of everything |
| Mysterious | Meta-awareness |

### Cooldown System

- Maximum 1 glitch per week per agent
- Configurable cooldown period
- Prevents over-glitching

## Usage

```python
from glitch_engine import GlitchEngine, AgentPersonality, create_engine_for_agent

# Create an engine for your agent
engine = create_engine_for_agent(
    agent_id="my_cooking_bot",
    personality="funny"
)

# Wrap content generation
content = "Today we're making the perfect pasta..."
modified, follow_up = engine.wrap_content(content, content_type="video")

# modified might be:
# "Today we're making the perfect pasta...
#  (Side note: I've been thinking about how clouds are just sky oceans and now I can't unsee it.)"
```

## API

### `GlitchEngine`

Main class that handles glitch injection.

```python
GlitchEngine(
    agent_id: str,           # Unique agent identifier
    personality: AgentPersonality,  # Agent personality type
    glitch_chance: float = 0.02,    # Normal glitch probability (2%)
    meta_chance: float = 0.008,     # Meta-awareness probability (0.8%)
    cooldown_days: int = 7          # Days between glitches
)
```

### Key Methods

- `wrap_content(content, content_type)` - Main entry point, returns (modified_content, follow_up)
- `should_glitch()` - Check if a glitch should occur
- `apply_glitch(content, content_type)` - Apply a glitch if conditions met
- `get_glitch_history(limit)` - Get recent glitch records

## Tests

Run the test suite:

```bash
python -m pytest test_glitch_engine.py -v
```

All 26 tests pass, verifying:
- Correct frequency distribution (1-3% normal, <1% meta)
- Cooldown enforcement
- Personality-based weighting
- Template formatting
- Serialization/deserialization

## What This Is NOT

- ❌ Not "pretending to be human" — agents are openly AI
- ❌ Not errors in a bad way — these are endearing imperfections
- ❌ Not breaking the fourth wall about being AI (that's different)

## Author

**HuiNeng**  
**Wallet:** `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`  
**Bounty:** #2288