# Governance Bundle Versioning

Single source of constitutional truth: this repository plus signed releases.

Versioning rules:
- Semantic versioning for governance bundles: MAJOR.MINOR.PATCH
- Bundle content includes: `CONSTITUTION.md`, governance templates/schemas, `OPS-INVARIANTS.md`, and controller policies.
- Each release produces:
  - `governance/VERSION` containing the version string
  - A signed tag/release (e.g., git tag -s vX.Y.Z)
  - A manifest of file hashes: `governance/bundle_manifest.json` (SHA-256 for each included file)

Node sync:
- Nodes pin to a bundle version X.Y.Z and fetch the release artifact.
- Local evidence is emitted per node, but governance inputs are pinned to the version.
- Upgrades require explicit bump + signature verification.
