#!/bin/bash
# Demo script for RustChain Floppy Witness Kit

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     RUSTCHAIN FLOPPY WITNESS KIT - DEMO SCRIPT               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Build if needed
if [ ! -f target/release/rustchain-witness ]; then
    echo "Building release binary..."
    cargo build --release
fi

echo ""
echo "1. Showing ASCII banner..."
./target/release/rustchain-witness banner

echo ""
echo "2. Writing epoch 500 witness to floppy image..."
./target/release/rustchain-witness write --epoch 500 --device demo.img --format img

echo ""
echo "3. Reading witness from floppy image..."
./target/release/rustchain-witness read --device demo.img

echo ""
echo "4. Writing epoch 501 witness to FAT file..."
./target/release/rustchain-witness write --epoch 501 --device witness.rcw --format fat

echo ""
echo "5. Writing epoch 502 witness to QR code..."
./target/release/rustchain-witness write --epoch 502 --device witness.png --format qr

echo ""
echo "6. Verifying witness..."
./target/release/rustchain-witness verify --file demo.img

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DEMO COMPLETE!                            ║"
echo "║                                                              ║"
echo "║  Files created:                                              ║"
echo "║    - demo.img (1.44MB floppy image)                          ║"
echo "║    - witness.rcw (FAT file)                                  ║"
echo "║    - witness.png (QR code)                                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"