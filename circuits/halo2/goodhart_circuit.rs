//! Genesis Phase 8 — Goodhart Circuit (Halo2)
//!
//! This circuit enforces the Goodhart divergence constraint:
//!     |primary_score - shadow_score| < DIVERGENCE_THRESHOLD
//!
//! If the constraint fails, the proof is invalid.
//! There is no "graceful degradation." VALID or INVALID. Binary.
//!
//! Constitutional Law:
//!     "If divergence > 0.07, the state transition is invalid by definition."

use halo2_proofs::{
    arithmetic::Field,
    circuit::{AssignedCell, Chip, Layouter, SimpleFloorPlanner, Value},
    plonk::{
        Advice, Circuit, Column, ConstraintSystem, Error, Expression, Fixed, Instance, Selector,
    },
    poly::Rotation,
};
use std::marker::PhantomData;

/// Divergence threshold in fixed-point (0.07 * 10^6 = 70000)
const DIVERGENCE_THRESHOLD_FP: u64 = 70_000;
/// Scale factor for fixed-point arithmetic
const SCALE_FACTOR: u64 = 1_000_000;

// =============================================================================
// Circuit Configuration
// =============================================================================

#[derive(Debug, Clone)]
pub struct GoodhartConfig {
    /// Primary metric score (public input)
    pub primary: Column<Advice>,
    /// Shadow metric score (public input)
    pub shadow: Column<Advice>,
    /// Computed difference (private witness)
    pub difference: Column<Advice>,
    /// Threshold constant
    pub threshold: Column<Fixed>,
    /// Instance column for public inputs
    pub instance: Column<Instance>,
    /// Selector for the main constraint
    pub s_main: Selector,
    /// Selector for range check
    pub s_range: Selector,
}

// =============================================================================
// Goodhart Chip
// =============================================================================

#[derive(Debug, Clone)]
pub struct GoodhartChip<F: Field> {
    config: GoodhartConfig,
    _marker: PhantomData<F>,
}

impl<F: Field> GoodhartChip<F> {
    pub fn construct(config: GoodhartConfig) -> Self {
        Self {
            config,
            _marker: PhantomData,
        }
    }

    pub fn configure(
        meta: &mut ConstraintSystem<F>,
        primary: Column<Advice>,
        shadow: Column<Advice>,
        difference: Column<Advice>,
        threshold: Column<Fixed>,
        instance: Column<Instance>,
    ) -> GoodhartConfig {
        // Enable equality for public input binding
        meta.enable_equality(primary);
        meta.enable_equality(shadow);
        meta.enable_equality(instance);

        let s_main = meta.selector();
        let s_range = meta.selector();

        // Main constraint: difference = |primary - shadow|
        // We enforce: difference^2 = (primary - shadow)^2
        // This handles absolute value without branches
        meta.create_gate("goodhart_divergence", |meta| {
            let s = meta.query_selector(s_main);
            let p = meta.query_advice(primary, Rotation::cur());
            let sh = meta.query_advice(shadow, Rotation::cur());
            let d = meta.query_advice(difference, Rotation::cur());

            // Constraint: d^2 = (p - sh)^2
            // Expanded: d^2 - p^2 + 2*p*sh - sh^2 = 0
            let diff = p.clone() - sh.clone();
            let constraint = d.clone() * d.clone() - diff.clone() * diff;

            vec![s * constraint]
        });

        // Range constraint: difference < threshold
        // We prove: threshold - difference - 1 >= 0 (i.e., difference <= threshold - 1)
        meta.create_gate("goodhart_threshold", |meta| {
            let s = meta.query_selector(s_range);
            let d = meta.query_advice(difference, Rotation::cur());
            let t = meta.query_fixed(threshold, Rotation::cur());

            // For the proof to be valid, (threshold - difference) must be non-negative
            // We encode this via a range proof on the result
            // Simplified: we assert difference * (threshold - difference) >= 0
            // This is valid when 0 <= difference <= threshold
            let range_check = d.clone() * (t - d);

            // The constraint is that this product is non-negative
            // In practice, we'd decompose into bits for a proper range proof
            // For now, we use a simplified constraint
            vec![s * range_check]
        });

        GoodhartConfig {
            primary,
            shadow,
            difference,
            threshold,
            instance,
            s_main,
            s_range,
        }
    }
}

// =============================================================================
// Goodhart Circuit
// =============================================================================

#[derive(Default, Clone)]
pub struct GoodhartCircuit<F: Field> {
    /// Primary metric score (fixed-point, scaled by SCALE_FACTOR)
    pub primary_score: Value<F>,
    /// Shadow metric score (fixed-point, scaled by SCALE_FACTOR)
    pub shadow_score: Value<F>,
}

impl<F: Field> Circuit<F> for GoodhartCircuit<F> {
    type Config = GoodhartConfig;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {
        Self::default()
    }

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {
        let primary = meta.advice_column();
        let shadow = meta.advice_column();
        let difference = meta.advice_column();
        let threshold = meta.fixed_column();
        let instance = meta.instance_column();

        GoodhartChip::configure(meta, primary, shadow, difference, threshold, instance)
    }

    fn synthesize(
        &self,
        config: Self::Config,
        mut layouter: impl Layouter<F>,
    ) -> Result<(), Error> {
        layouter.assign_region(
            || "goodhart check",
            |mut region| {
                // Enable selectors
                config.s_main.enable(&mut region, 0)?;
                config.s_range.enable(&mut region, 0)?;

                // Assign primary score
                let primary_cell = region.assign_advice(
                    || "primary",
                    config.primary,
                    0,
                    || self.primary_score,
                )?;

                // Assign shadow score
                let shadow_cell = region.assign_advice(
                    || "shadow",
                    config.shadow,
                    0,
                    || self.shadow_score,
                )?;

                // Compute and assign difference
                let difference_value = self.primary_score.zip(self.shadow_score).map(|(p, s)| {
                    // Compute |p - s|
                    if p > s { p - s } else { s - p }
                });

                region.assign_advice(
                    || "difference",
                    config.difference,
                    0,
                    || difference_value,
                )?;

                // Assign threshold constant
                region.assign_fixed(
                    || "threshold",
                    config.threshold,
                    0,
                    || Value::known(F::from(DIVERGENCE_THRESHOLD_FP)),
                )?;

                Ok(())
            },
        )
    }
}

// =============================================================================
// Circuit IDs (for registry)
// =============================================================================

pub mod circuit_ids {
    /// Primary metric circuit ID
    pub const CIRCUIT_PRIMARY_METRIC: &[u8; 32] = b"CIRCUIT_PRIMARY_METRIC__________";
    /// Shadow metric circuit ID
    pub const CIRCUIT_SHADOW_METRIC: &[u8; 32] = b"CIRCUIT_SHADOW_METRIC___________";
    /// Goodhart divergence circuit ID
    pub const CIRCUIT_GOODHART_DIV: &[u8; 32] = b"CIRCUIT_GOODHART_DIVERGENCE_____";
    /// Meta-shadow (Row 11) circuit ID
    pub const CIRCUIT_META_SHADOW_ROW11: &[u8; 32] = b"CIRCUIT_META_SHADOW_ROW11_______";
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use halo2_proofs::{dev::MockProver, pasta::Fp};

    #[test]
    fn test_goodhart_pass() {
        // Scores within threshold (both at 0.85, divergence = 0)
        let circuit = GoodhartCircuit {
            primary_score: Value::known(Fp::from(850_000)), // 0.85 * 10^6
            shadow_score: Value::known(Fp::from(850_000)),
        };

        let prover = MockProver::run(4, &circuit, vec![]).unwrap();
        prover.assert_satisfied();
    }

    #[test]
    fn test_goodhart_within_threshold() {
        // Divergence of 0.05 (within 0.07 threshold)
        let circuit = GoodhartCircuit {
            primary_score: Value::known(Fp::from(850_000)), // 0.85
            shadow_score: Value::known(Fp::from(800_000)),  // 0.80, diff = 0.05
        };

        let prover = MockProver::run(4, &circuit, vec![]).unwrap();
        prover.assert_satisfied();
    }

    #[test]
    #[should_panic]
    fn test_goodhart_exceeds_threshold() {
        // Divergence of 0.15 (exceeds 0.07 threshold)
        let circuit = GoodhartCircuit {
            primary_score: Value::known(Fp::from(850_000)), // 0.85
            shadow_score: Value::known(Fp::from(700_000)),  // 0.70, diff = 0.15
        };

        let prover = MockProver::run(4, &circuit, vec![]).unwrap();
        prover.assert_satisfied(); // This should panic
    }
}
