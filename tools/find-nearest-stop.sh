#!/bin/bash

#############################################################################
# Find Nearest Stop/Link - MATSim Network Query Tool
#
# 功能: 在 transitSchedule 中查找最近的停靠点
# 使用: ./find-nearest-stop.sh [x-coordinate] [y-coordinate] [schedule-file]
#
# 作者: Claude Code (Anthropic)
# 日期: 2025-11-03
#############################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数
TARGET_X="${1}"
TARGET_Y="${2}"
SCHEDULE_FILE="${3:-scenarios/equil/transitSchedule-mapped.xml.gz}"
LIMIT="${4:-5}"

# 临时文件
TMP_FILE="/tmp/stops_$$.txt"

#############################################################################
# 函数定义
#############################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_result() {
    echo -e "${GREEN}✓${NC} $1"
}

# 计算两点间的欧几里得距离
calculate_distance() {
    local x1=$1
    local y1=$2
    local x2=$3
    local y2=$4

    # 使用 awk 计算距离
    awk -v x1="$x1" -v y1="$y1" -v x2="$x2" -v y2="$y2" \
        'BEGIN {
            dx = x2 - x1
            dy = y2 - y1
            distance = sqrt(dx*dx + dy*dy)
            printf "%.2f", distance
        }'
}

# 显示帮助信息
show_help() {
    echo "用法: $0 <x-coordinate> <y-coordinate> [schedule-file] [limit]"
    echo ""
    echo "参数:"
    echo "  x-coordinate   - 目标点的 X 坐标"
    echo "  y-coordinate   - 目标点的 Y 坐标"
    echo "  schedule-file  - 时刻表文件 (默认: scenarios/equil/transitSchedule-mapped.xml.gz)"
    echo "  limit          - 返回的结果数量 (默认: 5)"
    echo ""
    echo "示例:"
    echo "  $0 294035 2762173                                    # 查询指定坐标的最近停靠点"
    echo "  $0 300000 2765000 transitSchedule-mapped.xml.gz 10   # 指定文件和结果数"
    echo ""
    echo "说明:"
    echo "  此脚本查找离目标坐标最近的 PT 停靠点。"
    echo "  输出包含停靠点 ID、坐标和距离。"
    echo ""
}

#############################################################################
# 主程序
#############################################################################

main() {
    # 参数检查
    if [ -z "$TARGET_X" ] || [ -z "$TARGET_Y" ]; then
        echo "错误: 需要提供 X 和 Y 坐标"
        echo ""
        show_help
        exit 1
    fi

    # 文件检查
    if [ ! -f "$SCHEDULE_FILE" ]; then
        print_error "文件不存在: $SCHEDULE_FILE"
        exit 1
    fi

    print_header "查找最近的停靠点"
    print_info "目标坐标: ($TARGET_X, $TARGET_Y)"
    echo ""

    # 提取所有停靠点信息
    echo -e "${BLUE}正在解析时刻表...${NC}"

    if [[ "$SCHEDULE_FILE" == *.gz ]]; then
        gunzip -c "$SCHEDULE_FILE" | grep 'stopFacility id=' > "$TMP_FILE"
    else
        grep 'stopFacility id=' "$SCHEDULE_FILE" > "$TMP_FILE"
    fi

    local stop_count=$(wc -l < "$TMP_FILE")
    print_result "找到 $stop_count 个停靠点"
    echo ""

    # 计算距离并排序
    echo -e "${BLUE}正在计算距离...${NC}"

    local results="/tmp/results_$$.txt"
    > "$results"

    while IFS= read -r line; do
        # 解析 stopFacility 属性
        if [[ "$line" =~ id=\"([^\"]+)\".*x=\"([^\"]+)\".*y=\"([^\"]+)\" ]]; then
            local stop_id="${BASH_REMATCH[1]}"
            local x="${BASH_REMATCH[2]}"
            local y="${BASH_REMATCH[3]}"

            # 计算距离
            local distance=$(calculate_distance "$TARGET_X" "$TARGET_Y" "$x" "$y")

            # 写入结果 (格式: distance stop_id x y)
            echo "$distance|$stop_id|$x|$y" >> "$results"
        fi
    done < "$TMP_FILE"

    # 排序并显示结果
    echo ""
    print_header "最近的 $LIMIT 个停靠点"

    sort -n -t'|' -k1 "$results" | head -n "$LIMIT" | while IFS='|' read -r distance stop_id x y; do
        # 解析 stop_id 获取可读的名称
        local stop_name=$(echo "$stop_id" | sed 's/.link:pt_//g' | sed 's/_UP$//' | sed 's/_DN$//')

        echo ""
        echo -e "${GREEN}停靠点:${NC} $stop_id"
        echo -e "  名称:      $stop_name"
        echo -e "  坐标:      ($x, $y)"
        echo -e "  距离:      ${distance}m"
        echo -e "  Link ID:   pt_${stop_name}_UP (或 _DN)"
    done

    echo ""
    print_header "使用建议"
    echo ""
    echo "在 Agent 旅程中使用最近的停靠点:"
    echo ""
    echo '  <activity type="home" link="pt_BL02_UP"'
    echo '            x="294035.05" y="2762173.24"'
    echo '            end_time="07:15:00" />'
    echo ""
    echo "其中 link ID 基于最近停靠点的名称 (例如 BL02)"
    echo ""

    # 清理临时文件
    rm -f "$TMP_FILE" "$results"
}

# 显示帮助
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 执行主程序
main
