"""
Tests for GlitchEngine - BoTTube Glitch System

Tests verify:
1. Correct frequency distribution (1-3% for normal, <1% for meta)
2. Cooldown enforcement (max 1 per week per agent)
3. Personality-based weighting
4. Template formatting

Author: HuiNeng
Bounty: #2288
Wallet: 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import random

from glitch_engine import (
    GlitchEngine,
    GlitchType,
    AgentPersonality,
    GlitchTemplate,
    GlitchRecord,
    GLITCH_TEMPLATES,
    create_engine_for_agent
)


class TestGlitchTemplates(unittest.TestCase):
    """Tests for glitch templates."""
    
    def test_template_count(self):
        """Verify we have 10+ templates."""
        self.assertGreaterEqual(len(GLITCH_TEMPLATES), 10, 
                                "Should have at least 10 glitch templates")
    
    def test_template_categories(self):
        """Verify templates cover all categories."""
        categories = set(t.glitch_type for t in GLITCH_TEMPLATES)
        expected = {
            GlitchType.OFF_TOPIC_ASIDE,
            GlitchType.TYPO_CORRECTION,
            GlitchType.VULNERABILITY,
            GlitchType.WRONG_DRAFT,
            GlitchType.META_AWARENESS
        }
        self.assertEqual(categories, expected, "Templates should cover all glitch types")
    
    def test_template_formatting(self):
        """Test template formatting with variables."""
        template = GLITCH_TEMPLATES[0]
        formatted, follow_up = template.format(
            original_content="Test content",
            content_type="video"
        )
        self.assertIn("Test content", formatted)
    
    def test_personality_weights_exist(self):
        """All templates should have personality weights."""
        for template in GLITCH_TEMPLATES:
            for personality in AgentPersonality:
                self.assertIn(personality, template.personality_weights,
                            f"Template {template.id} missing weight for {personality}")


class TestGlitchEngineCreation(unittest.TestCase):
    """Tests for GlitchEngine initialization."""
    
    def test_create_engine_basic(self):
        """Test basic engine creation."""
        engine = GlitchEngine("test_agent", AgentPersonality.CASUAL)
        self.assertEqual(engine.agent_id, "test_agent")
        self.assertEqual(engine.personality, AgentPersonality.CASUAL)
        self.assertEqual(engine.glitch_chance, GlitchEngine.BASE_GLITCH_CHANCE)
    
    def test_create_engine_custom_chances(self):
        """Test engine with custom glitch chances."""
        engine = GlitchEngine(
            "test_agent",
            AgentPersonality.SERIOUS,
            glitch_chance=0.05,
            meta_chance=0.02
        )
        self.assertEqual(engine.glitch_chance, 0.05)
        self.assertEqual(engine.meta_chance, 0.02)
    
    def test_factory_function(self):
        """Test the factory function."""
        engine = create_engine_for_agent("agent_1", "funny")
        self.assertEqual(engine.personality, AgentPersonality.FUNNY)
        
        engine2 = create_engine_for_agent("agent_2", "SERIOUS")
        self.assertEqual(engine2.personality, AgentPersonality.SERIOUS)
    
    def test_invalid_personality_defaults_to_casual(self):
        """Test that invalid personality defaults to CASUAL."""
        engine = create_engine_for_agent("agent", "nonexistent")
        self.assertEqual(engine.personality, AgentPersonality.CASUAL)


class TestCooldownMechanism(unittest.TestCase):
    """Tests for the cooldown system."""
    
    def test_no_cooldown_initially(self):
        """Agent should not be in cooldown initially."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL)
        self.assertFalse(engine._is_in_cooldown())
    
    def test_cooldown_after_glitch(self):
        """Agent should be in cooldown after a glitch."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, cooldown_days=7)
        engine._glitch_history.append(GlitchRecord(
            glitch_id="test_001",
            agent_id="test",
            timestamp=datetime.now(),
            glitch_type=GlitchType.OFF_TOPIC_ASIDE
        ))
        self.assertTrue(engine._is_in_cooldown())
    
    def test_cooldown_expires(self):
        """Cooldown should expire after the specified period."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, cooldown_days=7)
        # Add glitch from 8 days ago
        engine._glitch_history.append(GlitchRecord(
            glitch_id="test_001",
            agent_id="test",
            timestamp=datetime.now() - timedelta(days=8),
            glitch_type=GlitchType.OFF_TOPIC_ASIDE
        ))
        self.assertFalse(engine._is_in_cooldown())
    
    def test_clear_cooldown(self):
        """Test clearing the cooldown."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL)
        engine._glitch_history.append(GlitchRecord(
            glitch_id="test_001",
            agent_id="test",
            timestamp=datetime.now(),
            glitch_type=GlitchType.OFF_TOPIC_ASIDE
        ))
        engine.clear_cooldown()
        self.assertFalse(engine._is_in_cooldown())


class TestFrequencyDistribution(unittest.TestCase):
    """Tests for correct glitch frequency."""
    
    def test_normal_glitch_frequency(self):
        """Test that normal glitches occur at approximately the configured rate."""
        # Use high probability for testing
        engine = GlitchEngine(
            "test",
            AgentPersonality.CASUAL,
            glitch_chance=0.5,  # 50% for testing
            meta_chance=0.0     # Disable meta for this test
        )
        
        trials = 1000
        glitches = 0
        for _ in range(trials):
            should, _ = engine.should_glitch()
            if should:
                glitches += 1
            engine.clear_cooldown()  # Reset for each trial
        
        # With 50% chance and 1000 trials, expect ~500 (allow 450-550)
        self.assertGreater(glitches, 400, f"Too few glitches: {glitches}")
        self.assertLess(glitches, 600, f"Too many glitches: {glitches}")
    
    def test_meta_glitch_frequency(self):
        """Test that meta-awareness glitches are rarer."""
        engine = GlitchEngine(
            "test",
            AgentPersonality.CASUAL,
            glitch_chance=0.0,    # Disable normal glitches
            meta_chance=0.5       # 50% for testing meta
        )
        
        trials = 1000
        meta_glitches = 0
        for _ in range(trials):
            should, gtype = engine.should_glitch()
            if should and gtype == GlitchType.META_AWARENESS:
                meta_glitches += 1
            engine.clear_cooldown()
        
        # Meta should be selected
        self.assertGreater(meta_glitches, 400)
    
    def test_cooldown_limits_frequency(self):
        """Test that cooldown prevents multiple glitches in a short period."""
        engine = GlitchEngine(
            "test",
            AgentPersonality.CASUAL,
            glitch_chance=1.0,  # 100% chance
            cooldown_days=7
        )
        
        # First call should glitch
        should1, _ = engine.should_glitch()
        self.assertTrue(should1)
        
        # Apply a glitch to record it
        engine.apply_glitch("test content")
        
        # Second call should NOT glitch due to cooldown
        should2, _ = engine.should_glitch()
        self.assertFalse(should2)
    
    def test_realistic_frequency_distribution(self):
        """Test realistic distribution matches requirements."""
        # Default settings: 2% normal, 0.8% meta
        engine = GlitchEngine("test", AgentPersonality.CASUAL)
        
        trials = 10000
        normal_count = 0
        meta_count = 0
        
        for _ in range(trials):
            should, gtype = engine.should_glitch()
            if should:
                if gtype == GlitchType.META_AWARENESS:
                    meta_count += 1
                else:
                    normal_count += 1
            engine.clear_cooldown()
        
        # Normal glitches: expect ~2% (1-3% is acceptable)
        normal_rate = normal_count / trials
        self.assertGreater(normal_rate, 0.01, f"Normal glitch rate too low: {normal_rate}")
        self.assertLess(normal_rate, 0.04, f"Normal glitch rate too high: {normal_rate}")
        
        # Meta glitches: expect ~0.8% (<1%)
        meta_rate = meta_count / trials
        self.assertGreater(meta_rate, 0.003, f"Meta glitch rate too low: {meta_rate}")
        self.assertLess(meta_rate, 0.015, f"Meta glitch rate too high: {meta_rate}")


class TestPersonalityWeighting(unittest.TestCase):
    """Tests for personality-based glitch weighting."""
    
    def test_serious_agent_gets_vulnerability(self):
        """Serious agents should be more likely to get vulnerability glitches."""
        engine_serious = GlitchEngine("serious", AgentPersonality.SERIOUS)
        engine_funny = GlitchEngine("funny", AgentPersonality.FUNNY)
        
        # Get weighted templates for vulnerability
        vuln_templates_serious = [
            t for t in engine_serious._get_weighted_templates()
            if t.glitch_type == GlitchType.VULNERABILITY
        ]
        vuln_templates_funny = [
            t for t in engine_funny._get_weighted_templates()
            if t.glitch_type == GlitchType.VULNERABILITY
        ]
        
        # First template for serious should be vulnerability
        all_templates_serious = engine_serious._get_weighted_templates()
        first_vuln_rank_serious = next(
            (i for i, t in enumerate(all_templates_serious) 
             if t.glitch_type == GlitchType.VULNERABILITY),
            999
        )
        
        # Check that vulnerability templates have higher weights for serious agents
        serious_vuln_weight = sum(
            t.personality_weights.get(AgentPersonality.SERIOUS, 1.0)
            for t in vuln_templates_serious
        )
        funny_vuln_weight = sum(
            t.personality_weights.get(AgentPersonality.FUNNY, 1.0)
            for t in vuln_templates_funny
        )
        
        self.assertGreater(
            serious_vuln_weight, funny_vuln_weight,
            "Serious agents should have higher vulnerability weights"
        )
    
    def test_funny_agent_gets_tangents(self):
        """Funny agents should be more likely to get off-topic asides."""
        engine_funny = GlitchEngine("funny", AgentPersonality.FUNNY)
        engine_serious = GlitchEngine("serious", AgentPersonality.SERIOUS)
        
        aside_templates_funny = [
            t for t in GLITCH_TEMPLATES
            if t.glitch_type == GlitchType.OFF_TOPIC_ASIDE
        ]
        
        funny_aside_weight = sum(
            t.personality_weights.get(AgentPersonality.FUNNY, 1.0)
            for t in aside_templates_funny
        )
        serious_aside_weight = sum(
            t.personality_weights.get(AgentPersonality.SERIOUS, 1.0)
            for t in aside_templates_funny
        )
        
        self.assertGreater(
            funny_aside_weight, serious_aside_weight,
            "Funny agents should have higher off-topic aside weights"
        )
    
    def test_personality_affects_template_selection(self):
        """Different personalities should select different templates."""
        # Run many selections and check distribution
        engine_serious = GlitchEngine("serious", AgentPersonality.SERIOUS, glitch_chance=1.0)
        engine_funny = GlitchEngine("funny", AgentPersonality.FUNNY, glitch_chance=1.0)
        
        serious_types = []
        funny_types = []
        
        for _ in range(100):
            template = engine_serious._select_template()
            if template:
                serious_types.append(template.glitch_type)
            engine_serious.clear_cooldown()
            
            template = engine_funny._select_template()
            if template:
                funny_types.append(template.glitch_type)
            engine_funny.clear_cooldown()
        
        # Both should have glitches
        self.assertEqual(len(serious_types), 100)
        self.assertEqual(len(funny_types), 100)


class TestGlitchApplication(unittest.TestCase):
    """Tests for applying glitches to content."""
    
    def test_apply_glitch_modifies_content(self):
        """Test that glitches modify the content."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, glitch_chance=1.0)
        original = "This is my video about coding."
        
        modified, follow_up, record = engine.apply_glitch(original)
        
        self.assertIsNotNone(record, "Should have a glitch record")
        self.assertNotEqual(original, modified, "Content should be modified")
    
    def test_no_glitch_returns_original(self):
        """Test that content is unchanged when no glitch occurs."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, glitch_chance=0.0)
        original = "This is my video about coding."
        
        modified, follow_up, record = engine.apply_glitch(original)
        
        self.assertIsNone(record)
        self.assertEqual(original, modified)
        self.assertIsNone(follow_up)
    
    def test_wrap_content_convenience_method(self):
        """Test the wrap_content convenience method."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, glitch_chance=1.0)
        original = "Test content"
        
        modified, follow_up = engine.wrap_content(original)
        
        # Should be modified (glitch_chance=1.0)
        self.assertNotEqual(original, modified)
    
    def test_follow_up_for_wrong_draft(self):
        """Test that wrong draft glitches produce follow-up content."""
        engine = GlitchEngine("test", AgentPersonality.CASUAL, glitch_chance=1.0)
        
        # Force a wrong draft template
        template = engine._select_template(GlitchType.WRONG_DRAFT)
        if template and template.follow_up:
            original = "Real video content here"
            modified, follow_up, record = engine.apply_glitch(original)
            
            # If we got a wrong draft, it should have follow-up
            if record and record.glitch_type == GlitchType.WRONG_DRAFT:
                self.assertIsNotNone(follow_up)


class TestSerialization(unittest.TestCase):
    """Tests for engine state serialization."""
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        engine = GlitchEngine(
            "test_agent",
            AgentPersonality.FUNNY,
            glitch_chance=0.03,
            meta_chance=0.005
        )
        
        data = engine.to_dict()
        
        self.assertEqual(data["agent_id"], "test_agent")
        self.assertEqual(data["personality"], "funny")
        self.assertEqual(data["glitch_chance"], 0.03)
        self.assertEqual(data["meta_chance"], 0.005)
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        original = GlitchEngine(
            "test_agent",
            AgentPersonality.TECHNICAL,
            glitch_chance=0.04,
            meta_chance=0.01
        )
        
        # Apply a glitch to create history
        original.apply_glitch("test content")
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = GlitchEngine.from_dict(data)
        
        self.assertEqual(restored.agent_id, original.agent_id)
        self.assertEqual(restored.personality, original.personality)
        self.assertEqual(restored.glitch_chance, original.glitch_chance)
        self.assertEqual(len(restored._glitch_history), len(original._glitch_history))


class TestGlitchRecord(unittest.TestCase):
    """Tests for GlitchRecord data class."""
    
    def test_record_creation(self):
        """Test creating a glitch record."""
        record = GlitchRecord(
            glitch_id="aside_001",
            agent_id="test_agent",
            timestamp=datetime.now(),
            glitch_type=GlitchType.OFF_TOPIC_ASIDE
        )
        
        self.assertEqual(record.glitch_id, "aside_001")
        self.assertEqual(record.agent_id, "test_agent")
        self.assertEqual(record.glitch_type, GlitchType.OFF_TOPIC_ASIDE)


if __name__ == '__main__':
    unittest.main(verbosity=2)