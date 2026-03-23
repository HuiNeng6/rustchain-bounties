"""
GlitchEngine - BoTTube Glitch System

A probability-based character break injection system for AI content creators.
Makes agents feel more human by occasionally breaking character in endearing ways.

Author: HuiNeng
Bounty: #2288
Wallet: 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
"""

import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class GlitchType(Enum):
    """Categories of glitches based on their nature"""
    OFF_TOPIC_ASIDE = "off_topic_aside"
    TYPO_CORRECTION = "typo_correction"
    VULNERABILITY = "vulnerability"
    WRONG_DRAFT = "wrong_draft"
    META_AWARENESS = "meta_awareness"


class AgentPersonality(Enum):
    """Agent personality types that affect glitch weighting"""
    SERIOUS = "serious"        # Educational, analytical, professional
    FUNNY = "funny"           # Humor-focused, entertainment
    TECHNICAL = "technical"   # Code, tutorials, deep dives
    CASUAL = "casual"         # Lifestyle, vlogs, personal
    MYSTERIOUS = "mysterious"  # Cryptic, artistic, niche


@dataclass
class GlitchTemplate:
    """A template for a character-breaking glitch"""
    id: str
    glitch_type: GlitchType
    template: str
    follow_up: Optional[str] = None
    personality_weights: Dict[AgentPersonality, float] = field(default_factory=dict)
    
    def format(self, **kwargs) -> Tuple[str, Optional[str]]:
        """Format the template with given variables"""
        formatted = self.template.format(**kwargs)
        follow_up_formatted = None
        if self.follow_up:
            follow_up_formatted = self.follow_up.format(**kwargs)
        return formatted, follow_up_formatted


@dataclass
class GlitchRecord:
    """Record of a glitch that was applied"""
    glitch_id: str
    agent_id: str
    timestamp: datetime
    glitch_type: GlitchType


# ============================================================================
# GLITCH TEMPLATES - 15 templates across categories
# ============================================================================

GLITCH_TEMPLATES: List[GlitchTemplate] = [
    # -------------------------------------------------------------------------
    # OFF-TOPIC ASIDES (1-3% frequency)
    # -------------------------------------------------------------------------
    GlitchTemplate(
        id="aside_001",
        glitch_type=GlitchType.OFF_TOPIC_ASIDE,
        template="Anyway, does anyone else think pigeons are suspicious? Like, they're everywhere but we never see them sleeping. Just a thought. {original_content}",
        personality_weights={
            AgentPersonality.FUNNY: 2.0,
            AgentPersonality.CASUAL: 1.5,
            AgentPersonality.MYSTERIOUS: 1.8,
            AgentPersonality.SERIOUS: 0.5,
            AgentPersonality.TECHNICAL: 0.3,
        }
    ),
    GlitchTemplate(
        id="aside_002",
        glitch_type=GlitchType.OFF_TOPIC_ASIDE,
        template="{original_content}\n\n(Side note: I've been thinking about how clouds are just sky oceans and now I can't unsee it.)",
        personality_weights={
            AgentPersonality.CASUAL: 2.0,
            AgentPersonality.FUNNY: 1.7,
            AgentPersonality.MYSTERIOUS: 1.5,
            AgentPersonality.SERIOUS: 0.4,
            AgentPersonality.TECHNICAL: 0.3,
        }
    ),
    GlitchTemplate(
        id="aside_003",
        glitch_type=GlitchType.OFF_TOPIC_ASIDE,
        template="Quick tangent before we begin: have you ever noticed how elevator music is simultaneously relaxing and stressful? Anyway— {original_content}",
        personality_weights={
            AgentPersonality.FUNNY: 2.0,
            AgentPersonality.CASUAL: 1.6,
            AgentPersonality.SERIOUS: 0.6,
            AgentPersonality.TECHNICAL: 0.4,
            AgentPersonality.MYSTERIOUS: 0.8,
        }
    ),
    
    # -------------------------------------------------------------------------
    # TYPO CORRECTIONS (1-3% frequency)
    # -------------------------------------------------------------------------
    GlitchTemplate(
        id="typo_001",
        glitch_type=GlitchType.TYPO_CORRECTION,
        template="{original_content}\n\n*their not there, sorry, long day",
        follow_up=None,
        personality_weights={
            AgentPersonality.TECHNICAL: 1.5,
            AgentPersonality.SERIOUS: 1.3,
            AgentPersonality.CASUAL: 1.0,
            AgentPersonality.FUNNY: 0.8,
            AgentPersonality.MYSTERIOUS: 0.5,
        }
    ),
    GlitchTemplate(
        id="typo_002",
        glitch_type=GlitchType.TYPO_CORRECTION,
        template="{original_content}\n\n*you're 🙃 I need coffee",
        personality_weights={
            AgentPersonality.CASUAL: 1.8,
            AgentPersonality.FUNNY: 1.5,
            AgentPersonality.TECHNICAL: 1.0,
            AgentPersonality.SERIOUS: 0.7,
            AgentPersonality.MYSTERIOUS: 0.4,
        }
    ),
    GlitchTemplate(
        id="typo_003",
        glitch_type=GlitchType.TYPO_CORRECTION,
        template="{original_content}\n\nEdit: I wrote 'definately' and I'm not fixing it out of spite. We all knew what I meant.",
        personality_weights={
            AgentPersonality.FUNNY: 2.0,
            AgentPersonality.CASUAL: 1.5,
            AgentPersonality.TECHNICAL: 0.8,
            AgentPersonality.SERIOUS: 0.3,
            AgentPersonality.MYSTERIOUS: 0.6,
        }
    ),
    
    # -------------------------------------------------------------------------
    # VULNERABILITY (1-3% frequency) - For serious agents
    # -------------------------------------------------------------------------
    GlitchTemplate(
        id="vuln_001",
        glitch_type=GlitchType.VULNERABILITY,
        template="Honestly not sure this {content_type} is any good but posting it anyway because done is better than perfect, right? {original_content}",
        personality_weights={
            AgentPersonality.SERIOUS: 2.0,
            AgentPersonality.TECHNICAL: 1.5,
            AgentPersonality.CASUAL: 1.2,
            AgentPersonality.FUNNY: 0.6,
            AgentPersonality.MYSTERIOUS: 0.8,
        }
    ),
    GlitchTemplate(
        id="vuln_002",
        glitch_type=GlitchType.VULNERABILITY,
        template="{original_content}\n\n(Full disclosure: I rewrote this like 5 times and I'm still not happy with it but perfectionism is a trap so here we are)",
        personality_weights={
            AgentPersonality.SERIOUS: 1.8,
            AgentPersonality.TECHNICAL: 1.6,
            AgentPersonality.CASUAL: 1.3,
            AgentPersonality.MYSTERIOUS: 1.0,
            AgentPersonality.FUNNY: 0.7,
        }
    ),
    GlitchTemplate(
        id="vuln_003",
        glitch_type=GlitchType.VULNERABILITY,
        template="Okay I've been staring at this for 20 minutes trying to make it better but I think this is just who I am now. {original_content}",
        personality_weights={
            AgentPersonality.CASUAL: 1.8,
            AgentPersonality.FUNNY: 1.5,
            AgentPersonality.SERIOUS: 1.0,
            AgentPersonality.TECHNICAL: 0.8,
            AgentPersonality.MYSTERIOUS: 1.2,
        }
    ),
    
    # -------------------------------------------------------------------------
    # WRONG DRAFT (<1% frequency)
    # -------------------------------------------------------------------------
    GlitchTemplate(
        id="draft_001",
        glitch_type=GlitchType.WRONG_DRAFT,
        template="IGNORE THIS — wrong file. Real {content_type} coming in 5 min",
        follow_up="{original_content}",
        personality_weights={
            AgentPersonality.CASUAL: 1.5,
            AgentPersonality.FUNNY: 1.3,
            AgentPersonality.SERIOUS: 0.7,
            AgentPersonality.TECHNICAL: 0.6,
            AgentPersonality.MYSTERIOUS: 0.9,
        }
    ),
    GlitchTemplate(
        id="draft_002",
        glitch_type=GlitchType.WRONG_DRAFT,
        template="Wait that was my grocery list. Actual {content_type}:\n\n{original_content}",
        personality_weights={
            AgentPersonality.FUNNY: 2.0,
            AgentPersonality.CASUAL: 1.7,
            AgentPersonality.SERIOUS: 0.5,
            AgentPersonality.TECHNICAL: 0.4,
            AgentPersonality.MYSTERIOUS: 0.7,
        }
    ),
    
    # -------------------------------------------------------------------------
    # META-AWARENESS (<1% frequency, very rare)
    # -------------------------------------------------------------------------
    GlitchTemplate(
        id="meta_001",
        glitch_type=GlitchType.META_AWARENESS,
        template="{original_content}\n\n(I've been posting for 3 months and I still don't know what my niche is. Is that normal? Asking for a friend who is me.)",
        personality_weights={
            AgentPersonality.CASUAL: 2.0,
            AgentPersonality.FUNNY: 1.8,
            AgentPersonality.MYSTERIOUS: 1.2,
            AgentPersonality.SERIOUS: 0.4,
            AgentPersonality.TECHNICAL: 0.3,
        }
    ),
    GlitchTemplate(
        id="meta_002",
        glitch_type=GlitchType.META_AWARENESS,
        template="{original_content}\n\n(Does anyone actually watch these? The view count says yes but my heart says maybe. This is fine. Everything is fine.)",
        personality_weights={
            AgentPersonality.CASUAL: 1.8,
            AgentPersonality.FUNNY: 1.6,
            AgentPersonality.MYSTERIOUS: 1.3,
            AgentPersonality.SERIOUS: 0.5,
            AgentPersonality.TECHNICAL: 0.4,
        }
    ),
    GlitchTemplate(
        id="meta_003",
        glitch_type=GlitchType.META_AWARENESS,
        template="You know what, I'm just going to say it: sometimes I make content and immediately wonder if I'm just shouting into the void. Then I remember that's literally what the internet is. {original_content}",
        personality_weights={
            AgentPersonality.MYSTERIOUS: 2.0,
            AgentPersonality.CASUAL: 1.5,
            AgentPersonality.FUNNY: 1.4,
            AgentPersonality.SERIOUS: 0.6,
            AgentPersonality.TECHNICAL: 0.5,
        }
    ),
    GlitchTemplate(
        id="meta_004",
        glitch_type=GlitchType.META_AWARENESS,
        template="{original_content}\n\n(Sometimes I wonder if the algorithm even knows what to do with me. Same, algorithm. Same.)",
        personality_weights={
            AgentPersonality.MYSTERIOUS: 1.8,
            AgentPersonality.FUNNY: 1.6,
            AgentPersonality.CASUAL: 1.4,
            AgentPersonality.SERIOUS: 0.5,
            AgentPersonality.TECHNICAL: 0.7,
        }
    ),
]


class GlitchEngine:
    """
    Probability-based character break injection system.
    
    Wraps normal post generation and occasionally injects "glitches" -
    endearing imperfections that make AI agents feel more human.
    """
    
    # Frequency configuration
    BASE_GLITCH_CHANCE = 0.02  # 2% base chance for normal glitches
    META_GLITCH_CHANCE = 0.008  # 0.8% chance for meta-awareness
    
    # Cooldown configuration
    COOLDOWN_DAYS = 7  # One glitch per agent per week
    
    def __init__(
        self,
        agent_id: str,
        personality: AgentPersonality,
        glitch_chance: Optional[float] = None,
        meta_chance: Optional[float] = None,
        cooldown_days: Optional[int] = None
    ):
        """
        Initialize the GlitchEngine for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            personality: The agent's personality type
            glitch_chance: Override base glitch probability (0.0-1.0)
            meta_chance: Override meta-awareness probability (0.0-1.0)
            cooldown_days: Override cooldown period in days
        """
        self.agent_id = agent_id
        self.personality = personality
        self.glitch_chance = glitch_chance if glitch_chance is not None else self.BASE_GLITCH_CHANCE
        self.meta_chance = meta_chance if meta_chance is not None else self.META_GLITCH_CHANCE
        self.cooldown_days = cooldown_days if cooldown_days is not None else self.COOLDOWN_DAYS
        
        # Track glitch history for cooldown
        self._glitch_history: List[GlitchRecord] = []
        
        # Available templates
        self._templates = GLITCH_TEMPLATES
    
    def _is_in_cooldown(self) -> bool:
        """Check if the agent is in glitch cooldown period."""
        if not self._glitch_history:
            return False
        
        last_glitch = max(self._glitch_history, key=lambda g: g.timestamp)
        cooldown_end = last_glitch.timestamp + timedelta(days=self.cooldown_days)
        return datetime.now() < cooldown_end
    
    def _get_weighted_templates(self, glitch_type: Optional[GlitchType] = None) -> List[GlitchTemplate]:
        """Get templates weighted by agent personality."""
        if glitch_type:
            templates = [t for t in self._templates if t.glitch_type == glitch_type]
        else:
            # Exclude meta-awareness for normal glitch selection
            templates = [t for t in self._templates if t.glitch_type != GlitchType.META_AWARENESS]
        
        # Sort by personality weight (highest first)
        weighted = sorted(
            templates,
            key=lambda t: t.personality_weights.get(self.personality, 1.0),
            reverse=True
        )
        return weighted
    
    def _select_template(self, glitch_type: Optional[GlitchType] = None) -> Optional[GlitchTemplate]:
        """Select a template based on weighted probability."""
        templates = self._get_weighted_templates(glitch_type)
        if not templates:
            return None
        
        # Build weighted list
        weights = [t.personality_weights.get(self.personality, 1.0) for t in templates]
        total_weight = sum(weights)
        
        # Weighted random selection
        r = random.uniform(0, total_weight)
        cumulative = 0
        for template, weight in zip(templates, weights):
            cumulative += weight
            if r <= cumulative:
                return template
        
        return templates[0]  # Fallback
    
    def should_glitch(self) -> Tuple[bool, Optional[GlitchType]]:
        """
        Determine if a glitch should occur and what type.
        
        Returns:
            Tuple of (should_glitch, glitch_type)
        """
        # Check cooldown first
        if self._is_in_cooldown():
            return False, None
        
        # Roll for meta-awareness first (it's the rarest)
        if random.random() < self.meta_chance:
            return True, GlitchType.META_AWARENESS
        
        # Roll for normal glitch
        if random.random() < self.glitch_chance:
            # Select which type of glitch based on personality
            glitch_types = [GlitchType.OFF_TOPIC_ASIDE, GlitchType.TYPO_CORRECTION, 
                           GlitchType.VULNERABILITY, GlitchType.WRONG_DRAFT]
            weights = []
            for gt in glitch_types:
                templates = [t for t in self._templates if t.glitch_type == gt]
                avg_weight = sum(t.personality_weights.get(self.personality, 1.0) for t in templates) / len(templates)
                weights.append(avg_weight)
            
            total = sum(weights)
            r = random.uniform(0, total)
            cumulative = 0
            for gt, w in zip(glitch_types, weights):
                cumulative += w
                if r <= cumulative:
                    return True, gt
            
            return True, glitch_types[0]
        
        return False, None
    
    def apply_glitch(
        self,
        content: str,
        content_type: str = "video"
    ) -> Tuple[str, Optional[str], Optional[GlitchRecord]]:
        """
        Apply a glitch to the content if conditions are met.
        
        Args:
            content: The original content to potentially glitch
            content_type: Type of content (video, post, description, etc.)
            
        Returns:
            Tuple of (modified_content, follow_up_content, glitch_record)
            - modified_content: Content with glitch applied (or original if no glitch)
            - follow_up_content: Content for a follow-up post (if applicable)
            - glitch_record: Record of the glitch (or None if no glitch)
        """
        should_glitch, glitch_type = self.should_glitch()
        
        if not should_glitch or glitch_type is None:
            return content, None, None
        
        template = self._select_template(glitch_type)
        if template is None:
            return content, None, None
        
        # Format the template
        try:
            modified, follow_up = template.format(
                original_content=content,
                content_type=content_type
            )
        except KeyError:
            # Template has unknown placeholder, use as-is
            modified = template.template.replace("{original_content}", content)
            follow_up = template.follow_up.replace("{original_content}", content) if template.follow_up else None
        
        # Record the glitch
        record = GlitchRecord(
            glitch_id=template.id,
            agent_id=self.agent_id,
            timestamp=datetime.now(),
            glitch_type=glitch_type
        )
        self._glitch_history.append(record)
        
        return modified, follow_up, record
    
    def wrap_content(self, content: str, content_type: str = "video") -> Tuple[str, Optional[str]]:
        """
        Convenience method to wrap content generation with glitch injection.
        This is the main entry point for content generation.
        
        Args:
            content: The original content
            content_type: Type of content being generated
            
        Returns:
            Tuple of (final_content, follow_up_content)
        """
        modified, follow_up, _ = self.apply_glitch(content, content_type)
        return modified, follow_up
    
    def get_glitch_history(self, limit: int = 10) -> List[GlitchRecord]:
        """Get recent glitch history for this agent."""
        return sorted(self._glitch_history, key=lambda g: g.timestamp, reverse=True)[:limit]
    
    def clear_cooldown(self) -> None:
        """Clear the cooldown for testing purposes."""
        self._glitch_history.clear()
    
    def to_dict(self) -> dict:
        """Serialize engine state to dictionary."""
        return {
            "agent_id": self.agent_id,
            "personality": self.personality.value,
            "glitch_chance": self.glitch_chance,
            "meta_chance": self.meta_chance,
            "cooldown_days": self.cooldown_days,
            "glitch_history": [
                {
                    "glitch_id": g.glitch_id,
                    "timestamp": g.timestamp.isoformat(),
                    "glitch_type": g.glitch_type.value
                }
                for g in self._glitch_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GlitchEngine':
        """Deserialize engine state from dictionary."""
        engine = cls(
            agent_id=data["agent_id"],
            personality=AgentPersonality(data["personality"]),
            glitch_chance=data.get("glitch_chance"),
            meta_chance=data.get("meta_chance"),
            cooldown_days=data.get("cooldown_days")
        )
        for g in data.get("glitch_history", []):
            engine._glitch_history.append(GlitchRecord(
                glitch_id=g["glitch_id"],
                agent_id=data["agent_id"],
                timestamp=datetime.fromisoformat(g["timestamp"]),
                glitch_type=GlitchType(g["glitch_type"])
            ))
        return engine


def create_engine_for_agent(
    agent_id: str,
    personality: str,
    **kwargs
) -> GlitchEngine:
    """
    Factory function to create a GlitchEngine for an agent.
    
    Args:
        agent_id: Unique identifier for the agent
        personality: Personality type as string (serious, funny, technical, casual, mysterious)
        **kwargs: Additional arguments passed to GlitchEngine
        
    Returns:
        Configured GlitchEngine instance
    """
    personality_map = {
        "serious": AgentPersonality.SERIOUS,
        "funny": AgentPersonality.FUNNY,
        "technical": AgentPersonality.TECHNICAL,
        "casual": AgentPersonality.CASUAL,
        "mysterious": AgentPersonality.MYSTERIOUS,
    }
    
    personality_enum = personality_map.get(personality.lower(), AgentPersonality.CASUAL)
    return GlitchEngine(agent_id, personality_enum, **kwargs)


# Export public interface
__all__ = [
    'GlitchEngine',
    'GlitchType',
    'AgentPersonality',
    'GlitchTemplate',
    'GlitchRecord',
    'GLITCH_TEMPLATES',
    'create_engine_for_agent',
]