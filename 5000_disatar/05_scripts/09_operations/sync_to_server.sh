#!/bin/bash
# ============================================================
# 同步程式碼到伺服器 (Local → Server)
# ============================================================

SERVER="${MATSIM_SERVER:-user@DataServer01}"
REMOTE_PATH="${MATSIM_REMOTE_PATH:-~/projects/matsim-example-project}"

echo "=== 同步程式碼到伺服器 ==="
echo "目標: ${SERVER}:${REMOTE_PATH}"
echo ""

rsync -avz --progress \
    --include='src/***' \
    --include='5000_disatar/05_scripts/***' \
    --include='tools/***' \
    --include='docs/***' \
    --include='額外模組/***' \
    --include='pom.xml' \
    --include='pyproject.toml' \
    --include='mvnw' \
    --include='.mvn/***' \
    --exclude='*' \
    ./ ${SERVER}:${REMOTE_PATH}/

echo ""
echo "✓ 程式碼已同步到伺服器"
echo ""
echo "下一步 (在伺服器執行):"
echo "  ssh ${SERVER}"
echo "  cd ${REMOTE_PATH}"
echo "  ./mvnw clean package -DskipTests"
