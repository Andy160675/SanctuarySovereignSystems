# Rollback Procedure: S3-EXT-001 (confluence)

1. Tag pre-rollback state:
   git tag confluence-pre-rollback-<timestamp>
2. Revert extension commit:
   git revert <extension_commit_sha> --no-edit
3. Validate kernel:
   python -m sovereign_engine.tests.run_all
4. Re-validate extension absence/behavior as applicable.
5. If drill only, restore test branch from pre-rollback tag.
