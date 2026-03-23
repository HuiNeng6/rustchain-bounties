//! Compact Epoch Witness Format
//!
//! Target: <100KB per epoch witness
//! A full floppy (1.44MB) holds ~14,000 epoch witnesses

use serde::{Deserialize, Serialize};

/// Magic bytes for witness file identification
pub const MAGIC: &[u8; 4] = b"RCW\0";

/// Current format version
pub const VERSION: u16 = 1;

/// Maximum size per epoch witness (100KB)
pub const MAX_WITNESS_SIZE: usize = 100 * 1024;

/// Floppy disk size (1.44MB)
pub const FLOPPY_SIZE: usize = 1474560;

/// Epoch Witness - Compact blockchain proof
/// 
/// Total size target: <100KB
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpochWitness {
    /// Format version
    pub version: u16,
    
    /// Epoch number (8 bytes)
    pub epoch: u64,
    
    /// Unix timestamp (8 bytes)
    pub timestamp: u64,
    
    /// Miner lineup - compressed
    pub miners: Vec<MinerInfo>,
    
    /// Settlement hash (32 bytes)
    pub settlement_hash: [u8; 32],
    
    /// Ergo anchor TX ID (32 bytes)
    pub ergo_tx_id: [u8; 32],
    
    /// Commitment hash (32 bytes)
    pub commitment_hash: [u8; 32],
    
    /// Minimal Merkle proof
    pub merkle_proof: MerkleProof,
}

/// Miner information - compressed format
/// Size: ~16-32 bytes per miner
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MinerInfo {
    /// Miner ID (compressed, variable length)
    pub id: Vec<u8>,
    
    /// Architecture fingerprint hash (8 bytes)
    pub arch_hash: [u8; 8],
}

/// Minimal Merkle proof
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleProof {
    /// Merkle root (32 bytes)
    pub root: [u8; 32],
    
    /// Proof path (hashes)
    pub path: Vec<[u8; 32]>,
    
    /// Leaf index
    pub index: u64,
}

impl EpochWitness {
    /// Create a new epoch witness
    pub fn new(epoch: u64, timestamp: u64) -> Self {
        Self {
            version: VERSION,
            epoch,
            timestamp,
            miners: Vec::new(),
            settlement_hash: [0u8; 32],
            ergo_tx_id: [0u8; 32],
            commitment_hash: [0u8; 32],
            merkle_proof: MerkleProof {
                root: [0u8; 32],
                path: Vec::new(),
                index: 0,
            },
        }
    }
    
    /// Add a miner to the witness
    pub fn add_miner(&mut self, id: Vec<u8>, arch_hash: [u8; 8]) {
        self.miners.push(MinerInfo { id, arch_hash });
    }
    
    /// Serialize to binary format (compact)
    pub fn to_bytes(&self) -> Result<Vec<u8>, bincode::Error> {
        bincode::serialize(self)
    }
    
    /// Deserialize from binary format
    pub fn from_bytes(data: &[u8]) -> Result<Self, bincode::Error> {
        bincode::deserialize(data)
    }
    
    /// Calculate the total size in bytes
    pub fn size(&self) -> usize {
        self.to_bytes().map(|b| b.len()).unwrap_or(0)
    }
    
    /// Verify the witness fits within size constraints
    pub fn is_valid_size(&self) -> bool {
        self.size() <= MAX_WITNESS_SIZE
    }
}

/// Witness file header
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WitnessHeader {
    /// Magic bytes
    pub magic: [u8; 4],
    
    /// Format version
    pub version: u16,
    
    /// Number of witnesses in file
    pub count: u32,
    
    /// Total size of witness data
    pub total_size: u32,
    
    /// Creation timestamp
    pub created: u64,
    
    /// Reserved for future use
    pub reserved: [u8; 46],
}

impl WitnessHeader {
    pub fn new(count: u32, total_size: u32) -> Self {
        Self {
            magic: *MAGIC,
            version: VERSION,
            count,
            total_size,
            created: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            reserved: [0u8; 46],
        }
    }
    
    /// Header size (fixed at 64 bytes)
    pub const SIZE: usize = 64;
}