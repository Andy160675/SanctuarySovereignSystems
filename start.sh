#!/usr/bin/env bash
# =============================================================================
# Sovereign System - Atomic Boot Script (Unix/Linux/macOS)
# =============================================================================
# This script provides deterministic system startup with:
# - PID management for process tracking
# - Autobuild gate checking
# - Health verification
# - Evidence logging
#
# Usage: ./start.sh [--force] [--dev] [--validate-only]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PID_FILE="$SCRIPT_DIR/.sovereign.pid"
LOCK_FILE="$SCRIPT_DIR/.sovereign.lock"
LOG_DIR="$SCRIPT_DIR/logs"
COMPOSE_FILE="compose/docker-compose.mission.yml"
AUTOBUILD_CONFIG="config/autobuild.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Utility Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

cleanup() {
    rm -f "$LOCK_FILE"
}

trap cleanup EXIT

# =============================================================================
# Lock Management
# =============================================================================

acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_pid
        lock_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
            log_error "Another instance is running (PID: $lock_pid)"
            exit 1
        fi
        log_warn "Stale lock file found, removing..."
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
}

# =============================================================================
# PID Management
# =============================================================================

write_pid() {
    local boot_time
    boot_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    cat > "$PID_FILE" << EOF
{
  "boot_pid": $$,
  "boot_time_utc": "$boot_time",
  "compose_file": "$COMPOSE_FILE",
  "status": "running",
  "phase": $(cat governance/ACTIVE_PHASE 2>/dev/null || echo 0)
}
EOF
    log_info "PID file written: $$"
}

clear_pid() {
    if [ -f "$PID_FILE" ]; then
        # Mark as stopped rather than delete
        local stop_time
        stop_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        python3 -c "
import json
with open('$PID_FILE', 'r') as f:
    data = json.load(f)
data['status'] = 'stopped'
data['stop_time_utc'] = '$stop_time'
with open('$PID_FILE', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || rm -f "$PID_FILE"
    fi
}

# =============================================================================
# Autobuild Gate Check
# =============================================================================

check_autobuild_gate() {
    if [ -f "$AUTOBUILD_CONFIG" ]; then
        local enabled
        enabled=$(python3 -c "import json; print(json.load(open('$AUTOBUILD_CONFIG')).get('enabled', False))" 2>/dev/null || echo "False")
        if [ "$enabled" = "True" ] || [ "$enabled" = "true" ]; then
            log_success "Autobuild gate: ENABLED"
            return 0
        else
            log_warn "Autobuild gate: DISABLED"
            return 1
        fi
    else
        log_warn "Autobuild config not found, proceeding with manual mode"
        return 0
    fi
}

# =============================================================================
# Governance Validation
# =============================================================================

validate_governance() {
    log_info "Validating governance configuration..."

    # Check ACTIVE_PHASE exists
    if [ ! -f "governance/ACTIVE_PHASE" ]; then
        log_error "governance/ACTIVE_PHASE not found"
        return 1
    fi

    local phase
    phase=$(cat governance/ACTIVE_PHASE)
    log_info "Active Phase: $phase"

    # Validate phase definition exists
    if [ ! -f "governance/phases/phase${phase}.yaml" ]; then
        log_error "Phase definition not found: governance/phases/phase${phase}.yaml"
        return 1
    fi

    # Run governance validation if script exists
    if [ -f "scripts/validate_governance_config.py" ]; then
        if python3 scripts/validate_governance_config.py 2>/dev/null; then
            log_success "Governance config valid"
        else
            log_error "Governance validation failed"
            return 1
        fi
    fi

    # Run phase validation
    if [ -f "scripts/validate_phase.py" ]; then
        if python3 scripts/validate_phase.py "governance/phases/phase${phase}.yaml" 2>/dev/null; then
            log_success "Phase validation passed"
        else
            log_warn "Phase validation had warnings"
        fi
    fi

    return 0
}

# =============================================================================
# Docker Compose Operations
# =============================================================================

start_services() {
    log_info "Starting Sovereign System services..."

    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    # Build and start
    if docker compose -f "$COMPOSE_FILE" up -d --build; then
        log_success "Services started successfully"
        return 0
    else
        log_error "Failed to start services"
        return 1
    fi
}

check_health() {
    log_info "Checking service health..."

    local max_attempts=30
    local attempt=0
    local healthy_count=0
    local required_services=("policy_gate" "ledger_service" "command-center")

    while [ $attempt -lt $max_attempts ]; do
        healthy_count=0
        for service in "${required_services[@]}"; do
            if docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | grep -q "\"$service\".*\"healthy\""; then
                ((healthy_count++))
            fi
        done

        if [ $healthy_count -eq ${#required_services[@]} ]; then
            log_success "All core services healthy"
            return 0
        fi

        ((attempt++))
        log_info "Waiting for services... ($attempt/$max_attempts)"
        sleep 2
    done

    log_warn "Not all services reached healthy state"
    docker compose -f "$COMPOSE_FILE" ps
    return 1
}

stop_services() {
    log_info "Stopping Sovereign System services..."
    docker compose -f "$COMPOSE_FILE" down
    clear_pid
    log_success "Services stopped"
}

# =============================================================================
# Evidence Logging
# =============================================================================

log_boot_evidence() {
    mkdir -p "$LOG_DIR"
    local boot_log="$LOG_DIR/boot_evidence.jsonl"
    local entry
    entry=$(cat << EOF
{"timestamp_utc": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")", "event": "boot", "pid": $$, "phase": $(cat governance/ACTIVE_PHASE 2>/dev/null || echo 0), "mode": "${1:-manual}"}
EOF
)
    echo "$entry" >> "$boot_log"
    log_info "Boot evidence logged"
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    local force=false
    local dev_mode=false
    local validate_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force=true
                shift
                ;;
            --dev)
                dev_mode=true
                shift
                ;;
            --validate-only)
                validate_only=true
                shift
                ;;
            --stop)
                stop_services
                exit 0
                ;;
            --status)
                docker compose -f "$COMPOSE_FILE" ps
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--force] [--dev] [--validate-only] [--stop] [--status]"
                exit 1
                ;;
        esac
    done

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           SOVEREIGN SYSTEM - ATOMIC BOOT                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Acquire lock
    acquire_lock

    # Validate governance
    if ! validate_governance; then
        log_error "Governance validation failed. Boot aborted."
        exit 1
    fi

    if [ "$validate_only" = true ]; then
        log_success "Validation complete. Exiting (--validate-only mode)."
        exit 0
    fi

    # Check autobuild gate (skip if --force)
    if [ "$force" = false ]; then
        if ! check_autobuild_gate; then
            log_warn "Autobuild disabled. Use --force to override or enable via passcode."
            exit 0
        fi
    else
        log_warn "Force mode: skipping autobuild gate"
    fi

    # Write PID
    write_pid

    # Log evidence
    log_boot_evidence "${dev_mode:+dev}"

    # Start services
    if ! start_services; then
        clear_pid
        exit 1
    fi

    # Health check
    check_health

    echo ""
    log_success "Sovereign System boot complete"
    echo ""
    echo "  Dashboard: http://localhost:8100"
    echo "  Phase Status API: http://localhost:8097"
    echo "  Runtime Interface: http://localhost:8096"
    echo ""
}

main "$@"
