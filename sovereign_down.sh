#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
DC="docker-compose -f ${COMPOSE_FILE}"

echo -e "${YELLOW}⏻ Initiating Sovereign Shutdown...${NC}"

# 1. Optional: run a final ledger sanity check before stop
if [ -f verify_integration.py ]; then
  echo "🔎 Final ledger check..."
  python verify_integration.py || echo "   (Ledger check failed; investigate later)"
fi

# 2. Stop services gracefully
echo "🛑 Stopping containers..."
$DC down

echo -e "${GREEN}✅ Sovereign runtime stopped. Ledgers remain on disk.${NC}"
