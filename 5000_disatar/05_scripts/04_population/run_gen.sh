#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PATH="${SCRIPT_DIR}/gen.log"

echo "Starting population generation..." > "${LOG_PATH}"
python3 "${SCRIPT_DIR}/generate_augmented_pop_280k.py" >> "${LOG_PATH}" 2>&1
echo "Finished population generation." >> "${LOG_PATH}"
