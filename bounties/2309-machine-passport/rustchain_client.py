#!/usr/bin/env python3
"""
RustChain API Client for Machine Passport Ledger.
Fetches miner data from the RustChain node API.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import urllib.request
import urllib.error
import ssl

# RustChain node endpoint
RUSTCHAIN_NODE = "https://50.28.86.131"


class RustChainClient:
    """Client for interacting with the RustChain node API."""
    
    def __init__(self, node_url: str = RUSTCHAIN_NODE, timeout: int = 30):
        self.node_url = node_url.rstrip('/')
        self.timeout = timeout
        # Create SSL context that accepts self-signed certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the RustChain API."""
        url = f"{self.node_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if data:
                body = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise Exception("Rate limited - please retry with backoff")
            raise Exception(f"HTTP {e.code}: {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection error: {e.reason}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response")
    
    def health(self) -> Dict:
        """Check node health status."""
        return self._request("GET", "/health")
    
    def epoch(self) -> Dict:
        """Get current epoch information."""
        return self._request("GET", "/epoch")
    
    def get_miners(self, limit: int = 100, offset: int = 0) -> Dict:
        """Get list of active miners."""
        return self._request("GET", f"/api/miners?limit={limit}&offset={offset}")
    
    def get_balance(self, miner_id: str) -> Dict:
        """Get wallet balance for a miner."""
        return self._request("GET", f"/wallet/balance?miner_id={miner_id}")
    
    def get_challenge(self) -> Dict:
        """Request a challenge nonce for attestation."""
        return self._request("POST", "/attest/challenge", {})
    
    def submit_attestation(self, payload: Dict) -> Dict:
        """Submit an attestation."""
        return self._request("POST", "/attest/submit", payload)
    
    def enroll_epoch(self, miner_pubkey: str, miner_id: str, device_family: str, device_arch: str) -> Dict:
        """Enroll in epoch for reward distribution."""
        return self._request("POST", "/epoch/enroll", {
            "miner_pubkey": miner_pubkey,
            "miner_id": miner_id,
            "device": {
                "family": device_family,
                "arch": device_arch
            }
        })


class PassportDataFetcher:
    """
    Fetches and transforms data from RustChain API for passport generation.
    Uses mock data when API is unavailable.
    """
    
    def __init__(self, client: Optional[RustChainClient] = None):
        self.client = client or RustChainClient()
        self._cached_miners = None
        self._cache_time = 0
    
    def fetch_miner_data(self, use_cache: bool = True, cache_ttl: int = 60) -> List[Dict]:
        """
        Fetch miner data from the API.
        Returns mock data if API is unavailable.
        """
        now = time.time()
        
        if use_cache and self._cached_miners and (now - self._cache_time) < cache_ttl:
            return self._cached_miners
        
        try:
            response = self.client.get_miners(limit=500)
            miners = response.get("miners", [])
            self._cached_miners = miners
            self._cache_time = now
            return miners
        except Exception as e:
            print(f"Warning: Could not fetch miner data: {e}")
            print("Using mock data instead...")
            return self._get_mock_miners()
    
    def _get_mock_miners(self) -> List[Dict]:
        """Generate mock miner data for testing."""
        return [
            {
                "miner": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
                "device_family": "PowerPC",
                "device_arch": "g5",
                "antiquity_multiplier": 2.0,
                "last_attest": int(time.time()) - 3600,
                "total_attestations": 142,
                "total_rtc_earned": 284.5,
            },
            {
                "miner": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
                "device_family": "PowerPC",
                "device_arch": "g4",
                "antiquity_multiplier": 2.5,
                "last_attest": int(time.time()) - 7200,
                "total_attestations": 89,
                "total_rtc_earned": 222.25,
            },
            {
                "miner": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
                "device_family": "PowerPC",
                "device_arch": "g3",
                "antiquity_multiplier": 1.8,
                "last_attest": int(time.time()) - 1800,
                "total_attestations": 67,
                "total_rtc_earned": 120.6,
            },
            {
                "miner": "ExampleWallet123456789",
                "device_family": "x86_64",
                "device_arch": "core2duo",
                "antiquity_multiplier": 1.3,
                "last_attest": int(time.time()) - 14400,
                "total_attestations": 256,
                "total_rtc_earned": 332.8,
            },
            {
                "miner": "ExampleWallet987654321",
                "device_family": "ARM",
                "device_arch": "apple_silicon",
                "antiquity_multiplier": 1.2,
                "last_attest": int(time.time()) - 5400,
                "total_attestations": 45,
                "total_rtc_earned": 54.0,
            },
        ]
    
    def get_epoch_info(self) -> Dict:
        """Get current epoch information."""
        try:
            return self.client.epoch()
        except Exception as e:
            print(f"Warning: Could not fetch epoch info: {e}")
            return {
                "epoch": 73,
                "slot": 10554,
                "blocks_per_epoch": 144,
                "enrolled_miners": 12,
                "epoch_pot": 1.5,
            }
    
    def get_wallet_balance(self, wallet: str) -> Dict:
        """Get wallet balance."""
        try:
            return self.client.get_balance(wallet)
        except Exception as e:
            print(f"Warning: Could not fetch balance: {e}")
            return {
                "miner_id": wallet,
                "amount_rtc": 0.0,
                "amount_i64": 0,
            }


def sync_passports_from_api(ledger_path: str = "passport_ledger.json") -> int:
    """
    Sync passport data from the RustChain API.
    Creates new passports for miners not yet in the ledger.
    
    Returns the number of passports created/updated.
    """
    from passport_generator import PassportLedger
    
    fetcher = PassportDataFetcher()
    ledger = PassportLedger(ledger_path)
    
    miners = fetcher.fetch_miner_data()
    created_count = 0
    
    for miner in miners:
        wallet = miner.get("miner", "")
        device_arch = miner.get("device_arch", "modern")
        device_family = miner.get("device_family", "Unknown")
        
        # Skip if we already have a passport for this wallet+arch combination
        existing = [p for p in ledger.passports.values() 
                   if p.wallet_address == wallet and p.device_arch == device_arch]
        if existing:
            continue
        
        # Create new passport
        passport = ledger.create_passport(
            wallet_address=wallet,
            device_name=f"{device_family} {device_arch.upper()} Miner",
            device_family=device_family,
            device_arch=device_arch,
            cpu_model=f"{device_family} {device_arch.upper()} CPU",
            cpu_cores=2 if device_arch in ["g5", "core2duo"] else 1,
            ram_gb=4 if device_arch in ["g5", "core2duo"] else 1,
            os_type="Linux",
        )
        
        # Add existing attestation count and earnings from API data
        passport.total_attestations = miner.get("total_attestations", 0)
        passport.successful_attestations = miner.get("total_attestations", 0)
        passport.total_rtc_earned = miner.get("total_rtc_earned", 0.0)
        
        created_count += 1
    
    ledger.save()
    return created_count


if __name__ == "__main__":
    # Test the client
    print("Testing RustChain API Client...")
    
    client = RustChainClient()
    
    # Test health
    try:
        health = client.health()
        print(f"Node health: {health}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test epoch
    try:
        epoch = client.epoch()
        print(f"Current epoch: {epoch}")
    except Exception as e:
        print(f"Epoch fetch failed: {e}")
    
    # Test miners list
    fetcher = PassportDataFetcher()
    miners = fetcher.fetch_miner_data()
    print(f"\nMiners found: {len(miners)}")
    for m in miners[:3]:
        print(f"  - {m.get('miner', 'unknown')[:16]}... ({m.get('device_arch', '?')})")