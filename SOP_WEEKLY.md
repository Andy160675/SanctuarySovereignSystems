# Weekly Ops Cadence — Sovereign Recursion Engine

## Required Actions
1. **Rollback Drill**
   * Purpose: Verify system can return to a known good state.
   * Procedure: 
     1. Identify the most recent extension (e.g., `autonomous_build_command`).
     2. Execute the rollback procedure in `docs/procedures/rollback_<extension>.md`.
     3. Run `74/74` kernel tests.
     4. Restore the extension state and verify functionality.
   * Target: < 15 minutes to verified green state.

2. **Phase-9 Evidence Review**
   * Audit the `evidence/` directory for all PRs merged in the last week.
   * Ensure manifests match disk content.

3. **Performance Baseline Update**
   * Run `python scripts/validate_performance.py`.
   * If significant improvements are stable, update `baseline_metrics.json`.
