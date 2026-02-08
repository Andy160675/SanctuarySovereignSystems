#!/bin/bash
# docs/procedures/pre_merge_validation.sh
# Automated Phase 1-4 validation for Season 3 merges

set -e

echo "=== SEASON 3 CONSTITUTIONAL MERGE VALIDATION ==="

# Phase 1: Identity
echo "Phase 1: Identity Verification..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ ! $CURRENT_BRANCH =~ ^s3-ext- ]]; then
    echo "❌ Branch name '$CURRENT_BRANCH' does not follow 's3-ext-XXX' convention"
    exit 1
fi

git tag --contains $(git merge-base origin/main HEAD) | grep -q v1.0.0-kernel74 || {
    echo "❌ Kernel tag v1.0.0-kernel74 not in ancestry"
    exit 1
}

# Phase 2: Evidence
echo "Phase 2: Evidence Chain..."
SHORT_HASH=$(git rev-parse --short HEAD)
EVIDENCE_DIR="EVIDENCE-$SHORT_HASH"
if [ ! -d "$EVIDENCE_DIR" ]; then
    echo "❌ Evidence directory $EVIDENCE_DIR missing"
    exit 1
fi

EVIDENCE_FILES=("commit.txt" "tag_check.txt" "diff_files.txt" "test_results.log" "kernel_invariants_74_74.txt")
for file in "${EVIDENCE_FILES[@]}"; do
  if [ ! -f "$EVIDENCE_DIR/$file" ]; then
    echo "❌ Missing evidence file: $file"
    exit 1
  fi
done

# Phase 3: Kernel Proof
echo "Phase 3: Kernel Integrity..."
# Independent verification
python -m sovereign_engine.tests.run_all | tee /tmp/kernel_test.out
grep -q "74/74 tests passed" /tmp/kernel_test.out || {
    echo "❌ Kernel tests failed during independent verification"
    exit 1
}

# Verify evidence matches current state
grep -q "$(git rev-parse HEAD)" "$EVIDENCE_DIR/commit.txt" || {
    echo "❌ Evidence commit hash does not match current HEAD"
    exit 1
}

# Phase 4: Extension Isolation
echo "Phase 4: Extension Isolation..."
MODIFIED_FILES=$(git diff --name-only origin/main...HEAD)
for file in $MODIFIED_FILES; do
  if [[ ! $file =~ ^sovereign_engine/extensions/[^/]+/ ]]; then
    echo "❌ KERNEL MODIFICATION ATTEMPT - File '$file' is outside extension boundary"
    exit 1
  fi
done

echo "✅ All pre-merge validations passed"
exit 0
