# Motorcycle 模式整合指南

本文件整理 motorcycle 模式的啟用方式、設定重點與驗證流程。

---

## 一、兩種啟用策略

### 策略 A：走路網（真實路由）
適用於已在 network 中加入 `motorcycle` mode 的情境。

**必要條件**：
- network 的 links 包含 `motorcycle` mode
- `routing.networkModes` 包含 `motorcycle`
- `qsim.mainMode` 包含 `motorcycle`

### 策略 B：teleported（快速可用）
適用於網路尚未補齊 `motorcycle` links 的情境。

**必要條件**：
- `routing.networkModes` 不包含 `motorcycle`
- 在 `teleportedModeParameters` 加入 `motorcycle`

---

## 二、設定檔重點（config.xml）

### 策略 A 範例
```xml
<module name="routing">
  <param name="networkModes" value="car,motorcycle"/>
</module>

<module name="qsim">
  <param name="mainMode" value="car,motorcycle"/>
</module>
```

### 策略 B 範例
```xml
<module name="routing">
  <param name="networkModes" value="car"/>
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="motorcycle"/>
    <param name="teleportedModeSpeed" value="12.0"/>
    <param name="beelineDistanceFactor" value="1.3"/>
  </parameterset>
</module>
```

---

## 三、執行與驗證

```bash
./mvnw clean package -DskipTests
java -Xmx4g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar <config.xml>
```

`<config.xml>` 必須包含 motorcycle 的 routing 或 teleported 設定。

驗證：

```bash
grep motorcycle output/modestats.csv
zcat output/ITERS/it.0/0.events.xml.gz | grep -c motorcycle
```

---

## 四、常見問題

### 1) `Network does not contain any links for mode motorcycle`
- **原因**：network 中沒有 motorcycle mode
- **解法**：改用策略 B，或重新生成 network

### 2) 模擬過慢或記憶體不足
- **解法**：降低 iterations 或提高 `-Xmx` 記憶體
