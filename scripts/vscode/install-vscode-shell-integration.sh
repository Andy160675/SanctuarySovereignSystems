#!/bin/bash
# install-vscode-shell-integration.sh

SHELL_TYPE=${1:-bash}
VSCODE_PATH=$(which code 2>/dev/null)

if [[ -z "$VSCODE_PATH" ]]; then
    echo "Error: VS Code 'code' command not found in PATH"
    exit 1
fi

case $SHELL_TYPE in
    bash|zsh)
        CONFIG_FILE="$HOME/.${SHELL_TYPE}rc"
        INTEGRATION_CMD="[[ \"\$TERM_PROGRAM\" == \"vscode\" ]] && . \"\$(code --locate-shell-integration-path $SHELL_TYPE)\""
        ;;
    fish)
        CONFIG_FILE="$HOME/.config/fish/config.fish"
        INTEGRATION_CMD="if test \"\$TERM_PROGRAM\" = \"vscode\"; source (code --locate-shell-integration-path fish); end"
        ;;
    *)
        echo "Unsupported shell: $SHELL_TYPE"
        exit 1
        ;;
esac

echo "Adding shell integration to $CONFIG_FILE"
echo "$INTEGRATION_CMD" >> "$CONFIG_FILE"

echo "Installation complete. Restart your shell or source $CONFIG_FILE"
