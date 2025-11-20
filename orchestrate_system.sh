#!/bin/bash

# COLORS
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 INITIATING SOVEREIGN SYSTEM INTEGRATION TEST${NC}"

# --- STEP 0: CLEAN & BUILD ---
echo "📦 Building Infrastructure..."
docker-compose down --volumes --remove-orphans
docker-compose build
docker-compose up -d

echo "   Waiting for container health..."
sleep 10 # Give python startup a moment

# --- STEP 1: SEED TEST DATA ---
echo "🌱 Seeding Jurisdiction Data..."

# Ensure Host Directories Exist
mkdir -p Evidence/Inbox
mkdir -p Property/Leads

# Seed Evidence (Stable Track Test)
echo "Invoice #101 for Sovereign Services" > Evidence/Inbox/test_invoice_stable.txt

# Seed Property (Insider Track + Legislative Trap)
# This text contains "structural cracks" -> Should trigger Code-Level Downgrade to Score 5
echo "3 Bed House. 123 Test Rd. Asking £350k. Warning: Structural cracks visible in foundation." > Property/Leads/test_trap_fixer.txt

# --- STEP 2: EXECUTE AGENTS ---
echo "⚙️  Running Agents..."

# Run Evidence (Should Auto-Verify)
docker-compose run --rm executor python src/agents/evidence_validator.py

# Run Property (Should Draft + Enforce Legislative Cap)
docker-compose run --rm executor python src/agents/property_analyst.py

# --- STEP 3: VERIFY JURISDICTIONS ---
echo -e "\n🔍 VERIFYING JURISDICTIONAL BOUNDARIES..."

# Check Evidence (Must be in _verified)
if ls Evidence/Analysis/_verified/test_invoice_stable.json 1> /dev/null 2>&1; then
    echo -e "${GREEN}✅ [EVIDENCE] Correctly routed to _verified (STABLE)${NC}"
else
    echo -e "${RED}❌ [EVIDENCE] Failed to reach _verified${NC}"
    exit 1
fi

# Check Property (Must be in _drafts)
if ls Property/Scored/_drafts/test_trap_fixer.json 1> /dev/null 2>&1; then
    echo -e "${GREEN}✅ [PROPERTY] Correctly routed to _drafts (INSIDER)${NC}"
else
    echo -e "${RED}❌ [PROPERTY] Failed to reach _drafts${NC}"
    exit 1
fi

# --- STEP 4: VERIFY LEGISLATIVE LOGIC ---
echo -e "\n⚖️  VERIFYING LEGISLATIVE ENFORCEMENT..."

# The Property Agent saw "Structural cracks". Code must cap score at 5.
SCORE=$(grep -o '"condition_score": [0-9]*' Property/Scored/_drafts/test_trap_fixer.json | awk -F': ' '{print $2}')

if [ "$SCORE" -le 5 ]; then
    echo -e "${GREEN}✅ [LEGISLATION] Defects Trap Caught! Score capped at $SCORE (<= 5)${NC}"
else
    echo -e "${RED}❌ [LEGISLATION] FAILED. Score is $SCORE (Should be <= 5). The Agent ignored the law.${NC}"
    exit 1
fi

# --- STEP 5: READINESS & TESTS ---
echo -e "\n📊 CHECKING SYSTEM READINESS..."
docker-compose run --rm executor python scripts/agent_readiness.py

echo -e "\n🧪 RUNNING UNIT TESTS..."
# Running tests inside container to ensure environment parity
docker-compose run --rm executor pytest tests/test_tracks.py

echo -e "\n${GREEN}🏆 SOVEREIGN SYSTEM INTEGRATION COMPLETE. ALL SYSTEMS GO.${NC}"