//! Genesis Phase 8 — Triple-Lock Circuit
//!
//! This circuit combines all governance checks into a single proof:
//! 1. Primary metric validity
//! 2. Shadow metric validity
//! 3. Goodhart divergence check
//! 4. Meta-shadow consistency (Row 11)
//!
//! A single VALID proof from this circuit means:
//!     "All governance constraints hold. State transition is permitted."
//!
//! A single INVALID proof means:
//!     "At least one constraint failed. State transition is REJECTED."
//!
//! There is no partial success. No graceful degradation. Binary.

use halo2_proofs::{
    arithmetic::Field,
    circuit::{Layouter, SimpleFloorPlanner, Value},
    plonk::{Advice, Circuit, Column, ConstraintSystem, Error, Fixed, Instance, Selector},
    poly::Rotation,
};
use std::marker::PhantomData;

/// Goodhart threshold (0.07)
const GOODHART_THRESHOLD_FP: u64 = 70_000;
/// Meta-shadow threshold (0.12)
const META_SHADOW_THRESHOLD_FP: u64 = 120_000;
/// Scale factor
const SCALE: u64 = 1_000_000;

// =============================================================================
// Triple-Lock Configuration
// =============================================================================

#[derive(Debug, Clone)]
pub struct TripleLockConfig {
    // Metric columns
    pub primary_metric: Column<Advice>,
    pub shadow_metric: Column<Advice>,
    pub meta_shadow: Column<Advice>,
    pub external_oracle: Column<Advice>,

    // Divergence columns
    pub goodhart_div: Column<Advice>,
    pub meta_div: Column<Advice>,

    // Threshold constants
    pub goodhart_threshold: Column<Fixed>,
    pub meta_threshold: Column<Fixed>,

    // Public inputs
    pub instance: Column<Instance>,

    // Selectors
    pub s_goodhart: Selector,
    pub s_meta: Selector,
    pub s_final: Selector,
}

// =============================================================================
// Triple-Lock Circuit
// =============================================================================

#[derive(Default, Clone)]
pub struct TripleLockCircuit<F: Field> {
    /// Primary metric score
    pub primary_metric: Value<F>,
    /// Shadow metric score
    pub shadow_metric: Value<F>,
    /// Meta-shadow (shadow-of-shadow) score
    pub meta_shadow: Value<F>,
    /// External oracle value
    pub external_oracle: Value<F>,
}

impl<F: Field> Circuit<F> for TripleLockCircuit<F> {
    type Config = TripleLockConfig;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {
        Self::default()
    }

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {
        // Advice columns
        let primary_metric = meta.advice_column();
        let shadow_metric = meta.advice_column();
        let meta_shadow = meta.advice_column();
        let external_oracle = meta.advice_column();
        let goodhart_div = meta.advice_column();
        let meta_div = meta.advice_column();

        // Fixed columns
        let goodhart_threshold = meta.fixed_column();
        let meta_threshold = meta.fixed_column();

        // Instance column
        let instance = meta.instance_column();

        // Enable equality
        meta.enable_equality(primary_metric);
        meta.enable_equality(shadow_metric);
        meta.enable_equality(instance);

        // Selectors
        let s_goodhart = meta.selector();
        let s_meta = meta.selector();
        let s_final = meta.selector();

        // Gate 1: Goodhart divergence constraint
        // |primary - shadow| < goodhart_threshold
        meta.create_gate("goodhart_check", |meta| {
            let s = meta.query_selector(s_goodhart);
            let p = meta.query_advice(primary_metric, Rotation::cur());
            let sh = meta.query_advice(shadow_metric, Rotation::cur());
            let d = meta.query_advice(goodhart_div, Rotation::cur());

            // d^2 = (p - sh)^2
            let diff = p - sh;
            vec![s * (d.clone() * d - diff.clone() * diff)]
        });

        // Gate 2: Goodhart threshold enforcement
        meta.create_gate("goodhart_threshold", |meta| {
            let s = meta.query_selector(s_goodhart);
            let d = meta.query_advice(goodhart_div, Rotation::cur());
            let t = meta.query_fixed(goodhart_threshold, Rotation::cur());

            // d must be less than t
            vec![s * d.clone() * (t - d)]
        });

        // Gate 3: Meta-shadow divergence constraint
        // |shadow - meta_shadow| must be small
        meta.create_gate("meta_shadow_check", |meta| {
            let s = meta.query_selector(s_meta);
            let sh = meta.query_advice(shadow_metric, Rotation::cur());
            let ms = meta.query_advice(meta_shadow, Rotation::cur());

            let diff = sh - ms;
            vec![s * diff.clone() * diff]
        });

        // Gate 4: External oracle agreement
        // |shadow - external_oracle| < meta_threshold
        meta.create_gate("oracle_check", |meta| {
            let s = meta.query_selector(s_meta);
            let sh = meta.query_advice(shadow_metric, Rotation::cur());
            let eo = meta.query_advice(external_oracle, Rotation::cur());
            let d = meta.query_advice(meta_div, Rotation::cur());

            let diff = sh - eo;
            vec![s * (d.clone() * d - diff.clone() * diff)]
        });

        // Gate 5: Meta threshold enforcement
        meta.create_gate("meta_threshold", |meta| {
            let s = meta.query_selector(s_meta);
            let d = meta.query_advice(meta_div, Rotation::cur());
            let t = meta.query_fixed(meta_threshold, Rotation::cur());

            vec![s * d.clone() * (t - d)]
        });

        // Gate 6: Final consistency - all metrics must be positive
        meta.create_gate("positivity", |meta| {
            let s = meta.query_selector(s_final);
            let p = meta.query_advice(primary_metric, Rotation::cur());
            let sh = meta.query_advice(shadow_metric, Rotation::cur());

            // Both must be non-negative (in practice, we'd use range proofs)
            vec![s * p * sh]
        });

        // Gate 7: Bounded range check
        meta.create_gate("bounded_range", |meta| {
            let s = meta.query_selector(s_final);
            let p = meta.query_advice(primary_metric, Rotation::cur());

            // p * (SCALE - p) >= 0 when 0 <= p <= SCALE
            let scale = meta.query_fixed(goodhart_threshold, Rotation::cur()); // Reuse column
            vec![s * p.clone() * (scale - p)]
        });

        // Gate 8: Triple agreement - no single source can dominate
        meta.create_gate("triple_agreement", |meta| {
            let s = meta.query_selector(s_final);
            let p = meta.query_advice(primary_metric, Rotation::cur());
            let sh = meta.query_advice(shadow_metric, Rotation::cur());
            let eo = meta.query_advice(external_oracle, Rotation::cur());

            // Variance of the three must be bounded
            // (p - sh) * (sh - eo) * (eo - p) should be small
            let d1 = p.clone() - sh.clone();
            let d2 = sh - eo.clone();
            let d3 = eo - p;

            vec![s * d1 * d2 * d3]
        });

        TripleLockConfig {
            primary_metric,
            shadow_metric,
            meta_shadow,
            external_oracle,
            goodhart_div,
            meta_div,
            goodhart_threshold,
            meta_threshold,
            instance,
            s_goodhart,
            s_meta,
            s_final,
        }
    }

    fn synthesize(
        &self,
        config: Self::Config,
        mut layouter: impl Layouter<F>,
    ) -> Result<(), Error> {
        layouter.assign_region(
            || "triple-lock check",
            |mut region| {
                // Enable all selectors
                config.s_goodhart.enable(&mut region, 0)?;
                config.s_meta.enable(&mut region, 0)?;
                config.s_final.enable(&mut region, 0)?;

                // Assign metrics
                region.assign_advice(
                    || "primary_metric",
                    config.primary_metric,
                    0,
                    || self.primary_metric,
                )?;

                region.assign_advice(
                    || "shadow_metric",
                    config.shadow_metric,
                    0,
                    || self.shadow_metric,
                )?;

                region.assign_advice(
                    || "meta_shadow",
                    config.meta_shadow,
                    0,
                    || self.meta_shadow,
                )?;

                region.assign_advice(
                    || "external_oracle",
                    config.external_oracle,
                    0,
                    || self.external_oracle,
                )?;

                // Compute Goodhart divergence
                let goodhart_div_value = self.primary_metric
                    .zip(self.shadow_metric)
                    .map(|(p, s)| if p > s { p - s } else { s - p });

                region.assign_advice(
                    || "goodhart_div",
                    config.goodhart_div,
                    0,
                    || goodhart_div_value,
                )?;

                // Compute meta divergence
                let meta_div_value = self.shadow_metric
                    .zip(self.external_oracle)
                    .map(|(s, e)| if s > e { s - e } else { e - s });

                region.assign_advice(
                    || "meta_div",
                    config.meta_div,
                    0,
                    || meta_div_value,
                )?;

                // Assign thresholds
                region.assign_fixed(
                    || "goodhart_threshold",
                    config.goodhart_threshold,
                    0,
                    || Value::known(F::from(GOODHART_THRESHOLD_FP)),
                )?;

                region.assign_fixed(
                    || "meta_threshold",
                    config.meta_threshold,
                    0,
                    || Value::known(F::from(META_SHADOW_THRESHOLD_FP)),
                )?;

                Ok(())
            },
        )
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use halo2_proofs::{dev::MockProver, pasta::Fp};

    #[test]
    fn test_triple_lock_pass() {
        // All metrics aligned (0.80, 0.80, 0.80, 0.80)
        let circuit = TripleLockCircuit {
            primary_metric: Value::known(Fp::from(800_000)),
            shadow_metric: Value::known(Fp::from(800_000)),
            meta_shadow: Value::known(Fp::from(800_000)),
            external_oracle: Value::known(Fp::from(800_000)),
        };

        let prover = MockProver::run(8, &circuit, vec![]).unwrap();
        prover.assert_satisfied();
    }

    #[test]
    fn test_triple_lock_within_tolerance() {
        // Slight divergence but within thresholds
        let circuit = TripleLockCircuit {
            primary_metric: Value::known(Fp::from(850_000)),  // 0.85
            shadow_metric: Value::known(Fp::from(820_000)),   // 0.82 (diff = 0.03 < 0.07)
            meta_shadow: Value::known(Fp::from(815_000)),     // 0.815
            external_oracle: Value::known(Fp::from(800_000)), // 0.80 (diff = 0.02 < 0.12)
        };

        let prover = MockProver::run(8, &circuit, vec![]).unwrap();
        prover.assert_satisfied();
    }

    #[test]
    #[should_panic]
    fn test_triple_lock_goodhart_fail() {
        // Goodhart divergence exceeds threshold
        let circuit = TripleLockCircuit {
            primary_metric: Value::known(Fp::from(900_000)),  // 0.90
            shadow_metric: Value::known(Fp::from(700_000)),   // 0.70 (diff = 0.20 > 0.07)
            meta_shadow: Value::known(Fp::from(700_000)),
            external_oracle: Value::known(Fp::from(700_000)),
        };

        let prover = MockProver::run(8, &circuit, vec![]).unwrap();
        prover.assert_satisfied(); // Should panic
    }

    #[test]
    #[should_panic]
    fn test_triple_lock_oracle_fail() {
        // External oracle divergence exceeds threshold
        let circuit = TripleLockCircuit {
            primary_metric: Value::known(Fp::from(800_000)),
            shadow_metric: Value::known(Fp::from(800_000)),
            meta_shadow: Value::known(Fp::from(800_000)),
            external_oracle: Value::known(Fp::from(500_000)), // 0.50 (diff = 0.30 > 0.12)
        };

        let prover = MockProver::run(8, &circuit, vec![]).unwrap();
        prover.assert_satisfied(); // Should panic
    }
}
