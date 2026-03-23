#!/usr/bin/env python3
"""
RustChain Machine Passport Ledger - Bounty #2309
Generates unique identity passports for vintage hardware miners.

Features:
- Unique identity profile for each mining device
- Records: first online date, architecture, attestations, earnings, maintenance, ownership
- Visual passport page with QR code for on-chain verification
"""

import json
import hashlib
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import qrcode
import base64
from io import BytesIO

# Architecture types supported by RustChain
ARCH_TYPES = {
    "g3": {"name": "PowerPC G3", "multiplier": 1.8, "era": "1997-2004"},
    "g4": {"name": "PowerPC G4", "multiplier": 2.5, "era": "1999-2006"},
    "g5": {"name": "PowerPC G5", "multiplier": 2.0, "era": "2003-2006"},
    "68k": {"name": "Motorola 68K", "multiplier": 3.0, "era": "1984-1996"},
    "sparc": {"name": "SPARC", "multiplier": 2.2, "era": "1987-2010"},
    "mips": {"name": "MIPS", "multiplier": 2.0, "era": "1985-2008"},
    "power8": {"name": "POWER8", "multiplier": 1.5, "era": "2013-2018"},
    "core2duo": {"name": "Core 2 Duo", "multiplier": 1.3, "era": "2006-2011"},
    "apple_silicon": {"name": "Apple Silicon", "multiplier": 1.2, "era": "2020-present"},
    "modern": {"name": "Modern x86_64/ARM", "multiplier": 1.0, "era": "2010-present"},
}


@dataclass
class MaintenanceRecord:
    """Records maintenance events for a machine."""
    timestamp: str
    event_type: str  # "repair", "upgrade", "cleaning", "firmware", "other"
    description: str
    technician: Optional[str] = None
    cost_rtc: Optional[float] = None


@dataclass
class OwnershipRecord:
    """Records ownership changes for a machine."""
    from_wallet: str
    to_wallet: str
    timestamp: str
    transfer_type: str  # "sale", "gift", "inheritance"
    price_rtc: Optional[float] = None


@dataclass
class AttestationRecord:
    """Records a single attestation event."""
    timestamp: str
    epoch: int
    slot: int
    passed: bool
    device_arch: str
    device_family: str
    fingerprint_score: float


@dataclass
class MachinePassport:
    """
    Complete identity passport for a mining device.
    Tracks the full lifecycle and history of vintage hardware.
    """
    # Identity
    passport_id: str
    passport_uuid: str
    
    # Hardware Info
    wallet_address: str
    device_name: str
    device_family: str
    device_arch: str
    cpu_model: str
    cpu_cores: int
    ram_gb: int
    os_type: str
    
    # Lifecycle
    first_online: str
    last_attestation: Optional[str] = None
    is_active: bool = True
    
    # Statistics
    total_attestations: int = 0
    successful_attestations: int = 0
    total_rtc_earned: float = 0.0
    antiquity_multiplier: float = 1.0
    
    # History
    attestation_history: List[Dict] = field(default_factory=list)
    maintenance_history: List[Dict] = field(default_factory=list)
    ownership_history: List[Dict] = field(default_factory=list)
    
    # Verification
    verification_hash: str = ""
    qr_code_data: str = ""
    
    def generate_verification_hash(self) -> str:
        """Generate a cryptographic hash for verification."""
        data = f"{self.passport_id}{self.wallet_address}{self.first_online}{self.total_attestations}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def generate_qr_data(self, base_url: str = "https://rustchain.org/passport") -> str:
        """Generate QR code data URL for verification."""
        return f"{base_url}/{self.passport_id}?verify={self.verification_hash}"


class PassportLedger:
    """
    Manages the collection of all machine passports.
    Provides CRUD operations and statistics.
    """
    
    def __init__(self, storage_path: str = "passport_ledger.json"):
        self.storage_path = storage_path
        self.passports: Dict[str, MachinePassport] = {}
        self.load()
    
    def generate_passport_id(self, wallet: str, device_arch: str) -> str:
        """Generate a unique, human-readable passport ID."""
        arch_prefix = device_arch[:3].upper()
        wallet_short = wallet[:8] if len(wallet) >= 8 else wallet
        timestamp = datetime.now().strftime("%m%d")
        return f"RC-{arch_prefix}-{wallet_short}-{timestamp}"
    
    def create_passport(
        self,
        wallet_address: str,
        device_name: str,
        device_family: str,
        device_arch: str,
        cpu_model: str,
        cpu_cores: int,
        ram_gb: int,
        os_type: str,
    ) -> MachinePassport:
        """Create a new machine passport."""
        passport_id = self.generate_passport_id(wallet_address, device_arch)
        
        # Get multiplier for architecture
        arch_info = ARCH_TYPES.get(device_arch, ARCH_TYPES["modern"])
        
        passport = MachinePassport(
            passport_id=passport_id,
            passport_uuid=str(uuid.uuid4()),
            wallet_address=wallet_address,
            device_name=device_name,
            device_family=device_family,
            device_arch=device_arch,
            cpu_model=cpu_model,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            os_type=os_type,
            first_online=datetime.now().isoformat(),
            antiquity_multiplier=arch_info["multiplier"],
        )
        
        passport.verification_hash = passport.generate_verification_hash()
        passport.qr_code_data = passport.generate_qr_data()
        
        self.passports[passport_id] = passport
        self.save()
        
        return passport
    
    def record_attestation(
        self,
        passport_id: str,
        epoch: int,
        slot: int,
        passed: bool,
        fingerprint_score: float,
        rtc_earned: float = 0.0,
    ) -> Optional[MachinePassport]:
        """Record an attestation event for a passport."""
        if passport_id not in self.passports:
            return None
        
        passport = self.passports[passport_id]
        
        attestation = {
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "slot": slot,
            "passed": passed,
            "device_arch": passport.device_arch,
            "device_family": passport.device_family,
            "fingerprint_score": fingerprint_score,
        }
        
        passport.attestation_history.append(attestation)
        passport.total_attestations += 1
        if passed:
            passport.successful_attestations += 1
            passport.total_rtc_earned += rtc_earned * passport.antiquity_multiplier
        
        passport.last_attestation = datetime.now().isoformat()
        passport.verification_hash = passport.generate_verification_hash()
        
        self.save()
        return passport
    
    def add_maintenance_record(
        self,
        passport_id: str,
        event_type: str,
        description: str,
        technician: Optional[str] = None,
        cost_rtc: Optional[float] = None,
    ) -> Optional[MachinePassport]:
        """Add a maintenance record to a passport."""
        if passport_id not in self.passports:
            return None
        
        passport = self.passports[passport_id]
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "technician": technician,
            "cost_rtc": cost_rtc,
        }
        
        passport.maintenance_history.append(record)
        self.save()
        return passport
    
    def add_ownership_change(
        self,
        passport_id: str,
        to_wallet: str,
        transfer_type: str,
        price_rtc: Optional[float] = None,
    ) -> Optional[MachinePassport]:
        """Record an ownership change for a passport."""
        if passport_id not in self.passports:
            return None
        
        passport = self.passports[passport_id]
        
        record = {
            "from_wallet": passport.wallet_address,
            "to_wallet": to_wallet,
            "timestamp": datetime.now().isoformat(),
            "transfer_type": transfer_type,
            "price_rtc": price_rtc,
        }
        
        passport.ownership_history.append(record)
        passport.wallet_address = to_wallet  # Update current owner
        passport.verification_hash = passport.generate_verification_hash()
        
        self.save()
        return passport
    
    def get_passport(self, passport_id: str) -> Optional[MachinePassport]:
        """Get a passport by ID."""
        return self.passports.get(passport_id)
    
    def get_passports_by_wallet(self, wallet: str) -> List[MachinePassport]:
        """Get all passports owned by a wallet."""
        return [p for p in self.passports.values() if p.wallet_address == wallet]
    
    def get_passports_by_arch(self, arch: str) -> List[MachinePassport]:
        """Get all passports with a specific architecture."""
        return [p for p in self.passports.values() if p.device_arch == arch]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics for all passports."""
        total = len(self.passports)
        if total == 0:
            return {"total_passports": 0}
        
        active = sum(1 for p in self.passports.values() if p.is_active)
        total_attestations = sum(p.total_attestations for p in self.passports.values())
        total_earnings = sum(p.total_rtc_earned for p in self.passports.values())
        
        # Breakdown by architecture
        arch_breakdown = {}
        for p in self.passports.values():
            arch = p.device_arch
            if arch not in arch_breakdown:
                arch_breakdown[arch] = {"count": 0, "total_earnings": 0.0}
            arch_breakdown[arch]["count"] += 1
            arch_breakdown[arch]["total_earnings"] += p.total_rtc_earned
        
        return {
            "total_passports": total,
            "active_passports": active,
            "total_attestations": total_attestations,
            "total_rtc_earned": round(total_earnings, 6),
            "architecture_breakdown": arch_breakdown,
        }
    
    def save(self):
        """Save passports to JSON file."""
        data = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "passports": {pid: asdict(p) for pid, p in self.passports.items()},
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self):
        """Load passports from JSON file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for pid, pdata in data.get("passports", {}).items():
                passport = MachinePassport(**pdata)
                # Convert history lists from dicts if needed
                passport.attestation_history = pdata.get("attestation_history", [])
                passport.maintenance_history = pdata.get("maintenance_history", [])
                passport.ownership_history = pdata.get("ownership_history", [])
                self.passports[pid] = passport
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: Could not load passport ledger: {e}")


def generate_qr_code(data: str) -> str:
    """Generate a base64-encoded QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


if __name__ == "__main__":
    # Demo usage
    ledger = PassportLedger()
    
    # Create a sample passport
    passport = ledger.create_passport(
        wallet_address="9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
        device_name="PowerMac G5 Dual",
        device_family="PowerPC",
        device_arch="g5",
        cpu_model="PowerPC 970MP",
        cpu_cores=2,
        ram_gb=8,
        os_type="Linux",
    )
    
    print(f"Created passport: {passport.passport_id}")
    print(f"Verification hash: {passport.verification_hash}")
    print(f"QR data: {passport.qr_code_data}")