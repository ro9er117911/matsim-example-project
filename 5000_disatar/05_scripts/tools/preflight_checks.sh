#!/bin/bash
# Pre-flight checks before full PT mapping
# Usage: ./preflight_checks.sh

echo "=========================================="
echo "PT 映射啟動前檢查清單"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# 1. 檢查網路檔案
echo "[1/8] 檢查網路檔案..."
if [ -f "network_v2.xml" ]; then
    SIZE=$(du -h network_v2.xml | awk '{print $1}')
    echo "  ✓ network_v2.xml 存在 (大小: $SIZE)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ✗ network_v2.xml 不存在！"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 2. 檢查排程檔案
echo "[2/8] 檢查排程檔案..."
if [ -f "merged/transitSchedule.xml" ]; then
    SIZE=$(du -h merged/transitSchedule.xml | awk '{print $1}')
    echo "  ✓ merged/transitSchedule.xml 存在 (大小: $SIZE)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ✗ merged/transitSchedule.xml 不存在！"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 3. 檢查車輛檔案
echo "[3/8] 檢查車輛檔案..."
if [ -f "merged/transitVehicles.xml" ]; then
    echo "  ✓ merged/transitVehicles.xml 存在"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ✗ merged/transitVehicles.xml 不存在！"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 4. 驗證 XML 語法
echo "[4/8] 驗證 XML 語法..."
if command -v xmllint &> /dev/null; then
    xmllint --noout network_v2.xml 2>&1 | grep -q "parser error" && {
        echo "  ✗ network_v2.xml 語法錯誤！"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    } || {
        echo "  ✓ network_v2.xml 語法正確"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    }
else
    echo "  ⚠ xmllint 未安裝，跳過驗證"
fi

# 5. 檢查 Java 記憶體
echo "[5/8] 檢查 Java 記憶體設定..."
java -Xmx16g -version &> /dev/null && {
    echo "  ✓ Java 可使用 16GB 記憶體"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
} || {
    echo "  ✗ Java 無法使用 16GB 記憶體！"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

# 6. 檢查磁碟空間
echo "[6/8] 檢查磁碟空間..."
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
AVAILABLE_GB=$(df -k . | awk 'NR==2 {print int($4/1024/1024)}')
if [ $AVAILABLE_GB -gt 5 ]; then
    echo "  ✓ 磁碟空間充足 ($AVAILABLE 可用)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ⚠ 磁碟空間不足 ($AVAILABLE 可用，建議 > 5GB)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 7. 檢查配置檔案
echo "[7/8] 檢查配置檔案..."
if [ -f "ptmapper-config-full-final.xml" ]; then
    echo "  ✓ ptmapper-config-full-final.xml 存在"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ✗ ptmapper-config-full-final.xml 不存在！"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 8. 檢查日誌目錄
echo "[8/8] 檢查日誌目錄..."
if [ -d "logs" ]; then
    echo "  ✓ logs/ 目錄存在"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    mkdir -p logs && {
        echo "  ✓ logs/ 目錄已建立"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    } || {
        echo "  ✗ 無法建立 logs/ 目錄！"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    }
fi

echo ""
echo "=========================================="
echo "檢查結果: $CHECKS_PASSED 通過, $CHECKS_FAILED 失敗"
echo "=========================================="

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "✅ 所有檢查通過，可以啟動映射！"
    exit 0
else
    echo "❌ 有 $CHECKS_FAILED 項檢查失敗，請修正後再啟動"
    exit 1
fi
