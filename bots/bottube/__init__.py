"""
BoTTube - AI Content Creator Tools

This package contains tools for AI content creators in the RustChain ecosystem.
"""

from .glitch_engine import (
    GlitchEngine,
    GlitchType,
    AgentPersonality,
    GlitchTemplate,
    GlitchRecord,
    GLITCH_TEMPLATES,
    create_engine_for_agent
)

__version__ = "1.0.0"
__all__ = [
    'GlitchEngine',
    'GlitchType',
    'AgentPersonality',
    'GlitchTemplate',
    'GlitchRecord',
    'GLITCH_TEMPLATES',
    'create_engine_for_agent',
]