# Evidence

This directory stores audit trails and evidence artifacts.

## Purpose

Evidence files support:
- Compliance audits
- Security assessments
- Phase gate approvals
- Incident investigations
- Regulatory requirements

## Organization

Evidence files are organized by year and month:

```
evidence/
└── YYYY/
    └── MM/
        └── evidence_<type>_<date>_<identifier>_<hash>.<ext>
```

## Naming Convention

Follow the evidence hash naming convention in:
`docs/templates/evidence_hash_naming_template.md`

## Guidelines

- Generate hash for all evidence files
- Never modify evidence after creation
- Document chain of custody
- Follow retention policies
- Secure sensitive evidence with encryption
- Verify integrity regularly

## Access Control

Evidence access is restricted. See CODEOWNERS for approval requirements.
