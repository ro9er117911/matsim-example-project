# Build Agent Tracks

提取 MATSim 代理的legs数据并生成时间采样轨迹，用于可视化和分析。

## 📊 新增功能（v1.0）

### Activity 匹配
现在轨迹点会自动关联到相应的Activity（home, work等），便于分析：
- **时间匹配**：根据time_s判断点属于哪个活动时间段
- **空间匹配**：若无时间信息，则按地理位置最近的活动匹配
- **活动统计**：汇总每个代理的活动类型和数量

**输出列**：
```
- activity_type: 活动类型（home, work, etc.）
- activity_sequence: 计划中的第几个活动（0=first）
- activity_link: 活动所在的link ID
- activity_dist_km: 轨迹点到活动位置的距离
- activity_match_type: 匹配方式（'time'/'spatial'）
- activity_count: 该代理的活动总数
- activity_types: 代理的所有活动类型列表
```

## 📁 模块结构

```
build_agent_tracks/
├── __init__.py              # 包初始化
├── utils.py                 # 时间转换、文件处理
├── models.py                # 数据模型（Activity, Leg, PersonPlan）
├── parsers.py               # XML解析器
│   ├── parse_population_or_plans()
│   ├── load_transit_mode_lookup()
│   ├── load_transit_route_stops()
│   └── load_actively_used_vehicles()
├── legs_builder.py          # Legs表构建（支持PT展开）
│   └── build_legs_table()
├── tracks_builder.py        # 时间采样轨迹生成
│   └── build_tracks_from_legs()
├── activity_matcher.py      # ⭐ 新功能：Activity匹配
│   ├── extract_activities_by_person()
│   ├── match_activity_to_tracks()
│   └── add_activity_summaries()
├── vehicle_filter.py        # Vehicle过滤和报告
├── main.py                  # CLI入口和pipeline编排
└── README.md                # 本文档
```

## 🚀 使用方法

### 基础用法

```bash
python build_agent_tracks.py \
  --plans output/plans.xml.gz \
  --schedule transitSchedule.xml \
  --out analysis/
```

### 启用所有功能（包括Activity匹配）

```bash
python build_agent_tracks.py \
  --plans output/plans.xml.gz \
  --population population.xml.gz \
  --schedule transitSchedule.xml \
  --events output/events.xml.gz \
  --out analysis/ \
  --dt 5
```

### 跳过Activity匹配（加速）

```bash
python build_agent_tracks.py \
  --plans output/plans.xml.gz \
  --schedule transitSchedule.xml \
  --out analysis/ \
  --skip-activity-matching
```

### 仅包含特定模式

```bash
python build_agent_tracks.py \
  --plans output/plans.xml.gz \
  --out analysis/ \
  --include-mode walk \
  --include-mode pt \
  --include-mode subway
```

## 📝 参数说明

| 参数 | 说明 | 必需 |
|-----|------|------|
| `--plans PATH` | plans.xml(.gz) 路径 | 否 |
| `--population PATH` | population.xml(.gz) 路径（如果plans不存在） | 否 |
| `--schedule PATH` | transitSchedule.xml(.gz) 路径 | 否 |
| `--events PATH` | events.xml(.gz) 路径（用于vehicle过滤） | 否 |
| `--out PATH` | 输出目录 | ✅ 是 |
| `--dt SECONDS` | 轨迹采样间隔（秒），默认：5 | 否 |
| `--include-mode MODE` | 包含的模式（可重复），默认：walk,pt,subway,rail,bus,tram | 否 |
| `--skip-activity-matching` | 跳过Activity匹配（加速） | 否 |

## 📤 输出文件

### 必需输出
- **legs_table.csv** - 每条腿的详细信息（含PT展开）
  - 列：person_id, leg_index, mode, start_time_s, end_time_s, start_x, start_y, ...

- **tracks_dt5s.csv** - 时间采样轨迹点（包含Activity匹配）
  - 列：time_s, time, person_id, mode, x, y, activity_type, activity_sequence, ...

### 可选输出
- **tracks_dt5s.parquet** - Parquet格式（更高效）
- **filtered_vehicles.csv** - 被使用的vehicle列表（需--events）
- **vehicle_usage_report.txt** - Vehicle使用统计报告（需--events）

## 💡 Activity匹配示例

### 场景：分析特定活动前后的出行

```python
import pandas as pd

# 读取带Activity信息的轨迹
tracks = pd.read_csv("analysis/tracks_dt5s.csv")

# 找出所有"work"活动的时间段
work_activities = tracks[tracks["activity_type"] == "work"]

# 统计每个代理在work活动中的轨迹点数
work_stats = work_activities.groupby("person_id").agg({
    "time_s": ["min", "max"],
    "activity_dist_km": "mean",
})
```

### 场景：Activity与出行模式关联

```python
# 哪些模式用于离开work活动
pt_after_work = tracks[
    (tracks["activity_type"] == "work") &
    (tracks["mode"].isin(["pt", "subway"]))
]
print(f"PT trips from work: {len(pt_after_work)} points")
```

## 🔧 集成到Java代码

如果要从Java代码调用此脚本：

```java
// 例：RunMatsim.java
// imports: java.io.BufferedReader, java.io.InputStreamReader, java.nio.charset.StandardCharsets
String pyscript = "src/main/python/build_agent_tracks.py";
ProcessBuilder pb = new ProcessBuilder(
    "python", "-u", pyscript,
    "--plans", outputDir + "/plans.xml.gz",
    "--schedule", scheduleFile,
    "--out", outputDir + "/analysis"
);
pb.redirectErrorStream(true); // 合并 stderr，避免阻塞且更容易看到日志
Process p = pb.start();

try (BufferedReader reader = new BufferedReader(
        new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
    String line;
    while ((line = reader.readLine()) != null) {
        System.out.println(line);
    }
}

int exitCode = p.waitFor();
if (exitCode != 0) {
    throw new RuntimeException("build_agent_tracks failed, exit code=" + exitCode);
}
```
> 提示：`-u` 可关闭 Python 的输出缓冲，确保 stdout/stderr 及时回传。

## 🐛 故障排除

### ImportError: No module named 'build_agent_tracks'

**原因**：Python路径不包含 `src/main/python/`

**解决**：
```bash
cd /Users/ro9air/matsim-example-project
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/main/python"
python build_agent_tracks.py --plans ... --out ...
```

或直接从modules目录运行：
```bash
cd src/main/python
python -m build_agent_tracks.main --plans ... --out ...
```

### No such file or directory: 'plans.xml.gz'

**原因**：路径错误或文件不存在

**解决**：
```bash
# 检查文件是否存在
ls -lh output/plans.xml.gz

# 使用绝对路径
python build_agent_tracks.py --plans /absolute/path/to/plans.xml.gz --out ...
```

### Activity匹配导致内存溢出

**原因**：大型数据集中extracting活动占用内存过多

**解决**：
```bash
# 跳过Activity匹配
python build_agent_tracks.py --skip-activity-matching --plans ... --out ...
```

### Java调用没有 stdout/stderr 输出

**原因**：未读取子进程的 stdout/stderr，导致缓冲区阻塞或输出被丢弃

**解决**：
```text
- 使用 ProcessBuilder 并读取 getInputStream() 的内容
- 必要时加上 `python -u` 或在 Python 中使用 flush
- 如需分开 stdout/stderr，请使用两个线程分别读取，避免死锁
```

## 📊 性能指标

| 数据规模 | 代理数 | Legs | 轨迹点 | 耗时 | 内存 |
|---------|-------|------|-------|------|------|
| 小 | 3 | 12 | ~500 | <1s | 50MB |
| 中 | 100 | 400 | ~10k | 2-3s | 200MB |
| 大 | 1000+ | 5000+ | ~100k+ | 10-30s | 500MB+ |

*跳过Activity匹配可减少约20-30%的耗时*

## 🔄 迁移指南（从v0.x到v1.0）

### 代码迁移

**v0.x** (单文件结构)
```python
from build_agent_tracks import parse_population_or_plans, build_legs_table
```

**v1.0** (模块结构)
```python
from build_agent_tracks.parsers import parse_population_or_plans
from build_agent_tracks.legs_builder import build_legs_table
from build_agent_tracks.activity_matcher import match_activity_to_tracks
```

### CLI迁移

**v0.x** (无Activity支持)
```bash
python build_agent_tracks.py --plans ... --out ...
```

**v1.0** (默认启用Activity匹配)
```bash
python build_agent_tracks.py --plans ... --out ...
# 若要禁用Activity匹配，加上 --skip-activity-matching
```

## 🧪 测试

### 运行集成测试

```bash
cd src/main/python
python -m pytest build_agent_tracks/tests/ -v
```

### 手动测试

```bash
# 使用小数据集
python build_agent_tracks.py \
  --plans scenarios/equil/output/plans.xml.gz \
  --schedule scenarios/equil/transitSchedule.xml \
  --out /tmp/test_output

# 检查输出
wc -l /tmp/test_output/*.csv
head -5 /tmp/test_output/tracks_dt5s.csv
```

## 📚 API文档

### 主要函数

#### `run_pipeline()`
```python
from build_agent_tracks.main import run_pipeline

outputs = run_pipeline(
    plans_path="plans.xml.gz",
    population_fallback="population.xml.gz",
    events_path="events.xml.gz",
    outdir="analysis",
    dt=5,
    schedule_path="transitSchedule.xml",
    include_modes={"walk", "pt", "subway"},
    add_activity_matching=True,
)
```

#### `match_activity_to_tracks()`
```python
from build_agent_tracks.activity_matcher import (
    extract_activities_by_person,
    match_activity_to_tracks,
)

activities = extract_activities_by_person(plans)
tracks_with_activity = match_activity_to_tracks(tracks_df, activities)
```

## 📝 贡献指南

### 添加新功能

1. 在 `build_agent_tracks/` 下创建新模块
2. 添加到 `main.py` 的 `run_pipeline()` 中
3. 更新此 README

### 示例：添加GeoJSON导出

```python
# build_agent_tracks/export_geojson.py
def export_tracks_as_geojson(tracks_df, outpath):
    """Export tracks to GeoJSON format for mapping."""
    # 实现细节...
    pass

# build_agent_tracks/main.py
if enable_geojson:
    geojson_path = export_tracks_as_geojson(tracks_df, outdir)
    outputs["tracks_geojson"] = geojson_path
```

## 📞 支持

遇到问题？
1. 检查故障排除部分
2. 查看日志输出（加上 `-v` 或 `--verbose` 标志）
3. 提交Issue到项目仓库

## 📜 更新历史

### v1.0 (2025-11-04)
- ✨ 新增：Activity匹配功能
- 🔨 重构：代码拆分为模块化结构
- 📚 改进：更详细的文档和API
- ✅ 测试：更好的测试覆盖

### v0.9
- 初始版本：单文件脚本
