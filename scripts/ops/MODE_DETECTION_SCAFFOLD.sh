#!/bin/bash
#
# Sovereign System - Mode Detection Scaffold
#
# Purpose: Detects the node's current connectivity mode and applies the
#          corresponding security policies. This script is intended to be run
#          on the Main Command Node (`[MAIN_COMMAND_NODE]`).
#

# --- Configuration ---
# Define network identifiers for each mode.
# These should be replaced with actual network details.

# The interface name for the hardwired ethernet connection.
WIRED_INTERFACE="eth0"

# The SSID of the trusted WiFi network at the secure base.
TRUSTED_WIFI_SSID="Sovereign-Sanctuary-WiFi"

# The Tailscale interface name (usually 'tailscale0').
TAILSCALE_INTERFACE="tailscale0"

# --- State ---
CURRENT_MODE="UNKNOWN"

# --- Functions ---

log() {
    echo "[$(date --iso-8601=seconds)] [MODE_DETECTION] - $1"
    # In a production environment, this should write to a secure, remote syslog.
    # logger -t MODE_DETECTION "$1"
}

apply_firewall_rules() {
    local mode=$1
    log "Applying firewall rules for $mode mode..."

    # Default deny policy
    # ufw default deny incoming
    # ufw default allow outgoing

    case "$mode" in
        "HARDWIRED")
            # Unrestricted access to the local LAN for orchestration.
            # ufw allow in on $WIRED_INTERFACE to 192.168.50.0/24
            # ufw allow out on $WIRED_INTERFACE from any to 192.168.50.0/24
            log "Firewall configured for full LAN access."
            ;;
        "WIFI")
            # Trusted local access, but perhaps more restricted than hardwired.
            # ufw allow in on wlan0 from 192.168.50.0/24 to any port 22
            log "Firewall configured for trusted WiFi access."
            ;;
        "REMOTE")
            # Highly restricted. Only allow Tailscale traffic.
            # ufw allow in on $TAILSCALE_INTERFACE
            # ufw deny in on any # Deny all other incoming traffic
            log "Firewall configured for Tailscale-only remote access."
            ;;
        *)
            # Fallback to the most secure state if mode is unknown.
            # ufw deny in on any
            log "WARNING: Unknown mode. Applying most restrictive firewall rules."
            ;;
    esac

    # ufw enable
    log "Firewall rules applied."
}

detect_mode() {
    log "Starting network mode detection..."

    # 1. Check for Hardwired connection first (highest priority)
    if ip addr show $WIRED_INTERFACE | grep -q "state UP"; then
        NEW_MODE="HARDWIRED"
    # 2. Check for trusted WiFi connection
    elif iwgetid -r | grep -q "$TRUSTED_WIFI_SSID"; then
        NEW_MODE="WIFI"
    # 3. Check if Tailscale is the only primary connection
    elif ip addr show $TAILSCALE_INTERFACE | grep -q "state UP"; then
        NEW_MODE="REMOTE"
    else
        NEW_MODE="UNKNOWN"
    fi

    if [ "$NEW_MODE" != "$CURRENT_MODE" ]; then
        log "Mode transition detected: $CURRENT_MODE -> $NEW_MODE"
        CURRENT_MODE=$NEW_MODE
        apply_firewall_rules $CURRENT_MODE
    else
        log "No mode change detected. Current mode remains $CURRENT_MODE."
    fi
}

# --- Main Loop ---
# This script can be run as a one-off, or as a daemon that periodically
# checks for network changes.

log "Initializing Main Command Node policy enforcement..."
detect_mode

# To run as a daemon, uncomment the following loop:
# while true; do
#     detect_mode
#     sleep 60 # Check for network changes every 60 seconds
# done
