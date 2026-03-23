#!/usr/bin/env python3
"""
Passport Renderer - Generates HTML passport pages from passport data.
Uses the passport_template.html template to create visual passports.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
import base64
import re

try:
    import qrcode
    from io import BytesIO
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

from passport_generator import MachinePassport, generate_qr_code


def generate_passport_html(passport: MachinePassport, output_path: str = None) -> str:
    """
    Generate an HTML passport page from a MachinePassport.
    
    Args:
        passport: The MachinePassport object to render
        output_path: Optional path to save the HTML file
    
    Returns:
        The generated HTML string
    """
    # Read template
    template_path = os.path.join(os.path.dirname(__file__), "passport_template.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Generate QR code
    qr_base64 = ""
    if QR_AVAILABLE:
        try:
            qr_base64 = generate_qr_code(passport.qr_code_data)
        except Exception as e:
            print(f"Warning: Could not generate QR code: {e}")
    
    # Calculate derived values
    success_rate = 0
    if passport.total_attestations > 0:
        success_rate = round((passport.successful_attestations / passport.total_attestations) * 100, 1)
    
    # Calculate active days
    first_online = datetime.fromisoformat(passport.first_online)
    active_days = (datetime.now() - first_online).days
    
    # Prepare attestation history for display (last 10)
    attestation_html = ""
    for att in passport.attestation_history[-10:]:
        status_class = "status-passed" if att.get("passed") else "status-failed"
        status_text = "✓ Passed" if att.get("passed") else "✗ Failed"
        timestamp_short = att.get("timestamp", "")[:19].replace("T", " ")
        
        attestation_html += f"""
        <tr>
            <td>{timestamp_short}</td>
            <td>{att.get('epoch', '-')}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{att.get('fingerprint_score', '-'):.2f}</td>
        </tr>"""
    
    # Prepare maintenance history
    maintenance_html = ""
    has_maintenance = len(passport.maintenance_history) > 0
    for maint in passport.maintenance_history[-5:]:
        timestamp_short = maint.get("timestamp", "")[:10]
        maintenance_html += f"""
        <tr>
            <td>{timestamp_short}</td>
            <td>{maint.get('event_type', '-')}</td>
            <td>{maint.get('description', '-')}</td>
            <td>{maint.get('cost_rtc', '-') or '-'}</td>
        </tr>"""
    
    # Prepare ownership history
    ownership_html = ""
    has_ownership = len(passport.ownership_history) > 0
    for own in passport.ownership_history[-5:]:
        timestamp_short = own.get("timestamp", "")[:10]
        from_short = own.get("from_wallet", "")[:8] + "..." if own.get("from_wallet") else "-"
        to_short = own.get("to_wallet", "")[:8] + "..." if own.get("to_wallet") else "-"
        ownership_html += f"""
        <tr>
            <td>{timestamp_short}</td>
            <td>{from_short}</td>
            <td>{to_short}</td>
            <td>{own.get('transfer_type', '-')}</td>
        </tr>"""
    
    # Replace template variables
    html = template
    
    # Simple replacements
    replacements = {
        "{{passport_id}}": passport.passport_id,
        "{{verification_hash}}": passport.verification_hash,
        "{{qr_code_base64}}": qr_base64,
        "{{wallet_address}}": passport.wallet_address,
        "{{device_name}}": passport.device_name,
        "{{device_arch}}": passport.device_arch.upper(),
        "{{cpu_model}}": passport.cpu_model,
        "{{cpu_cores}}": str(passport.cpu_cores),
        "{{ram_gb}}": str(passport.ram_gb),
        "{{os_type}}": passport.os_type,
        "{{antiquity_multiplier}}": f"{passport.antiquity_multiplier}x",
        "{{total_attestations}}": str(passport.total_attestations),
        "{{success_rate}}": str(success_rate),
        "{{total_rtc_earned}}": f"{passport.total_rtc_earned:.6f}",
        "{{active_days}}": str(active_days),
        "{{first_online}}": passport.first_online[:10],
    }
    
    for key, value in replacements.items():
        html = html.replace(key, value)
    
    # Handle conditional sections
    # Attestation history
    att_pattern = r"\{\{#attestation_history\}\}(.*?)\{\{/attestation_history\}\}"
    if attestation_html:
        html = re.sub(att_pattern, attestation_html, html, flags=re.DOTALL)
    else:
        html = re.sub(att_pattern, "<tr><td colspan='4'>No attestations yet</td></tr>", html, flags=re.DOTALL)
    
    # Maintenance section
    if has_maintenance:
        maint_pattern = r"\{\{#has_maintenance\}\}(.*?)\{\{/has_maintenance\}\}"
        maint_inner_pattern = r"\{\{#maintenance_history\}\}(.*?)\{\{/maintenance_history\}\}"
        html = re.sub(maint_inner_pattern, maintenance_html, html, flags=re.DOTALL)
        html = re.sub(maint_pattern, r"\1", html, flags=re.DOTALL)
    else:
        maint_pattern = r"\{\{#has_maintenance\}\}.*?\{\{/has_maintenance\}\}"
        html = re.sub(maint_pattern, "", html, flags=re.DOTALL)
    
    # Ownership section
    if has_ownership:
        own_pattern = r"\{\{#has_ownership\}\}(.*?)\{\{/has_ownership\}\}"
        own_inner_pattern = r"\{\{#ownership_history\}\}(.*?)\{\{/ownership_history\}\}"
        html = re.sub(own_inner_pattern, ownership_html, html, flags=re.DOTALL)
        html = re.sub(own_pattern, r"\1", html, flags=re.DOTALL)
    else:
        own_pattern = r"\{\{#has_ownership\}\}.*?\{\{/has_ownership\}\}"
        html = re.sub(own_pattern, "", html, flags=re.DOTALL)
    
    # Save to file if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Passport saved to: {output_path}")
    
    return html


def generate_passport_index(passports: list, output_path: str = "index.html") -> str:
    """
    Generate an index page listing all passports.
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RustChain Machine Passport Ledger</title>
    <style>
        :root {{
            --primary: #1a1a2e;
            --secondary: #16213e;
            --accent: #e94560;
            --gold: #f4a300;
            --text: #eaeaea;
            --muted: #8b8b8b;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: var(--text);
            min-height: 100vh;
            padding: 40px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: var(--gold);
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: var(--muted);
            margin-bottom: 30px;
        }}
        
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            color: var(--gold);
        }}
        
        .stat-label {{
            color: var(--muted);
            font-size: 0.9em;
        }}
        
        .passports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .passport-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .passport-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .passport-id {{
            color: var(--gold);
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .arch-badge {{
            background: linear-gradient(135deg, var(--gold) 0%, #ff8c00 100%);
            color: var(--primary);
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        
        .card-info {{
            display: grid;
            gap: 8px;
            margin-bottom: 15px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
        }}
        
        .info-label {{
            color: var(--muted);
        }}
        
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .rtc-earned {{
            color: var(--accent);
            font-weight: bold;
        }}
        
        .view-link {{
            color: var(--accent);
            text-decoration: none;
            font-size: 0.9em;
        }}
        
        .view-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Machine Passport Ledger</h1>
        <p class="subtitle">RustChain Vintage Hardware Identity Registry</p>
        
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{len(passports)}</div>
                <div class="stat-label">Total Passports</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for p in passports if p.is_active)}</div>
                <div class="stat-label">Active Machines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(p.total_attestations for p in passports)}</div>
                <div class="stat-label">Total Attestations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(p.total_rtc_earned for p in passports):.2f}</div>
                <div class="stat-label">Total RTC Earned</div>
            </div>
        </div>
        
        <div class="passports-grid">
"""
    
    for p in passports:
        html += f"""
            <div class="passport-card">
                <div class="card-header">
                    <span class="passport-id">{p.passport_id}</span>
                    <span class="arch-badge">{p.device_arch.upper()}</span>
                </div>
                <div class="card-info">
                    <div class="info-row">
                        <span class="info-label">Device</span>
                        <span>{p.device_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">CPU</span>
                        <span>{p.cpu_model[:25]}...</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Attestations</span>
                        <span>{p.total_attestations}</span>
                    </div>
                </div>
                <div class="card-footer">
                    <span class="rtc-earned">{p.total_rtc_earned:.4f} RTC</span>
                    <a href="passport_{p.passport_id}.html" class="view-link">View Passport →</a>
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Index saved to: {output_path}")
    
    return html


if __name__ == "__main__":
    # Demo: Generate sample passports
    from passport_generator import PassportLedger
    
    # Create sample data
    ledger = PassportLedger("demo_ledger.json")
    
    # Create sample passports
    sample_devices = [
        {
            "wallet_address": "9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT",
            "device_name": "PowerMac G5 Dual",
            "device_family": "PowerPC",
            "device_arch": "g5",
            "cpu_model": "PowerPC 970MP @ 2.3GHz",
            "cpu_cores": 2,
            "ram_gb": 8,
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
    ]
    
    for device in sample_devices:
        passport = ledger.create_passport(**device)
        
        # Add sample attestations
        for i in range(5):
            ledger.record_attestation(
                passport.passport_id,
                epoch=73 + i,
                slot=10554 + i * 144,
                passed=True,
                fingerprint_score=0.85 + i * 0.02,
                rtc_earned=0.5 + i * 0.1,
            )
    
    # Generate HTML pages
    output_dir = "passports"
    os.makedirs(output_dir, exist_ok=True)
    
    for passport in ledger.passports.values():
        generate_passport_html(
            passport,
            output_path=os.path.join(output_dir, f"passport_{passport.passport_id}.html")
        )
    
    # Generate index
    generate_passport_index(
        list(ledger.passports.values()),
        output_path=os.path.join(output_dir, "index.html")
    )
    
    print(f"\nGenerated {len(ledger.passports)} passport pages in {output_dir}/")