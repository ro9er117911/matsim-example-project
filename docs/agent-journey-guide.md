# Agent 旅程建立指南
**目的**: 帮助用户从零开始创建有效的 MATSim 代理人单日旅程计划
**难度**: 初级至中级
**预期时间**: 30-60 分钟

---

## 📖 目录

1. [基本概念](#基本概念)
2. [旅程规划步骤](#旅程规划步骤)
3. [Home 和 Work 活动定义](#home-和-work-活动定义)
4. [交通方式选择](#交通方式选择)
5. [网络查询方法](#网络查询方法)
6. [完整的旅程示例](#完整的旅程示例)
7. [验证检查清单](#验证检查清单)
8. [常见问题](#常见问题)
9. [實戰案例：修正 population.xml](#實戰案例修正-populationxml)

---

## 基本概念

### 什么是 Agent 旅程？

在 MATSim 中，一个「Agent 旅程」包含：

```
活动 (home) → 腿 (leg) → 活动 (work) → 腿 (leg) → 活动 (home)
```

**关键元素**:
- **活动 (Activity)**: 代理人在某个位置停留的时间 (home, work, shopping 等)
- **腿 (Leg)**: 代理人在两个活动之间的移动方式 (car, pt, walk 等)
- **时间**: 每个活动的开始和结束时间

### 为什么需要验证？

创建的旅程必须满足：
- ✅ 所有活动位置必须在网络中存在
- ✅ 选择的交通方式必须在网络中支持
- ✅ 时间逻辑必须合理 (结束时间 < 下个活动的开始时间)
- ✅ 路由模式必须与交通方式一致

---

## 旅程规划步骤

### 整体流程

```
第 1 步: 定义活动位置 (Home, Work)
    ↓
第 2 步: 选择交通方式
    ↓
第 3 步: 在网络中找到相近的 link/node
    ↓
第 4 步: 创建 XML 旅程计划
    ↓
第 5 步: 验证旅程有效性
    ↓
第 6 步: 添加到 population.xml
```

---

## Home 和 Work 活动定义

### 什么是 Home?

**Home** 是代理人一天开始和结束的位置。

```xml
<!-- Home 活动示例 -->
<activity type="home"
          link="pt_BL02_UP"           <!-- 必须是网络中存在的 link -->
          x="294035.05"
          y="2762173.24"              <!-- 地理坐标 -->
          end_time="07:15:00" />      <!-- 离开 home 的时间 -->
```

**Home 的特点**:
- 📍 必须有有效的 link ID
- 📍 必须有精确的 (x, y) 坐标
- 📍 end_time 是离开时间（用 HH:MM:SS 格式）
- 📍 通常在一天的开始和结束各出现一次

### 什么是 Work?

**Work** 是代理人工作的位置。

```xml
<!-- Work 活动示例 -->
<activity type="work"
          link="pt_BL14_UP"           <!-- 必须是网络中存在的 link -->
          x="303804.19"
          y="2770590.71"              <!-- 地理坐标 -->
          end_time="17:00:00" />      <!-- 离开 work 的时间 -->
```

**Work 的特点**:
- 📍 必须有有效的 link ID
- 📍 通常在工作日出现
- 📍 end_time 是下班时间

### 定义活动的关键步骤

#### 步骤 1: 确定位置

```
选择 Home:
  - 应该是城市中代表性的地点
  - 如果是 PT 出行，可以选择站点附近 (link = "pt_STATION_UP")
  - 如果是汽车，选择任何有效的网络 link

选择 Work:
  - 与 home 有合理的距离
  - 如果使用 PT，选择不同的车站 (pt_STATION_UP)
  - 应该在 home 和其他设施之间
```

#### 步骤 2: 获取准确的坐标

```bash
# 方法 1: 从网络文件中查询
gunzip -c network-with-pt.xml.gz | grep "link id=\"pt_BL02_UP\"" | head -5

# 输出将包含:
# <link id="pt_BL02_UP" from="pt_BL02_UP" to="pt_BL02_UP" length="1.0" ... />

# 从 transitSchedule 中查询确切坐标:
gunzip -c transitSchedule-mapped.xml.gz | grep -A2 "stopFacility id=\"BL02_UP"
```

#### 步骤 3: 确定合理的时间

```
Home end_time (早上):
  - 通勤者: 7:00-8:30
  - 灵活工作者: 8:00-10:00
  - 晚出行: 9:00-11:00

Work end_time (下午):
  - 标准工作: 17:00-18:00
  - 早班: 14:00-15:00
  - 晚班: 20:00-22:00

总规则: work_end_time - home_end_time >= 8 小时
```

---

## 交通方式选择

### 三种主要交通方式

| 方式 | 描述 | 适用场景 | 配置 |
|------|------|--------|------|
| **Car** | 驾车 | 长距离、灵活路线 | `<leg mode="car" />` |
| **PT** | 公共交通 | 城市通勤、预定路线 | `<leg mode="pt" />` |
| **Walk** | 步行 | 短距离、本地出行 | `<leg mode="walk" />` |

### 如何选择交通方式？

#### Car 出行

```
选择 Car 的条件:
✓ Home 和 Work 距离 > 5 km
✓ 网络有支持 "car" 模式的 links
✓ 希望模拟自驾行为

XML 配置:
<leg mode="car" />

网络要求:
- 检查 link 的 modes 属性是否包含 "car"
```

**示例**:
```bash
# 查询网络中是否有 car 模式
gunzip -c network-with-pt.xml.gz | grep 'modes=".*car' | head -5
```

#### PT 出行

```
选择 PT 的条件:
✓ 城市内通勤
✓ Home 和 Work 都靠近公交站点
✓ 需要遵循时刻表

XML 配置:
<leg mode="pt" />

网络要求:
- link ID 应该以 "pt_" 开头 (pt_STATION_UP/DN)
- transitSchedule 中必须定义了停靠点
```

**示例**:
```bash
# 查询可用的 PT 站点
gunzip -c network-with-pt.xml.gz | grep -o 'link id="pt_[^"]*"' | head -20

# 检查时刻表中的站点
gunzip -c transitSchedule-mapped.xml.gz | grep "stopFacility id=" | head -10
```

#### Walk 出行

```
选择 Walk 的条件:
✓ Home 和 Work 距离 < 2 km
✓ 用于最后一英里连接
✓ 与 PT 结合使用

XML 配置:
<leg mode="walk" />

网络要求:
- 通常使用 "walk" 或 "pt_" link
- 距离自动计算为 beeline × 1.3
```

### 组合交通方式

**多模式旅程示例** (使用 PT):

```xml
<!-- 家 → 站点 (步行) → PT → 工作地点 (步行) → 家 -->
<person id="agent_multimodal">
  <plan selected="yes">
    <activity type="home" link="pt_BL02_UP" ... end_time="07:15:00" />

    <!-- 第 1 段: 步行到站点 -->
    <leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
      <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" />
    </leg>

    <!-- 在站点等待和互动 -->
    <activity type="pt interaction" link="pt_BL02_UP" max_dur="00:00:00" />

    <!-- 第 2 段: 使用 PT -->
    <leg mode="pt" dep_time="07:16:00">
      <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP">
        {"transitLineId":"Blue","boardingTime":"07:16:08"}
      </route>
    </leg>

    <!-- 在终点站互动 -->
    <activity type="pt interaction" link="pt_BL14_UP" max_dur="00:00:00" />

    <!-- 第 3 段: 步行到工作地点 -->
    <leg mode="walk" ...>
      <route type="generic" start_link="pt_BL14_UP" end_link="pt_BL14_UP" />
    </leg>

    <activity type="work" link="pt_BL14_UP" ... end_time="17:00:00" />
  </plan>
</person>
```

---

## 网络查询方法

### 方法 1: 查询可用的 Link IDs

```bash
# 查看所有 PT station links
gunzip -c network-with-pt.xml.gz | grep -o 'link id="pt_[^"]*"' | sort | uniq

# 输出:
# link id="pt_BL01_UP"
# link id="pt_BL01_DN"
# link id="pt_BL02_UP"
# ...

# 查看 car links
gunzip -c network.xml.gz | grep 'modes=".*car' | grep -o 'id="[^"]*"' | head -20
```

### 方法 2: 查询 Link 的详细信息

```bash
# 查询特定 link 的属性
gunzip -c network-with-pt.xml.gz | grep -A5 'link id="pt_BL02_UP"'

# 输出应该包含:
# <link id="pt_BL02_UP" from="pt_BL02_UP" to="pt_BL02_UP"
#       length="1.0" freespeed="20.0" capacity="..."
#       permlanes="..." modes="artificial,stopFacilityLink,subway" />
```

### 方法 3: 在时刻表中查询站点坐标

```bash
# 查询站点信息
gunzip -c transitSchedule-mapped.xml.gz | grep -A3 'id="BL02_UP'

# 输出应该包含:
# <stopFacility id="BL02_UP.link:pt_BL02_UP" name="BL02_UP"
#              link="pt_BL02_UP" x="294035.05" y="2762173.24" />
```

### 方法 4: 查找最近的 Link

```bash
# 使用 grep 和正则表达式查找距离特定点近的站点
# (查看下面的 "find-nearest-node.sh" 脚本)

# 快速方法: 列出所有 station 并手动选择
gunzip -c transitSchedule-mapped.xml.gz | grep 'stopFacility id=' | \
  sed 's/.*id="\([^"]*\)".*/\1/' | head -30
```

### 检查交通方式支持

```bash
# 检查 link 是否支持特定模式
gunzip -c network-with-pt.xml.gz | grep 'link id="pt_BL02_UP"' | grep -o 'modes="[^"]*"'

# 输出: modes="artificial,stopFacilityLink,subway"

# 检查 car 模式支持
gunzip -c network.xml.gz | grep 'modes="[^"]*car' | wc -l
```

---

## 完整的旅程示例

### 示例 1: 简单的汽车通勤

```xml
<person id="car_commuter_01">
  <plan selected="yes">
    <!-- 早上在家 -->
    <activity type="home" link="10000"
              x="100000.0" y="200000.0"
              end_time="07:30:00" />

    <!-- 驾车到工作地点 -->
    <leg mode="car" dep_time="07:30:00">
      <route type="links" distance="15000.0">
        10000 10001 10002 10003
      </route>
    </leg>

    <!-- 工作 -->
    <activity type="work" link="10003"
              x="115000.0" y="200000.0"
              end_time="17:00:00" />

    <!-- 驾车回家 -->
    <leg mode="car" dep_time="17:00:00">
      <route type="links">
        10003 10002 10001 10000
      </route>
    </leg>

    <!-- 晚上在家 -->
    <activity type="home" link="10000"
              x="100000.0" y="200000.0" />
  </plan>
</person>
```

### 示例 2: PT 通勤者

```xml
<person id="pt_commuter_01">
  <plan selected="yes">
    <!-- 早上在家 (靠近 BL02 站) -->
    <activity type="home" link="pt_BL02_UP"
              x="294035.05" y="2762173.24"
              end_time="07:15:00" />

    <!-- 步行到站点 -->
    <leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
      <route type="generic" start_link="pt_BL02_UP"
              end_link="pt_BL02_UP" distance="50.0" />
    </leg>

    <!-- 在站点等待 -->
    <activity type="pt interaction" link="pt_BL02_UP"
              x="294035.05" y="2762173.24"
              max_dur="00:00:00" />

    <!-- 坐 PT 前往 BL14 -->
    <leg mode="pt" dep_time="07:16:00" trav_time="00:27:55">
      <route type="default_pt" start_link="pt_BL02_UP"
              end_link="pt_BL14_UP" distance="7646.14">
        {"transitLineId":"Blue","boardingTime":"07:16:08",
         "transitRouteId":"403_1438_UP"}
      </route>
    </leg>

    <!-- 在工作地点站点等待 -->
    <activity type="pt interaction" link="pt_BL14_UP"
              x="303804.19" y="2770590.71"
              max_dur="00:00:00" />

    <!-- 步行到工作地点 -->
    <leg mode="walk" dep_time="07:43:55" trav_time="00:01:00">
      <route type="generic" start_link="pt_BL14_UP"
              end_link="pt_BL14_UP" distance="50.0" />
    </leg>

    <!-- 工作 -->
    <activity type="work" link="pt_BL14_UP"
              x="303804.19" y="2770590.71"
              end_time="17:00:00" />

    <!-- 回程类似 (省略以节省空间) -->
    ...
  </plan>
</person>
```

### 示例 3: 多模式出行 (购物后回家)

```xml
<person id="mixed_commuter_01">
  <plan selected="yes">
    <!-- 早上在家 -->
    <activity type="home" link="pt_BL02_UP"
              x="294035.05" y="2762173.24"
              end_time="07:15:00" />

    <!-- 步行 + PT 到工作地点 (如示例 2) -->
    ...
    <activity type="work" link="pt_BL14_UP" ... end_time="17:00:00" />

    <!-- PT 回家到 BL02 -->
    ...
    <activity type="pt interaction" link="pt_BL02_UP" ... />

    <!-- 步行到购物中心 -->
    <leg mode="walk" dep_time="18:30:00" trav_time="00:10:00">
      <route type="generic" start_link="pt_BL02_UP"
              end_link="shopping_01" distance="800.0" />
    </leg>

    <!-- 购物 -->
    <activity type="shopping" link="shopping_01"
              x="294500.0" y="2762500.0"
              end_time="20:00:00" />

    <!-- 步行回家 -->
    <leg mode="walk" dep_time="20:00:00" trav_time="00:10:00">
      <route type="generic" start_link="shopping_01"
              end_link="pt_BL02_UP" distance="800.0" />
    </leg>

    <!-- 晚上在家 -->
    <activity type="home" link="pt_BL02_UP"
              x="294035.05" y="2762173.24" />
  </plan>
</person>
```

---

## 验证检查清单

创建旅程后，使用这个清单验证：

### 活动验证
- [ ] **Home** 有有效的 link ID
- [ ] **Work** 有有效的 link ID
- [ ] 所有 link IDs 在网络文件中存在
- [ ] 坐标 (x, y) 与网络中的位置相符

### 时间验证
- [ ] Home end_time < Work start_time
- [ ] Work end_time > Work start_time
- [ ] 末日 Home 活动没有 end_time (代表一天结束)
- [ ] 所有时间格式为 HH:MM:SS

### 交通方式验证
- [ ] 每条 leg 有有效的 mode (car, pt, walk)
- [ ] PT legs 有 pt interaction activities
- [ ] Walk legs 的距离合理 (< 5km)
- [ ] Car legs 如果有 links 路由，链接有效

### 网络验证
- [ ] Car links 确实支持 "car" 模式
- [ ] PT links 以 "pt_" 开头
- [ ] transitSchedule 包含所有引用的站点

### 语法验证
- [ ] XML 格式正确 (可用 XML 验证工具)
- [ ] 所有属性值用引号括起
- [ ] 嵌套标签正确配对
- [ ] 特殊字符正确转义 (如 & → &amp;)

---

## 常见问题

### Q1: 我的 link ID 应该在哪里找？

**A**:
```bash
# 对于 PT:
gunzip -c network-with-pt.xml.gz | grep -o 'link id="pt_[^"]*"' | sort

# 对于 Car:
gunzip -c network.xml.gz | grep 'modes=".*car' | grep -o 'id="[^"]*"'

# 或查看 transitSchedule 中的 stopFacility
gunzip -c transitSchedule-mapped.xml.gz | grep 'stopFacility id='
```

### Q2: 我可以使用任意坐标吗？

**A**: 不建议。最好使用实际网络中的坐标，这样更准确。
```bash
# 从网络查询真实坐标
gunzip -c transitSchedule-mapped.xml.gz | grep -A5 'stopFacility id="BL02_UP'
# 查看 x 和 y 属性
```

### Q3: PT 旅程为什么需要 pt interaction 活动？

**A**: `pt interaction` 是 MATSim 中 PT 系统的特殊要求：
- 代理人在站点上车前需要等待
- 代理人在站点下车后需要互动
- 这让时间逻辑更清晰

### Q4: 我的旅程验证失败，怎么办？

**A**:
1. 检查 log 文件找到具体错误
2. 使用验证脚本检查每个活动的 link ID
3. 在 transitSchedule/network 中确认 link 存在
4. 查看是否有 XML 语法错误

### Q5: 如何为多个 agents 创建旅程？

**A**:
```bash
# 使用脚本批量生成
for i in {1..10}; do
  cat agent-journey-template.xml | \
    sed "s/AGENT_ID/agent_$i/g" >> population.xml
done
```

### Q6: 我可以添加其他活动类型吗？

**A**: 是的，MATSim 支持多种活动类型：
- home, work, shopping, leisure, education, 等等

配置方法相同，只需改变 `type` 属性。


---

# MATSim Population.xml 快速參考卡

## 🎯 必要元素檢查清單

### ✅ 所有 Leg 必須包含：

```xml
<leg mode="[模式]" dep_time="HH:MM:SS" trav_time="HH:MM:SS">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">[模式]</attribute>
  </attributes>
  <route type="..." ... trav_time="HH:MM:SS" ...>...</route>
</leg>
```

---

## 📋 不同模式的 routingMode 值

| Leg Mode | routingMode 值 | 使用場景 |
|----------|---------------|---------|
| walk (接駁PT) | `"pt"` | PT 旅程的接駁步行 |
| walk (純步行) | `"walk"` | 純步行旅程 |
| pt | `"pt"` | 公共交通 |
| car | `"car"` | 汽車 |

---

## 🚶 Walk Leg 格式

### PT 接駁步行：
```xml
<leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" 
         trav_time="00:01:00" distance="50.0"></route>
</leg>
```

### 純步行：
```xml
<leg mode="walk" dep_time="07:45:00" trav_time="00:20:00">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">walk</attribute>
  </attributes>
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL03_UP" 
         trav_time="00:20:00" distance="1500.0"></route>
</leg>
```

---

## 🚇 PT Leg 格式

```xml
<leg mode="pt" dep_time="07:16:00" trav_time="00:27:55">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
  <route type="default_pt" 
         start_link="pt_BL02_UP" 
         end_link="pt_BL14_UP" 
         trav_time="00:27:55" 
         distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
</leg>
```

### PT Route JSON 必要欄位：
- ✅ `transitRouteId` - 路線 ID
- ✅ `boardingTime` - 上車時間
- ✅ `transitLineId` - 線路名稱
- ✅ `accessFacilityId` - 上車站點設施 ID
- ✅ `egressFacilityId` - 下車站點設施 ID

**格式範例：**
```json
{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}
```

⚠️ **注意：JSON 必須在同一行！**

---

## 🚗 Car Leg 格式

### Person 屬性：
```xml
<person id="car_1">
  <attributes>
    <attribute name="carAvail" class="java.lang.String">always</attribute>
  </attributes>
  <plan selected="yes">
    ...
  </plan>
</person>
```

### Car Leg：
```xml
<leg mode="car" dep_time="07:30:00" trav_time="00:06:15">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">car</attribute>
  </attributes>
  <route type="links" 
         start_link="10000" 
         end_link="100000" 
         trav_time="00:06:21" 
         distance="7201.46" 
         vehicleRefId="car_1">10000 119735 52071 ... 62785</route>
</leg>
```

### Car Route 必要屬性：
- ✅ `type="links"`
- ✅ `start_link` - 起點 link ID
- ✅ `end_link` - 終點 link ID
- ✅ `trav_time` - 旅行時間
- ✅ `distance` - 距離
- ✅ `vehicleRefId` - 車輛 ID（通常與 person ID 相同）

---

## 🔄 PT Interaction Activity 格式

```xml
<activity type="pt interaction" 
          link="pt_BL02_UP" 
          x="294035.05" 
          y="2762173.24" 
          max_dur="00:00:00" />
```

⚠️ **重要：PT 旅程結構**
```
home 
→ walk (routingMode="pt") 
→ pt interaction 
→ pt (routingMode="pt") 
→ pt interaction 
→ walk (routingMode="pt") 
→ work
```

---

## ⏰ 時間格式

所有時間必須使用 **HH:MM:SS** 格式：
- ✅ `07:15:00`
- ✅ `00:01:00`
- ✅ `17:30:00`
- ❌ `7:15` (錯誤)
- ❌ `1:00` (錯誤)

---

## 📍 座標和 Link

### Activity：
```xml
<activity type="home" 
          link="pt_BL02_UP"      ← 必須存在於網路中
          x="294035.05"          ← TWD97 座標
          y="2762173.24"         ← TWD97 座標
          end_time="07:15:00" />
```

### 注意事項：
- Link ID 必須在 network.xml 中存在
- 上行(UP)和下行(DN)要使用不同的 link
- x, y 座標應該接近對應的 link 位置

---

## 🎨 完整 PT 旅程範例

```xml
<person id="metro_1">
  <plan selected="yes">
    <!-- 1. 在家 -->
    <activity type="home" link="pt_BL02_UP" x="294035.05" y="2762173.24" end_time="07:15:00" />
    
    <!-- 2. 步行到站 -->
    <leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
      <attributes>
        <attribute name="routingMode" class="java.lang.String">pt</attribute>
      </attributes>
      <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" 
             trav_time="00:01:00" distance="50.0"></route>
    </leg>
    
    <!-- 3. 在站等待 -->
    <activity type="pt interaction" link="pt_BL02_UP" x="294035.05" y="2762173.24" max_dur="00:00:00" />
    
    <!-- 4. 乘坐PT -->
    <leg mode="pt" dep_time="07:16:00" trav_time="00:27:55">
      <attributes>
        <attribute name="routingMode" class="java.lang.String">pt</attribute>
      </attributes>
      <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" 
             trav_time="00:27:55" distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
    </leg>
    
    <!-- 5. 在站等待 -->
    <activity type="pt interaction" link="pt_BL14_UP" x="303804.19" y="2770590.71" max_dur="00:00:00" />
    
    <!-- 6. 步行到工作 -->
    <leg mode="walk" dep_time="07:43:55" trav_time="00:01:00">
      <attributes>
        <attribute name="routingMode" class="java.lang.String">pt</attribute>
      </attributes>
      <route type="generic" start_link="pt_BL14_UP" end_link="pt_BL14_UP" 
             trav_time="00:01:00" distance="50.0"></route>
    </leg>
    
    <!-- 7. 工作 -->
    <activity type="work" link="pt_BL14_UP" x="303804.19" y="2770590.71" end_time="17:00:00" />
    
    <!-- ... 回程類似 ... -->
  </plan>
</person>
```

---

## 🎨 完整 Car 旅程範例

```xml
<person id="car_1">
  <attributes>
    <attribute name="carAvail" class="java.lang.String">always</attribute>
  </attributes>
  <plan selected="yes">
    <!-- 1. 在家 -->
    <activity type="home" link="10000" x="300488.79" y="2769778.54" end_time="07:30:00" />
    
    <!-- 2. 駕車到工作 -->
    <leg mode="car" dep_time="07:30:00" trav_time="00:06:15">
      <attributes>
        <attribute name="routingMode" class="java.lang.String">car</attribute>
      </attributes>
      <route type="links" start_link="10000" end_link="100000" 
             trav_time="00:06:21" distance="7201.46" 
             vehicleRefId="car_1">10000 119735 52071 ... 62785</route>
    </leg>
    
    <!-- 3. 工作 -->
    <activity type="work" link="100000" x="305544.29" y="2770487.68" end_time="18:30:00" />
    
    <!-- ... 回程類似 ... -->
  </plan>
</person>
```

---

## ⚠️ 常見錯誤

| 錯誤 | 後果 | 修正 |
|------|------|------|
| 缺少 `<attributes>` 標籤 | MATSim 無法識別路由模式 | 為每個 leg 添加 attributes |
| 缺少 `trav_time` 屬性 | 無法計算旅行時間 | 為每個 route 添加 trav_time |
| PT JSON 不完整 | 無法追蹤上下車站點 | 添加 accessFacilityId 和 egressFacilityId |
| Car 缺少 `vehicleRefId` | 無法追蹤車輛 | 添加 vehicleRefId（通常與 person ID 相同） |
| Car 缺少 `carAvail` | MATSim 不知道代理人有車 | 在 person 添加 carAvail="always" |
| JSON 分行 | 可能解析錯誤 | 確保 JSON 在同一行 |
| 時間格式錯誤 | 解析失敗 | 使用 HH:MM:SS 格式 |

---

## 🔍 驗證檢查表

創建或修改 population.xml 時，請確認：

- [ ] 每個 leg 都有 `<attributes>` 和 `routingMode`
- [ ] 每個 route 都有 `trav_time` 屬性
- [ ] PT route 的 JSON 包含所有 5 個必要欄位
- [ ] Car route 有 `vehicleRefId`, `start_link`, `end_link`
- [ ] Car person 有 `carAvail` 屬性
- [ ] 所有時間都是 HH:MM:SS 格式
- [ ] 所有 link ID 存在於 network.xml 中
- [ ] PT 旅程有正確的 interaction activities
- [ ] 座標與 link 位置相符

---

## 實戰案例：修正 population.xml

下面的流程記錄了最近一次「從錯誤模板到可執行旅程」的完整思路，可作為排查參考。

### 1. 發現症狀與定位對象
- 開啟 `scenarios/equil/population.xml` 與 `tools/agent-journey-templates.xml` 對照，注意到模板內容直接被複製進人口檔，仍帶有「模板」註解與 `car_commuter_template_01` 等暫用 ID。
- 錯誤徵兆：缺少 `routingMode`、`trav_time`、PT JSON 欄位不完整，`carAvail` 與 `vehicleRefId` 也缺失。這些問題可在 MATSim 日誌或驗證腳本中被放大。

### 2. 收集正確資料
- 先鎖定旅程要用到的 link 和坐標，利用 `tools/find-nearest-stop.sh <x> <y>` 或直接查 `network-with-pt.xml.gz` 裡的 `<link>`。
- 針對汽車旅程，保留模板中現成的 link 序列，僅調整 person/vehicle ID 與活動時間即可。

### 3. 重建旅程計畫
- 以模板為骨架，逐段檢查並補齊以下要素：
  - `leg` 內的 `<attributes>` 與 `routingMode`
  - `route` 的 `trav_time`、`start_link`、`end_link`、距離與（汽車）`vehicleRefId`
  - PT `route` JSON：`transitRouteId`、`boardingTime`、`transitLineId`、`accessFacilityId`、`egressFacilityId`
- 給每個代理唯一的 person ID，例如 `metro_up_01`、`metro_down_01`、`car_commuter_01`，避免與模板名稱混淆。

### 4. 驗證並迭代
- 先跑工具驗證：
  ```bash
  ./tools/validate-agent-journey.sh \
      scenarios/equil/population.xml \
      scenarios/equil/network-with-pt.xml.gz \
      scenarios/equil/transitSchedule-mapped.xml.gz
  ```
  - 所有代理顯示 `✓` 即代表結構正確；若出現 `NaN` 距離或欄位缺失，根據輸出調整。
- 驗證通過後，執行模擬確認整體配置：
  ```bash
  ./mvnw -DskipTests exec:java \
      -Dexec.mainClass=org.matsim.project.RunMatsimApplication \
      -Dexec.args='run'
  ```
  - 觀察 `scenarios/equil/output` 內的行程統計與 `logfileWarningsErrors.log`，確認不再出現原先錯誤。

### 5. 寫回知識庫
- 將排錯心得補進本指南與 `population_explain.md`，維持模板、工具、流程三者的一致性。
- 建議在日後新增代理時重複上述驗證流程，確保 population.xml 保持高品質。

---

## 📚 相關文件

- 修正後的模板：`agent-journey-templates-FIXED.xml`
- 詳細修正說明：`修正說明.md`
- 成功範例：`population.xml`

---

## 💡 提示

1. **複製模板**：使用修正後的模板作為起點
2. **小步驟測試**：先用少量代理人測試
3. **檢查日誌**：查看 MATSim 的錯誤訊息
4. **保持一致**：確保所有代理人使用相同的格式
---
## 下一步

1. ✅ 使用这个指南定义你的 agents
2. ✅ 运行验证脚本检查有效性
3. ✅ 添加到 population.xml
4. ✅ 运行模拟并检查结果

---

**相关脚本和工具**:
- `ValidateAgentJourney.sh` - 验证脚本
- `find-nearest-node.sh` - 查询脚本
- `agent-journey-template.xml` - XML 模板

---

**最后更新**: 2025-11-03
**作者**: Claude Code (Anthropic)
