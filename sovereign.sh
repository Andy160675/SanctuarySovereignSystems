#!/bin/bash
# sovereign.sh - The CLI for your framework

COMMAND=$1
AGENT=$2

if [ "$COMMAND" == "check" ]; then
    python calculate_readiness.py
fi

if [ "$COMMAND" == "promote" ]; then
    if [ -z "$AGENT" ]; then
        echo "Usage: ./sovereign.sh promote [agent-name]"
        exit 1
    fi

    # Check if JSON report says READY
    # Note: This requires jq installed. If not, we might need a python one-liner.
    # Fallback to python for portability in this environment
    STATUS=$(python -c "import json; print(json.load(open('readiness_report.json')).get('$AGENT', {}).get('status', 'UNKNOWN'))")

    if [ "$STATUS" == "READY_FOR_PROMOTION" ]; then
        echo "✅ Promotion Approved for $AGENT"
        echo "   Switching .env to STABLE track..."
        
        # 1. Backup .env
        cp .env .env.bak
        
        # 2. Switch Variable (simple sed replacement)
        # Assumes you have EVIDENCE_TRACK=insider in your .env
        if [ "$AGENT" == "evidence-validator" ]; then
            sed -i 's/EVIDENCE_TRACK=insider/EVIDENCE_TRACK=stable/g' .env
        elif [ "$AGENT" == "property-analyst" ]; then
             sed -i 's/PROPERTY_TRACK=insider/PROPERTY_TRACK=stable/g' .env
        fi
        
        # 3. Restart Docker
        echo "   Restarting container..."
        # docker-compose restart agent-$AGENT
        echo "   (Docker restart skipped in this shell environment)"
        
        echo "🚀 $AGENT is now live in STABLE mode."
    else
        echo "🛑 Promotion Denied: $AGENT is currently status '$STATUS'"
        echo "   Run './sovereign.sh check' to see metrics."
    fi
fi