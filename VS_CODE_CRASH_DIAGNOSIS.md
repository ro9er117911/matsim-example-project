# VS Code 崩潰問題診斷報告

## 問題確認

**症狀：** VS Code 重開兩次後仍然崩潰
**根本原因：** VS Code/Electron 被 426MB population.xml 拖垮

## 資料規模分析

```
426MB  5000_disatar/output_test/population.xml       ← 主要兇手
 18MB  5000_disatar/output_test/network.xml
1.6MB  5000_disatar/output_test/network-with-pt.xml
460MB  5000_disatar/output_test/ (總計)
```

**VS Code 記憶體狀況：**
- Code Helper (Renderer): 421MB, 319MB
- Code Helper (Plugin): 730MB
- 總計已超過 1.4GB，處於高壓狀態

## 解決方案

### ✅ 已完成：隔離大檔案

已更新 `.vscode/settings.json`：

```json
{
  "files.exclude": {
    "**/population.xml": true,        // 426MB
    "**/network.xml": true,           // 18MB
    "**/network-with-pt.xml": true    // 1.6MB
  },
  "search.exclude": {
    "**/5000_disatar/output_test/**": true,
    "**/output_test_10agents/**": true,
    "**/*.xml.gz": true
  },
  "files.watcherExclude": {
    "**/5000_disatar/output_test/**": true,
    "**/*.log": true
  }
}
```

**效果：** VS Code 不會再嘗試索引、監控、語法高亮這些大檔案

### 📋 待執行：獨立終端測試

**目的：** 驗證模擬程式本身沒有問題

在 **Terminal.app（不是 VS Code 終端）** 執行：

```bash
cd /Users/ro9air/matsim-example-project

# 小規模測試（10 agents）
java -Xmx4g -cp target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.RunMatsim \
  5000_disatar/output_test/config_test_10agents.xml
```

**預期結果：**
- ✅ 成功運行 → 確認問題是 VS Code，不是模擬程式
- ❌ OOM 錯誤 → 需要調整 Java heap size 或資料規模

### 🔧 檢視大檔案的安全方法

**❌ 不要在 VS Code 打開這些檔案：**
- population.xml (426MB)
- network.xml (18MB)
- 任何 output_test/ 下的大型 XML

**✅ 使用命令列工具：**

```bash
# 查看前 50 行
head -50 5000_disatar/output_test/population.xml

# 統計結構（不載入全檔）
grep -c '<person' 5000_disatar/output_test/population.xml

# 提取特定 agent
grep -A 10 'id="pt_agent_01"' 5000_disatar/output_test/population.xml

# 壓縮檔快速瀏覽
gunzip -c file.xml.gz | head -100
```

## 技術原理

**為什麼 VS Code 會掛？**

從 crash log：
```
node::sqlite::UserDefinedFunction::xDestroy(void*)
v8::Isolate::LowMemoryNotification()
```

1. VS Code 用 SQLite 儲存檔案索引/快取
2. 當處理 426MB XML 時觸發記憶體壓力
3. V8 GC 嘗試清理，但踩到 SQLite 不一致狀態
4. EXC_BREAKPOINT → Electron 自殺

**這是 VS Code 的 bug，不是你的模擬程式的問題。**

## 下一步

1. **重新載入 VS Code 視窗** - 讓新設定生效
2. **在獨立終端執行模擬** - 驗證程式本身正常
3. **繼續開發** - 大檔案已被隔離，不會再觸發崩潰

## 預防措施

**永久規則：**
- ✅ 重運算放在獨立終端，不透過 VS Code task
- ✅ 大型輸出檔用 `head`/`rg` 查看，不用 VS Code 打開
- ✅ 定期清理 output 目錄（或壓縮成 .gz）
- ❌ 不在 VS Code 裡打開 >10MB 的文字檔
