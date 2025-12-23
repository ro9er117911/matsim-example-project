# GTFS 数据合并分析报告

**日期**: 2025-11-17
**任务**: 合并 gtfs_tw_v5 与 tp_metro_gtfs
**状态**: ⚠️ **发现关键问题 - 需要调整策略**

---

## 📊 数据集概览

### 1. gtfs_tw_v5（全台湾交通数据）

**文件清单**:
```
✅ agency.txt          (393 agencies - 航空、公交、铁路等)
✅ calendar.txt        (261,385 服务日历)
✅ calendar_dates.txt  (56,884 日期例外)
✅ routes.txt          (9,663 路线)
✅ stops.txt           (154,477 站点)
✅ stops_epsg3826.txt  (154,477 站点 - TWD97坐标)
✅ trips.txt           (326,645 行程)
❌ stop_times.txt      **【缺失 - 致命问题】**
```

**路线类型分布**:
- `route_type=1` (地铁/捷运): 47 条
- `route_type=2` (铁路): 1,234 条
- `route_type=3` (公交车): 8,329 条
- `route_type=4` (渡轮): 49 条
- `route_type=6` (缆车/航空): 4 条

**关键问题**:
🔴 **缺少 stop_times.txt** - 这是 GTFS 规范中的**必需文件**，包含每个行程在每个站点的到达/离开时间。没有这个文件，数据集**无法用于 MATSim 模拟**。

### 2. tp_metro_gtfs（台北捷运完整数据）

**文件清单**:
```
✅ agency.txt          (1 agency - TRTC 台北捷运)
✅ calendar.txt        (12 服务日历)
✅ calendar_dates.txt  (80 日期例外)
✅ frequencies.txt     (16 班次频率定义)
✅ routes.txt          (7 地铁线路)
✅ stop_times.txt      (100,015 站点时刻) ✓
✅ stops.txt           (722 站点)
✅ stops_epsg3826.txt  (722 站点 - TWD97坐标)
✅ transitions.txt     (6,723 翻译条目 - 多语言支持)
✅ trips.txt           (5,990 行程)
```

**路线清单**:
- Blue (板南线)
- Red (淡水信义线)
- Green (松山新店线)
- Orange (中和新芦线)
- Brown (文湖线)
- 等...

**数据完整性**: ✅ **完全符合 GTFS 规范，可直接使用**

---

## 🔍 兼容性分析

### Agency ID 冲突检查
- ✅ **无冲突**: gtfs_tw_v5 使用 `AirLine_XX`, `Bus_XX` 等前缀
- ✅ **无冲突**: tp_metro_gtfs 使用 `TRTC`

### 坐标系统
- ✅ **一致**: 两个数据集都使用 **EPSG:3826 (TWD97/TM2)**
- ✅ **格式**: 都包含 `stop_x_EPSG3826` 和 `stop_y_EPSG3826` 字段

### Stop ID 命名规则
- **gtfs_tw_v5**: `AirLine_CMJ`, `Bus_XXXX` 等（按运营商分类）
- **tp_metro_gtfs**: `BL01_UP`, `BL01_DN`, `076` 等（按线路和方向分类）
- ✅ **无冲突**: 命名模式完全不同

---

## ❌ 关键障碍

### 问题 1: gtfs_tw_v5 缺少 stop_times.txt

**影响**:
- 无法知道车辆何时到达每个站点
- 无法生成 MATSim 的 `transitSchedule.xml`
- 无法计算行程时间和班次间隔
- **数据集无法用于任何基于时刻表的仿真**

**根本原因**（推测）:
- 可能是数据导出不完整
- 可能使用 `frequencies.txt` 替代（但 gtfs_tw_v5 也没有这个文件）
- 可能是原始数据源就不包含时刻表信息

### 问题 2: transitions.txt 不是转乘信息

**发现**:
```
table_name,field_name,language,translation,record_id,record_sub_id,field_value
agency,agency_name,en,Taipei Rapid Transit Corporation,TRTC,,
routes,route_short_name,en,Bannan Line,Blue,,
```

这是 **translations.txt** 的内容（多语言翻译），不是 **transfers.txt**（转乘信息）。

**影响**:
- 无法直接使用现有文件建立转乘关系
- 需要从零开始计算站点间的转乘距离

---

## 🎯 解决方案与建议

### 选项 1: 🔴 **放弃合并 gtfs_tw_v5**（推荐）

**理由**:
- gtfs_tw_v5 **缺少核心时刻表数据**，无法用于 MATSim
- 即使合并，也无法生成有效的 `transitSchedule.xml`
- 数据质量不符合项目需求

**替代方案**:
- **仅使用 tp_metro_gtfs** 进行台北捷运模拟（数据完整且可靠）
- 如需公交数据，寻找**完整的 GTFS 数据源**（例如：政府开放数据平台）

### 选项 2: 🟡 **从其他来源获取完整 GTFS**

**台湾公共运输 GTFS 数据源**:
1. **交通部 PTX 平台**: https://ptx.transportdata.tw/
   - 提供全台湾公交、铁路、捷运 GTFS 数据
   - 数据完整且定期更新
   - 需要申请 API 密钥

2. **各县市政府开放数据平台**:
   - 台北市: https://data.taipei/
   - 新北市: https://data.ntpc.gov.tw/
   - 高雄市: https://data.kcg.gov.tw/

3. **OpenStreetMap 相关项目**:
   - Transitland: https://www.transit.land/

### 选项 3: 🟢 **仅使用台北捷运数据**（立即可行）

**优势**:
- ✅ 数据完整且高质量
- ✅ 已有 100,015 条 stop_times 记录
- ✅ 包含 frequencies.txt（班次频率）
- ✅ 适合测试和原型开发

**建议操作**:
1. 直接使用 `tp_metro_gtfs` 或 `tp_metro_gtfs_small`
2. 使用现有的 GtfsToMatsim 工具转换
3. 后续如需公交数据，再从 PTX 平台获取

---

## 📝 技术细节记录

### GTFS 必需文件清单（根据 GTFS Reference）

**核心必需文件**:
- ✅ `agency.txt` - 运营商信息
- ✅ `stops.txt` - 站点位置
- ✅ `routes.txt` - 路线定义
- ✅ `trips.txt` - 行程定义
- ✅ `stop_times.txt` - **时刻表** ← gtfs_tw_v5 缺失
- ✅ `calendar.txt` 或 `calendar_dates.txt` - 服务日历

**可选文件**:
- `frequencies.txt` - 班次频率（tp_metro_gtfs 有）
- `transfers.txt` - 转乘信息（两个数据集都没有）
- `shapes.txt` - 路线形状（两个数据集都没有）

### 数据量对比

| 项目 | gtfs_tw_v5 | tp_metro_gtfs |
|------|-----------|---------------|
| Agencies | 393 | 1 |
| Routes | 9,663 | 7 |
| Stops | 154,477 | 722 |
| Trips | 326,645 | 5,990 |
| Stop Times | **0** ❌ | 100,015 ✅ |
| Frequencies | **0** | 16 |

---

## 💡 下一步行动建议

### 立即可行方案

1. **使用 tp_metro_gtfs 进行 MATSim 转换**:
   ```bash
   python src/main/java/org/matsim/project/tools/GtfsToMatsim.py \
     --gtfs pt2matsim/data/gtfs/tp_metro_gtfs/ \
     --network scenarios/taipei/network.xml \
     --output scenarios/taipei/
   ```

2. **验证转换结果**:
   ```bash
   # 检查生成的 transitSchedule 和 transitVehicles
   ls -lh scenarios/taipei/transitSchedule.xml
   ls -lh scenarios/taipei/transitVehicles.xml
   ```

### 如需公交数据

3. **从 PTX 平台下载完整 GTFS**:
   ```bash
   # 示例：下载台北市公交 GTFS
   curl -X GET "https://ptx.transportdata.tw/MOTC/v2/Bus/GTFS/City/Taipei" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -o taipei_bus_gtfs.zip
   ```

4. **合并 PTX 公交数据与捷运数据**:
   - 此时两个数据集都完整
   - 可以使用本报告中的合并脚本框架

---

## 📌 结论

**当前状态**: gtfs_tw_v5 因缺少 `stop_times.txt` 而**无法用于 MATSim 模拟**。

**推荐方案**:
1. 短期：使用 `tp_metro_gtfs`（台北捷运）进行原型开发
2. 中期：从 PTX 平台获取完整的公交 GTFS 数据
3. 长期：建立自动化 GTFS 更新和合并流程

**风险提示**:
- ⚠️ 不要在缺少 `stop_times.txt` 的数据集上浪费时间
- ⚠️ 合并前务必验证数据完整性
- ⚠️ PTX API 有流量限制，需要合理规划下载策略

---

**报告生成**: Claude Code
**分析工具**: Bash, awk, grep, wc
**数据位置**: `/home/user/matsim-example-project/pt2matsim/data/gtfs/`
