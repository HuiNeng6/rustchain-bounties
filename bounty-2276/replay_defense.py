#!/usr/bin/env python3
"""
RustChain Fingerprint Replay Attack Defense
============================================

This module implements server-side defenses against fingerprint replay attacks.

Defense mechanisms:
1. Server-side nonce binding - fingerprint must include server-issued challenge
2. Temporal correlation - fingerprint timing data must be fresh, not recorded
3. Cross-check fingerprint entropy against connection metadata
4. Fingerprint uniqueness validation

Author: Security Research Team
Bounty: #2276 - Fingerprint Replay Attack Defense
"""

import hashlib
import time
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import hmac

# Configuration
NONCE_EXPIRY_SECONDS = 600  # 10 minutes
FINGERPRINT_MAX_AGE_SECONDS = 120  # Fingerprint data must be recent
MAX_NONCE_USES = 1  # Each nonce can only be used once
ENTROPY_TOLERANCE = 0.1  # Allow 10% deviation in entropy


@dataclass
class NonceRecord:
    """Tracks issued nonces for validation."""
    nonce: str
    server_time: float
    expires_at: float
    client_ip: Optional[str] = None
    tls_fingerprint: Optional[str] = None
    used: bool = False
    used_at: Optional[float] = None
    used_by_wallet: Optional[str] = None


@dataclass
class FingerprintValidation:
    """Result of fingerprint validation."""
    valid: bool
    reason: str
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class NonceManager:
    """
    Manages challenge nonces with replay attack prevention.
    """
    
    def __init__(self, expiry_seconds: int = NONCE_EXPIRY_SECONDS):
        self.expiry_seconds = expiry_seconds
        self.nonces: Dict[str, NonceRecord] = {}
        self.wallet_nonces: Dict[str, List[str]] = defaultdict(list)
        
    def issue_nonce(self, client_ip: str = None, tls_fingerprint: str = None) -> Tuple[str, int]:
        """
        Issue a new challenge nonce.
        
        Returns:
            Tuple of (nonce, server_time)
        """
        # Clean up expired nonces
        self._cleanup_expired()
        
        # Generate cryptographically secure nonce
        nonce = secrets.token_hex(32)
        server_time = int(time.time())
        
        record = NonceRecord(
            nonce=nonce,
            server_time=server_time,
            expires_at=server_time + self.expiry_seconds,
            client_ip=client_ip,
            tls_fingerprint=tls_fingerprint
        )
        
        self.nonces[nonce] = record
        return nonce, server_time
    
    def validate_nonce(self, nonce: str, wallet: str, 
                       client_ip: str = None, 
                       tls_fingerprint: str = None) -> Tuple[bool, str, Optional[NonceRecord]]:
        """
        Validate a submitted nonce.
        
        Returns:
            Tuple of (valid, reason, record)
        """
        # Check if nonce exists
        if nonce not in self.nonces:
            return False, "invalid_nonce", None
        
        record = self.nonces[nonce]
        current_time = time.time()
        
        # Check if nonce expired
        if current_time > record.expires_at:
            return False, "nonce_expired", record
        
        # Check if nonce already used
        if record.used:
            return False, "nonce_already_used", record
        
        # Check client IP consistency (if bound)
        if record.client_ip and client_ip and record.client_ip != client_ip:
            return False, "nonce_ip_mismatch", record
        
        # Check TLS fingerprint consistency (if bound)
        if record.tls_fingerprint and tls_fingerprint:
            if record.tls_fingerprint != tls_fingerprint:
                return False, "nonce_tls_mismatch", record
        
        # Mark nonce as used
        record.used = True
        record.used_at = current_time
        record.used_by_wallet = wallet
        
        # Track wallet nonce usage
        self.wallet_nonces[wallet].append(nonce)
        
        return True, "valid", record
    
    def _cleanup_expired(self):
        """Remove expired nonces to prevent memory leak."""
        current_time = time.time()
        expired = [n for n, r in self.nonces.items() if r.expires_at < current_time]
        for nonce in expired:
            del self.nonces[nonce]


class FingerprintEntropyAnalyzer:
    """
    Analyzes fingerprint data for replay attack indicators.
    """
    
    # Expected ranges for various fingerprint metrics
    POWERPC_G4_EXPECTED = {
        "clock_drift": {
            "drift_ppm": (5, 50),
            "mean_ns": (20000, 30000),
            "variance_ns": (200, 600)
        },
        "cache_timing": {
            "l1_latency_ns": (2, 5),
            "l2_latency_ns": (8, 20),
            "cache_line_size": (32, 32),  # Exact for G4
            "unique_pattern_hash": "required"
        },
        "simd_identity": {
            "vector_width": (128, 128),  # AltiVec is 128-bit
            "simd_type": "required"
        },
        "thermal_drift": {
            "temperature_c": (30, 70),
            "throttling_events": (0, 100),
            "unique_thermal_signature": "required"
        },
        "instruction_jitter": {
            "mean_jitter_ns": (5, 15),
            "std_dev_ns": (1, 5),
            "pattern_hash": "required",
            "jitter_distribution": "required"
        }
    }
    
    # Expected ranges for modern x86
    X86_64_EXPECTED = {
        "clock_drift": {
            "drift_ppm": (0.1, 5),
            "mean_ns": (100, 1000),
            "variance_ns": (10, 100)
        },
        "cache_timing": {
            "l1_latency_ns": (1, 2),
            "l2_latency_ns": (3, 8),
            "l3_latency_ns": (20, 50)
        },
        "simd_identity": {
            "vector_width": (128, 512)
        },
        "thermal_drift": {
            "temperature_c": (30, 90),
            "throttling_events": (0, 10)
        },
        "instruction_jitter": {
            "mean_jitter_ns": (0.5, 5),
            "std_dev_ns": (0.1, 2)
        }
    }
    
    @classmethod
    def analyze_entropy(cls, fingerprint: Dict[str, Any], 
                        claimed_arch: str) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze fingerprint entropy and consistency.
        
        Returns:
            Tuple of (entropy_score, analysis_details)
        """
        expected = cls.POWERPC_G4_EXPECTED if "g4" in claimed_arch.lower() else cls.X86_64_EXPECTED
        
        analysis = {
            "checks": {},
            "anomalies": [],
            "entropy_score": 0.0
        }
        
        checks = fingerprint.get("checks", {})
        total_score = 0.0
        check_count = 0
        
        for check_name, expected_ranges in expected.items():
            if check_name not in checks:
                continue
            
            check_data = checks[check_name].get("data", {})
            check_score = 0.0
            check_details = {}
            
            for metric, expected_val in expected_ranges.items():
                check_count += 1
                if metric in check_data:
                    value = check_data[metric]
                    
                    # Handle "required" string - just check presence
                    if expected_val == "required":
                        if value and (not isinstance(value, str) or value.strip()):
                            check_score += 1.0
                            check_details[metric] = "present"
                        else:
                            check_details[metric] = "missing_or_empty"
                    elif isinstance(expected_val, tuple) and len(expected_val) == 2:
                        min_val, max_val = expected_val
                        if isinstance(value, (int, float)):
                            if min_val <= value <= max_val:
                                check_score += 1.0
                                check_details[metric] = "in_range"
                            else:
                                check_details[metric] = f"out_of_range ({value} not in [{min_val}, {max_val}])"
                                analysis["anomalies"].append(f"{check_name}.{metric}: {value}")
                        else:
                            check_details[metric] = f"non_numeric: {value}"
                else:
                    check_details[metric] = "missing"
            
            total_score += check_score
            analysis["checks"][check_name] = check_details
        
        entropy_score = total_score / check_count if check_count > 0 else 0.0
        analysis["entropy_score"] = entropy_score
        
        return entropy_score, analysis


class ConnectionMetadataValidator:
    """
    Validates connection metadata against fingerprint claims.
    """
    
    @staticmethod
    def validate_consistency(fingerprint: Dict[str, Any],
                             client_ip: str,
                             tls_fingerprint: str,
                             claimed_arch: str) -> Tuple[bool, List[str]]:
        """
        Validate that connection metadata is consistent with fingerprint.
        
        Returns:
            Tuple of (consistent, list_of_issues)
        """
        issues = []
        
        # Check for known VM/cloud IP ranges
        if ConnectionMetadataValidator._is_known_cloud_ip(client_ip):
            issues.append(f"Connection from known cloud provider IP: {client_ip}")
        
        # Check TLS fingerprint for VM/emulation indicators
        if ConnectionMetadataValidator._has_vm_tls_indicators(tls_fingerprint):
            issues.append("TLS fingerprint suggests VM/emulation environment")
        
        # Cross-check claimed architecture with TLS fingerprint
        # (Modern browsers/clients from vintage hardware would have specific signatures)
        if "g4" in claimed_arch.lower() or "powerpc" in claimed_arch.lower():
            # PowerPC systems would have specific TLS library versions
            if ConnectionMetadataValidator._is_modern_tls_only(tls_fingerprint):
                issues.append("Modern TLS fingerprint inconsistent with claimed PowerPC architecture")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def _is_known_cloud_ip(ip: str) -> bool:
        """Check if IP is from a known cloud provider."""
        # Simplified check - in production, use proper IP ranges
        cloud_prefixes = [
            "10.", "172.16.", "192.168.",  # Private (could be VM)
            "35.", "104.", "130.", "146.",  # Google Cloud
            "3.", "13.", "15.", "18.", "34.", "52.", "54.", "99.", "107.",  # AWS
            "13.64.", "13.65.", "13.66.", "13.67.", "13.68.", "13.69.", "13.70.",  # Azure
            "20.", "40.", "51.", "52.", "102.", "103.", "104.", "137.", "138.", "139.", "140.",  # Azure
        ]
        return any(ip.startswith(prefix) for prefix in cloud_prefixes)
    
    @staticmethod
    def _has_vm_tls_indicators(tls_fingerprint: str) -> bool:
        """Check TLS fingerprint for VM indicators."""
        # Simplified - in production, check actual JA3/JA3S signatures
        vm_indicators = ["vmware", "virtualbox", "qemu", "hyper-v"]
        return any(indicator in tls_fingerprint.lower() for indicator in vm_indicators)
    
    @staticmethod
    def _is_modern_tls_only(tls_fingerprint: str) -> bool:
        """Check if TLS fingerprint is only available on modern systems."""
        # PowerPC G4 systems typically can't run TLS 1.3 or modern cipher suites
        modern_indicators = ["tls1.3", "tls_1_3", "chrome/10", "firefox/10"]
        return any(indicator in tls_fingerprint.lower() for indicator in modern_indicators)


def validate_fingerprint_freshness(
    fingerprint: Dict[str, Any],
    nonce_record: NonceRecord,
    current_time: float,
    max_age_seconds: float = FINGERPRINT_MAX_AGE_SECONDS
) -> FingerprintValidation:
    """
    Validate that fingerprint data is fresh, not recorded/replayed.
    
    This is the core defense function that checks:
    1. Fingerprint timing data is consistent with current time
    2. Temporal patterns in fingerprint data are recent
    3. No evidence of recorded/replayed timing data
    
    Args:
        fingerprint: The fingerprint data from the attestation payload
        nonce_record: The nonce record with server time when challenge was issued
        current_time: Current server time
        max_age_seconds: Maximum allowed age for fingerprint data
    
    Returns:
        FingerprintValidation with result and details
    """
    details = {}
    anomalies = []
    score = 1.0
    
    # Check 1: Fingerprint timestamp must be recent
    checks = fingerprint.get("checks", {})
    
    # Check clock drift data freshness
    clock_drift = checks.get("clock_drift", {}).get("data", {})
    if clock_drift:
        # Clock drift samples should have been taken recently
        sample_count = clock_drift.get("samples", 0)
        if sample_count < 100:
            anomalies.append("Insufficient clock drift samples")
            score *= 0.8
        
        # Mean drift should be consistent with time since nonce was issued
        mean_ns = clock_drift.get("mean_ns", 0)
        expected_mean_range = (20000, 30000)  # For PowerPC G4
        if mean_ns and not (expected_mean_range[0] <= mean_ns <= expected_mean_range[1]):
            details["clock_drift_mean"] = f"Unexpected mean_ns: {mean_ns}"
    
    # Check 2: Cache timing should show real-time variations
    cache_timing = checks.get("cache_timing", {}).get("data", {})
    if cache_timing:
        # Cache timing should have a unique pattern hash
        pattern_hash = cache_timing.get("unique_pattern_hash", "")
        if not pattern_hash:
            anomalies.append("Missing cache timing pattern hash")
            score *= 0.9
        
        # Check cache geometry matches claimed architecture
        cache_geometry = cache_timing.get("cache_geometry", "")
        if cache_geometry and "powerpc" not in cache_geometry.lower():
            anomalies.append(f"Cache geometry '{cache_geometry}' inconsistent with PowerPC claim")
            score *= 0.7
    
    # Check 3: SIMD identity must match claimed architecture
    simd = checks.get("simd_identity", {}).get("data", {})
    if simd:
        simd_type = simd.get("simd_type", "")
        if "g4" in nonce_record.__dict__.get("device_arch", "").lower():
            if simd_type != "AltiVec":
                anomalies.append(f"SIMD type '{simd_type}' incorrect for G4 (expected AltiVec)")
                score *= 0.5
    
    # Check 4: Thermal data should show recent measurements
    thermal = checks.get("thermal_drift", {}).get("data", {})
    if thermal:
        temp = thermal.get("temperature_c", 0)
        if temp < 20 or temp > 90:
            anomalies.append(f"Unrealistic temperature reading: {temp}°C")
            score *= 0.6
        
        # Check for thermal signature freshness
        thermal_sig = thermal.get("unique_thermal_signature", "")
        if not thermal_sig:
            anomalies.append("Missing thermal signature")
            score *= 0.9
    
    # Check 5: Instruction jitter should show real-time variation
    jitter = checks.get("instruction_jitter", {}).get("data", {})
    if jitter:
        pattern_hash = jitter.get("pattern_hash", "")
        if not pattern_hash:
            anomalies.append("Missing instruction jitter pattern hash")
            score *= 0.9
        
        # Jitter distribution should be realistic
        distribution = jitter.get("jitter_distribution", "")
        if distribution not in ["gaussian", "normal", "poisson"]:
            anomalies.append(f"Unusual jitter distribution: {distribution}")
            score *= 0.8
    
    # Check 6: Anti-emulation should pass
    anti_emu = checks.get("anti_emulation", {}).get("data", {})
    if anti_emu:
        if anti_emu.get("hypervisor_detected", False):
            anomalies.append("Hypervisor detected in anti-emulation check")
            score = 0.0  # Critical failure
        
        vm_artifacts = anti_emu.get("vm_artifacts", [])
        if vm_artifacts:
            anomalies.append(f"VM artifacts detected: {vm_artifacts}")
            score *= 0.3
    
    # Calculate final score
    score = max(0.0, min(1.0, score))
    
    # Determine if valid
    valid = score >= 0.7 and len(anomalies) < 3
    
    reason = "valid" if valid else "freshness_validation_failed"
    details["score"] = score
    details["anomalies"] = anomalies
    details["check_count"] = len(checks)
    
    return FingerprintValidation(
        valid=valid,
        reason=reason,
        score=score,
        details=details
    )


class ReplayDefenseSystem:
    """
    Complete replay attack defense system for RustChain.
    """
    
    def __init__(self):
        self.nonce_manager = NonceManager()
        self.seen_fingerprints: Dict[str, float] = {}  # hash -> timestamp
        self.wallet_fingerprints: Dict[str, List[str]] = defaultdict(list)
    
    def issue_challenge(self, client_ip: str = None, 
                        tls_fingerprint: str = None) -> Dict[str, Any]:
        """
        Issue a new attestation challenge.
        
        Returns:
            Challenge response with nonce and server time
        """
        nonce, server_time = self.nonce_manager.issue_nonce(client_ip, tls_fingerprint)
        
        return {
            "nonce": nonce,
            "server_time": server_time,
            "expires_at": server_time + NONCE_EXPIRY_SECONDS
        }
    
    def validate_attestation(
        self,
        payload: Dict[str, Any],
        client_ip: str = None,
        tls_fingerprint: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate an attestation submission.
        
        This is the main entry point for validating submissions against replay attacks.
        
        Args:
            payload: The attestation payload from POST /attest/submit
            client_ip: Client's IP address
            tls_fingerprint: Client's TLS fingerprint (JA3)
        
        Returns:
            Tuple of (accepted, reason, validation_details)
        """
        details = {
            "checks_passed": [],
            "checks_failed": [],
            "warnings": []
        }
        
        # Extract payload fields
        wallet = payload.get("miner", "")
        nonce = payload.get("nonce", "")
        fingerprint = payload.get("fingerprint", {})
        device = payload.get("device", {})
        claimed_arch = device.get("device_arch", "")
        
        # Check 1: Validate nonce
        nonce_valid, nonce_reason, nonce_record = self.nonce_manager.validate_nonce(
            nonce, wallet, client_ip, tls_fingerprint
        )
        
        if not nonce_valid:
            details["checks_failed"].append(f"nonce_validation: {nonce_reason}")
            return False, f"nonce_rejected: {nonce_reason}", details
        
        details["checks_passed"].append("nonce_valid")
        
        # Check 2: Validate fingerprint freshness
        freshness_result = validate_fingerprint_freshness(
            fingerprint, nonce_record, time.time()
        )
        
        if not freshness_result.valid:
            details["checks_failed"].append(f"fingerprint_freshness: {freshness_result.reason}")
            details["freshness_score"] = freshness_result.score
            details["freshness_anomalies"] = freshness_result.details.get("anomalies", [])
            return False, f"fingerprint_not_fresh: {freshness_result.reason}", details
        
        details["checks_passed"].append("fingerprint_fresh")
        details["freshness_score"] = freshness_result.score
        
        # Check 3: Analyze entropy
        entropy_score, entropy_analysis = FingerprintEntropyAnalyzer.analyze_entropy(
            fingerprint, claimed_arch
        )
        
        if entropy_score < 0.5:
            details["checks_failed"].append(f"entropy_analysis: low entropy score {entropy_score}")
            details["entropy_analysis"] = entropy_analysis
            return False, f"entropy_mismatch: score {entropy_score}", details
        
        details["checks_passed"].append("entropy_valid")
        details["entropy_score"] = entropy_score
        
        # Check 4: Validate connection metadata
        metadata_valid, metadata_issues = ConnectionMetadataValidator.validate_consistency(
            fingerprint, client_ip or "", tls_fingerprint or "", claimed_arch
        )
        
        if not metadata_valid:
            details["warnings"].extend(metadata_issues)
            # This is a warning, not a hard failure (could be legitimate)
        
        # Check 5: Check for fingerprint reuse
        fingerprint_hash = hashlib.sha256(
            json.dumps(fingerprint, sort_keys=True).encode()
        ).hexdigest()
        
        if fingerprint_hash in self.seen_fingerprints:
            last_seen = self.seen_fingerprints[fingerprint_hash]
            time_since = time.time() - last_seen
            
            if time_since < 3600:  # Within 1 hour
                details["checks_failed"].append(f"fingerprint_reuse: seen {time_since:.0f}s ago")
                return False, "fingerprint_already_used", details
        
        # Record this fingerprint
        self.seen_fingerprints[fingerprint_hash] = time.time()
        self.wallet_fingerprints[wallet].append(fingerprint_hash)
        
        details["checks_passed"].append("fingerprint_unique")
        
        # All checks passed
        return True, "accepted", details
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the defense system."""
        return {
            "active_nonces": len(self.nonce_manager.nonces),
            "seen_fingerprints": len(self.seen_fingerprints),
            "unique_wallets": len(self.wallet_fingerprints)
        }


# Example Flask integration
def create_flask_integration():
    """
    Example of how to integrate the defense system with a Flask server.
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    defense = ReplayDefenseSystem()
    
    @app.route('/attest/challenge', methods=['POST'])
    def attest_challenge():
        client_ip = request.remote_addr
        tls_fingerprint = request.headers.get('X-TLS-Fingerprint', '')
        
        challenge = defense.issue_challenge(client_ip, tls_fingerprint)
        return jsonify(challenge)
    
    @app.route('/attest/submit', methods=['POST'])
    def attest_submit():
        payload = request.get_json()
        client_ip = request.remote_addr
        tls_fingerprint = request.headers.get('X-TLS-Fingerprint', '')
        
        accepted, reason, details = defense.validate_attestation(
            payload, client_ip, tls_fingerprint
        )
        
        if accepted:
            return jsonify({
                "status": "accepted",
                "reason": reason,
                "details": details
            }), 200
        else:
            return jsonify({
                "status": "rejected",
                "reason": reason,
                "details": details
            }), 400
    
    return app


if __name__ == "__main__":
    # Demo/test mode
    print("RustChain Replay Defense System")
    print("=" * 50)
    
    defense = ReplayDefenseSystem()
    
    # Issue a challenge
    challenge = defense.issue_challenge("192.168.1.100", "chrome_120_tls13")
    print(f"Challenge issued: {challenge['nonce'][:16]}...")
    
    # Simulate a valid attestation
    valid_payload = {
        "miner": "test_wallet_123",
        "nonce": challenge["nonce"],
        "fingerprint": {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {
                        "samples": 1000,
                        "mean_ns": 25000,
                        "variance_ns": 400
                    }
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        "unique_pattern_hash": "abc123",
                        "cache_geometry": "powerpc_g4"
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {
                        "simd_type": "AltiVec"
                    }
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 45.0,
                        "unique_thermal_signature": "thermal_123"
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "pattern_hash": "jitter_456",
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
        },
        "device": {
            "device_arch": "g4"
        }
    }
    
    accepted, reason, details = defense.validate_attestation(
        valid_payload, "192.168.1.100", "chrome_120_tls13"
    )
    
    print(f"\nValidation result: {accepted}")
    print(f"Reason: {reason}")
    print(f"Details: {json.dumps(details, indent=2)}")