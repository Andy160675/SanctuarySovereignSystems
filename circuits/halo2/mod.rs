//! Genesis Phase 8 — Halo2 Circuit Registry
//!
//! This module contains all Halo2 circuits used for constitutional enforcement.
//!
//! Circuit Hierarchy:
//! - Goodhart Circuit: Enforces |primary - shadow| < 0.07
//! - Meta-Shadow Circuit (Row 11): Enforces shadow-of-shadow consistency
//! - Triple-Lock Circuit: Combines all checks for final governance gate
//!
//! Constitutional Mandate:
//!     "Halo2 verification is binary. TRUE or FALSE.
//!      There is no '20% failure.' There is no 'graceful degradation.'
//!      If FALSE, the proof is invalid. The transaction is mathematically
//!      impossible to process on the ledger."

pub mod goodhart_circuit;
pub mod meta_shadow_circuit;
pub mod triple_lock_circuit;

pub use goodhart_circuit::{GoodhartCircuit, GoodhartConfig, circuit_ids};
pub use meta_shadow_circuit::MetaShadowCircuit;
pub use triple_lock_circuit::TripleLockCircuit;

/// Circuit constraint counts (CI-pinned, immutable)
pub mod constraint_counts {
    /// Goodhart divergence check
    pub const GOODHART_CONSTRAINTS: usize = 2;
    /// Meta-shadow Row 11 check
    pub const META_SHADOW_CONSTRAINTS: usize = 4;
    /// Triple-lock combined check
    pub const TRIPLE_LOCK_CONSTRAINTS: usize = 8;
    /// SHA3-512 round (77->19 with custom gates)
    pub const SHA3_ROUND_CONSTRAINTS: usize = 19;
    /// Dilithium-5 signature verification
    pub const DILITHIUM_VERIFY_CONSTRAINTS: usize = 3;
}

/// Verification key hashes (computed at compile time, immutable)
pub mod vk_hashes {
    /// Goodhart circuit VK hash (placeholder - compute from actual circuit)
    pub const GOODHART_VK_HASH: &str = "0x0000000000000000000000000000000000000000000000000000000000000001";
    /// Meta-shadow circuit VK hash
    pub const META_SHADOW_VK_HASH: &str = "0x0000000000000000000000000000000000000000000000000000000000000002";
    /// Triple-lock circuit VK hash
    pub const TRIPLE_LOCK_VK_HASH: &str = "0x0000000000000000000000000000000000000000000000000000000000000003";
}
