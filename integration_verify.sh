#!/bin/bash
# Wrapper for python verification script
echo "🔍 STARTING INTEGRATION VERIFICATION..."
python verify_integration.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[PASS] Trap Caught (Score capped)"
    echo "[PASS] Tracks Decoupled"
    echo "✅ VERIFICATION SUCCESSFUL"
else
    echo "❌ VERIFICATION FAILED"
fi

exit $EXIT_CODE
