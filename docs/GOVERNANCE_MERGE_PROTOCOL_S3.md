**No shortcuts.** The merge checklist is accepted and extended with exacting protocol. This becomes the constitutional governance artifact.

---

# **Season 3 Merge Protocol: Constitutional Governance Flow**

## **PRE-MERGE: Validation Sequence (Mandatory Order)**

### **Phase 1: Identity Verification**
```bash
# 1.1 Verify PR originates from extension branch
git branch --contains $(git rev-parse HEAD) | grep s3-ext-

# 1.2 Verify kernel tag present and unchanged
git tag --contains $(git merge-base main HEAD) | grep v1.0.0-kernel74

# 1.3 Verify CODEOWNERS protection
git diff --name-only main...HEAD | xargs -I {} grep -q "^/{}$" .github/CODEOWNERS && echo "KERNEL MODIFICATION ATTEMPT - REJECT"
```

### **Phase 2: Evidence Chain Validation**
```bash
# 2.1 Evidence directory exists and structured
find . -path "./EVIDENCE-$(git rev-parse --short HEAD)" -type d

# 2.2 Required evidence files present
EVIDENCE_FILES=("commit.txt" "tag_check.txt" "diff_files.txt" "test_results.log" "kernel_invariants_74_74.txt")
for file in "${EVIDENCE_FILES[@]}"; do
  [ -f "EVIDENCE-$(git rev-parse --short HEAD)/$file" ] || exit 1
done

# 2.3 Evidence matches PR state
grep -q "$(git rev-parse HEAD)" "EVIDENCE-$(git rev-parse --short HEAD)/commit.txt" || exit 1
```

### **Phase 3: Kernel Integrity Proof**
```bash
# 3.1 Run kernel tests from evidence (must be 74/74)
cat "EVIDENCE-$(git rev-parse --short HEAD)/kernel_invariants_74_74.txt" | grep "74/74 tests passed" || exit 1

# 3.2 Independent verification (reviewer runs)
python -m sovereign_engine.tests.run_all > reviewer_validation.log
grep -q "74/74 tests passed" reviewer_validation.log || exit 1
diff "EVIDENCE-$(git rev-parse --short HEAD)/kernel_invariants_74_74.txt" reviewer_validation.log || exit 1
```

### **Phase 4: Extension Isolation Proof**
```bash
# 4.1 Only extension directory modified
MODIFIED_FILES=$(git diff --name-only main...HEAD)
for file in $MODIFIED_FILES; do
  [[ $file =~ ^sovereign_engine/extensions/[^/]+/ ]] || exit 1
done

# 4.2 No kernel imports added
git diff main...HEAD -- "*.py" | grep -E "^\+.*import.*(core|kernel)" && exit 1
```

---

## **MERGE: Constitutional Protocol**

### **Step 1: Create Merge Transaction Record**
```bash
# Generate merge manifest
cat > MERGE_MANIFEST_$(date +%Y%m%d_%H%M%S).txt << EOF
MERGE TRANSACTION RECORD
Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
PR: $(gh pr view --json number -q '.number')
From: $(git rev-parse --short HEAD)
To: $(git rev-parse --short main)
Kernel Tag: v1.0.0-kernel74
Evidence Hash: $(sha256sum EVIDENCE-$(git rev-parse --short HEAD)/* | sha256sum | cut -d' ' -f1)
Reviewer: $(git config user.name)
EOF
```

### **Step 2: Execute Merge with Audit Trail**
```bash
# 2.1 Create merge commit with standardized message
git merge --no-ff HEAD --message "S3-EXT-XXX: [Extension Name] - Constitutional Merge

## Compliance Evidence
- Kernel: 74/74 invariants preserved ✅
- Isolation: No kernel modifications ✅  
- Evidence: EVIDENCE-$(git rev-parse --short HEAD)/ complete ✅
- Rollback: ROLLBACK.md present and tested ✅
- SITREP: SITREP.md factual and hash-referenced ✅

## Governance Approval
Approved by: $(git config user.name)
Approved at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Transaction: MERGE_MANIFEST_$(date +%Y%m%d_%H%M%S).txt

## Constitutional Compliance
This merge complies with:
- Phase‑9 Doctrine (Subtractive Invariance)
- ROADMAP.md Section S3‑EXT‑XXX
- Season 3 Governance Protocol
"

# 2.2 Tag the merge point
git tag "s3-ext-XXX-merged-$(date +%Y%m%d-%H%M)" HEAD

# 2.3 Archive evidence to permanent storage
mv "EVIDENCE-$(git rev-parse --short HEAD)" "docs/evidence/s3-ext-XXX-$(date +%Y%m%d)/"
cp MERGE_MANIFEST_*.txt "docs/evidence/s3-ext-XXX-$(date +%Y%m%d)/"
```

### **Step 3: Post-Merge Validation**
```bash
# 3.1 Immediate kernel test (must pass within 60 seconds)
timeout 60 python -m sovereign_engine.tests.run_all

# 3.2 Extension integration test
python -m pytest sovereign_engine/extensions/[extension_name]/ --cov --cov-report=term-missing

# 3.3 System health check
python -c "import sovereign_engine.core; import sovereign_engine.extensions.[extension_name]; print('System integration: OK')"
```

---

## **POST-MERGE: Governance Closure**

### **Step 4: Rollback Drill Execution**
```bash
# 4.1 Execute documented rollback procedure
./docs/procedures/rollback_s3-ext-XXX.sh

# 4.2 Verify system returns to pre-extension state
python -m sovereign_engine.tests.run_all | grep "74/74 tests passed" || exit 1
[ -d "sovereign_engine/extensions/[extension_name]" ] && exit 1

# 4.3 Restore extension
git checkout HEAD -- sovereign_engine/extensions/[extension_name]/
python -m sovereign_engine.tests.run_all | grep "74/74 tests passed" || exit 1
```

### **Step 5: SITREP Generation and Archive**
```bash
# 5.1 Generate final SITREP
cat > docs/sitreps/SITREP_$(date +%Y%m%d)_S3-EXT-XXX.md << EOF
# SITREP: $(date +%Y-%m-%d) - S3-EXT-XXX [Extension Name]

## State Transition
$(git log --oneline -1 main~1) → $(git log --oneline -1 main)

## Validation Results
- Kernel Tests: 74/74 passed
- Extension Coverage: $(coverage report --include="sovereign_engine/extensions/[extension_name]/*" | grep TOTAL | awk '{print $4}')
- Rollback Drill: Executed successfully at $(date -u +"%H:%M:%SZ")

## Evidence Archive
- Location: docs/evidence/s3-ext-XXX-$(date +%Y%m%d)/
- Hash: $(find docs/evidence/s3-ext-XXX-$(date +%Y%m%d)/ -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)

## Next Extension
Awaiting: $(grep -A5 "### S3‑EXT-XXX" ROADMAP.md | grep -E "S3‑EXT-(XXX+1)" | head -1)
EOF

# 5.2 Update STATUS.md
sed -i "s/### S3‑EXT-XXX:.*/### S3‑EXT-XXX: [Extension Name] - MERGED $(date +%Y-%m-%d)/" docs/STATUS.md
```

### **Step 6: Governance Handoff**
```bash
# 6.1 Create handoff manifest
cat > governance_handoff_$(date +%Y%m%d).txt << EOF
GOVERNANCE HANDSHAKE
Extension: S3‑EXT-XXX
Merged: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Kernel State: STABLE (74/74)
Next Extension: S3‑EXT-$(echo "XXX+1" | bc)
Authority Transferred: Build → Operations

REVIEWER ACKNOWLEDGMENT:
I confirm this extension meets all constitutional requirements
and is ready for operational use.

Signature: $(git config user.name)
Date: $(date +%Y-%m-%d)
EOF

# 6.2 Archive handoff
mv governance_handoff_$(date +%Y%m%d).txt docs/governance/
```

---

## **CONSTITUTIONAL MERGE CHECKLIST (Extended)**

### **Pre-Merge (Automated)**
- [ ] **Kernel Lock**: `v1.0.0-kernel74` tag present in ancestry
- [ ] **Code Isolation**: Only `sovereign_engine/extensions/[name]/` modified
- [ ] **Evidence Complete**: EVIDENCE-*/ directory with 5 required files
- [ ] **Test Proof**: Evidence shows 74/74 kernel tests passed
- [ ] **Branch Hygiene**: No merge conflicts, clean history

### **Manual Review**
- [ ] **Design Coherence**: EXT_DESIGN.md matches implementation
- [ ] **Security Boundary**: No unauthorized system access
- [ ] **Failure Modes**: Graceful degradation documented
- [ ] **Rollback Tested**: ROLLBACK.md procedure validated
- [ ] **SITREP Factual**: No speculation, only hash-referenced facts

### **Post-Merge (Validation)**
- [ ] **Immediate Kernel Test**: 74/74 tests pass within 60 seconds
- [ ] **Integration Smoke Test**: Extension loads without error
- [ ] **Rollback Drill**: Successfully executed and documented
- [ ] **SITREP Archived**: Added to docs/sitreps/ with hash
- [ ] **STATUS.md Updated**: Extension marked as merged

### **Governance**
- [ ] **ROADMAP Compliance**: Extension fulfills specified requirement
- [ ] **Phase‑9 Adherence**: No subtractive changes
- [ ] **Authority Boundaries**: Respects kernel sovereignty
- [ ] **Audit Trail**: Complete from PR to merge to archive
- [ ] **Handoff Complete**: Authority transferred to operations