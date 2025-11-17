# 2025-11-17: GTFS 数据合并分析

## 任务概述

分析并合并两个 GTFS 数据集：
1. `gtfs_tw_v5` - 全台湾交通数据
2. `tp_metro_gtfs` - 台北捷运数据

## 关键发现

### ❌ 主要障碍：gtfs_tw_v5 缺少 stop_times.txt

**问题**：
- gtfs_tw_v5 缺少 **stop_times.txt**（GTFS 必需文件）
- 该文件包含每个行程在每个站点的到达/离开时间
- 没有它，无法生成 MATSim 的 transitSchedule.xml
- **数据集无法用于任何基于时刻表的仿真**

**数据集对比**：

| 项目 | gtfs_tw_v5 | tp_metro_gtfs |
|------|-----------|---------------|
| Agencies | 393 | 1 |
| Routes | 9,663 | 7 |
| Stops | 154,477 | 722 |
| Trips | 326,645 | 5,990 |
| **Stop Times** | **0** ❌ | **100,015** ✅ |
| MATSim 兼容 | ❌ 不可用 | ✅ 完全兼容 |

### ✅ 正面发现

1. **Agency IDs 无冲突**：
   - gtfs_tw_v5: `AirLine_XX`, `Bus_XX` 等
   - tp_metro_gtfs: `TRTC`

2. **坐标系统一致**：
   - 两者都使用 EPSG:3826 (TWD97/TM2)
   - 都包含 `stops_epsg3826.txt`

3. **transitions.txt 发现**：
   - 不是转乘信息（transfers.txt）
   - 而是多语言翻译表（translations.txt）

## 交付成果

### 1. GTFS 验证工具：`validate_gtfs.py`

**功能**：
- 检查 GTFS 文件完整性
- 统计记录数
- 分析路线类型
- 验证外键完整性
- 评估 MATSim 兼容性

**使用**：
```bash
python src/main/python/validate_gtfs.py <gtfs_directory>
```

**输出示例**：
```
=== 文件完整性检查 ===
  ✓ agency.txt
  ✓ stops.txt
  ✓ routes.txt
  ✓ trips.txt
  ✓ stop_times.txt       ← 关键检查

=== 数据集总结 ===
  ✓ 数据集完整 - 包含所有必需文件
  ✓ MATSim 兼容性 - 可用于 MATSim 转换
```

**验证结果**：
- ✅ tp_metro_gtfs: 完整且兼容
- ❌ gtfs_tw_v5: 缺少 stop_times.txt

### 2. GTFS 合并工具：`merge_gtfs.py`

**功能**：
- 合并两个 GTFS 数据集
- 自动处理 ID 冲突（添加前缀）
- 生成转乘关系（transfers.txt）
- 基于地理距离识别转乘站点

**使用**：
```bash
python src/main/python/merge_gtfs.py \
    gtfs1/ gtfs2/ output/ \
    --prefix1 MRT_ \
    --prefix2 BUS_ \
    --transfer-distance 100 \
    --transfer-time 180
```

**特性**：
- ID 前缀自动化（避免冲突）
- Haversine 距离计算（识别邻近站点）
- 双向转乘关系生成
- 支持自定义转乘参数

### 3. 文档

**GTFS_MERGE_ANALYSIS.md**：
- 详细的数据分析报告
- 问题诊断和根本原因
- 解决方案和替代方案
- PTX 平台数据获取指南

**GTFS_TOOLS_GUIDE.md**：
- 完整的工具使用指南
- 工作流程说明
- 常见问题解答
- 数据源推荐

**工作日志**（本文件）：
- 任务总结
- 技术细节
- 下一步建议

## 技术实现

### 验证工具核心功能

```python
# 文件完整性检查
REQUIRED_FILES = ['agency.txt', 'stops.txt', 'routes.txt',
                  'trips.txt', 'stop_times.txt']

# 路线类型映射
ROUTE_TYPES = {
    0: '电车/轻轨',
    1: '地铁/捷运',
    2: '铁路',
    3: '公交车',
    ...
}

# 外键验证（采样检查）
- trips.txt → routes.txt (route_id)
- stop_times.txt → trips.txt (trip_id)
```

### 合并工具核心算法

```python
# ID 前缀处理
for row in reader:
    if key_field in row:
        row[key_field] = f"{prefix}{row[key_field]}"
    for ref_field in ref_fields:
        row[ref_field] = f"{prefix}{row[ref_field]}"

# 转乘关系生成（Haversine 距离）
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球半径（米）
    # ... 标准 Haversine 公式
    return distance

# 双向转乘
if distance <= max_distance:
    transfers.append({
        'from_stop_id': stop1_id,
        'to_stop_id': stop2_id,
        'transfer_type': '2',
        'min_transfer_time': str(transfer_time),
    })
```

## 结论和建议

### 短期方案（立即可行）

✅ **使用 tp_metro_gtfs 进行开发**：
- 数据完整且高质量
- 100,015 条 stop_times 记录
- 适合原型开发和测试

```bash
# 验证数据
python src/main/python/validate_gtfs.py pt2matsim/data/gtfs/tp_metro_gtfs/

# 转换为 MATSim
# 使用现有 GtfsToMatsim 工具
```

### 中期方案（推荐）

✅ **从 PTX 平台获取完整公交数据**：
1. 注册 PTX API（https://ptx.transportdata.tw/）
2. 下载台北市公交 GTFS
3. 验证数据完整性
4. 使用 merge_gtfs.py 合并捷运和公交
5. 转换为 MATSim 格式

```bash
# 下载公交数据
curl -X GET "https://ptx.transportdata.tw/MOTC/v2/Bus/GTFS/City/Taipei" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o taipei_bus_gtfs.zip

## 2025-11-17 追加记录：PT 映射排查（今天的工作）

### 今日产出
- 复习 `PT_MAPPING_QUICK_START.md`、`docs/GTFS_MAPPING_GUIDE.md`、`docs/PT_MAPPING_STRATEGY.md` 与 `docs/early-stop-strategy.md`，整理执行顺序与资源要求。
- 重新验证 `pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra`：共 8,375 条路线、6,513 个 trips、100,015 笔 stop_times，但只有 **87.9%** trips 出现在 stop_times 中，缺少 791 条（全是 TRA 行程，见 `pt2matsim/output_v1/gtfs_validation_summary.txt`）。已记录命令与结果供后续修复。
- 检查 Phase 2 输出 (`pt2matsim/output_v1/transitSchedule.xml`)：`ScheduleCleaner` 合并后仅剩 1,309 条 `<transitRoute>` 与 26,152 个 `<stop refId>`，远低于目标 2,000+/40,000+，需注意这会限制后续映射。
- 两次以 `ptmapper-config-merged.xml` 运行 `PublicTransitMapper`（`java -Xmx12g …`），均因 CLI 10 分钟限制被迫中断，日志显示 mapper 正常启动、开始计算 pseudoTransitRoutes。确认需要更长 timeout 才能完成。
- 整理「放宽标准」的执行手册：先以 `ptmapper-config-metro-v4.xml` 在 `tp_metro_gtfs_small` 上做 5 分钟烟囱测试，确认 mapper 正常；然后再用 `timeout 3h` + `-Xmx12g` 跑正式的 `ptmapper-config-merged.xml`，并提醒用 `tail -f` 监控。

### 建议的下一步
1. 修补或移除缺少 stop_times 的 791 条 TRA 行程，让验证脚本回到 >90% 覆盖，避免 mapper 中途反复报错。
2. 完成烟囱测试后，以较大的 timeout/内存跑正式映射，生成 `transitSchedule-mapped.xml.gz` 与 `network-with-pt.xml.gz`。
3. 映射完成后执行 `CheckMappedSchedulePlausibility` 并重新统计 `<transitRoute>`/`<stop refId>`，确认放宽后的流程仍能达到可运行的 PT 网络。

# 验证
python src/main/python/validate_gtfs.py taipei_bus/

# 合并
python src/main/python/merge_gtfs.py \
  tp_metro_gtfs/ taipei_bus/ merged/ \
  --prefix1 MRT_ --prefix2 BUS_
```

### 长期方案

✅ **建立自动化 GTFS 更新流程**：
- 定期从 PTX 平台更新数据
- 自动验证和合并
- 集成到 MATSim 工作流

## 风险和注意事项

⚠️ **不要使用 gtfs_tw_v5**：
- 缺少关键时刻表数据
- 无法生成有效的 MATSim 输入

⚠️ **PTX API 限制**：
- 需要注册账号
- 有流量限制（需合理规划下载）
- 数据更新频率不一

⚠️ **转乘关系生成**：
- 基于地理距离，可能不准确
- 建议人工审核重要转乘站
- 可能需要调整 transfer-distance 参数

## 文件清单

### 新增文件

```
src/main/python/
├── validate_gtfs.py           # GTFS 验证工具
└── merge_gtfs.py              # GTFS 合并工具

文档/
├── GTFS_MERGE_ANALYSIS.md     # 详细分析报告
├── GTFS_TOOLS_GUIDE.md        # 工具使用指南
└── working_journal/
    └── 2025-11-17-GTFS-Merge-Analysis.md  # 本文件
```

### 数据状态

```
pt2matsim/data/gtfs/
├── tp_metro_gtfs/             # ✅ 完整可用
├── tp_metro_gtfs_small/       # ✅ 完整可用
├── gtfs_tw_v5/                # ❌ 缺 stop_times.txt
└── tp_metro_gtfs_osm_filtered # ✅ 完整可用
```

## 下一步行动

1. ✅ **已完成**：数据分析和工具开发
2. ⏭️ **待处理**：从 PTX 平台获取公交数据
3. ⏭️ **待处理**：合并捷运和公交 GTFS
4. ⏭️ **待处理**：转换为 MATSim 格式
5. ⏭️ **待处理**：运行仿真验证

## 技术债务

- [ ] 验证工具可增加更多检查（如时刻表合理性）
- [ ] 合并工具可支持 3+ 个数据集
- [ ] 需要添加单元测试
- [ ] 可考虑使用 gtfs-kit 或 transitfeed 库简化代码

## 参考资料

- GTFS 官方规范：https://gtfs.org/schedule/reference/
- 交通部 PTX 平台：https://ptx.transportdata.tw/
- MATSim PT 教程：https://matsim.org/docs/tutorials/pt
- Haversine 公式：https://en.wikipedia.org/wiki/Haversine_formula

---

**任务完成时间**: 2025-11-17
**工作时长**: ~2 小时
**状态**: ✅ 已完成分析和工具开发
**下一里程碑**: 获取完整公交 GTFS 并执行合并
