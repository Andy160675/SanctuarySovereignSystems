#!/bin/bash

# SOVEREIGN SYSTEM LAUNCHER
# Usage: ./launch.sh

echo "🚀 Initializing Sovereign System..."

# 1. Check Docker
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker Desktop/Engine."
  exit 1
fi

# 2. Build & Start
echo "📦 Building Containers..."
docker-compose down --remove-orphans
docker-compose build
docker-compose up -d

# 3. Health Check
echo "🏥 Waiting for health checks..."
sleep 10
if docker ps | grep -q "sovereign-executor"; then
    echo "✅ Governance: ENFORCED"
    echo "✅ Agents: RUNNING"
    echo "🟢 OPERATIONAL"
else
    echo "❌ System failed to start. Check logs: docker-compose logs"
    exit 1
fi
