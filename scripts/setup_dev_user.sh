#!/bin/bash
# =============================================================================
# DEV USER SETUP SCRIPT
# =============================================================================
# Purpose: Create a scoped developer user on PC4 with read-only access
# Usage: sudo ./scripts/setup_dev_user.sh <username> <public_key_file>
#
# This script creates a user that can:
#   - SSH into PC4
#   - Read logs and status
#   - Pull from git repos
#
# But CANNOT:
#   - Run deploy.sh
#   - Modify system config
#   - Access production secrets
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[+]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# =============================================================================
# VALIDATION
# =============================================================================

if [ "$EUID" -ne 0 ]; then
    error "Please run as root (sudo)"
fi

if [ $# -lt 2 ]; then
    echo "Usage: $0 <username> <public_key_file>"
    echo ""
    echo "Arguments:"
    echo "  username        - The username to create (e.g., 'dev_laptop_andy')"
    echo "  public_key_file - Path to the user's SSH public key file"
    echo ""
    echo "Example:"
    echo "  sudo $0 dev_laptop_andy /tmp/andy_id_ed25519.pub"
    exit 1
fi

USERNAME="$1"
PUBKEY_FILE="$2"

# Validate inputs
if [[ ! "$USERNAME" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    error "Invalid username: $USERNAME (must be lowercase, start with letter)"
fi

if [ ! -f "$PUBKEY_FILE" ]; then
    error "Public key file not found: $PUBKEY_FILE"
fi

# =============================================================================
# CREATE USER
# =============================================================================

log "Creating developer user '$USERNAME'..."

# Check if user exists
if id "$USERNAME" &>/dev/null; then
    warn "User $USERNAME already exists, updating configuration..."
else
    # Create user with home directory, no login shell by default
    useradd -m -s /bin/bash "$USERNAME"
    log "User $USERNAME created"
fi

# =============================================================================
# SET UP SSH ACCESS
# =============================================================================

log "Configuring SSH access..."

USER_HOME=$(eval echo "~$USERNAME")
SSH_DIR="$USER_HOME/.ssh"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# Add public key (append to allow multiple keys)
if ! grep -qF "$(cat "$PUBKEY_FILE")" "$SSH_DIR/authorized_keys" 2>/dev/null; then
    cat "$PUBKEY_FILE" >> "$SSH_DIR/authorized_keys"
    log "SSH public key added"
else
    warn "SSH public key already present"
fi

chmod 600 "$SSH_DIR/authorized_keys"
chown -R "$USERNAME":"$USERNAME" "$SSH_DIR"

# =============================================================================
# CREATE DEV GROUP (if not exists)
# =============================================================================

if ! getent group developers &>/dev/null; then
    groupadd developers
    log "Created 'developers' group"
fi

usermod -aG developers "$USERNAME"
log "Added $USERNAME to 'developers' group"

# =============================================================================
# SET UP READ-ONLY ACCESS TO LOGS
# =============================================================================

log "Configuring read-only access to logs..."

# Common log directories
LOG_DIRS=(
    "/var/log/sovereign-system"
    "/var/log/docker"
    "$USER_HOME/../sovereign/logs"
)

for LOG_DIR in "${LOG_DIRS[@]}"; do
    if [ -d "$LOG_DIR" ]; then
        # Allow developers group to read logs
        setfacl -R -m g:developers:rX "$LOG_DIR" 2>/dev/null || {
            chgrp -R developers "$LOG_DIR" 2>/dev/null || true
            chmod -R g+rX "$LOG_DIR" 2>/dev/null || true
        }
        log "Granted read access to $LOG_DIR"
    fi
done

# =============================================================================
# CREATE RESTRICTED SUDOERS (optional, for specific commands)
# =============================================================================

SUDOERS_FILE="/etc/sudoers.d/developers"

if [ ! -f "$SUDOERS_FILE" ]; then
    log "Creating restricted sudoers for developers..."

    cat > "$SUDOERS_FILE" << 'EOF'
# Developers can run these commands without password
# But NOT deploy.sh or docker commands

%developers ALL=(ALL) NOPASSWD: /usr/bin/docker ps
%developers ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
%developers ALL=(ALL) NOPASSWD: /usr/bin/systemctl status *
%developers ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u sovereign-*

# Explicitly deny dangerous operations
%developers ALL=(ALL) !ALL
EOF

    chmod 440 "$SUDOERS_FILE"
    visudo -c -f "$SUDOERS_FILE" || {
        rm "$SUDOERS_FILE"
        warn "Sudoers file had errors, removed"
    }
fi

# =============================================================================
# SET UP GIT ACCESS
# =============================================================================

log "Configuring git repository access..."

REPO_DIR="/home/$(logname 2>/dev/null || echo sovereign)/sovereign-system"

if [ -d "$REPO_DIR" ]; then
    # Allow developers to read the repo
    setfacl -R -m g:developers:rX "$REPO_DIR" 2>/dev/null || {
        chmod -R g+rX "$REPO_DIR" 2>/dev/null || true
    }
    log "Granted read access to $REPO_DIR"
fi

# =============================================================================
# CREATE USER PROFILE
# =============================================================================

log "Setting up user profile..."

cat > "$USER_HOME/.bashrc.d/sovereign-dev.sh" << 'EOF'
# Sovereign System Developer Environment

# Aliases for common operations
alias sov-status='docker ps --filter name=sovereign'
alias sov-logs='docker logs --tail 100 -f'
alias sov-health='curl -s http://localhost:8000/health | python3 -m json.tool'

# Git shortcuts
alias gs='git status'
alias gp='git pull origin main'
alias gl='git log --oneline -10'

# Remind user of their access level
echo ""
echo "=== Sovereign System - Developer Access ==="
echo "You have READ-ONLY access to logs and status."
echo "To deploy, contact an ops team member."
echo ""
EOF

# Source custom bashrc if exists
if ! grep -q "bashrc.d/sovereign-dev.sh" "$USER_HOME/.bashrc" 2>/dev/null; then
    mkdir -p "$USER_HOME/.bashrc.d"
    echo '[ -f ~/.bashrc.d/sovereign-dev.sh ] && . ~/.bashrc.d/sovereign-dev.sh' >> "$USER_HOME/.bashrc"
fi

chown -R "$USERNAME":"$USERNAME" "$USER_HOME/.bashrc.d" "$USER_HOME/.bashrc"

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "============================================================"
log "Developer user '$USERNAME' setup complete!"
echo "============================================================"
echo ""
echo "The user can now:"
echo "  - SSH to this machine using their private key"
echo "  - Read logs in /var/log/sovereign-system"
echo "  - View docker container status"
echo "  - Pull from git repositories"
echo ""
echo "The user CANNOT:"
echo "  - Run deploy.sh or docker stack commands"
echo "  - Modify system configuration"
echo "  - Access production secrets"
echo ""
echo "Test SSH access:"
echo "  ssh $USERNAME@$(hostname -f || hostname)"
echo ""
