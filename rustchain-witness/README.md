# RustChain Floppy Witness Kit

> **Compact epoch proofs for 1.44MB media — Block proofs carried by sneakernet into air-gapped or museum-grade machines.**

A tiny RustChain epoch witness format that fits on old media — 1.44MB floppies, ZIP disks, even QR codes. It should feel less like a backup and more like a **portable relic of the chain.**

## Features

- **Compact format**: <100KB per epoch witness
- **14,000+ epochs** fit on a single 1.44MB floppy
- **Multiple output formats**:
  - Raw floppy image (`.img`)
  - FAT file (for ZIP disks)
  - QR code (for really small witnesses)
- **Verification** against live chain state
- **ASCII art** headers for that retro feel

## Installation

```bash
cd rustchain-witness
cargo build --release
```

The binary will be at `target/release/rustchain-witness`.

## Usage

### Write Epoch Witness

Write epoch 500 to a floppy image:
```bash
rustchain-witness write --epoch 500 --device witness.img --format img
```

Write to FAT file (ZIP disk):
```bash
rustchain-witness write --epoch 500 --device /mnt/zip/witness.rcw --format fat
```

Write to QR code:
```bash
rustchain-witness write --epoch 500 --device witness.png --format qr
```

Options:
- `--epoch`: Epoch number to witness
- `--device`: Output device or file path
- `--format`: Output format (`img`, `fat`, `qr`)
- `--node`: Node API endpoint (default: http://50.28.86.131:8080)

### Read Epoch Witness

Read witness from device:
```bash
rustchain-witness read --device witness.img
```

Output as JSON:
```bash
rustchain-witness read --device witness.img --format json
```

Output as hex:
```bash
rustchain-witness read --device witness.img --format hex
```

### Verify Witness

Verify witness against current chain state:
```bash
rustchain-witness verify --file witness.img
```

The verifier checks:
- Settlement hash matches
- Commitment hash matches
- Merkle root matches
- Merkle proof is valid

### Show ASCII Banner

```bash
rustchain-witness banner
```

## Witness Format

### Epoch Witness Structure

```
Epoch Witness (<100KB):
├── Version (2 bytes)
├── Epoch number (8 bytes)
├── Timestamp (8 bytes)
├── Miners (variable)
│   ├── Miner ID (variable)
│   └── Arch hash (8 bytes)
├── Settlement hash (32 bytes)
├── Ergo TX ID (32 bytes)
├── Commitment hash (32 bytes)
└── Merkle proof
    ├── Root (32 bytes)
    ├── Path (variable)
    └── Index (8 bytes)
```

### File Format

```
Witness File:
├── Header (64 bytes)
│   ├── Magic ("RCW\0")
│   ├── Version (2 bytes)
│   ├── Witness count (4 bytes)
│   ├── Total size (4 bytes)
│   ├── Created timestamp (8 bytes)
│   └── Reserved (46 bytes)
└── Witnesses (variable)
    ├── Length (2 bytes)
    └── Witness data (variable)
```

## Size Calculations

| Component | Size |
|-----------|------|
| Header | 64 bytes |
| Epoch data | ~50 bytes |
| Per-miner overhead | ~20 bytes |
| Merkle proof (4 levels) | ~128 bytes |
| **Typical witness** | **~500-2000 bytes** |

With 10 miners and a 4-level Merkle proof:
- Single witness: ~1KB
- Floppy capacity: ~14,000 witnesses
- ZIP disk (100MB): ~100,000 witnesses

## Use Cases

1. **Air-gapped verification**: Transfer epoch proofs to offline machines
2. **Museum exhibits**: Display real blockchain data on period-correct hardware
3. **Cold storage**: Archive chain state on physical media
4. **Sneakernet**: Carry proofs across networks physically

## ASCII Art

The kit includes beautiful ASCII art for:
- Boot banner
- Floppy disk label
- QR code label

Run `rustchain-witness banner` to see it!

## API Integration

The tool fetches epoch data from RustChain nodes via the REST API:

```
GET /api/epoch/{epoch}
```

Response includes:
- Timestamp
- Miner lineup (IDs + architectures)
- Settlement hash
- Ergo anchor TX ID
- Commitment hash
- Merkle proof

## Building for Retro Platforms

Cross-compile for vintage hardware:
```bash
# For 16-bit DOS (8086)
rustup target add i686-pc-windows-msvc
cargo build --target i686-pc-windows-msvc --release

# For 32-bit Linux
rustup target add i686-unknown-linux-gnu
cargo build --target i686-unknown-linux-gnu --release
```

## Contributing

This is part of the RustChain bounties program. See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](../LICENSE) for details.

---

**Part of the [RustChain](https://github.com/Scottcjn/RustChain) ecosystem**

*"Proof of Antiquity on Vintage Hardware"*