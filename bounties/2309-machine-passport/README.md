# RustChain Machine Passport Ledger - Bounty #2309

A unique identity passport system for vintage hardware miners on the RustChain network.

## 🎯 Bounty Details

- **Bounty ID**: #2309
- **Reward**: 70 RTC
- **Wallet**: `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`

## 📋 Features

### 1. Unique Identity Profiles
Each mining device receives a unique passport with:
- Passport ID (human-readable, e.g., `RC-G5-9dRRMiHi-0323`)
- UUID for internal tracking
- Cryptographic verification hash

### 2. Complete Historical Records
- **First Online Date**: When the device first joined the network
- **Architecture Type**: 68K, G3, G4, G5, SPARC, MIPS, POWER8, Core 2 Duo, Apple Silicon, Modern
- **Total Attestations**: Number of proof-of-authenticity submissions
- **Total RTC Earnings**: Cumulative rewards with antiquity bonus applied
- **Maintenance History**: Repairs, upgrades, firmware updates, cleaning
- **Ownership Records**: Transfers, sales, gifts between wallets

### 3. Visual Passport Page
Beautiful HTML passport with:
- Hardware profile card
- QR code for on-chain verification
- Statistics dashboard
- Attestation history table
- Maintenance and ownership logs

### 4. QR Code Verification
Each passport includes a QR code linking to:
```
https://rustchain.org/passport/{passport_id}?verify={verification_hash}
```

## 🚀 Quick Start

### Prerequisites
```bash
pip install qrcode pillow
```

### Create a Passport
```bash
python passport_cli.py create \
  --wallet 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT \
  --name "PowerMac G5 Dual" \
  --family PowerPC \
  --arch g5 \
  --cpu "PowerPC 970MP @ 2.3GHz" \
  --cores 2 \
  --ram 8 \
  --os Linux \
  --output passport.html
```

### Record an Attestation
```bash
python passport_cli.py attest RC-G5-9dRRMiHi-0323 \
  --epoch 73 \
  --passed \
  --score 0.95 \
  --rtc 0.5
```

### Add Maintenance Record
```bash
python passport_cli.py maintenance RC-G5-9dRRMiHi-0323 \
  --type upgrade \
  --description "Upgraded RAM from 4GB to 8GB" \
  --cost 0.1
```

### Transfer Ownership
```bash
python passport_cli.py transfer RC-G5-9dRRMiHi-0323 \
  --to-wallet NewOwnerWalletAddress123 \
  --type sale \
  --price 10.0
```

### List All Passports
```bash
python passport_cli.py list
python passport_cli.py list --arch g5 --wallet 9dRRMiHi
```

### Show Passport Details
```bash
python passport_cli.py show RC-G5-9dRRMiHi-0323
python passport_cli.py show RC-G5-9dRRMiHi-0323 --output passport.html
```

### Sync from RustChain API
```bash
python passport_cli.py sync --generate-html --output-dir passports
```

## 📁 File Structure

```
bounties/2309-machine-passport/
├── README.md                 # This file
├── passport_generator.py     # Core passport data model and ledger
├── passport_renderer.py      # HTML passport generation
├── passport_template.html    # HTML template for passports
├── passport_cli.py           # Command-line interface
├── rustchain_client.py       # RustChain API client
├── passport_ledger.json      # Default ledger storage
└── passports/                # Generated HTML passports
    ├── index.html
    └── passport_*.html
```

## 🏗️ Architecture Types

| Code | Name | Multiplier | Era |
|------|------|------------|-----|
| `68k` | Motorola 68K | 3.0x | 1984-1996 |
| `g3` | PowerPC G3 | 1.8x | 1997-2004 |
| `g4` | PowerPC G4 | 2.5x | 1999-2006 |
| `g5` | PowerPC G5 | 2.0x | 2003-2006 |
| `sparc` | SPARC | 2.2x | 1987-2010 |
| `mips` | MIPS | 2.0x | 1985-2008 |
| `power8` | POWER8 | 1.5x | 2013-2018 |
| `core2duo` | Core 2 Duo | 1.3x | 2006-2011 |
| `apple_silicon` | Apple Silicon | 1.2x | 2020-present |
| `modern` | Modern x86_64/ARM | 1.0x | 2010-present |

## 🔧 API Integration

The system integrates with the RustChain node API:

- `GET /health` - Node health check
- `GET /epoch` - Current epoch info
- `GET /api/miners` - List active miners
- `GET /wallet/balance?miner_id=...` - Wallet balance
- `POST /attest/challenge` - Request attestation nonce
- `POST /attest/submit` - Submit attestation
- `POST /epoch/enroll` - Enroll for rewards

## 📊 Passport Data Model

```json
{
  "passport_id": "RC-G5-9dRRMiHi-0323",
  "passport_uuid": "uuid-v4",
  "wallet_address": "9dRRMiHi...",
  "device_name": "PowerMac G5 Dual",
  "device_family": "PowerPC",
  "device_arch": "g5",
  "cpu_model": "PowerPC 970MP @ 2.3GHz",
  "cpu_cores": 2,
  "ram_gb": 8,
  "os_type": "Linux",
  "first_online": "2026-03-23T11:10:00",
  "last_attestation": "2026-03-23T15:30:00",
  "total_attestations": 142,
  "successful_attestations": 140,
  "total_rtc_earned": 284.5,
  "antiquity_multiplier": 2.0,
  "verification_hash": "a1b2c3d4e5f6",
  "attestation_history": [...],
  "maintenance_history": [...],
  "ownership_history": [...]
}
```

## 🎨 Visual Passport Example

The generated HTML passport includes:

1. **Header** - Passport title and verification badge
2. **QR Section** - Scan to verify on-chain
3. **Hardware Profile** - Device specs and architecture
4. **Statistics Dashboard** - Attestations, success rate, RTC earned
5. **History Tables** - Recent attestations, maintenance, ownership
6. **Footer** - Links to on-chain verification

## 🔐 Verification

Each passport generates a cryptographic hash for verification:
```python
hash = SHA256(passport_id + wallet_address + first_online + total_attestations)[:16]
```

This hash is embedded in the QR code URL for on-chain verification.

## 📝 License

MIT License - Part of RustChain Bounties

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a PR with your wallet address

---

**Built for RustChain Bounty #2309** 🏴‍☠️