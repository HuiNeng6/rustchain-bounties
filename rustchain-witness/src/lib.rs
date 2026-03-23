//! Tests for Floppy Witness Kit

#[cfg(test)]
mod tests {
    use rustchain_witness::*;
    
    #[test]
    fn test_witness_creation() {
        let witness = witness::EpochWitness::new(500, 1234567890);
        assert_eq!(witness.epoch, 500);
        assert_eq!(witness.timestamp, 1234567890);
        assert_eq!(witness.version, witness::VERSION);
    }
    
    #[test]
    fn test_witness_size() {
        let mut witness = witness::EpochWitness::new(500, 1234567890);
        
        // Add some miners
        for i in 0..10 {
            witness.add_miner(format!("miner_{}", i).into_bytes(), [i as u8; 8]);
        }
        
        let size = witness.size();
        println!("Witness size: {} bytes", size);
        
        // Should be less than 100KB
        assert!(size < witness::MAX_WITNESS_SIZE);
    }
    
    #[test]
    fn test_witness_serialization() {
        let mut witness = witness::EpochWitness::new(500, 1234567890);
        witness.add_miner(b"test_miner".to_vec(), [1, 2, 3, 4, 5, 6, 7, 8]);
        
        // Serialize
        let bytes = witness.to_bytes().expect("Failed to serialize");
        
        // Deserialize
        let restored = witness::EpochWitness::from_bytes(&bytes).expect("Failed to deserialize");
        
        assert_eq!(witness.epoch, restored.epoch);
        assert_eq!(witness.timestamp, restored.timestamp);
        assert_eq!(witness.miners.len(), restored.miners.len());
    }
    
    #[test]
    fn test_header_size() {
        assert_eq!(witness::WitnessHeader::SIZE, 64);
    }
    
    #[test]
    fn test_format_detection() {
        use format::Format;
        
        assert!(matches!(Format::from_str("img").unwrap(), Format::FloppyImage));
        assert!(matches!(Format::from_str("fat").unwrap(), Format::FatFile));
        assert!(matches!(Format::from_str("qr").unwrap(), Format::QrCode));
    }
}