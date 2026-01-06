#!/bin/bash
# ============================================================
# 首次上傳大型資料到伺服器
# 只需執行一次
# ============================================================

SERVER="${MATSIM_SERVER:-user@DataServer01}"
REMOTE_PATH="${MATSIM_REMOTE_PATH:-~/projects/matsim-example-project}"

echo "=== 首次上傳大型資料 ==="
echo "目標: ${SERVER}:${REMOTE_PATH}"
echo ""
echo "⚠️  此操作將上傳約 12GB 資料，可能需要數小時"
echo "按 Ctrl+C 取消，或任意鍵繼續..."
read -n 1

echo ""
echo "[1/3] 上傳 5000_disatar/ (~11 GB)..."
rsync -avz --progress \
    5000_disatar/ \
    ${SERVER}:${REMOTE_PATH}/5000_disatar/

echo ""
echo "[2/3] 上傳 scenarios/ (~800 MB)..."
rsync -avz --progress \
    scenarios/ \
    ${SERVER}:${REMOTE_PATH}/scenarios/

echo ""
echo "[3/3] 上傳 pt2matsim/ (~200 MB)..."
rsync -avz --progress \
    pt2matsim/ \
    ${SERVER}:${REMOTE_PATH}/pt2matsim/

echo ""
echo "✓ 大型資料上傳完成"
