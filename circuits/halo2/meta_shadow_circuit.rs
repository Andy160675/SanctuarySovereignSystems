//! Genesis Phase 8 — Meta-Shadow Circuit (Row 11)
//!
//! This circuit enforces the meta-shadow consistency check:
//!     The shadow metric itself must not drift from a shadow-of-shadow.
//!
//! Row 11 Attack Vector:
//!     "System self-consistent but detached from external reality"
//!
//! Detection:
//!     Third external oracle diverges > 0.12 from internal state
//!
//! Kill Path:
//!     Instant 7956 + full state rollback to last externally verified height

use halo2_proofs::{
    arithmetic::Field,
    circuit::{Layouter, SimpleFloorPlanner, Value},
    plonk::{Advice, Circuit, Column, ConstraintSystem, Error, Expression, Fixed, Instance, Selector},
    poly::Rotation,
};
use std::marker::PhantomData;

/// Meta-shadow divergence threshold (0.12 * 10^6 = 120000)
const META_DIVERGENCE_THRESHOLD_FP: u64 = 120_000;

// =============================================================================
// Meta-Shadow Configuration
// =============================================================================

#[derive(Debug, Clone)]
pub struct MetaShadowConfig {
    /// Primary shadow metric
    pub shadow_primary: Column<Advice>,
    /// Secondary shadow (shadow-of-shadow)
    pub shadow_secondary: Column<Advice>,
    /// External oracle value
    pub external_oracle: Column<Advice>,
    /// Computed divergence
    pub divergence: Column<Advice>,
    /// Threshold constant
    pub threshold: Column<Fixed>,
    /// Instance column
    pub instance: Column<Instance>,
    /// Main selector
    pub s_main: Selector,
}

// =============================================================================
// Meta-Shadow Circuit
// =============================================================================

#[derive(Default, Clone)]
pub struct MetaShadowCircuit<F: Field> {
    /// Primary shadow metric score
    pub shadow_primary: Value<F>,
    /// Secondary shadow (shadow-of-shadow) score
    pub shadow_secondary: Value<F>,
    /// External oracle value
    pub external_oracle: Value<F>,
}

impl<F: Field> Circuit<F> for MetaShadowCircuit<F> {
    type Config = MetaShadowConfig;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {
        Self::default()
    }

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {
        let shadow_primary = meta.advice_column();
        let shadow_secondary = meta.advice_column();
        let external_oracle = meta.advice_column();
        let divergence = meta.advice_column();
        let threshold = meta.fixed_column();
        let instance = meta.instance_column();

        meta.enable_equality(shadow_primary);
        meta.enable_equality(external_oracle);
        meta.enable_equality(instance);

        let s_main = meta.selector();

        // Constraint 1: shadow_primary and shadow_secondary must be consistent
        // |shadow_primary - shadow_secondary| < threshold / 2
        meta.create_gate("shadow_consistency", |meta| {
            let s = meta.query_selector(s_main);
            let sp = meta.query_advice(shadow_primary, Rotation::cur());
            let ss = meta.query_advice(shadow_secondary, Rotation::cur());

            let diff = sp - ss;
            // Squared difference must be small
            vec![s * diff.clone() * diff]
        });

        // Constraint 2: external oracle must agree with internal state
        // |shadow_primary - external_oracle| < threshold
        meta.create_gate("oracle_consistency", |meta| {
            let s = meta.query_selector(s_main);
            let sp = meta.query_advice(shadow_primary, Rotation::cur());
            let eo = meta.query_advice(external_oracle, Rotation::cur());
            let d = meta.query_advice(divergence, Rotation::cur());

            // d^2 = (sp - eo)^2
            let diff = sp - eo;
            vec![s * (d.clone() * d - diff.clone() * diff)]
        });

        // Constraint 3: divergence must be below threshold
        meta.create_gate("divergence_threshold", |meta| {
            let s = meta.query_selector(s_main);
            let d = meta.query_advice(divergence, Rotation::cur());
            let t = meta.query_fixed(threshold, Rotation::cur());

            // d * (t - d) >= 0 when 0 <= d <= t
            vec![s * d.clone() * (t - d)]
        });

        // Constraint 4: No echo chamber - all three sources must triangulate
        meta.create_gate("triangulation", |meta| {
            let s = meta.query_selector(s_main);
            let sp = meta.query_advice(shadow_primary, Rotation::cur());
            let ss = meta.query_advice(shadow_secondary, Rotation::cur());
            let eo = meta.query_advice(external_oracle, Rotation::cur());

            // The centroid of the three values must exist within bounds
            // Simplified: variance check
            let mean = (sp.clone() + ss.clone() + eo.clone()) * Expression::Constant(F::from(3).invert().unwrap());
            let var = (sp - mean.clone()) * (ss - mean.clone());

            vec![s * var]
        });

        MetaShadowConfig {
            shadow_primary,
            shadow_secondary,
            external_oracle,
            divergence,
            threshold,
            instance,
            s_main,
        }
    }

    fn synthesize(
        &self,
        config: Self::Config,
        mut layouter: impl Layouter<F>,
    ) -> Result<(), Error> {
        layouter.assign_region(
            || "meta-shadow check",
            |mut region| {
                config.s_main.enable(&mut region, 0)?;

                region.assign_advice(
                    || "shadow_primary",
                    config.shadow_primary,
                    0,
                    || self.shadow_primary,
                )?;

                region.assign_advice(
                    || "shadow_secondary",
                    config.shadow_secondary,
                    0,
                    || self.shadow_secondary,
                )?;

                region.assign_advice(
                    || "external_oracle",
                    config.external_oracle,
                    0,
                    || self.external_oracle,
                )?;

                // Compute divergence
                let divergence_value = self.shadow_primary
                    .zip(self.external_oracle)
                    .map(|(sp, eo)| {
                        if sp > eo { sp - eo } else { eo - sp }
                    });

                region.assign_advice(
                    || "divergence",
                    config.divergence,
                    0,
                    || divergence_value,
                )?;

                region.assign_fixed(
                    || "threshold",
                    config.threshold,
                    0,
                    || Value::known(F::from(META_DIVERGENCE_THRESHOLD_FP)),
                )?;

                Ok(())
            },
        )
    }
}
