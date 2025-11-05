# Agent Journey Templates 修正說明

## 📋 修正日期：2025-11-03

---

## ❌ 原始模板的問題

對比成功執行的 `population.xml` 與原始的 `agent-journey-templates.xml`，發現以下問題：

### 1. **缺少 routingMode 屬性**
- **問題**：所有 leg 都缺少 `<attributes>` 標籤和 `routingMode` 屬性
- **影響**：MATSim 無法正確識別路由模式
- **範例**：
  ```xml
  ❌ 錯誤：
  <leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
    <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" distance="50.0" />
  </leg>

  ✅ 正確：
  <leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
    <attributes>
      <attribute name="routingMode" class="java.lang.String">pt</attribute>
    </attributes>
    <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" trav_time="00:01:00" distance="50.0"></route>
  </leg>
  ```

### 2. **Route 標籤缺少 trav_time 屬性**
- **問題**：所有 route 標籤都缺少必要的 `trav_time` 屬性
- **影響**：MATSim 無法正確計算旅行時間
- **範例**：
  ```xml
  ❌ 錯誤：
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" distance="50.0" />

  ✅ 正確：
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" trav_time="00:01:00" distance="50.0"></route>
  ```

### 3. **PT Route JSON 格式不完整**
- **問題**：PT route 的 JSON 缺少 `accessFacilityId` 和 `egressFacilityId`
- **影響**：MATSim 無法正確追蹤乘客的上下車站點
- **範例**：
  ```xml
  ❌ 錯誤：
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" distance="7646.14">
    {"transitLineId":"Blue","boardingTime":"07:16:08","transitRouteId":"403_1438_UP"}
  </route>

  ✅ 正確：
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" trav_time="00:27:55" distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
  ```

### 4. **Car Route 格式問題**
- **問題 A**：缺少 `vehicleRefId` 屬性
- **問題 B**：缺少 `start_link` 和 `end_link` 屬性
- **問題 C**：缺少 `trav_time` 屬性
- **影響**：MATSim 無法正確追蹤車輛
- **範例**：
  ```xml
  ❌ 錯誤：
  <leg mode="car" dep_time="07:30:00" trav_time="01:00:00">
    <route type="links" distance="50000.0">
      10000 10001 10002 10003
    </route>
  </leg>

  ✅ 正確：
  <leg mode="car" dep_time="07:30:00" trav_time="00:06:15">
    <attributes>
      <attribute name="routingMode" class="java.lang.String">car</attribute>
    </attributes>
    <route type="links" start_link="10000" end_link="100000" trav_time="00:06:21" distance="7201.46" vehicleRefId="car_1">10000 119735 52071 ... 62785</route>
  </leg>
  ```

### 5. **Car Person 缺少屬性**
- **問題**：Car person 沒有 `carAvail` 屬性
- **影響**：MATSim 無法知道代理人是否有車可用
- **範例**：
  ```xml
  ❌ 錯誤：
  <person id="car_commuter_template_01">
    <plan selected="yes">

  ✅ 正確：
  <person id="car_commuter_template_01">
    <attributes>
      <attribute name="carAvail" class="java.lang.String">always</attribute>
    </attributes>
    <plan selected="yes">
  ```

### 6. **JSON 格式問題**
- **問題**：JSON 內容分行，應該在同一行
- **影響**：可能導致解析錯誤
- **範例**：
  ```xml
  ❌ 錯誤：
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP">
    {"transitLineId":"Blue","boardingTime":"07:16:08",
     "transitRouteId":"403_1438_UP"}
  </route>

  ✅ 正確：
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" trav_time="00:27:55" distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
  ```

---

## ✅ 修正後的特點

### 1. 完整的 Leg 結構
所有 leg 都包含：
- `<attributes>` 標籤
- `routingMode` 屬性（值為 "pt", "car", 或 "walk"）
- 完整的 route 資訊（包含 trav_time）

### 2. 正確的 PT Route 格式
```xml
<route type="default_pt" 
       start_link="pt_BL02_UP" 
       end_link="pt_BL14_UP" 
       trav_time="00:27:55" 
       distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
```

### 3. 正確的 Car Route 格式
```xml
<route type="links" 
       start_link="10000" 
       end_link="100000" 
       trav_time="00:06:21" 
       distance="7201.46" 
       vehicleRefId="car_1">10000 119735 52071 ...</route>
```

### 4. 完整的 Person 屬性
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

---

## 📌 關鍵要點總結

| 項目 | 必要屬性 | 說明 |
|------|---------|------|
| **Walk Leg (PT用)** | routingMode="pt" | 用於 PT 旅程的接駁步行 |
| **Walk Leg (純步行)** | routingMode="walk" | 純步行旅程 |
| **PT Leg** | routingMode="pt" | 公共交通 |
| **Car Leg** | routingMode="car" | 汽車 |
| **All Routes** | trav_time | 旅行時間（HH:MM:SS 格式） |
| **PT Route** | accessFacilityId, egressFacilityId | 上下車站點設施 ID |
| **Car Route** | vehicleRefId, start_link, end_link | 車輛ID和起終點link |
| **Car Person** | carAvail="always" | 表示代理人有車可用 |

---

## 🎯 使用建議

1. **複製模板時**：確保複製完整的 XML 結構，包括所有屬性
2. **修改參數時**：只修改必要的值（ID、座標、時間等），保持結構不變
3. **驗證格式**：確保所有必要屬性都存在
4. **測試執行**：先用小規模測試，確認格式正確後再擴大規模

---

## 🔍 對比範例

### PT Commuter 完整對比

#### ❌ 原始錯誤版本（部分）：
```xml
<leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" distance="50.0" />
</leg>

<leg mode="pt" dep_time="07:16:00" trav_time="00:27:55">
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" distance="7646.14">
    {"transitLineId":"Blue","boardingTime":"07:16:08","transitRouteId":"403_1438_UP"}
  </route>
</leg>
```

#### ✅ 修正後正確版本：
```xml
<leg mode="walk" dep_time="07:15:00" trav_time="00:01:00">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
  <route type="generic" start_link="pt_BL02_UP" end_link="pt_BL02_UP" trav_time="00:01:00" distance="50.0"></route>
</leg>

<leg mode="pt" dep_time="07:16:00" trav_time="00:27:55">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
  <route type="default_pt" start_link="pt_BL02_UP" end_link="pt_BL14_UP" trav_time="00:27:55" distance="7646.14">{"transitRouteId":"403_1438_UP","boardingTime":"07:16:08","transitLineId":"Blue","accessFacilityId":"BL02_UP.link:pt_BL02_UP","egressFacilityId":"BL14_UP.link:pt_BL14_UP"}</route>
</leg>
```

---

## 📚 參考文件

根據 MATSim 文件 Chapter 12.6：
> "Interaction activities (in the Java code called 'stage' activities) are inserted between legs. 
> There is also functionality to extract trips: TripStructureUtils.getTrips(...). 
> The current convention is to attach such information to all legs of a trip, 
> and to warn or abort if that information has become inconsistent between the legs of a trip."

這解釋了為什麼 routingMode 屬性對於每個 leg 都是必要的。

---

## 📝 修正清單

- [x] 所有 leg 添加 routingMode 屬性
- [x] 所有 route 添加 trav_time 屬性
- [x] PT route 添加完整 JSON 格式（包含 accessFacilityId 和 egressFacilityId）
- [x] Car route 添加 vehicleRefId 屬性
- [x] Car route 添加 start_link 和 end_link 屬性
- [x] Car person 添加 carAvail 屬性
- [x] 修正 JSON 格式（確保在同一行）
- [x] 添加下行方向（DN）的 PT 模板
- [x] 更新所有模板的中文註釋

---

## ⚠️ 常見錯誤提醒

1. **忘記添加 attributes 標籤**：每個 leg 都需要！
2. **忘記添加 trav_time**：每個 route 都需要！
3. **PT JSON 不完整**：必須包含 accessFacilityId 和 egressFacilityId
4. **vehicleRefId 不一致**：建議使用 person ID 作為 vehicleRefId
5. **時間格式錯誤**：必須是 HH:MM:SS 格式（例如：07:15:00）

---

## 🎉 結論

修正後的模板已經包含所有必要的屬性和格式，可以直接用於 MATSim 模擬。建議使用修正後的 `agent-journey-templates-FIXED.xml` 作為創建新代理人旅程的參考。