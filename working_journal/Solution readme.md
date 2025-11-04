# MATSim 捷運與汽車路網顯示問題解決方案

## 問題診斷

### 您遇到的問題：
1. **捷運和汽車代理人都不照著路網走**
2. **汽車代理人沒有顯示汽車標籤**
3. **ClassCastException 錯誤**

### 根本原因：
**您的 PT（公共運輸）被設定為 teleportation 模式**，導致代理人直接「傳送」而非實際搭乘。

## 解決方案

### 1. 核心問題修正

#### ❌ 錯誤設定（您原本的 config.xml）：
```xml
<parameterset type="teleportedModeParameters">
    <param name="mode" value="pt"/>
    <param name="teleportedModeSpeed" value="8.33"/> 
</parameterset>
```

#### ✅ 正確設定：
**完全移除 PT 的 teleportedModeParameters！** PT 應該由 SwissRailRaptor 處理，不是 teleportation。

### 2. 關鍵配置要點

| 設定項目 | 正確值 | 說明 |
|---------|--------|------|
| `transit.useTransit` | `true` | 啟用公共運輸模組 |
| `transit.usingTransitInMobsim` | `true` | 在模擬中使用公共運輸 |
| `qsim.mainMode` | `"car"` | **不包含 pt** |
| `qsim.vehiclesSource` | `"defaultVehicle"` | 為汽車自動創建車輛 |
| `routing.networkModes` | `"car"` | PT 不是 network mode |

### 3. 捷運路網映射

因為您的捷運是「虛擬路網」，需要映射到實際路網：

#### A. 確保 Transit Schedule 包含路網路徑
```xml
<transitRoute id="route1">
    <transportMode>rail</transportMode>
    <routeProfile>
        <stop refId="station1" departureOffset="00:00:00"/>
        <stop refId="station2" departureOffset="00:05:00"/>
    </routeProfile>
    <route>
        <!-- 重要：必須有實際的路網連結序列 -->
        <link refId="link123"/>
        <link refId="link124"/>
        <link refId="link456"/>
    </route>
</transitRoute>
```

#### B. 確保站點連結到路網
```xml
<stopFacility id="station1" x="1000" y="2000" linkRefId="link123"/>
<!--                                            ^^^^^^^^^^^^^^^^ 必須有這個 -->
```

### 4. 使用提供的工具

#### 檔案說明：

1. **fixed_config.xml** - 修正後的配置檔案
2. **RunMatsimWithTransit.java** - 確保 Transit 正確載入的執行檔
3. **TransitNetworkMapper.java** - 將虛擬站點映射到路網的工具
4. **diagnose_transit.sh** - 診斷腳本，檢查配置問題

### 5. 執行步驟

```bash
# 1. 診斷當前配置
bash diagnose_transit.sh

# 2. 如果需要映射捷運路網
java -cp matsim.jar org.matsim.project.TransitNetworkMapper

# 3. 執行修正後的模擬
java -cp matsim.jar org.matsim.project.RunMatsimWithTransit fixed_config.xml
```

### 6. 視覺化設定（讓汽車顯示標籤）

在 OTFVis 中確保：
```xml
<module name="otfvis">
    <param name="agentSize" value="120.0"/>
    <param name="showTeleportedAgents" value="false"/>
    <param name="drawTransitFacilities" value="true"/>
</module>
```

## 回答您的具體問題

### Q：我一定要給完整 link 才能顯示嗎？

**答：是的！** 對於非 teleportation 模式：
- **汽車**：需要完整的路網連結序列（通常由路由器自動生成）
- **捷運**：Transit 路線必須包含 `<route>` 標籤，列出所有經過的連結

### Q：捷運是虛擬路網，如何顯示路徑？

**答：使用路網映射工具**
1. 使用 `PublicTransitMapper` 或我提供的 `TransitNetworkMapper.java`
2. 將站點映射到最近的路網連結（linkRefId）
3. 生成站點間的路網路徑
4. 這樣捷運車輛就會沿著實際路網移動

## 常見錯誤檢查清單

- [ ] PT 不應在 `teleportedModeParameters` 中
- [ ] PT 不應在 `mainMode` 中
- [ ] PT 不應在 `networkModes` 中
- [ ] Transit Schedule 必須有 `<route>` 標籤
- [ ] 站點必須有 `linkRefId` 屬性
- [ ] `useTransit` 必須為 `true`

## 預期結果

修正後，您應該看到：
1. ✅ 汽車代理人沿著路網行駛，有汽車圖標
2. ✅ 捷運列車沿著指定路線行駛
3. ✅ 乘客在站點等車、上車、下車
4. ✅ 沒有 ClassCastException 錯誤

## 需要進一步協助？

如果問題仍然存在，請檢查：
1. `transitSchedule-mapped.xml.gz` 是否包含 `<route>` 標籤
2. 執行 `diagnose_transit.sh` 的輸出
3. 確認所有站點都有對應的 `linkRefId`