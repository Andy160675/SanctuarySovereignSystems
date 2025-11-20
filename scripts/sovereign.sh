#!/bin/bash
# Sovereign CLI - Operations Controller

COMMAND=$1
ARG=$2

function show_help {
    echo "Usage: ./scripts/sovereign.sh [command]"
    echo "Commands:"
    echo "  check      - Run readiness analysis on audit logs"
    echo "  promote    - Promote an agent to STABLE track (edits .env)"
    echo "  audit      - Verify cryptographic integrity of the ledger"
    echo "  clean      - Wipe draft folders (Insider reset)"
}

if [ -z "$COMMAND" ]; then
    show_help
    exit 1
fi

if [ "$COMMAND" == "check" ]; then
    echo "📊 Checking Agent Readiness..."
    python3 scripts/calculate_readiness.py
fi

if [ "$COMMAND" == "audit" ]; then
    echo "🔐 Verifying Ledger Integrity..."
    python3 scripts/verify_ledger.py
fi

if [ "$COMMAND" == "promote" ]; then
    if [ -z "$ARG" ]; then
        echo "Error: Specify agent name (e.g., 'evidence')"
        exit 1
    fi
    echo "🚀 Promoting $ARG to STABLE..."
    cp .env .env.bak
    sed -i 's/TRACK=insider/TRACK=stable/g' .env
    echo "✅ .env updated. Restarting containers..."
    docker-compose down && docker-compose up -d
fi

if [ "$COMMAND" == "clean" ]; then
    echo "🧹 Cleaning Insider Drafts..."
    rm -rf Evidence/Analysis/_drafts/*
    rm -rf Property/Scored/_drafts/*
    echo "✅ Cleaned."
fi
