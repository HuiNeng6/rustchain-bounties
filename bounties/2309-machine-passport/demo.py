#!/usr/bin/env python3
"""
Demo script for RustChain Machine Passport Ledger.
Creates sample passports and demonstrates all features.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passport_generator import PassportLedger, ARCH_TYPES
from passport_renderer import generate_passport_html, generate_passport_index
from rustchain_client import PassportDataFetcher


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_create_passports():
    """Demo: Create sample passports for various hardware types."""
    print_header("Creating Sample Passports")
    
    ledger = PassportLedger("demo_ledger.json")
    
    # Sample vintage hardware devices
    devices = [
        {
            "wallet_address": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
            "device_name": "PowerMac G5 Quad",
            "device_family": "PowerPC",
            "device_arch": "g5",
            "cpu_model": "PowerPC 970MP @ 2.5GHz",
            "cpu_cores": 4,
            "ram_gb": 16,
            "os_type": "Linux",
        },
        {
            "wallet_address": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
            "device_name": "PowerBook G4 Titanium",
            "device_family": "PowerPC",
            "device_arch": "g4",
            "cpu_model": "PowerPC 7455 @ 1GHz",
            "cpu_cores": 1,
            "ram_gb": 1,
            "os_type": "Linux",
        },
        {
            "wallet_address": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
            "device_name": "iMac G3 DV",
            "device_family": "PowerPC",
            "device_arch": "g3",
            "cpu_model": "PowerPC 750 @ 400MHz",
            "cpu_cores": 1,
            "ram_gb": 0.5,
            "os_type": "Linux",
        },
        {
            "wallet_address": "ExampleWallet123456789",
            "device_name": "Sun SPARCstation 20",
            "device_family": "SPARC",
            "device_arch": "sparc",
            "cpu_model": "SuperSPARC II @ 75MHz",
            "cpu_cores": 1,
            "ram_gb": 0.25,
            "os_type": "NetBSD",
        },
        {
            "wallet_address": "ExampleWallet987654321",
            "device_name": "SGI Indy",
            "device_family": "MIPS",
            "device_arch": "mips",
            "cpu_model": "R4600 @ 133MHz",
            "cpu_cores": 1,
            "ram_gb": 0.128,
            "os_type": "IRIX",
        },
    ]
    
    for device in devices:
        passport = ledger.create_passport(**device)
        print(f"[OK] Created: {passport.passport_id}")
        print(f"  Device: {passport.device_name}")
        print(f"  Arch: {passport.device_arch.upper()} ({passport.antiquity_multiplier}x bonus)")
    
    return ledger


def demo_record_attestations(ledger):
    """Demo: Record attestation history."""
    print_header("Recording Attestations")
    
    for passport_id, passport in ledger.passports.items():
        # Add several attestations
        for i in range(5):
            ledger.record_attestation(
                passport_id=passport_id,
                epoch=73 + i,
                slot=10554 + i * 144,
                passed=True,
                fingerprint_score=0.80 + i * 0.03,
                rtc_earned=0.3 + i * 0.1,
            )
        
        print(f"[OK] {passport_id}: 5 attestations recorded")
        print(f"  Total: {ledger.passports[passport_id].total_attestations}")
        print(f"  Earned: {ledger.passports[passport_id].total_rtc_earned:.4f} RTC")


def demo_maintenance_records(ledger):
    """Demo: Add maintenance history."""
    print_header("Adding Maintenance Records")
    
    # Add maintenance to the G5
    passport_id = list(ledger.passports.keys())[0]  # First passport
    
    maintenance_events = [
        ("upgrade", "Upgraded RAM from 8GB to 16GB", 0.5),
        ("cleaning", "Cleaned dust from heatsinks and fans", None),
        ("firmware", "Updated Open Firmware to latest version", None),
    ]
    
    for event_type, description, cost in maintenance_events:
        ledger.add_maintenance_record(
            passport_id=passport_id,
            event_type=event_type,
            description=description,
            cost_rtc=cost,
        )
        print(f"[OK] Added: {event_type} - {description[:40]}...")


def demo_ownership_transfer(ledger):
    """Demo: Record ownership transfer."""
    print_header("Recording Ownership Transfer")
    
    passport_id = list(ledger.passports.keys())[0]  # First passport
    
    ledger.add_ownership_change(
        passport_id=passport_id,
        to_wallet="NewOwnerWallet123456789",
        transfer_type="sale",
        price_rtc=15.0,
    )
    
    passport = ledger.passports[passport_id]
    print(f"[OK] Transferred: {passport_id}")
    print(f"  New owner: {passport.wallet_address[:20]}...")


def demo_generate_html(ledger):
    """Demo: Generate HTML passports."""
    print_header("Generating HTML Passports")
    
    output_dir = "passports"
    os.makedirs(output_dir, exist_ok=True)
    
    for passport in ledger.passports.values():
        output_path = os.path.join(output_dir, f"passport_{passport.passport_id}.html")
        generate_passport_html(passport, output_path)
    
    # Generate index
    index_path = os.path.join(output_dir, "index.html")
    generate_passport_index(list(ledger.passports.values()), index_path)
    
    print(f"[OK] Generated {len(ledger.passports)} passport pages")
    print(f"[OK] Index created at: {index_path}")


def demo_show_statistics(ledger):
    """Demo: Show ledger statistics."""
    print_header("Ledger Statistics")
    
    stats = ledger.get_statistics()
    
    print(f"Total Passports:    {stats.get('total_passports', 0)}")
    print(f"Active Passports:   {stats.get('active_passports', 0)}")
    print(f"Total Attestations: {stats.get('total_attestations', 0)}")
    print(f"Total RTC Earned:   {stats.get('total_rtc_earned', 0):.6f}")
    
    print(f"\nArchitecture Breakdown:")
    for arch, data in stats.get("architecture_breakdown", {}).items():
        print(f"  {arch.upper():<12} {data['count']} passports, {data['total_earnings']:.2f} RTC")


def demo_api_sync():
    """Demo: Sync from RustChain API."""
    print_header("Syncing from RustChain API")
    
    fetcher = PassportDataFetcher()
    
    # Try to fetch from API (will use mock if unavailable)
    miners = fetcher.fetch_miner_data()
    print(f"[OK] Fetched {len(miners)} miners from API")
    
    epoch = fetcher.get_epoch_info()
    print(f"[OK] Current epoch: {epoch.get('epoch', '?')}")
    print(f"  Enrolled miners: {epoch.get('enrolled_miners', '?')}")


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║     RustChain Machine Passport Ledger Demo                  ║
║     Bounty #2309 - 70 RTC                                   ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # Create passports
    ledger = demo_create_passports()
    
    # Record attestations
    demo_record_attestations(ledger)
    
    # Add maintenance records
    demo_maintenance_records(ledger)
    
    # Record ownership transfer
    demo_ownership_transfer(ledger)
    
    # Show statistics
    demo_show_statistics(ledger)
    
    # Generate HTML
    demo_generate_html(ledger)
    
    # Try API sync
    demo_api_sync()
    
    print("\n" + "="*60)
    print("  Demo Complete!")
    print("="*60)
    print(f"\n  View generated passports in: passports/")
    print(f"  Ledger saved to: demo_ledger.json")
    print("\n  Use the CLI for more operations:")
    print("    python passport_cli.py --help")
    print()


if __name__ == "__main__":
    main()