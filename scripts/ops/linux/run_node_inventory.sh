#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=${1:-"$HOME/SovereignInventory"}
STAMP=$(date +%Y%m%d_%H%M%S)
HOST=$(hostname)
OUT="$ROOT_DIR/${HOST}_${STAMP}"
mkdir -p "$OUT"

# Identity
{
  echo "host: $HOST"
  date -u +%FT%TZ
  uname -a
} > "$OUT/identity.txt"

# System
lscpu > "$OUT/cpu.txt" 2>&1 || true
free -h > "$OUT/ram.txt" 2>&1 || true
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE > "$OUT/disks.txt" 2>&1 || true
df -hT > "$OUT/volumes.txt" 2>&1 || true

# RAID/ZFS (best-effort)
command -v mdadm >/dev/null && mdadm --detail --scan > "$OUT/raid_mdadm.txt" 2>&1 || true
command -v zpool >/dev/null && zpool status > "$OUT/zpool_status.txt" 2>&1 || true
command -v zfs >/dev/null && zfs list > "$OUT/zfs_list.txt" 2>&1 || true

# Network
ip addr show > "$OUT/network_addr.txt" 2>&1 || true
ip route show > "$OUT/network_route.txt" 2>&1 || true
ss -tupan > "$OUT/connections.txt" 2>&1 || true

# Services/Processes
systemctl list-units --type=service --no-pager > "$OUT/services.txt" 2>&1 || true
ps auxww > "$OUT/processes.txt" 2>&1 || true

# Shares (best-effort)
command -v smbstatus >/dev/null && smbstatus -S > "$OUT/samba.txt" 2>&1 || true
showmount -e 2>/dev/null > "$OUT/nfs_exports.txt" || true

# SMART (best-effort)
if command -v smartctl >/dev/null; then
  for d in /dev/sd? /dev/nvme?n?; do
    [ -e "$d" ] || continue
    smartctl -H "$d" >> "$OUT/smart_health.txt" 2>&1 || true
  done
fi

# Package versions
{
  echo "--- versions ---"
  which python3 && python3 --version || true
  which docker && docker --version || true
} > "$OUT/versions.txt" 2>&1 || true

# Archive
TAR="$OUT.tar.gz"
( cd "$ROOT_DIR" && tar -czf "${HOST}_${STAMP}.tar.gz" "${HOST}_${STAMP}" )

echo "Inventory complete -> $TAR"
