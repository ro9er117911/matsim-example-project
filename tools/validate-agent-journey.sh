#!/bin/bash

#############################################################################
# Agent Journey Validator - MATSim Population Verification Script
#
# 功能: 验证 population.xml 中的 agents 旅程有效性
# 使用: ./validate-agent-journey.sh [population.xml] [network-file] [schedule-file]
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
NC='\033[0m' # No Color

# 默认文件路径
POPULATION_FILE="${1:-scenarios/equil/population.xml}"
NETWORK_FILE="${2:-scenarios/equil/network-with-pt.xml.gz}"
SCHEDULE_FILE="${3:-scenarios/equil/transitSchedule-mapped.xml.gz}"

# 统计变量
TOTAL_AGENTS=0
VALID_AGENTS=0
INVALID_AGENTS=0
WARNINGS=0
ERRORS=0

# 临时文件
TMP_DIR="/tmp/agent-validation-$$"
REPORT_FILE="${TMP_DIR}/validation_report.txt"
LINK_LIST_FILE="${TMP_DIR}/available_links.txt"
STOP_LIST_FILE="${TMP_DIR}/available_stops.txt"

# 创建临时目录
mkdir -p "${TMP_DIR}"

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

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_file_exists() {
    if [ ! -f "$1" ]; then
        echo ""
        echo -e "${RED}错误: 文件不存在 - $1${NC}"
        echo ""
        exit 1
    fi
}

build_available_links() {
    echo -e "${BLUE}正在解析网络文件...${NC}"

    if [ ! -f "${LINK_LIST_FILE}" ]; then
        if [[ "$NETWORK_FILE" == *.gz ]]; then
            gunzip -c "$NETWORK_FILE" | grep -o 'link id="[^"]*"' | \
                sed 's/link id="\([^"]*\)".*/\1/' > "${LINK_LIST_FILE}"
        else
            grep -o 'link id="[^"]*"' "$NETWORK_FILE" | \
                sed 's/link id="\([^"]*\)".*/\1/' > "${LINK_LIST_FILE}"
        fi
    fi

    local link_count=$(wc -l < "${LINK_LIST_FILE}")
    echo -e "${GREEN}✓ 找到 ${link_count} 个有效的 link${NC}"
}

build_available_stops() {
    echo -e "${BLUE}正在解析时刻表...${NC}"

    if [ ! -f "${STOP_LIST_FILE}" ]; then
        if [[ "$SCHEDULE_FILE" == *.gz ]]; then
            gunzip -c "$SCHEDULE_FILE" | grep 'stopFacility id=' | \
                sed 's/.*stopFacility id="\([^"]*\)".*/\1/' > "${STOP_LIST_FILE}"
        else
            grep 'stopFacility id=' "$SCHEDULE_FILE" | \
                sed 's/.*stopFacility id="\([^"]*\)".*/\1/' > "${STOP_LIST_FILE}"
        fi
    fi

    local stop_count=$(wc -l < "${STOP_LIST_FILE}")
    echo -e "${GREEN}✓ 找到 ${stop_count} 个有效的停靠点${NC}"
}

link_exists() {
    local link_id="$1"
    grep -q "^${link_id}$" "${LINK_LIST_FILE}"
}

time_to_seconds() {
    local time_str="$1"

    if [[ ! "$time_str" =~ ^[0-9]{1,2}:[0-9]{2}:[0-9]{2}$ ]]; then
        echo "-1"
        return 1
    fi

    local hours=$(echo "$time_str" | cut -d':' -f1)
    local mins=$(echo "$time_str" | cut -d':' -f2)
    local secs=$(echo "$time_str" | cut -d':' -f3)

    echo $((hours * 3600 + mins * 60 + secs))
}

validate_activity() {
    local agent_id="$1"
    local activity_type="$2"
    local link_id="$3"
    local end_time="$4"
    local index="$5"

    # 检查 link ID
    if [ -z "$link_id" ]; then
        print_error "Agent $agent_id: Activity $index ($activity_type) 缺少 link ID"
        return 1
    fi

    if ! link_exists "$link_id"; then
        print_error "Agent $agent_id: Activity $index ($activity_type) 的 link '$link_id' 不在网络中"
        return 1
    fi

    # 检查 end_time 格式
    if [ -n "$end_time" ]; then
        if ! time_to_seconds "$end_time" > /dev/null 2>&1; then
            print_error "Agent $agent_id: Activity $index 的 end_time 格式无效 '$end_time' (应该是 HH:MM:SS)"
            return 1
        fi
    fi

    return 0
}

validate_leg() {
    local agent_id="$1"
    local leg_mode="$2"
    local leg_index="$3"

    # 检查交通方式
    case "$leg_mode" in
        car|pt|walk|access_walk|egress_walk|transit_walk)
            return 0
            ;;
        *)
            print_error "Agent $agent_id: Leg $leg_index 的交通方式无效 '$leg_mode'"
            return 1
            ;;
    esac
}

validate_agent() {
    local agent_id="$1"
    local valid=1

    # 提取 agent 的 XML
    local agent_xml=$(sed -n "/<person id=\"$agent_id\"/,/<\/person>/p" "$POPULATION_FILE")

    if [ -z "$agent_xml" ]; then
        print_error "无法找到 agent: $agent_id"
        return 1
    fi

    # 检查是否有 plan
    if ! echo "$agent_xml" | grep -q '<plan'; then
        print_error "Agent $agent_id: 没有定义 plan"
        return 1
    fi

    # 计算活动数量
    local activity_count=$(echo "$agent_xml" | grep -c '<activity')
    if [ "$activity_count" -lt 2 ]; then
        print_warning "Agent $agent_id: 活动数量少于 2 个"
        valid=0
    fi

    # 验证每个活动
    local activity_index=0
    while IFS= read -r line; do
        if [[ "$line" =~ activity.*type=\"([^\"]+)\".*link=\"([^\"]+)\".*end_time=\"([^\"]*)\" ]]; then
            local act_type="${BASH_REMATCH[1]}"
            local link_id="${BASH_REMATCH[2]}"
            local end_time="${BASH_REMATCH[3]}"

            if ! validate_activity "$agent_id" "$act_type" "$link_id" "$end_time" "$activity_index"; then
                valid=0
            fi
            activity_index=$((activity_index + 1))
        elif [[ "$line" =~ activity.*type=\"([^\"]+)\".*link=\"([^\"]+)\" ]]; then
            local act_type="${BASH_REMATCH[1]}"
            local link_id="${BASH_REMATCH[2]}"

            if ! validate_activity "$agent_id" "$act_type" "$link_id" "" "$activity_index"; then
                valid=0
            fi
            activity_index=$((activity_index + 1))
        fi
    done < <(echo "$agent_xml" | grep '<activity')

    # 验证每条 leg
    local leg_index=0
    while IFS= read -r line; do
        if [[ "$line" =~ leg.*mode=\"([^\"]+)\" ]]; then
            local leg_mode="${BASH_REMATCH[1]}"
            if ! validate_leg "$agent_id" "$leg_mode" "$leg_index"; then
                valid=0
            fi
            leg_index=$((leg_index + 1))
        fi
    done < <(echo "$agent_xml" | grep '<leg')

    # PT 特殊检查
    if echo "$agent_xml" | grep -q 'mode="pt"'; then
        if ! echo "$agent_xml" | grep -q 'pt interaction'; then
            print_warning "Agent $agent_id: 使用 PT 但缺少 pt interaction activities"
            valid=0
        fi
    fi

    return $((1 - valid))
}

#############################################################################
# 主程序
#############################################################################

main() {
    print_header "MATSim Agent Journey Validator"

    # 检查文件存在
    echo "验证输入文件..."
    check_file_exists "$POPULATION_FILE"
    check_file_exists "$NETWORK_FILE"
    check_file_exists "$SCHEDULE_FILE"
    print_success "所有输入文件都存在"

    # 构建可用链接和停靠点列表
    echo ""
    build_available_links
    build_available_stops

    # 提取所有 agent IDs
    echo ""
    echo -e "${BLUE}正在验证 agents...${NC}"

    local agent_ids=$(grep -o 'person id="[^"]*"' "$POPULATION_FILE" | \
                      sed 's/person id="\([^"]*\)".*/\1/')

    TOTAL_AGENTS=$(echo "$agent_ids" | wc -l)
    echo "找到 $TOTAL_AGENTS 个 agents"
    echo ""

    # 验证每个 agent
    for agent_id in $agent_ids; do
        if validate_agent "$agent_id"; then
            print_success "Agent: $agent_id"
            VALID_AGENTS=$((VALID_AGENTS + 1))
        else
            print_error "Agent: $agent_id"
            INVALID_AGENTS=$((INVALID_AGENTS + 1))
        fi
    done

    # 生成总结报告
    echo ""
    print_header "验证总结"

    echo "验证统计:"
    echo "  总 Agents:     $TOTAL_AGENTS"
    echo "  有效 Agents:   $VALID_AGENTS"
    echo "  无效 Agents:   $INVALID_AGENTS"
    echo "  警告:         $WARNINGS"
    echo "  错误:         $ERRORS"
    echo ""

    if [ "$INVALID_AGENTS" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
        echo -e "${GREEN}✓ 所有 agents 验证通过！${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ 验证失败，请检查上面的错误信息${NC}"
        echo ""
        return 1
    fi
}

# 显示帮助信息
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [population.xml] [network-file.xml.gz] [transitSchedule.xml.gz]"
    echo ""
    echo "示例:"
    echo "  $0                                                    # 使用默认文件"
    echo "  $0 scenarios/equil/population.xml                    # 指定 population 文件"
    echo "  $0 my_population.xml my_network.xml my_schedule.xml  # 全部指定"
    echo ""
    exit 0
fi

# 执行主程序
main
EXIT_CODE=$?

# 清理临时文件
rm -rf "$TMP_DIR"

exit $EXIT_CODE
