#!/bin/bash
# =============================================================================
# SOVEREIGN SYSTEM DEPLOYMENT SCRIPT
# =============================================================================
# Purpose: Controlled deployment to PC4 Docker Swarm
# Location: Run this ONLY on PC4 (Swarm Manager)
#
# ISO/IEC 42001 Alignment:
#   - Clause 8 (Operation): Controlled, repeatable deployment process
#   - Annex A A.5: Change and configuration management
#
# Prerequisites:
#   - Docker Swarm initialized (PC4 as manager)
#   - Git repository cloned to PROJECT_DIR
#   - NAS mounted at /mnt/sovereign-data (optional)
# =============================================================================

set -e  # Exit immediately on any error
set -o pipefail  # Fail on pipe errors

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_DIR="${PROJECT_DIR:-/home/$(whoami)/sovereign-system}"
STACK_NAME="${STACK_NAME:-sovereign-mesh}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8000/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"
SMOKE_TEST_DELAY="${SMOKE_TEST_DELAY:-30}"
LOG_FILE="${PROJECT_DIR}/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    case "$level" in
        INFO)  echo -e "${BLUE}[INFO]${NC} $message" ;;
        OK)    echo -e "${GREEN}[OK]${NC} $message" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" ;;
    esac

    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

check_prerequisites() {
    log INFO "Checking prerequisites..."

    # Check if running on Swarm manager
    if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
        log ERROR "Docker Swarm is not active. Initialize swarm first."
        exit 1
    fi

    if ! docker info 2>/dev/null | grep -q "Is Manager: true"; then
        log ERROR "This node is not a Swarm manager. Run deploy.sh on PC4."
        exit 1
    fi

    # Check project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log ERROR "Project directory not found: $PROJECT_DIR"
        exit 1
    fi

    # Check compose file exists
    if [ ! -f "$PROJECT_DIR/$COMPOSE_FILE" ]; then
        log ERROR "Compose file not found: $PROJECT_DIR/$COMPOSE_FILE"
        exit 1
    fi

    log OK "Prerequisites check passed"
}

pull_latest() {
    log INFO "Pulling latest code from origin/main..."

    cd "$PROJECT_DIR" || exit 1

    # Stash any local changes
    if [ -n "$(git status --porcelain)" ]; then
        log WARN "Local changes detected, stashing..."
        git stash push -m "deploy-auto-stash-$(date +%s)"
    fi

    # Pull latest
    git fetch origin
    git checkout main
    git pull origin main

    # Get current commit for logging
    COMMIT_SHA=$(git rev-parse HEAD)
    COMMIT_SHORT=$(git rev-parse --short HEAD)
    log OK "Now at commit: $COMMIT_SHORT"

    echo "$COMMIT_SHA" > "$PROJECT_DIR/.last_deploy_commit"
}

verify_integrity() {
    log INFO "Verifying hash chain integrity..."

    cd "$PROJECT_DIR" || exit 1

    # Run hash chain verification if script exists
    if [ -f "scripts/verify_hash_chain.py" ]; then
        if python3 scripts/verify_hash_chain.py --quiet; then
            log OK "Hash chain integrity verified"
        else
            log ERROR "Hash chain integrity check FAILED"
            exit 1
        fi
    elif [ -f "scripts/verify_chain.py" ]; then
        if python3 scripts/verify_chain.py --quiet; then
            log OK "Hash chain integrity verified"
        else
            log ERROR "Hash chain integrity check FAILED"
            exit 1
        fi
    else
        log WARN "No hash chain verification script found, skipping..."
    fi
}

deploy_stack() {
    log INFO "Deploying stack '$STACK_NAME' to Docker Swarm..."

    cd "$PROJECT_DIR" || exit 1

    # Deploy with registry auth if available
    if docker stack deploy -c "$COMPOSE_FILE" --with-registry-auth "$STACK_NAME" 2>/dev/null; then
        log OK "Stack deployment initiated"
    else
        # Retry without registry auth
        docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"
        log OK "Stack deployment initiated (without registry auth)"
    fi

    # Wait for services to start
    log INFO "Waiting ${SMOKE_TEST_DELAY}s for services to initialize..."
    sleep "$SMOKE_TEST_DELAY"
}

health_check() {
    log INFO "Running health check against $HEALTH_ENDPOINT..."

    local max_attempts=$((HEALTH_TIMEOUT / 5))
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            log OK "Health check passed"
            return 0
        fi

        log INFO "Attempt $attempt/$max_attempts - waiting 5s..."
        sleep 5
        attempt=$((attempt + 1))
    done

    log ERROR "Health check failed after $HEALTH_TIMEOUT seconds"
    return 1
}

show_status() {
    log INFO "Deployment status:"

    echo ""
    echo "Services:"
    docker stack services "$STACK_NAME" 2>/dev/null || true

    echo ""
    echo "Recent tasks:"
    docker stack ps "$STACK_NAME" --no-trunc 2>/dev/null | head -20 || true
}

rollback() {
    log WARN "Initiating rollback..."

    # If we have a previous commit, check it out
    if [ -f "$PROJECT_DIR/.last_good_commit" ]; then
        local last_good=$(cat "$PROJECT_DIR/.last_good_commit")
        log INFO "Rolling back to last known good commit: $last_good"

        cd "$PROJECT_DIR" || exit 1
        git checkout "$last_good"

        # Redeploy
        docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"
        log WARN "Rollback deployed. Manual verification required."
    else
        log ERROR "No rollback point available"
    fi
}

save_good_state() {
    # Save this commit as last known good
    if [ -f "$PROJECT_DIR/.last_deploy_commit" ]; then
        cp "$PROJECT_DIR/.last_deploy_commit" "$PROJECT_DIR/.last_good_commit"
        log INFO "Saved current commit as last known good state"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    echo ""
    echo "============================================================"
    echo "  SOVEREIGN SYSTEM DEPLOYMENT"
    echo "  $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "============================================================"
    echo ""

    # Initialize log
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== Deployment started at $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"

    # Run deployment steps
    check_prerequisites
    pull_latest
    verify_integrity
    deploy_stack

    # Health check
    if health_check; then
        save_good_state
        show_status

        echo ""
        echo "============================================================"
        log OK "DEPLOYMENT SUCCESSFUL"
        echo "============================================================"
        echo ""
        echo "Stack:   $STACK_NAME"
        echo "Commit:  $(cat "$PROJECT_DIR/.last_deploy_commit" 2>/dev/null || echo 'unknown')"
        echo "Log:     $LOG_FILE"
        echo ""

        exit 0
    else
        show_status

        echo ""
        echo "============================================================"
        log ERROR "DEPLOYMENT FAILED"
        echo "============================================================"
        echo ""

        # Offer rollback
        read -p "Attempt rollback? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi

        exit 1
    fi
}

# Run main function
main "$@"
