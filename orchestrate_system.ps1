Write-Host "🚀 INITIATING SOVEREIGN SYSTEM INTEGRATION TEST" -ForegroundColor Green

# --- STEP 0: CLEAN & BUILD ---
Write-Host "📦 Building Infrastructure..."
docker-compose down --volumes --remove-orphans
docker-compose build
docker-compose up -d

Write-Host "   Waiting for container health..."
Start-Sleep -Seconds 10

# --- STEP 1: SEED TEST DATA ---
Write-Host "🌱 Seeding Jurisdiction Data..."

New-Item -ItemType Directory -Force Evidence/Inbox | Out-Null
New-Item -ItemType Directory -Force Property/Leads | Out-Null

"Invoice #101 for Sovereign Services" | Set-Content Evidence/Inbox/test_invoice_stable.txt -Encoding UTF8
"3 Bed House. 123 Test Rd. Asking £350k. Warning: Structural cracks visible in foundation." | Set-Content Property/Leads/test_trap_fixer.txt -Encoding UTF8

# --- STEP 2: EXECUTE AGENTS ---
Write-Host "⚙️  Running Agents..."

# Run Evidence
docker-compose run --rm executor python src/agents/evidence_validator.py

# Run Property
docker-compose run --rm executor python src/agents/property_analyst.py

# --- STEP 3: VERIFY JURISDICTIONS ---
Write-Host "`n🔍 VERIFYING JURISDICTIONAL BOUNDARIES..."

if (Test-Path Evidence/Analysis/_verified/test_invoice_stable.json) {
    Write-Host "✅ [EVIDENCE] Correctly routed to _verified (STABLE)" -ForegroundColor Green
} else {
    Write-Host "❌ [EVIDENCE] Failed to reach _verified" -ForegroundColor Red
    exit 1
}

if (Test-Path Property/Scored/_drafts/test_trap_fixer.json) {
    Write-Host "✅ [PROPERTY] Correctly routed to _drafts (INSIDER)" -ForegroundColor Green
} else {
    Write-Host "❌ [PROPERTY] Failed to reach _drafts" -ForegroundColor Red
    exit 1
}

# --- STEP 4: VERIFY LEGISLATIVE LOGIC ---
Write-Host "`n⚖️  VERIFYING LEGISLATIVE ENFORCEMENT..."

$json = Get-Content Property/Scored/_drafts/test_trap_fixer.json | ConvertFrom-Json
$score = $json.condition_score

if ($score -le 5) {
    Write-Host "✅ [LEGISLATION] Defects Trap Caught! Score capped at $score (<= 5)" -ForegroundColor Green
} else {
    Write-Host "❌ [LEGISLATION] FAILED. Score is $score (Should be <= 5). The Agent ignored the law." -ForegroundColor Red
    exit 1
}

# --- STEP 5: READINESS & TESTS ---
Write-Host "`n📊 CHECKING SYSTEM READINESS..."
docker-compose run --rm executor python scripts/agent_readiness.py

Write-Host "`n🧪 RUNNING UNIT TESTS..."
docker-compose run --rm executor pytest tests/test_tracks.py

Write-Host "`n🏆 SOVEREIGN SYSTEM INTEGRATION COMPLETE. ALL SYSTEMS GO." -ForegroundColor Green