# Bolt-Ons Quick Start

## Installed Bolt-Ons

### 1. Observatory (S3-EXT-006)
Live telemetry, health, and drift monitoring.

**Usage:**
```python
from sovereign_engine.extensions.observatory import Observatory
obs = Observatory()
health = obs.generate_health_report()
```

### 2. Evidence Vault (S3-EXT-004)
Immutable evidence storage with hash manifests.

**Usage:**
```python
from sovereign_engine.extensions.evidence_vault import EvidenceVault
vault = EvidenceVault("./vault")
evidence_id = vault.store_evidence("test", {"data": "example"})
```

### 3. Merge Gate (S3-EXT-007)
Constitutional PR/merge enforcement pipeline.

**Usage:**
```python
from sovereign_engine.extensions.merge_gate import MergeGate
mg = MergeGate()
results = mg.validate_merge("PR-123", "feature-branch")
```

### 4. Compliance Pack (S3-EXT-016)
Configurable controls mapped to policy sets.

**Usage:**
```python
from sovereign_engine.extensions.compliance import get_compliance_pack
soc2 = get_compliance_pack("soc2")
audit = soc2.run_audit()
```

### 5. Board Pack Templates (S3-EXT-015)
Investor, governance, and audit reporting.

**Usage:**
```python
from sovereign_engine.extensions.board_packs import BoardPackGenerator
gen = BoardPackGenerator("Your Company")
report = gen.generate_investor_pack(metrics, "Q1 2024")
```

### 6. Slack Connector
Real-time notifications.

**Set environment variable:**
```powershell
$env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## Next Steps

1. Configure Slack webhook for alerts
2. Run demo: `python scripts/demo_bolt_ons.py`
3. Integrate with your workflow
4. Contact support for custom configurations
