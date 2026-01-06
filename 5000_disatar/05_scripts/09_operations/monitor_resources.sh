#!/usr/bin/env bash
# Lightweight resource monitor. Logs system memory/disk and top processes.
# Usage: INTERVAL=30 COUNT=20 ./monitor_resources.sh

set -euo pipefail

INTERVAL=${INTERVAL:-30}   # seconds between samples
COUNT=${COUNT:-10}         # number of samples

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/monitor_$(date +%Y-%m-%d_%H-%M-%S).log"

echo "Monitoring: interval=${INTERVAL}s, count=${COUNT}"
echo "Log: ${LOG_FILE}"

sample() {
  echo "---- $(date '+%Y-%m-%d %H:%M:%S') ----"
  # Free/inactive memory (macOS vm_stat if available)
  if command -v vm_stat >/dev/null 2>&1; then
    vm_stat | head -n 10
  fi
  # Disk usage summary
  df -h .
  # Top memory/CPU processes (java/python prioritized)
  ps aux | grep -E 'java|python' | grep -v grep | sort -nrk4 | head -n 10
  echo
}

for i in $(seq 1 "${COUNT}"); do
  sample | tee -a "${LOG_FILE}"
  if [[ "${i}" -lt "${COUNT}" ]]; then
    sleep "${INTERVAL}"
  fi
done

echo "Monitor finished. Log saved to ${LOG_FILE}"
