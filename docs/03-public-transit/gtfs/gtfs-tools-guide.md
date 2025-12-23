# GTFS 工具使用指南

本项目提供两个实用的 GTFS 数据处理工具，用于验证和合并 GTFS 数据集。

---

## 📋 工具清单

### 1. `validate_gtfs.py` - GTFS 数据完整性验证

**功能**：
- ✅ 检查必需文件是否存在
- ✅ 统计各文件记录数
- ✅ 分析路线类型分布
- ✅ 检查坐标系统
- ✅ 验证外键完整性
- ✅ 评估 MATSim 兼容性

**使用方法**：
```bash
python src/main/python/validate_gtfs.py <gtfs_directory>
```

**示例**：
```bash
# 验证台北捷运数据
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/tp_metro_gtfs/

# 验证全台湾交通数据
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/gtfs_tw_v5/
```

**输出示例**：
```
============================================================
GTFS 数据完整性验证工具
============================================================

=== 文件完整性检查 ===

必需文件:
  ✓ agency.txt           - Agency (运营商信息)
  ✓ stops.txt            - Stops (站点位置)
  ✓ routes.txt           - Routes (路线定义)
  ✓ trips.txt            - Trips (行程定义)
  ✓ stop_times.txt       - Stop Times (时刻表) - 关键文件

=== 数据量统计 ===

  agency.txt          :          1 条记录
  stops.txt           :        722 条记录
  routes.txt          :          7 条记录
  trips.txt           :      5,990 条记录
  stop_times.txt      :    100,015 条记录

=== 数据集总结 ===

  ✓ 数据集完整 - 包含所有必需文件
  ✓ MATSim 兼容性 - 可用于 MATSim 转换
```

---

### 2. `merge_gtfs.py` - GTFS 数据集合并

**功能**：
- ✅ 合并两个 GTFS 数据集
- ✅ 自动处理 ID 冲突（添加前缀）
- ✅ 生成转乘关系（transfers.txt）
- ✅ 保留坐标系统信息

**使用方法**：
```bash
python src/main/python/merge_gtfs.py \
    <gtfs1_dir> \
    <gtfs2_dir> \
    <output_dir> \
    [--prefix1 PREFIX1] \
    [--prefix2 PREFIX2] \
    [--transfer-distance METERS] \
    [--transfer-time SECONDS]
```

**参数说明**：
- `gtfs1_dir`: 第一个 GTFS 数据集目录
- `gtfs2_dir`: 第二个 GTFS 数据集目录
- `output_dir`: 输出目录
- `--prefix1`: 第一个数据集的 ID 前缀（默认：GTFS1_）
- `--prefix2`: 第二个数据集的 ID 前缀（默认：GTFS2_）
- `--transfer-distance`: 转乘站点的最大距离（米，默认：100）
- `--transfer-time`: 转乘时间（秒，默认：180）

**示例**：
```bash
# 合并台北捷运和公交数据（假设公交数据已准备好）
python src/main/python/merge_gtfs.py \
    pt2matsim/data/gtfs/tp_metro_gtfs/ \
    pt2matsim/data/gtfs/taipei_bus_gtfs/ \
    pt2matsim/data/gtfs/merged_gtfs/ \
    --prefix1 MRT_ \
    --prefix2 BUS_ \
    --transfer-distance 150 \
    --transfer-time 240
```

**输出**：
- 合并后的 GTFS 文件（agency.txt, stops.txt, routes.txt, etc.）
- 新生成的 transfers.txt（转乘关系）
- 保留的坐标文件（stops_epsg3826.txt）

---

## 🔄 完整工作流程

### 步骤 1: 验证输入数据

在合并前，务必验证两个数据集：

```bash
# 验证数据集 1
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/dataset1/

# 验证数据集 2
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/dataset2/
```

**⚠️ 关键检查项**：
- ✅ 两个数据集都必须包含 `stop_times.txt`
- ✅ 确认坐标系统一致（WGS84 或 EPSG:3826）
- ✅ 确认没有严重的外键错误

### 步骤 2: 执行合并

```bash
python src/main/python/merge_gtfs.py \
    pt2matsim/data/gtfs/dataset1/ \
    pt2matsim/data/gtfs/dataset2/ \
    pt2matsim/data/gtfs/merged/ \
    --prefix1 DS1_ \
    --prefix2 DS2_
```

### 步骤 3: 验证合并结果

```bash
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/merged/
```

### 步骤 4: 转换为 MATSim 格式

```bash
# 使用项目中的 GtfsToMatsim 工具
# （具体命令参见 ../CLAUDE.md）
```

---

## ⚠️ 当前项目数据状态

### ✅ 可用数据：`tp_metro_gtfs`

**台北捷运完整数据**：
- ✅ 包含所有必需文件
- ✅ 100,015 条 stop_times 记录
- ✅ 7 条地铁线路，722 个站点
- ✅ **可直接用于 MATSim 转换**

**使用建议**：
```bash
# 验证数据
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/tp_metro_gtfs/

# 转换为 MATSim（使用现有工具）
# 参见 src/main/java/org/matsim/project/tools/GtfsToMatsim.java
```

### ❌ 不可用数据：`gtfs_tw_v5`

**全台湾交通数据**：
- ❌ **缺少 stop_times.txt**（致命问题）
- ✅ 包含 9,663 条路线（公交、铁路、捷运等）
- ✅ 154,477 个站点
- ❌ **无法用于 MATSim 模拟**

**问题原因**：
- 缺少时刻表数据（stop_times.txt）
- 无法生成 MATSim 的 transitSchedule.xml

**解决方案**：
1. 从 [交通部 PTX 平台](https://ptx.transportdata.tw/) 下载完整 GTFS
2. 或仅使用台北捷运数据（已足够完整）

---

## 📚 获取完整 GTFS 数据

### 台湾公共运输 GTFS 数据源

#### 1. **交通部 PTX 平台**（推荐）

**网址**：https://ptx.transportdata.tw/

**提供数据**：
- 全台湾公交 GTFS
- 铁路 GTFS
- 捷运 GTFS（台北、高雄、桃园）
- 渡轮 GTFS

**申请 API 密钥**：
```bash
# 注册后获取 API 密钥
# 下载示例（台北市公交）
curl -X GET "https://ptx.transportdata.tw/MOTC/v2/Bus/GTFS/City/Taipei" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o taipei_bus_gtfs.zip

# 解压
unzip taipei_bus_gtfs.zip -d pt2matsim/data/gtfs/taipei_bus/

# 验证
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/taipei_bus/
```

#### 2. **各县市政府开放数据平台**

- **台北市**：https://data.taipei/
- **新北市**：https://data.ntpc.gov.tw/
- **高雄市**：https://data.kcg.gov.tw/
- **台中市**：https://opendata.taichung.gov.tw/

#### 3. **Transitland**

**网址**：https://www.transit.land/

- 全球 GTFS 数据聚合平台
- 台湾部分数据可能不完整

---

## 🛠️ 高级用法

### 自定义转乘距离和时间

```bash
# 宽松转乘：200米，5分钟
python src/main/python/merge_gtfs.py \
    dataset1/ dataset2/ output/ \
    --transfer-distance 200 \
    --transfer-time 300

# 严格转乘：50米，2分钟
python src/main/python/merge_gtfs.py \
    dataset1/ dataset2/ output/ \
    --transfer-distance 50 \
    --transfer-time 120
```

### 批量验证多个数据集

```bash
# 验证所有 GTFS 数据集
for dir in pt2matsim/data/gtfs/*/; do
    echo "验证: $dir"
    python src/main/python/validate_gtfs.py "$dir"
    echo "---"
done
```

---

## 📝 常见问题

### Q1: 验证工具报告"缺少 stop_times.txt"，怎么办？

**答**：这是致命问题，数据集无法用于 MATSim。解决方案：
1. 从其他来源获取完整 GTFS（如 PTX 平台）
2. 或使用其他已验证的数据集（如 tp_metro_gtfs）

### Q2: 合并时出现"距离小于 100m 的站点未找到"？

**答**：两个数据集的站点地理位置差距较大，无法自动匹配转乘。解决方案：
1. 增加 `--transfer-distance` 参数（如 200 或 300）
2. 手动编辑 transfers.txt 添加转乘关系

### Q3: 如何确认数据坐标系统？

**答**：运行验证工具：
```bash
python src/main/python/validate_gtfs.py <gtfs_dir>
```
查看"坐标系统检查"部分：
- ✓ WGS84：标准经纬度（stop_lat, stop_lon）
- ✓ EPSG:3826：台湾坐标系（TWD97/TM2）

### Q4: 合并后如何转换为 MATSim 格式？

**答**：使用项目中的 GtfsToMatsim 工具：
```bash
# 参见 src/main/java/org/matsim/project/tools/GtfsToMatsim.java
# 或参考 ../CLAUDE.md 中的 Public Transit Workflow 部分
```

---

## 📌 文件结构

```
src/main/python/
├── validate_gtfs.py      # GTFS 验证工具
├── merge_gtfs.py         # GTFS 合并工具
└── build_agent_tracks.py # Via 导出工具（已有）

pt2matsim/data/gtfs/
├── tp_metro_gtfs/        # ✅ 台北捷运（完整）
├── tp_metro_gtfs_small/  # ✅ 台北捷运（小型）
├── gtfs_tw_v5/           # ❌ 全台湾交通（缺 stop_times.txt）
└── merged_gtfs/          # 合并输出目录（需手动创建）
```

---

## 📖 相关文档

- **gtfs-merge-analysis.md**: 详细的数据分析报告
- **../CLAUDE.md**: MATSim 项目完整指南
- **GTFS Reference**: https://gtfs.org/schedule/reference/

---

**工具作者**: Claude Code
**创建日期**: 2025-11-17
**项目**: MATSim Example Project
