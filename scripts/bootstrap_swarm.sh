#!/usr/bin/env bash
set -euo pipefail

# Minimal helper for your two-node (and beyond) mission swarm.
# It does NOT hide what's happening; it just removes copy/paste pain.
#
# Usage:
#   On manager:
#     ./scripts/bootstrap_swarm.sh init <CONTROL_NODE_IP>
#
#   On worker:
#     ./scripts/bootstrap_swarm.sh join <MANAGER_IP> <WORKER_JOIN_TOKEN>
#
#   On any node:
#     ./scripts/bootstrap_swarm.sh status

CMD="${1:-}"

if [[ -z "$CMD" ]]; then
  echo "Usage:"
  echo "  $0 init <CONTROL_NODE_IP>"
  echo "  $0 join <MANAGER_IP> <WORKER_JOIN_TOKEN>"
  echo "  $0 status"
  exit 1
fi

mission_network_name="mission-network"

init_swarm() {
  local control_ip="${1:-}"
  if [[ -z "$control_ip" ]]; then
    echo "ERROR: control IP required"
    echo "Usage: $0 init <CONTROL_NODE_IP>"
    exit 1
  fi

  echo ">>> Initialising swarm on manager at ${control_ip}..."
  docker swarm init --advertise-addr "${control_ip}" || {
    echo "Swarm may already be initialised. Current status:"
    docker info | grep -i "Swarm"
  }

  echo ">>> Ensuring overlay network '${mission_network_name}' exists..."
  if ! docker network ls --format '{{.Name}}' | grep -q "^${mission_network_name}\$"; then
    docker network create --driver overlay --attachable "${mission_network_name}"
    echo "Created overlay network: ${mission_network_name}"
  else
    echo "Overlay network ${mission_network_name} already exists."
  fi

  echo
  echo ">>> Swarm nodes:"
  docker node ls || true

  echo
  echo ">>> Worker join command (copy this to worker nodes):"
  docker swarm join-token worker --quiet | awk -v ip="${control_ip}" '{print "docker swarm join --token "$0" "ip":2377"}'

  echo
  echo ">>> Manager status complete."
}

join_swarm() {
  local manager_ip="${1:-}"
  local token="${2:-}"

  if [[ -z "$manager_ip" || -z "$token" ]]; then
    echo "ERROR: manager IP and worker token required"
    echo "Usage: $0 join <MANAGER_IP> <WORKER_JOIN_TOKEN>"
    exit 1
  fi

  echo ">>> Joining swarm as worker..."
  docker swarm join --token "${token}" "${manager_ip}:2377"
  echo ">>> Joined swarm. Current local swarm status:"
  docker info | grep -i "Swarm"
}

status_swarm() {
  echo ">>> Docker / Swarm status"
  docker info | grep -E 'Swarm:|Docker Root Dir|Server Version' || true
  echo
  echo ">>> Nodes (if this is a manager):"
  docker node ls 2>/dev/null || echo "(not a manager or no permission)"
  echo
  echo ">>> Services (if any stacks deployed):"
  docker service ls 2>/dev/null || echo "(no services or not a manager)"
}

case "${CMD}" in
  init)
    init_swarm "${2:-}"
    ;;
  join)
    join_swarm "${2:-}" "${3:-}"
    ;;
  status)
    status_swarm
    ;;
  *)
    echo "Unknown command: ${CMD}"
    echo "Usage:"
    echo "  $0 init <CONTROL_NODE_IP>"
    echo "  $0 join <MANAGER_IP> <WORKER_JOIN_TOKEN>"
    echo "  $0 status"
    exit 1
    ;;
esac
