//! Floppy Witness Kit — Epoch Proofs on 1.44MB Media
//!
//! A tiny RustChain epoch witness format that fits on old media — 
//! 1.44MB floppies, ZIP disks, even cassette tapes.

mod witness;
mod format;
mod commands;
mod ascii;

use clap::{Parser, Subcommand};

/// RustChain Floppy Witness Kit
#[derive(Parser)]
#[command(name = "rustchain-witness")]
#[command(author = "RustChain Contributors")]
#[command(version = "0.1.0")]
#[command(about = "Compact epoch proofs for 1.44MB media")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Write epoch witness to device or file
    Write {
        /// Epoch number to witness
        #[arg(short, long)]
        epoch: u64,
        
        /// Output device or file path
        #[arg(short, long)]
        device: String,
        
        /// Output format (img, fat, qr)
        #[arg(short, long, default_value = "img")]
        format: String,
        
        /// Node API endpoint
        #[arg(short, long, default_value = "http://50.28.86.131:8080")]
        node: String,
    },
    
    /// Read epoch witness from device or file
    Read {
        /// Input device or file path
        #[arg(short, long)]
        device: String,
        
        /// Output format (json, hex)
        #[arg(short, long, default_value = "json")]
        format: String,
    },
    
    /// Verify witness against current chain state
    Verify {
        /// Witness file to verify
        #[arg(short, long)]
        file: String,
        
        /// Node API endpoint
        #[arg(short, long, default_value = "http://50.28.86.131:8080")]
        node: String,
    },
    
    /// Show ASCII art banner
    Banner,
}

fn main() {
    let cli = Cli::parse();
    
    if let Err(e) = match cli.command {
        Commands::Write { epoch, device, format, node } => {
            commands::write(epoch, &device, &format, &node)
        }
        Commands::Read { device, format } => {
            commands::read(&device, &format)
        }
        Commands::Verify { file, node } => {
            commands::verify(&file, &node)
        }
        Commands::Banner => {
            println!("{}", ascii::BANNER);
            Ok(())
        }
    } {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}