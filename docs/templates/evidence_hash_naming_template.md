# Evidence Hash Naming Convention

## Purpose

This document defines the naming convention for evidence artifacts to ensure traceability, integrity, and auditability.

## Naming Convention

Evidence files should follow this format:

```
evidence_<type>_<date>_<identifier>_<hash>.<ext>
```

### Components

1. **Prefix**: Always `evidence_`
2. **Type**: Category of evidence (see types below)
3. **Date**: ISO 8601 date format `YYYYMMDD`
4. **Identifier**: Brief descriptive name (lowercase, hyphens)
5. **Hash**: First 8 characters of SHA-256 hash
6. **Extension**: File type extension

### Example

```
evidence_audit_20260207_phase2-review_a3f8c9d1.pdf
evidence_test_20260207_integration-results_7b2e4f6a.json
evidence_security_20260207_pentest-report_5c1d8e9f.pdf
```

## Evidence Types

| Type | Code | Description |
|------|------|-------------|
| Audit | `audit` | Audit reports, compliance reviews |
| Test | `test` | Test results, coverage reports |
| Security | `security` | Security assessments, vulnerability scans |
| Review | `review` | Code reviews, design reviews |
| Deployment | `deploy` | Deployment records, release notes |
| Incident | `incident` | Incident reports, post-mortems |
| Approval | `approval` | Phase gate approvals, sign-offs |
| Monitoring | `monitor` | System logs, metrics, alerts |
| Training | `training` | Training records, certifications |
| Change | `change` | Change requests, impact assessments |

## Hash Generation

### Linux/macOS

```bash
# Generate SHA-256 hash and take first 8 characters
sha256sum filename | cut -c1-8
```

### Python

```python
import hashlib

def generate_evidence_hash(filepath):
    """Generate first 8 chars of SHA-256 hash"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()[:8]
```

### PowerShell

```powershell
# Generate SHA-256 hash and take first 8 characters
(Get-FileHash -Path filename -Algorithm SHA256).Hash.Substring(0,8)
```

## File Organization

Evidence should be organized in subdirectories by year and month:

```
evidence/
├── 2026/
│   ├── 01/
│   ├── 02/
│   │   ├── evidence_audit_20260207_phase2-review_a3f8c9d1.pdf
│   │   ├── evidence_test_20260207_integration-results_7b2e4f6a.json
│   │   └── evidence_security_20260207_pentest-report_5c1d8e9f.pdf
│   └── 03/
└── 2027/
```

## Metadata Tracking

Each evidence file should have a corresponding metadata entry:

```json
{
  "filename": "evidence_audit_20260207_phase2-review_a3f8c9d1.pdf",
  "type": "audit",
  "date": "2026-02-07",
  "identifier": "phase2-review",
  "hash": "a3f8c9d10e4f7b2c8a5d9f1e3b7c6a4d2f8e1b9c0a7d5e2f4b8c1a6d3e9f7b5c",
  "created_by": "john.doe@example.com",
  "related_requirement": "REQ-042",
  "related_phase_gate": "Phase 2",
  "description": "Phase 2 audit review documentation",
  "retention_period": "7 years",
  "classification": "Internal"
}
```

## Best Practices

### DO

- ✅ Generate hash immediately after creating evidence file
- ✅ Store original hash in metadata
- ✅ Verify hash before using evidence
- ✅ Use descriptive identifiers
- ✅ Include date of evidence creation
- ✅ Document chain of custody
- ✅ Store evidence in appropriate directory structure

### DON'T

- ❌ Modify evidence files after hashing
- ❌ Use spaces in filenames
- ❌ Omit hash from filename
- ❌ Mix evidence types in same directory
- ❌ Store sensitive data without encryption
- ❌ Delete evidence before retention period
- ❌ Use ambiguous identifiers

## Hash Verification

Regularly verify evidence integrity:

```bash
# Verify a specific evidence file
stored_hash="a3f8c9d1"
actual_hash=$(sha256sum evidence_audit_20260207_phase2-review_a3f8c9d1.pdf | cut -c1-8)

if [ "$stored_hash" = "$actual_hash" ]; then
    echo "✓ Evidence integrity verified"
else
    echo "✗ Evidence integrity check FAILED"
fi
```

## Automation Script

Create evidence file with proper naming:

```bash
#!/bin/bash
# create_evidence.sh

TYPE=$1
IDENTIFIER=$2
SOURCE_FILE=$3

DATE=$(date +%Y%m%d)
HASH=$(sha256sum "$SOURCE_FILE" | cut -c1-8)
EXT="${SOURCE_FILE##*.}"

TARGET_DIR="evidence/$(date +%Y)/$(date +%m)"
mkdir -p "$TARGET_DIR"

TARGET_FILE="${TARGET_DIR}/evidence_${TYPE}_${DATE}_${IDENTIFIER}_${HASH}.${EXT}"
cp "$SOURCE_FILE" "$TARGET_FILE"

echo "Evidence file created: $TARGET_FILE"
```

Usage:
```bash
./create_evidence.sh audit phase2-review report.pdf
```

## Retention Policy

| Evidence Type | Retention Period | Disposal Method |
|---------------|------------------|-----------------|
| Audit | 7 years | Secure deletion |
| Test | 3 years | Secure deletion |
| Security | 5 years | Secure deletion |
| Review | 3 years | Secure deletion |
| Deployment | 2 years | Archive then delete |
| Incident | 7 years | Secure deletion |
| Approval | Permanent | Archive |
| Monitoring | 1 year | Rolling deletion |
| Training | 3 years | Secure deletion |
| Change | 3 years | Secure deletion |

## Compliance Considerations

- GDPR: Personal data in evidence must be anonymized or encrypted
- SOC 2: Evidence must demonstrate control effectiveness
- ISO 27001: Evidence must support security management system
- HIPAA: Healthcare-related evidence requires additional protection

## References

- NIST SP 800-53: Security and Privacy Controls
- ISO/IEC 27001: Information Security Management
- Evidence handling best practices
- Chain of custody procedures

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | | | Initial evidence naming convention |
