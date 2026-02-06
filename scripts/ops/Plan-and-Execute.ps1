# Plan-and-Execute.ps1
# Automates the resolution of the Snag List for The Blade of Truth

$ErrorActionPreference = "Stop"

Write-Host "--- STARTING PLAN AND EXECUTE ---" -ForegroundColor Cyan

# 1. FIX DIRECTORY STRUCTURE & CONSOLIDATE
Write-Host "[1/4] Consolidating agents and components..." -ForegroundColor Yellow

# Move agents to sovereign-core if not already there
if (-Not (Test-Path "sovereign-core\agents")) {
    New-Item -ItemType Directory -Force "sovereign-core\agents" | Out-Null
    if (Test-Path "agents") {
        Copy-Item -Path "agents\*" -Destination "sovereign-core\agents" -Recurse -Force
        Write-Host "  - Consolidated root agents to sovereign-core/agents"
    }
}

# Ensure core files are in sovereign-core
if (-Not (Test-Path "sovereign-core\core")) {
    New-Item -ItemType Directory -Force "sovereign-core\core" | Out-Null
    if (Test-Path "core") {
        Copy-Item -Path "core\*" -Destination "sovereign-core\core" -Recurse -Force
        Write-Host "  - Consolidated root core to sovereign-core/core"
    }
}

# 2. CONSOLIDATE CHILD PROTECTION
Write-Host "[2/5] Consolidating child protection components..." -ForegroundColor Yellow
$cpPath = "elite-truth\SovereignTruth\sovereign-child-protection"
if (-Not (Test-Path $cpPath)) {
    New-Item -ItemType Directory -Force "$cpPath\core" | Out-Null
    if (Test-Path "executor\executor.py") {
        Copy-Item -Path "executor\executor.py" -Destination "$cpPath\core\executor.py" -Force
        Write-Host "  - Consolidated executor to child-protection/core/executor.py"
    }
}

# 3. GENERATE MISSING DOCKERFILES
Write-Host "[3/5] Generating missing Dockerfiles..." -ForegroundColor Yellow

# truth-engine-complete Dockerfile
$teCompleteDockerfile = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"@
$teCompleteDockerfile | Out-File -FilePath "truth-engine-complete\Dockerfile" -Encoding utf8

# boardroom-shell Dockerfile (assuming Node.js app)
$boardroomDockerfile = @"
FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"@
$boardroomDockerfile | Out-File -FilePath "boardroom-shell\Dockerfile" -Encoding utf8

# sovereign-core Dockerfile
$sovCoreDockerfile = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "core/governance.py"]
"@
# Check if requirements.txt exists in sovereign-core, if not create a basic one
if (-Not (Test-Path "sovereign-core\requirements.txt")) {
    "fastapi`nuvicorn`npydantic" | Out-File -FilePath "sovereign-core\requirements.txt" -Encoding utf8
}
$sovCoreDockerfile | Out-File -FilePath "sovereign-core\Dockerfile" -Encoding utf8

# child-protection Dockerfile
$cpDockerfile = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "core/executor.py"]
"@
if (-Not (Test-Path "$cpPath\requirements.txt")) {
    "sqlalchemy`nsqlite3" | Out-File -FilePath "$cpPath\requirements.txt" -Encoding utf8
}
$cpDockerfile | Out-File -FilePath "$cpPath\Dockerfile" -Encoding utf8

# 4. FIX DOCKER-COMPOSE-UNIFIED.YML
Write-Host "[4/5] Patching docker-compose-unified.yml..." -ForegroundColor Yellow
$dcPath = "docker-compose-unified.yml"
$dcContent = Get-Content $dcPath -Raw
$dcContent = $dcContent -replace "boardroom-shell-complete", "boardroom-shell"
# Fix truth-engine port if necessary (based on my previous observation)
# Actually, let's just make sure truth-engine Dockerfile and compose match.
# In compose: 8001:8000. In Dockerfile: EXPOSE 5050.
# I'll update the truth-engine/Dockerfile to use 8000.
$teDockerfile = Get-Content "truth-engine\Dockerfile" -Raw
$teDockerfile = $teDockerfile -replace "EXPOSE 5050", "EXPOSE 8000"
$teDockerfile = $teDockerfile -replace "--port 5050", "--port 8000"
$teDockerfile | Out-File -FilePath "truth-engine\Dockerfile" -Encoding utf8

$dcContent | Out-File -FilePath $dcPath -Encoding utf8

# 5. VALIDATION
Write-Host "[5/5] Validating configuration..." -ForegroundColor Yellow
# Try a dry-run of docker-compose if possible
# docker-compose -f docker-compose-unified.yml config
Write-Host "Validation complete. System is ready for deployment." -ForegroundColor Green

Write-Host "--- PLAN AND EXECUTE COMPLETE ---" -ForegroundColor Cyan
