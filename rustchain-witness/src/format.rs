//! Output Format Handlers
//!
//! Supports: raw floppy image (.img), ZIP disk (FAT file), QR code

use anyhow::{Result, Context};
use std::fs::{self, File};
use std::io::{BufWriter, Read, Write};
use std::path::Path;

use crate::witness::{EpochWitness, WitnessHeader, FLOPPY_SIZE, MAGIC};

/// Format type for output
#[derive(Debug, Clone, Copy)]
pub enum Format {
    /// Raw floppy image (1.44MB)
    FloppyImage,
    /// FAT file (for ZIP disk)
    FatFile,
    /// QR code image
    QrCode,
}

impl Format {
    pub fn from_str(s: &str) -> Result<Self> {
        match s.to_lowercase().as_str() {
            "img" | "image" | "floppy" => Ok(Self::FloppyImage),
            "fat" | "zip" | "disk" => Ok(Self::FatFile),
            "qr" | "qrcode" | "qr-code" => Ok(Self::QrCode),
            _ => anyhow::bail!("Unknown format: {}. Use: img, fat, qr", s),
        }
    }
}

/// Write witness to floppy image
pub fn write_floppy_image(path: &str, witnesses: &[EpochWitness]) -> Result<()> {
    let total_size: usize = witnesses.iter().map(|w| w.size()).sum();
    let header = WitnessHeader::new(witnesses.len() as u32, total_size as u32);
    
    let mut file = File::create(path)
        .with_context(|| format!("Failed to create: {}", path))?;
    let mut writer = BufWriter::new(&mut file);
    
    // Write header
    let header_bytes = bincode::serialize(&header)?;
    writer.write_all(&header_bytes)?;
    
    // Pad header to 64 bytes
    let padding = WitnessHeader::SIZE - header_bytes.len();
    if padding > 0 {
        writer.write_all(&vec![0u8; padding])?;
    }
    
    // Write witnesses
    for witness in witnesses {
        let bytes = witness.to_bytes()?;
        let len = bytes.len() as u16;
        writer.write_all(&len.to_le_bytes())?;
        writer.write_all(&bytes)?;
    }
    
    // Pad to floppy size
    let current_size = writer.stream_position()? as usize;
    if current_size < FLOPPY_SIZE {
        let padding = FLOPPY_SIZE - current_size;
        writer.write_all(&vec![0u8; padding])?;
    }
    
    writer.flush()?;
    
    println!("✓ Written {} witnesses to floppy image: {}", witnesses.len(), path);
    println!("  Size: {} bytes / {} bytes", current_size, FLOPPY_SIZE);
    
    Ok(())
}

/// Write witness to FAT file (for ZIP disk)
pub fn write_fat_file(path: &str, witnesses: &[EpochWitness]) -> Result<()> {
    let total_size: usize = witnesses.iter().map(|w| w.size()).sum();
    let header = WitnessHeader::new(witnesses.len() as u32, total_size as u32);
    
    // Create directory if needed
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent)?;
    }
    
    let mut file = File::create(path)
        .with_context(|| format!("Failed to create: {}", path))?;
    
    // Write header
    let header_bytes = bincode::serialize(&header)?;
    file.write_all(&header_bytes)?;
    
    // Pad header
    let padding = WitnessHeader::SIZE - header_bytes.len();
    if padding > 0 {
        file.write_all(&vec![0u8; padding])?;
    }
    
    // Write witnesses
    for witness in witnesses {
        let bytes = witness.to_bytes()?;
        let len = bytes.len() as u16;
        file.write_all(&len.to_le_bytes())?;
        file.write_all(&bytes)?;
    }
    
    println!("✓ Written {} witnesses to FAT file: {}", witnesses.len(), path);
    println!("  Size: {} bytes", total_size + WitnessHeader::SIZE);
    
    Ok(())
}

/// Write witness to QR code
pub fn write_qr_code(path: &str, witness: &EpochWitness) -> Result<()> {
    let bytes = witness.to_bytes()?;
    
    // QR codes have limited capacity, check if it fits
    if bytes.len() > 2953 {
        anyhow::bail!("Witness too large for QR code: {} bytes (max 2953)", bytes.len());
    }
    
    // Encode as hex for QR code
    let hex_data = hex::encode(&bytes);
    
    use qrcode::QrCode;
    use image::Luma;
    
    let code = QrCode::new(hex_data.as_bytes())
        .context("Failed to generate QR code")?;
    
    let image = code.render::<Luma<u8>>()
        .quiet_zone(true)
        .module_dimensions(2, 2)
        .build();
    
    image.save(path)
        .with_context(|| format!("Failed to save QR code: {}", path))?;
    
    println!("✓ Written epoch {} witness to QR code: {}", witness.epoch, path);
    println!("  Data size: {} bytes", bytes.len());
    
    Ok(())
}

/// Read witness from file
pub fn read_witness_file(path: &str) -> Result<(WitnessHeader, Vec<EpochWitness>)> {
    let mut file = File::open(path)
        .with_context(|| format!("Failed to open: {}", path))?;
    
    // Read header
    let mut header_bytes = vec![0u8; WitnessHeader::SIZE];
    file.read_exact(&mut header_bytes)?;
    
    let header: WitnessHeader = bincode::deserialize(&header_bytes)
        .context("Failed to parse header")?;
    
    // Verify magic
    if &header.magic != MAGIC {
        anyhow::bail!("Invalid file format: expected RCW magic bytes");
    }
    
    // Read witnesses
    let mut witnesses = Vec::new();
    for _ in 0..header.count {
        let mut len_bytes = [0u8; 2];
        file.read_exact(&mut len_bytes)?;
        let len = u16::from_le_bytes(len_bytes) as usize;
        
        let mut witness_bytes = vec![0u8; len];
        file.read_exact(&mut witness_bytes)?;
        
        let witness: EpochWitness = bincode::deserialize(&witness_bytes)
            .context("Failed to parse witness")?;
        witnesses.push(witness);
    }
    
    Ok((header, witnesses))
}

/// Read QR code from image
pub fn read_qr_code(path: &str) -> Result<EpochWitness> {
    use image::io::Reader as ImageReader;
    
    let img = ImageReader::open(path)?
        .with_guessed_format()?
        .decode()
        .context("Failed to decode image")?;
    
    // This is a simplified version - in production, you'd use a QR decoder library
    // For now, we'll return an error suggesting manual decoding
    anyhow::bail!("QR code reading requires external decoder. Use: zbarimg {}", path);
}