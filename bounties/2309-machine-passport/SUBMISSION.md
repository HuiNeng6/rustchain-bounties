# RustChain Bounty #2309 Submission

## Bounty: Machine Passport Ledger (70 RTC)

### Wallet Address
```
9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
```

## Implementation Summary

### Features Implemented

1. **Unique Identity Profiles**
   - Each mining device receives a unique passport ID (e.g., `RC-G5-9dRRMiHi-0323`)
   - UUID for internal tracking
   - Cryptographic verification hash

2. **Complete Historical Records**
   - First online date tracking
   - Architecture type classification (68K, G3, G4, G5, SPARC, MIPS, POWER8, Core 2 Duo, Apple Silicon)
   - Total attestation count with success rate
   - Total RTC earnings with antiquity bonus applied
   - Maintenance history (repairs, upgrades, cleaning, firmware)
   - Ownership transfer records

3. **Visual Passport Page**
   - Beautiful HTML passport with dark theme
   - Hardware profile card
   - QR code for on-chain verification
   - Statistics dashboard (attestations, success rate, RTC earned, active days)
   - History tables (attestations, maintenance, ownership)

4. **QR Code Verification**
   - Base64-encoded QR code embedded in HTML
   - Links to `https://rustchain.org/passport/{id}?verify={hash}`

### Files Created

```
bounties/2309-machine-passport/
├── README.md                 # Documentation
├── passport_generator.py     # Core data model and ledger
├── passport_renderer.py      # HTML generation
├── passport_template.html    # HTML template
├── passport_cli.py           # Command-line interface
├── rustchain_client.py       # API client
├── demo.py                   # Demo script
├── requirements.txt          # Python dependencies
├── demo_ledger.json          # Sample ledger data
└── passports/                # Generated HTML passports
    ├── index.html
    └── passport_*.html
```

### Architecture Support

| Arch | Name | Multiplier | Era |
|------|------|------------|-----|
| 68k | Motorola 68K | 3.0x | 1984-1996 |
| g3 | PowerPC G3 | 1.8x | 1997-2004 |
| g4 | PowerPC G4 | 2.5x | 1999-2006 |
| g5 | PowerPC G5 | 2.0x | 2003-2006 |
| sparc | SPARC | 2.2x | 1987-2010 |
| mips | MIPS | 2.0x | 1985-2008 |
| power8 | POWER8 | 1.5x | 2013-2018 |
| core2duo | Core 2 Duo | 1.3x | 2006-2011 |
| apple_silicon | Apple Silicon | 1.2x | 2020-present |
| modern | Modern x86_64/ARM | 1.0x | 2010-present |

### CLI Usage

```bash
# Create a passport
python passport_cli.py create \
  --wallet 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT \
  --name "PowerMac G5" \
  --family PowerPC \
  --arch g5 \
  --cpu "PowerPC 970MP"

# Record attestation
python passport_cli.py attest RC-G5-... --epoch 73 --passed --rtc 0.5

# Add maintenance
python passport_cli.py maintenance RC-G5-... --type upgrade --description "RAM upgrade"

# Transfer ownership
python passport_cli.py transfer RC-G5-... --to-wallet NewWallet --type sale --price 10

# List passports
python passport_cli.py list

# Sync from API
python passport_cli.py sync --generate-html
```

### API Integration

The system integrates with RustChain API:
- `GET /api/miners` - Fetch active miners
- `GET /wallet/balance` - Get wallet balance
- `GET /epoch` - Current epoch info

When API is unavailable, mock data is used for demonstration.

### Testing

Run the demo to see all features:
```bash
pip install qrcode pillow
python demo.py
```

This creates 5 sample passports with attestations, maintenance records, and ownership transfers, then generates HTML files.

---

## Verification

The implementation fulfills all bounty requirements:

- [x] Generate unique identity profile for each mining device
- [x] Record first online date
- [x] Track architecture type (68K, G3, G4, G5, SPARC, MIPS, POWER8, etc.)
- [x] Record total attestation count
- [x] Track total RTC earnings
- [x] Maintain maintenance history
- [x] Track ownership changes
- [x] Create visual passport page
- [x] Include QR code for on-chain verification
- [x] Works with mock data when API unavailable