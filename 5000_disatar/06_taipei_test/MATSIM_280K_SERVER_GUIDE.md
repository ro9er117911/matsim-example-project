# MATSim 280k Server 設定指南

## 關鍵修改摘要

### 1. pom.xml 重要依賴

```xml
<parent>
    <groupId>org.matsim</groupId>
    <artifactId>matsim-all</artifactId>
    <version>2025.0</version>  <!-- 使用最新版 -->
</parent>

<!-- 修復 exec:java 缺少 CaseFormat 問題 -->
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
    <version>33.3.0-jre</version>
</dependency>

<!-- SimWrapper 可視化 -->
<dependency>
    <groupId>org.matsim.contrib</groupId>
    <artifactId>simwrapper</artifactId>
    <version>${matsim.version}</version>
</dependency>

<!-- pt2matsim 處理公車/捷運 -->
<dependency>
    <groupId>org.matsim</groupId>
    <artifactId>pt2matsim</artifactId>
    <version>25.12</version>
</dependency>
```

---

### 2. RunMatsim.java 關鍵修改

```java
// 1. 清除包含冒號的 attribute (Avro/SimWrapper 相容)
for (Link link : scenario.getNetwork().getLinks().values()) {
    for (String key : link.getAttributes().getAsMap().keySet().toArray(new String[0])) {
        if (key.contains(":")) {
            link.getAttributes().removeAttribute(key);
        }
    }
}

// 2. NetworkCleaner 修復斷開的路段
new NetworkCleaner().run(scenario.getNetwork());

// 3. SimWrapperModule 生成可視化
controler.addOverridingModule(new SimWrapperModule());
```

---

### 3. config_taipei_280k.xml 關鍵設定

```xml
<!-- 路網：需要 PT Mapping 後的版本 -->
<param name="inputNetworkFile" value="combined_network_pt.xml.gz" />

<!-- Transit 設定 -->
<module name="transit">
    <param name="useTransit" value="true" />
    <param name="transitScheduleFile" value="transitSchedule_mapped.xml.gz" />
    <param name="vehiclesFile" value="transitVehicles.xml" />
    <param name="usingTransitInMobsim" value="true" />
</module>

<!-- Routing 設定 -->
<module name="routing">
    <param name="networkRouteConsistencyCheck" value="disable" />
</module>
```

---

## Server 執行步驟

### Step 1: 確認 Java 21+
```bash
java -version  # 需要 21+
```

### Step 2: 建置專案 (在專案根目錄)
```bash
cd matsim-example-project
./mvnw clean compile
```

### Step 3: 執行模擬
```bash
./mvnw exec:java \
    -Dexec.mainClass="org.matsim.project.RunMatsim" \
    -Dexec.args="5000_disatar/06_taipei_test/config_taipei_280k.xml" \
    -Djava.awt.headless=true \
    -Dexec.classpathScope="compile"
```

### 或使用 JAR (如果已打包)
```bash
java -Xmx32G -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    5000_disatar/06_taipei_test/config_taipei_280k.xml
```

---

## 常見問題

| 問題 | 解決方案 |
|------|----------|
| `CaseFormat` not found | 確認 guava 33.3.0-jre 在 pom.xml |
| Network disconnected | RunMatsim 已包含 NetworkCleaner |
| SimWrapper 錯誤 | 設定 `DISABLE_SIMWRAPPER=1` 環境變數 |
| PT routing 失敗 | 確認使用 `*_mapped.xml.gz` 檔案 |
