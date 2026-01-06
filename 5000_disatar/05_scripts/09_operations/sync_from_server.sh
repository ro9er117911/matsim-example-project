#!/bin/bash
# ============================================================
# 從伺服器下載模擬結果 (Server → Local)
# ============================================================

SERVER="${MATSIM_SERVER:-user@DataServer01}"
REMOTE_PATH="${MATSIM_REMOTE_PATH:-~/projects/matsim-example-project}"
OUTPUT_DIR=$1

if [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <output_directory>"
    echo "Example: $0 output_optimized_iter10"
    exit 1
fi

LOCAL_DIR="./analysis_results/${OUTPUT_DIR}"
mkdir -p "${LOCAL_DIR}"

echo "=== 從伺服器下載結果 ==="
echo "來源: ${SERVER}:${REMOTE_PATH}/${OUTPUT_DIR}"
echo "目標: ${LOCAL_DIR}"
echo ""

rsync -avz --progress \
    --include='*.csv' \
    --include='*.yaml' \
    --include='*.png' \
    --include='*.log' \
    --include='*.txt' \
    --include='*/' \
    --exclude='*.xml.gz' \
    --exclude='ITERS/' \
    ${SERVER}:${REMOTE_PATH}/${OUTPUT_DIR}/ \
    ${LOCAL_DIR}/

echo ""
echo "✓ 結果已下載到 ${LOCAL_DIR}/"
echo ""
echo "可視化: cd ${LOCAL_DIR} && python -m http.server 8000"
