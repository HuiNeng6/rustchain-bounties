#!/usr/bin/env python3
"""
RustChain Fingerprint Replay Defense Tests
===========================================

Tests that prove the defense mechanisms work correctly:
1. Replayed fingerprint → REJECTED
2. Fresh fingerprint → ACCEPTED
3. Modified replay (changed nonce but old data) → REJECTED

Author: Security Research Team
Bounty: #2276 - Fingerprint Replay Attack Defense
"""

import pytest
import time
import json
import hashlib
from unittest.mock import Mock, patch
import sys
import os

# Add the bounty directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from replay_defense import (
    ReplayDefenseSystem,
    NonceManager,
    FingerprintEntropyAnalyzer,
    ConnectionMetadataValidator,
    validate_fingerprint_freshness,
    NonceRecord,
    NONCE_EXPIRY_SECONDS,
    FINGERPRINT_MAX_AGE_SECONDS
)


# ─────────────────────────────────────────────────────────────────────────────
# Test Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def defense_system():
    """Create a fresh defense system for each test."""
    return ReplayDefenseSystem()


@pytest.fixture
def valid_g4_fingerprint():
    """A valid G4 PowerBook fingerprint."""
    return {
        "all_passed": True,
        "checks": {
            "clock_drift": {
                "passed": True,
                "data": {
                    "drift_ppm": 15.0,
                    "oscillator_type": "quartz",
                    "mean_ns": 25000,
                    "variance_ns": 400,
                    "samples": 1000,
                    "hardware_age_years": 22
                }
            },
            "cache_timing": {
                "passed": True,
                "data": {
                    "l1_latency_ns": 3,
                    "l2_latency_ns": 12,
                    "cache_line_size": 32,
                    "associativity": 8,
                    "cache_geometry": "powerpc_g4",
                    "unique_pattern_hash": "g4_cache_unique_abc123"
                }
            },
            "simd_identity": {
                "passed": True,
                "data": {
                    "simd_type": "AltiVec",
                    "vector_width": 128,
                    "implementation_hash": "altivec_g4_7447a"
                }
            },
            "thermal_drift": {
                "passed": True,
                "data": {
                    "temperature_c": 48.5,
                    "throttling_events": 2,
                    "fan_speed_rpm": 2800,
                    "unique_thermal_signature": "g4_thermal_xyz789"
                }
            },
            "instruction_jitter": {
                "passed": True,
                "data": {
                    "mean_jitter_ns": 8.5,
                    "std_dev_ns": 2.1,
                    "pattern_hash": "g4_jitter_def456",
                    "jitter_distribution": "gaussian"
                }
            },
            "anti_emulation": {
                "passed": True,
                "data": {
                    "hypervisor_detected": False,
                    "vm_artifacts": [],
                    "emulation_signatures": [],
                    "hardware_serial": "CK245XXXXXXXXX"
                }
            }
        }
    }


@pytest.fixture
def valid_g4_device():
    """Valid G4 device info."""
    return {
        "device_family": "PowerPC",
        "device_arch": "g4",
        "device_model": "PowerBook5,6"
    }


@pytest.fixture
def fresh_nonce_record():
    """A fresh nonce record for testing."""
    current_time = time.time()
    return NonceRecord(
        nonce="test_nonce_" + "a" * 54,
        server_time=int(current_time),
        expires_at=current_time + NONCE_EXPIRY_SECONDS,
        client_ip="192.168.1.100",
        tls_fingerprint="chrome_120",
        used=False
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Replayed Fingerprint → REJECTED
# ─────────────────────────────────────────────────────────────────────────────

class TestReplayAttackRejection:
    """
    Test that replayed fingerprints are correctly rejected.
    """
    
    def test_direct_replay_rejected(self, defense_system, valid_g4_fingerprint, valid_g4_device):
        """
        TEST: Direct replay of the same payload should be rejected.
        """
        # Step 1: Submit a valid attestation
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        payload1 = {
            "miner": "wallet_abc123",
            "nonce": challenge["nonce"],
            "fingerprint": valid_g4_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted1, reason1, details1 = defense_system.validate_attestation(
            payload1, "192.168.1.100", "chrome_120"
        )
        
        assert accepted1, f"First submission should be accepted, got: {reason1}"
        
        # Step 2: Get a NEW challenge (simulating attacker trying to replay)
        challenge2 = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        # Step 3: Replay the SAME fingerprint data with new nonce
        payload2 = {
            "miner": "wallet_abc123",
            "nonce": challenge2["nonce"],
            "fingerprint": valid_g4_fingerprint,  # SAME fingerprint
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted2, reason2, details2 = defense_system.validate_attestation(
            payload2, "192.168.1.100", "chrome_120"
        )
        
        # ASSERTION: Replay should be rejected
        assert not accepted2, "Replayed fingerprint should be rejected"
        assert "fingerprint_already_used" in reason2 or "fingerprint_reuse" in reason2, \
            f"Expected fingerprint reuse reason, got: {reason2}"
        
        print("✓ TEST PASSED: Direct replay correctly rejected")
    
    def test_old_fingerprint_data_rejected(self, defense_system, fresh_nonce_record):
        """
        TEST: Fingerprint with old/cached timing data should be rejected.
        """
        # Create fingerprint with timing data that looks recorded/old
        old_fingerprint = {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {
                        "mean_ns": 50000,  # Out of expected range
                        "variance_ns": 100,
                        "samples": 10  # Too few samples
                    }
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        # Missing unique_pattern_hash
                        "cache_geometry": "powerpc_g4"
                    }
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 5.0,  # Unrealistic temperature
                        # Missing thermal signature
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "pattern_hash": "",  # Empty hash
                        "jitter_distribution": "unknown"  # Unknown distribution
                    }
                },
                "anti_emulation": {
                    "passed": True,
                    "data": {
                        "hypervisor_detected": False,
                        "vm_artifacts": []
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {
                        "simd_type": "AltiVec"
                    }
                }
            }
        }
        
        result = validate_fingerprint_freshness(
            old_fingerprint,
            fresh_nonce_record,
            time.time()
        )
        
        # ASSERTION: Old/fake fingerprint should be rejected
        assert not result.valid, "Old fingerprint data should be rejected"
        assert result.score < 0.7, f"Score should be low, got: {result.score}"
        
        print("✓ TEST PASSED: Old fingerprint data correctly rejected")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Fresh Fingerprint → ACCEPTED
# ─────────────────────────────────────────────────────────────────────────────

class TestFreshFingerprintAcceptance:
    """
    Test that fresh, valid fingerprints are correctly accepted.
    """
    
    def test_fresh_valid_fingerprint_accepted(self, defense_system, valid_g4_fingerprint, valid_g4_device):
        """
        TEST: Fresh, valid fingerprint should be accepted.
        """
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        payload = {
            "miner": "wallet_test_" + str(time.time()),
            "nonce": challenge["nonce"],
            "fingerprint": valid_g4_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted, reason, details = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        
        # ASSERTIONS
        assert accepted, f"Fresh valid fingerprint should be accepted, reason: {reason}"
        assert "accepted" in reason, f"Expected 'accepted' reason, got: {reason}"
        assert "nonce_valid" in details["checks_passed"], "Nonce validation should pass"
        assert "fingerprint_fresh" in details["checks_passed"], "Freshness check should pass"
        assert "entropy_valid" in details["checks_passed"], "Entropy check should pass"
        
        print("✓ TEST PASSED: Fresh valid fingerprint correctly accepted")
    
    def test_multiple_unique_fingerprints_accepted(self, defense_system, valid_g4_device):
        """
        TEST: Multiple submissions with different fingerprints should all be accepted.
        """
        for i in range(3):
            # Each iteration gets a unique fingerprint with ALL required fields
            unique_fingerprint = {
                "all_passed": True,
                "checks": {
                    "clock_drift": {
                        "passed": True,
                        "data": {
                            "drift_ppm": 15.0,  # Required for entropy
                            "mean_ns": 25000,
                            "variance_ns": 400,
                            "samples": 1000
                        }
                    },
                    "cache_timing": {
                        "passed": True,
                        "data": {
                            "l1_latency_ns": 3,  # Required
                            "l2_latency_ns": 12,  # Required
                            "cache_line_size": 32,
                            "unique_pattern_hash": f"unique_hash_{i}_{time.time()}",
                            "cache_geometry": "powerpc_g4"
                        }
                    },
                    "simd_identity": {
                        "passed": True,
                        "data": {
                            "simd_type": "AltiVec",  # Required
                            "vector_width": 128  # Required for G4
                        }
                    },
                    "thermal_drift": {
                        "passed": True,
                        "data": {
                            "temperature_c": 45.0 + i,
                            "throttling_events": 2,  # Required
                            "unique_thermal_signature": f"thermal_{i}_{time.time()}"
                        }
                    },
                    "instruction_jitter": {
                        "passed": True,
                        "data": {
                            "mean_jitter_ns": 8.5,  # Required
                            "std_dev_ns": 2.1,  # Required
                            "pattern_hash": f"jitter_{i}_{time.time()}",
                            "jitter_distribution": "gaussian"
                        }
                    },
                    "anti_emulation": {
                        "passed": True,
                        "data": {
                            "hypervisor_detected": False,
                            "vm_artifacts": []
                        }
                    }
                }
            }
            
            challenge = defense_system.issue_challenge(f"192.168.1.{100+i}", f"client_{i}")
            
            payload = {
                "miner": f"wallet_{i}_{time.time()}",
                "nonce": challenge["nonce"],
                "fingerprint": unique_fingerprint,
                "device": valid_g4_device,
                "report": {"cpu_model": "PowerPC G4"},
                "signals": {"macs": [f"00:0a:27:xx:xx:{i:x}"]}
            }
            
            accepted, reason, details = defense_system.validate_attestation(
                payload, f"192.168.1.{100+i}", f"client_{i}"
            )
            
            assert accepted, f"Unique fingerprint {i} should be accepted, reason: {reason}"
        
        print("✓ TEST PASSED: Multiple unique fingerprints correctly accepted")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Modified Replay (changed nonce but old data) → REJECTED
# ─────────────────────────────────────────────────────────────────────────────

class TestModifiedReplayRejection:
    """
    Test that modified replays with fresh nonce but old data are rejected.
    """
    
    def test_fresh_nonce_old_fingerprint_rejected(self, defense_system, valid_g4_device):
        """
        TEST: Fresh nonce with old/captured fingerprint should be rejected.
        
        This simulates the main attack vector:
        1. Attacker captures fingerprint from legitimate G4 PowerBook
        2. Gets a fresh nonce from server
        3. Submits old fingerprint with new nonce
        """
        # Simulate captured fingerprint (would be from real G4 in actual attack)
        captured_fingerprint = {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {
                        "drift_ppm": 15.0,
                        "mean_ns": 25000,
                        "variance_ns": 400,
                        "samples": 1000
                    }
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        "l1_latency_ns": 3,
                        "l2_latency_ns": 12,
                        "cache_line_size": 32,
                        "unique_pattern_hash": "captured_g4_hash_abc",  # Old hash
                        "cache_geometry": "powerpc_g4"
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {
                        "simd_type": "AltiVec",
                        "vector_width": 128
                    }
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 45.0,
                        "throttling_events": 2,
                        "unique_thermal_signature": "captured_thermal_xyz"  # Old signature
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "mean_jitter_ns": 8.5,
                        "std_dev_ns": 2.1,
                        "pattern_hash": "captured_jitter_def",  # Old pattern
                        "jitter_distribution": "gaussian"
                    }
                },
                "anti_emulation": {
                    "passed": True,
                    "data": {
                        "hypervisor_detected": False,
                        "vm_artifacts": []
                    }
                }
            }
        }
        
        # Step 1: Original submission (capture happens here)
        challenge1 = defense_system.issue_challenge("192.168.1.200", "g4_client")
        payload1 = {
            "miner": "victim_wallet",
            "nonce": challenge1["nonce"],
            "fingerprint": captured_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:aa:bb:cc"]}
        }
        
        accepted1, _, _ = defense_system.validate_attestation(
            payload1, "192.168.1.200", "g4_client"
        )
        assert accepted1, "Original submission should be accepted"
        
        # Step 2: Attacker gets fresh nonce from DIFFERENT IP
        challenge2 = defense_system.issue_challenge("10.0.0.50", "attacker_client")
        
        # Step 3: Attacker submits CAPTURED fingerprint with FRESH nonce
        attack_payload = {
            "miner": "attacker_wallet",
            "nonce": challenge2["nonce"],  # FRESH nonce
            "fingerprint": captured_fingerprint,  # OLD/captured fingerprint
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:aa:bb:cc"]}  # Same MACs
        }
        
        accepted2, reason2, details2 = defense_system.validate_attestation(
            attack_payload, "10.0.0.50", "attacker_client"
        )
        
        # ASSERTION: Attack should be rejected
        assert not accepted2, "Modified replay should be rejected"
        assert "fingerprint_already_used" in reason2 or "fingerprint_reuse" in reason2, \
            f"Expected fingerprint reuse detection, got: {reason2}"
        
        print("✓ TEST PASSED: Fresh nonce with old fingerprint correctly rejected")
    
    def test_nonce_reuse_rejected(self, defense_system, valid_g4_fingerprint, valid_g4_device):
        """
        TEST: Attempting to use the same nonce twice should be rejected.
        """
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        payload = {
            "miner": "wallet_test",
            "nonce": challenge["nonce"],
            "fingerprint": valid_g4_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        # First use - should succeed
        accepted1, reason1, _ = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        assert accepted1, f"First use should succeed: {reason1}"
        
        # Second use of SAME nonce - should fail
        accepted2, reason2, _ = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        
        assert not accepted2, "Nonce reuse should be rejected"
        assert "nonce_already_used" in reason2, f"Expected nonce_already_used, got: {reason2}"
        
        print("✓ TEST PASSED: Nonce reuse correctly rejected")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Entropy and Architecture Validation
# ─────────────────────────────────────────────────────────────────────────────

class TestEntropyAndArchitectureValidation:
    """
    Test that entropy and architecture checks work correctly.
    """
    
    def test_powerpc_entropy_validation(self, valid_g4_fingerprint):
        """
        TEST: PowerPC G4 fingerprint should have valid entropy.
        """
        score, analysis = FingerprintEntropyAnalyzer.analyze_entropy(
            valid_g4_fingerprint, "g4"
        )
        
        assert score > 0.5, f"PowerPC G4 entropy score should be > 0.5, got: {score}"
        assert len(analysis["anomalies"]) == 0, f"Should have no anomalies, got: {analysis['anomalies']}"
        
        print("✓ TEST PASSED: PowerPC entropy validation works")
    
    def test_x86_fingerprint_claiming_powerpc_rejected(self, defense_system):
        """
        TEST: x86 fingerprint claiming to be PowerPC should be detected.
        """
        # x86-style fingerprint
        x86_fingerprint = {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {
                        "mean_ns": 500,  # x86 timing (much faster)
                        "variance_ns": 20,
                        "samples": 1000
                    }
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        "l1_latency_ns": 1,  # x86 cache
                        "l2_latency_ns": 4,
                        "l3_latency_ns": 30,  # Has L3 (not on G4)
                        "unique_pattern_hash": "x86_hash",
                        "cache_geometry": "x86_64_modern"
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {
                        "simd_type": "AVX-512",  # Not AltiVec!
                    }
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 65.0,
                        "unique_thermal_signature": "x86_thermal"
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "pattern_hash": "x86_jitter",
                        "jitter_distribution": "gaussian"
                    }
                },
                "anti_emulation": {
                    "passed": True,
                    "data": {
                        "hypervisor_detected": False,
                        "vm_artifacts": []
                    }
                }
            }
        }
        
        # Claim it's a G4 PowerBook
        g4_device = {
            "device_family": "PowerPC",
            "device_arch": "g4",
            "device_model": "PowerBook5,6"
        }
        
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        payload = {
            "miner": "attacker_wallet",
            "nonce": challenge["nonce"],
            "fingerprint": x86_fingerprint,  # x86 fingerprint
            "device": g4_device,  # Claiming to be G4
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted, reason, details = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        
        # ASSERTION: Should be rejected due to entropy/architecture mismatch
        # (Either entropy score is low, or other checks fail)
        assert not accepted, "x86 fingerprint claiming to be PowerPC should be rejected"
        
        # Check that entropy analysis detected the mismatch
        if "entropy_score" in details:
            assert details["entropy_score"] < 0.7, "Entropy should indicate mismatch"
        
        print("✓ TEST PASSED: x86 claiming PowerPC correctly rejected")


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: VM/Emulation Detection
# ─────────────────────────────────────────────────────────────────────────────

class TestVMEmulationDetection:
    """
    Test that VM and emulation environments are detected.
    """
    
    def test_hypervisor_detected_rejected(self, defense_system, valid_g4_device):
        """
        TEST: Fingerprint showing hypervisor should be rejected.
        """
        vm_fingerprint = {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {"mean_ns": 25000, "samples": 1000}
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        "unique_pattern_hash": "vm_hash",
                        "cache_geometry": "powerpc_g4"
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {"simd_type": "AltiVec"}
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 45.0,
                        "unique_thermal_signature": "vm_thermal"
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "pattern_hash": "vm_jitter",
                        "jitter_distribution": "gaussian"
                    }
                },
                "anti_emulation": {
                    "passed": True,
                    "data": {
                        "hypervisor_detected": True,  # VM DETECTED!
                        "vm_artifacts": ["vmware", "virtualbox"]
                    }
                }
            }
        }
        
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        payload = {
            "miner": "vm_wallet",
            "nonce": challenge["nonce"],
            "fingerprint": vm_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted, reason, details = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        
        assert not accepted, "VM fingerprint should be rejected"
        assert "freshness" in reason.lower() or "vm" in reason.lower() or "hypervisor" in reason.lower(), \
            f"Expected VM/hypervisor related rejection, got: {reason}"
        
        print("✓ TEST PASSED: Hypervisor detection works")


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Nonce Expiry
# ─────────────────────────────────────────────────────────────────────────────

class TestNonceExpiry:
    """
    Test that expired nonces are rejected.
    """
    
    def test_expired_nonce_rejected(self, defense_system, valid_g4_fingerprint, valid_g4_device):
        """
        TEST: Expired nonce should be rejected.
        """
        # Issue nonce
        challenge = defense_system.issue_challenge("192.168.1.100", "chrome_120")
        
        # Manually expire the nonce
        nonce = challenge["nonce"]
        defense_system.nonce_manager.nonces[nonce].expires_at = time.time() - 1
        
        payload = {
            "miner": "wallet_test",
            "nonce": nonce,
            "fingerprint": valid_g4_fingerprint,
            "device": valid_g4_device,
            "report": {"cpu_model": "PowerPC G4"},
            "signals": {"macs": ["00:0a:27:xx:xx:xx"]}
        }
        
        accepted, reason, _ = defense_system.validate_attestation(
            payload, "192.168.1.100", "chrome_120"
        )
        
        assert not accepted, "Expired nonce should be rejected"
        assert "nonce_expired" in reason, f"Expected nonce_expired, got: {reason}"
        
        print("✓ TEST PASSED: Expired nonce correctly rejected")


# ─────────────────────────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests():
    """Run all tests and print summary."""
    print("=" * 70)
    print("RustChain Fingerprint Replay Defense Tests")
    print("=" * 70)
    print()
    
    # Run pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    print()
    print("=" * 70)
    if exit_code == 0:
        print("[PASS] ALL TESTS PASSED")
    else:
        print(f"[FAIL] SOME TESTS FAILED (exit code: {exit_code})")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    exit(run_all_tests())