#!/bin/bash
# diagnose-shell-integration.sh

echo "=== VS Code Shell Integration Diagnostic ==="
echo ""
echo "1. Environment Variables:"
echo "   TERM_PROGRAM: $TERM_PROGRAM"
echo "   VSCODE_SHELL_INTEGRATION: $VSCODE_SHELL_INTEGRATION"
echo ""
echo "2. Shell Type: $SHELL"
echo ""
echo "3. Integration Script Location:"
code --locate-shell-integration-path $SHELL 2>/dev/null && echo "   Found" || echo "   Not found"
echo ""
echo "4. VS Code Version:"
code --version | head -1
echo ""
echo "5. Terminal Settings:"
echo "   Shell Integration Enabled: $(code --get-setting terminal.integrated.shellIntegration.enabled)"
echo ""
echo "=== End Diagnostic ==="
