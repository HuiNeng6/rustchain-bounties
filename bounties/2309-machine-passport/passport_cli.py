#!/usr/bin/env python3
"""
RustChain Machine Passport CLI
Command-line interface for managing machine passports.
"""

import argparse
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passport_generator import PassportLedger, ARCH_TYPES
from passport_renderer import generate_passport_html, generate_passport_index
from rustchain_client import PassportDataFetcher, sync_passports_from_api


def cmd_create(args):
    """Create a new passport."""
    ledger = PassportLedger(args.ledger)
    
    passport = ledger.create_passport(
        wallet_address=args.wallet,
        device_name=args.name,
        device_family=args.family,
        device_arch=args.arch,
        cpu_model=args.cpu,
        cpu_cores=args.cores,
        ram_gb=args.ram,
        os_type=args.os,
    )
    
    print(f"\n✓ Created passport: {passport.passport_id}")
    print(f"  UUID: {passport.passport_uuid}")
    print(f"  Verification: {passport.verification_hash}")
    print(f"  Antiquity Bonus: {passport.antiquity_multiplier}x")
    
    if args.output:
        generate_passport_html(passport, args.output)
        print(f"  HTML: {args.output}")


def cmd_attest(args):
    """Record an attestation for a passport."""
    ledger = PassportLedger(args.ledger)
    
    passport = ledger.record_attestation(
        passport_id=args.passport_id,
        epoch=args.epoch,
        slot=args.slot,
        passed=args.passed,
        fingerprint_score=args.score,
        rtc_earned=args.rtc,
    )
    
    if not passport:
        print(f"✗ Passport not found: {args.passport_id}")
        return 1
    
    print(f"\n✓ Recorded attestation for {args.passport_id}")
    print(f"  Total attestations: {passport.total_attestations}")
    print(f"  Total RTC earned: {passport.total_rtc_earned:.6f}")
    
    return 0


def cmd_maintenance(args):
    """Add a maintenance record."""
    ledger = PassportLedger(args.ledger)
    
    passport = ledger.add_maintenance_record(
        passport_id=args.passport_id,
        event_type=args.type,
        description=args.description,
        technician=args.technician,
        cost_rtc=args.cost,
    )
    
    if not passport:
        print(f"✗ Passport not found: {args.passport_id}")
        return 1
    
    print(f"\n✓ Added maintenance record for {args.passport_id}")
    print(f"  Type: {args.type}")
    print(f"  Total maintenance events: {len(passport.maintenance_history)}")
    
    return 0


def cmd_transfer(args):
    """Record an ownership transfer."""
    ledger = PassportLedger(args.ledger)
    
    passport = ledger.add_ownership_change(
        passport_id=args.passport_id,
        to_wallet=args.to_wallet,
        transfer_type=args.type,
        price_rtc=args.price,
    )
    
    if not passport:
        print(f"✗ Passport not found: {args.passport_id}")
        return 1
    
    print(f"\n✓ Recorded ownership transfer for {args.passport_id}")
    print(f"  New owner: {args.to_wallet}")
    print(f"  Transfer type: {args.type}")
    
    return 0


def cmd_show(args):
    """Display passport details."""
    ledger = PassportLedger(args.ledger)
    passport = ledger.get_passport(args.passport_id)
    
    if not passport:
        print(f"✗ Passport not found: {args.passport_id}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"  PASSPORT: {passport.passport_id}")
    print(f"{'='*60}")
    print(f"\n  Identity")
    print(f"  --------")
    print(f"  UUID:      {passport.passport_uuid}")
    print(f"  Wallet:    {passport.wallet_address}")
    print(f"  Verified:  {passport.verification_hash}")
    
    print(f"\n  Hardware")
    print(f"  --------")
    print(f"  Name:      {passport.device_name}")
    print(f"  Family:    {passport.device_family}")
    print(f"  Arch:      {passport.device_arch}")
    print(f"  CPU:       {passport.cpu_model}")
    print(f"  Cores:     {passport.cpu_cores}")
    print(f"  RAM:       {passport.ram_gb} GB")
    print(f"  OS:        {passport.os_type}")
    
    print(f"\n  Statistics")
    print(f"  ----------")
    print(f"  First Online:       {passport.first_online[:10]}")
    print(f"  Last Attestation:   {passport.last_attestation[:19] if passport.last_attestation else 'Never'}")
    print(f"  Total Attestations: {passport.total_attestations}")
    print(f"  Success Rate:       {passport.successful_attestations}/{passport.total_attestations}")
    print(f"  RTC Earned:         {passport.total_rtc_earned:.6f}")
    print(f"  Antiquity Bonus:    {passport.antiquity_multiplier}x")
    
    if args.output:
        generate_passport_html(passport, args.output)
        print(f"\n  HTML exported to: {args.output}")
    
    return 0


def cmd_list(args):
    """List all passports."""
    ledger = PassportLedger(args.ledger)
    passports = list(ledger.passports.values())
    
    if args.arch:
        passports = [p for p in passports if p.device_arch == args.arch]
    
    if args.wallet:
        passports = [p for p in passports if args.wallet in p.wallet_address]
    
    print(f"\n{'='*80}")
    print(f"  {'ID':<20} {'Architecture':<12} {'Attestations':<14} {'RTC Earned':<15}")
    print(f"{'='*80}")
    
    for p in passports:
        print(f"  {p.passport_id:<20} {p.device_arch.upper():<12} {p.total_attestations:<14} {p.total_rtc_earned:.6f}")
    
    print(f"\n  Total: {len(passports)} passport(s)")
    
    if args.output:
        generate_passport_index(passports, args.output)
        print(f"\n  Index exported to: {args.output}")
    
    return 0


def cmd_stats(args):
    """Show ledger statistics."""
    ledger = PassportLedger(args.ledger)
    stats = ledger.get_statistics()
    
    print(f"\n{'='*50}")
    print(f"  LEDGER STATISTICS")
    print(f"{'='*50}")
    print(f"\n  Total Passports:    {stats.get('total_passports', 0)}")
    print(f"  Active Passports:   {stats.get('active_passports', 0)}")
    print(f"  Total Attestations: {stats.get('total_attestations', 0)}")
    print(f"  Total RTC Earned:   {stats.get('total_rtc_earned', 0):.6f}")
    
    print(f"\n  Architecture Breakdown:")
    for arch, data in stats.get("architecture_breakdown", {}).items():
        print(f"    {arch.upper():<12} {data['count']} passports, {data['total_earnings']:.2f} RTC")
    
    return 0


def cmd_sync(args):
    """Sync passports from RustChain API."""
    print("Syncing passports from RustChain API...")
    
    created = sync_passports_from_api(args.ledger)
    
    print(f"\n✓ Created {created} new passport(s)")
    
    if args.generate_html:
        ledger = PassportLedger(args.ledger)
        os.makedirs(args.output_dir, exist_ok=True)
        
        for passport in ledger.passports.values():
            generate_passport_html(
                passport,
                os.path.join(args.output_dir, f"passport_{passport.passport_id}.html")
            )
        
        generate_passport_index(
            list(ledger.passports.values()),
            os.path.join(args.output_dir, "index.html")
        )
        
        print(f"✓ Generated HTML files in {args.output_dir}/")
    
    return 0


def cmd_arch_types(args):
    """List supported architecture types."""
    print("\nSupported Architecture Types:")
    print(f"{'='*60}")
    print(f"{'Code':<15} {'Name':<20} {'Multiplier':<12} {'Era':<15}")
    print(f"{'='*60}")
    
    for code, info in ARCH_TYPES.items():
        print(f"{code:<15} {info['name']:<20} {info['multiplier']:<12} {info['era']:<15}")
    
    return 0


def cmd_export(args):
    """Export passports to JSON."""
    ledger = PassportLedger(args.ledger)
    
    import json
    from dataclasses import asdict
    
    data = {
        "exported_at": datetime.now().isoformat(),
        "statistics": ledger.get_statistics(),
        "passports": {pid: asdict(p) for pid, p in ledger.passports.items()},
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Exported {len(ledger.passports)} passports to {args.output}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="RustChain Machine Passport Ledger CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new passport
  python passport_cli.py create --wallet 9dRR... --name "PowerMac G5" --arch g5 --cpu "PowerPC 970MP"

  # Record an attestation
  python passport_cli.py attest RC-G5-9dRRMiHi-0323 --epoch 73 --passed --score 0.95

  # List all passports
  python passport_cli.py list

  # Show passport details
  python passport_cli.py show RC-G5-9dRRMiHi-0323

  # Sync from API
  python passport_cli.py sync --generate-html --output-dir passports
        """
    )
    
    parser.add_argument("--ledger", default="passport_ledger.json", help="Path to ledger JSON file")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new passport")
    create_parser.add_argument("--wallet", required=True, help="Wallet address")
    create_parser.add_argument("--name", required=True, help="Device name")
    create_parser.add_argument("--family", required=True, help="Device family (e.g., PowerPC, x86_64)")
    create_parser.add_argument("--arch", required=True, help="Architecture (e.g., g3, g4, g5)")
    create_parser.add_argument("--cpu", required=True, help="CPU model")
    create_parser.add_argument("--cores", type=int, default=1, help="CPU cores")
    create_parser.add_argument("--ram", type=int, default=1, help="RAM in GB")
    create_parser.add_argument("--os", default="Linux", help="Operating system")
    create_parser.add_argument("--output", help="Output HTML file path")
    create_parser.set_defaults(func=cmd_create)
    
    # Attest command
    attest_parser = subparsers.add_parser("attest", help="Record an attestation")
    attest_parser.add_argument("passport_id", help="Passport ID")
    attest_parser.add_argument("--epoch", type=int, required=True, help="Epoch number")
    attest_parser.add_argument("--slot", type=int, default=0, help="Slot number")
    attest_parser.add_argument("--passed", action="store_true", default=True, help="Attestation passed")
    attest_parser.add_argument("--score", type=float, default=0.85, help="Fingerprint score")
    attest_parser.add_argument("--rtc", type=float, default=0.0, help="RTC earned")
    attest_parser.set_defaults(func=cmd_attest)
    
    # Maintenance command
    maint_parser = subparsers.add_parser("maintenance", help="Add maintenance record")
    maint_parser.add_argument("passport_id", help="Passport ID")
    maint_parser.add_argument("--type", required=True, choices=["repair", "upgrade", "cleaning", "firmware", "other"])
    maint_parser.add_argument("--description", required=True, help="Description of maintenance")
    maint_parser.add_argument("--technician", help="Technician name")
    maint_parser.add_argument("--cost", type=float, help="Cost in RTC")
    maint_parser.set_defaults(func=cmd_maintenance)
    
    # Transfer command
    transfer_parser = subparsers.add_parser("transfer", help="Record ownership transfer")
    transfer_parser.add_argument("passport_id", help="Passport ID")
    transfer_parser.add_argument("--to-wallet", required=True, help="New owner wallet")
    transfer_parser.add_argument("--type", default="sale", choices=["sale", "gift", "inheritance"])
    transfer_parser.add_argument("--price", type=float, help="Sale price in RTC")
    transfer_parser.set_defaults(func=cmd_transfer)
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show passport details")
    show_parser.add_argument("passport_id", help="Passport ID")
    show_parser.add_argument("--output", help="Output HTML file path")
    show_parser.set_defaults(func=cmd_show)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all passports")
    list_parser.add_argument("--arch", help="Filter by architecture")
    list_parser.add_argument("--wallet", help="Filter by wallet address")
    list_parser.add_argument("--output", help="Output HTML index path")
    list_parser.set_defaults(func=cmd_list)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show ledger statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync passports from API")
    sync_parser.add_argument("--generate-html", action="store_true", help="Generate HTML files")
    sync_parser.add_argument("--output-dir", default="passports", help="Output directory for HTML files")
    sync_parser.set_defaults(func=cmd_sync)
    
    # Arch types command
    arch_parser = subparsers.add_parser("arch-types", help="List supported architecture types")
    arch_parser.set_defaults(func=cmd_arch_types)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export passports to JSON")
    export_parser.add_argument("--output", default="passports_export.json", help="Output file path")
    export_parser.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)