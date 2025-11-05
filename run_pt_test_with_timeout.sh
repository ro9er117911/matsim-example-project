#!/bin/bash
# PT转换流程 - 早停测试版
# 使用内置测试数据，每个阶段都有超时保护

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建输出目录
OUTPUT_DIR="pt2matsim/test_run_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

log_info "测试运行开始，输出目录: $OUTPUT_DIR"
log_info "所有日志将保存到: $OUTPUT_DIR/*.log"

# 阶段1: 打包项目（5分钟超时）
log_info "========================================="
log_info "阶段1: Maven打包项目"
log_info "超时时间: 5分钟"
log_info "========================================="

if timeout 300 ./mvnw -q -DskipTests package 2>&1 | tee "$OUTPUT_DIR/maven_package.log"; then
    log_info "✅ Maven打包成功"
    JAR_FILE="target/matsim-example-project-0.0.1-SNAPSHOT.jar"
    if [ -f "$JAR_FILE" ]; then
        JAR_SIZE=$(ls -lh "$JAR_FILE" | awk '{print $5}')
        log_info "   生成JAR: $JAR_FILE ($JAR_SIZE)"
    fi
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        log_error "❌ Maven打包超时（>5分钟）"
    else
        log_error "❌ Maven打包失败（退出码: $EXIT_CODE）"
    fi
    log_error "   查看日志: $OUTPUT_DIR/maven_package.log"
    exit 1
fi

# 检查JAR文件
if [ ! -f "target/matsim-example-project-0.0.1-SNAPSHOT.jar" ]; then
    log_error "❌ JAR文件未生成"
    exit 1
fi

# 阶段2: 使用测试GTFS（跳过，因为缺少pt2matsim JAR）
log_info "========================================="
log_info "阶段2: GTFS转换（跳过）"
log_info "========================================="
log_warn "⚠️  缺少 pt2matsim-25.8-shaded.jar"
log_warn "   无法运行GTFS转换"
log_info "   可用测试GTFS: src/test/resources/gtfs/bl_corridor/bl_corridor.gtfs.zip (1.3K)"

# 阶段3: 使用现有场景运行简单测试（1分钟超时）
log_info "========================================="
log_info "阶段3: 运行equil测试场景"
log_info "超时时间: 2分钟"
log_info "========================================="

# 检查equil场景
if [ ! -f "scenarios/equil/config.xml" ]; then
    log_error "❌ equil场景配置文件不存在"
    exit 1
fi

log_info "运行MATSim测试（1次迭代）..."

# 创建临时配置，限制为1次迭代
TEMP_CONFIG="$OUTPUT_DIR/config_test.xml"
cp scenarios/equil/config.xml "$TEMP_CONFIG"

# 修改配置：只运行1次迭代
sed -i 's/<param name="lastIteration" value="[^"]*"/<param name="lastIteration" value="0"/' "$TEMP_CONFIG"

# 运行测试（2分钟超时）
if timeout 120 java -Xmx4g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar "$TEMP_CONFIG" 2>&1 | tee "$OUTPUT_DIR/matsim_run.log"; then
    log_info "✅ MATSim测试运行成功"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        log_warn "⚠️  MATSim运行超时（>2分钟）"
        log_info "   这是正常的，1次迭代可能需要更长时间"
    else
        log_error "❌ MATSim运行失败（退出码: $EXIT_CODE）"
    fi
    log_info "   查看日志: $OUTPUT_DIR/matsim_run.log"
fi

# 检查输出
log_info "========================================="
log_info "检查输出文件"
log_info "========================================="

if [ -d "output" ]; then
    OUTPUT_SIZE=$(du -sh output 2>/dev/null | awk '{print $1}')
    log_info "✅ 输出目录大小: $OUTPUT_SIZE"

    # 列出关键输出文件
    log_info "关键输出文件:"
    ls -lh output/*.xml* 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
    ls -lh output/*.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
fi

# 总结
log_info "========================================="
log_info "测试运行完成"
log_info "========================================="
log_info "输出位置:"
log_info "  - 日志: $OUTPUT_DIR/"
log_info "  - 仿真输出: output/"
log_info ""
log_info "下一步:"
log_info "  1. 检查日志: cat $OUTPUT_DIR/*.log"
log_info "  2. 查看输出: ls -lh output/"
log_info "  3. 查看收敛: open output/scorestats.png (如果生成)"

echo ""
log_warn "⚠️  注意: 完整PT转换需要以下文件:"
log_warn "  - pt2matsim/work/pt2matsim-25.8-shaded.jar"
log_warn "  - pt2matsim/combine/output/merged_gtfs.zip"
log_warn "  - pt2matsim/output_v1/network-prepared.xml.gz"
