# VS Code Shell Integration Guide

This guide describes how to enable and use VS Code shell integration features for `SanctuarySovereignSystems`.

## 1. Automatic Workspace Settings
The following settings are pre-configured in `.vscode/settings.json`:
- **Shell Integration**: Enabled (`terminal.integrated.shellIntegration.enabled`)
- **Command Decorations**: Success/failure indicators enabled.
- **Sticky Scroll**: Terminal sticky scroll enabled.
- **IntelliSense**: Terminal suggestions enabled.
- **Quick Fixes**: Enabled for common git and npm commands.

## 2. Keybindings
Custom keybindings are provided in `.vscode/keybindings.json` (Note: You may need to manually merge these into your global `keybindings.json` if they don't apply automatically):
- `Ctrl+R`: Run recent command.
- `Ctrl+Alt+R`: Send standard `Ctrl+R` to shell (reverse search).
- `Ctrl+G`: Go to recent directory.
- `Ctrl+Shift+C`: Clear terminal suggestion cache.
- `Ctrl+Space`: Enhanced IntelliSense (PowerShell).

## 3. Installation Scripts
Located in `scripts/vscode/`:

### Install Integration
Add the integration hook to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
./scripts/vscode/install-vscode-shell-integration.sh <shell_type>
```
Supported types: `bash`, `zsh`, `fish`.

### Diagnostic
Verify your current integration status:
```bash
./scripts/vscode/diagnose-shell-integration.sh
```

## 4. Manual PowerShell Setup
If using PowerShell, add this to your `$PROFILE`:
```powershell
if ($env:TERM_PROGRAM -eq "vscode") {
    . (code --locate-shell-integration-path pwsh)
}
```

## 5. Troubleshooting
If decorations are missing or performance is slow:
1. Run the Diagnostic script.
2. Clear the global suggestion cache: `Terminal: Clear Suggest Cached Globals` from the Command Palette.
3. Ensure `code` is in your system PATH.
