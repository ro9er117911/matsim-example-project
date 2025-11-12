# 下週執行計劃摘要 - Weekly Execution Summary

**Week:** 2025-11-05 ~ 2025-11-09
**Status:** ✅ 分析完成，等待執行 (Analysis Complete, Ready for Execution)
**Total Effort:** ~6-8 小時
**Complexity:** 🟡 中等 (Medium)

---

## 🎯 核心問題 (3 個)

### ❌ 問題 1：走路時間超限
- **現象：** 許多代理用走路，超過合理時間
- **改進：** MAX_WALK_DURATION_MIN：30 → **20 分鐘**
- **檔案：** 2 個（generate, validate）
- **時間：** 1-2 小時

### ❌ 問題 2：汽車代理在 OSM 範圍外
- **現象：** 汽車代理「直接走路在不存在的地圖上」
- **改進：** 驗證並調整 OSM_BOUNDS 邊界
- **檔案：** 1-2 個
- **時間：** 1-2 小時

### ❌ 問題 3：PT 代理不使用轉運
- **現象：** PT 代理直接走路而不用公共運輸
- **改進：**
  - 使用有效的停靠點 link ID（非座標）
  - 補全缺失的 10 個轉運代理（現在只有 6 個）
- **檔案：** 2-3 個
- **時間：** 2-4 小時

---

## 📋 分 4 個執行階段 (Four Phases)

### Phase 1️⃣：走路時間限制 (1-2 小時)
```bash
# 修改兩個檔案
src/main/python/generate_test_population.py (line 264): 30 → 20
src/main/python/validate_population.py (line 217): 30 → 20

# 重新生成並驗證
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' python generate_test_population.py
python validate_population.py scenarios/equil/test_population_50.xml

# 提交
git commit -m "Phase 1: Reduce max walk duration to 20 minutes"
```

**預期結果：**
- ✓ 轉運代理可能減少（因走路時間）
- ✓ 總代理：50 → ? (檢查結果)
- ✓ 驗證通過，0 個錯誤

---

### Phase 2️⃣：OSM 邊界驗證 (1-2 小時)
```bash
# 1. 檢查網絡邊界
gunzip -c scenarios/equil/network-with-pt.xml.gz | grep -E 'x=|y=' | head -20

# 2. 比對 OSM_BOUNDS（line 71-80）
# 檢查是否需要擴大邊界以包含 BL02, BL06

# 3. 調整邊界（如需要）
# 重新生成人口

# 4. 驗證汽車代理都在邊界內
python validate_population.py scenarios/equil/test_population_50.xml | grep "outside"
# 應該看不到任何邊界外代理

# 提交
git commit -m "Phase 2: Verify and adjust OSM bounds"
```

**預期結果：**
- ✓ OSM 邊界已驗證或調整
- ✓ 汽車有效站點：32 → ? (應該增加)
- ✓ 0 個邊界外錯誤

---

### Phase 3️⃣：PT 轉運深度修復 (2-4 小時) ⭐ 最重要
```bash
# 1. 提取實際停靠點 ID（從 transitSchedule-mapped.xml.gz）
# 2. 建立 PT_STOP_MAPPING（48 個站點）
# 3. 修改 generate_pt_agent() 函數
#    - 座標 (x, y) → link ID (pt_STATION_UP)
# 4. 修改 generate_transfer_pt_agent() 函數（同樣改動）
# 5. 調查缺失的 4 個轉運代理
#    - 提高 PT 速度模型：500 → 550 m/min
#    - 或降低轉運等待時間
# 6. 重新生成人口，確保 10 個轉運代理全部生成

# 驗證
python validate_population.py scenarios/equil/test_population_50.xml | grep "pt_transfer"
# 應該看到 10 個轉運代理

# 提交
git commit -m "Phase 3: Fix PT transfer agents and use proper stop facility IDs"
```

**預期結果：**
- ✓ 所有 PT 活動使用 link ID（不是座標）
- ✓ 轉運代理：6 → **10 個**（全部生成）
- ✓ 0 個缺失代理

---

### Phase 4️⃣：整體驗證與測試 (1-2 小時)
```bash
# 1. 完整驗證
python validate_population.py scenarios/equil/test_population_50.xml
# 應該看到：Total Errors: 0, 50 agents

# 2. 構建項目
./mvnw clean package

# 3. 運行短期模擬（2 次迭代）
cd scenarios/equil/
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.lastIteration 2 \
  --config:controller.snapshotFormat null

# 4. 檢查結果
cd output/
head -6 scorestats.csv       # 代理分數應該逐次改善
head -6 modestats.csv        # PT 腿應該 > 60（不是走路回退）
grep "ClassCastException" ../logfile.log  # 應該找不到

# 5. Via 導出
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events --out forVia --dt 5

# 提交
git commit -m "Phase 4: Complete validation and testing - all improvements verified"
```

**預期結果：**
- ✓ 驗證 100% 通過（0 個錯誤）
- ✓ 模擬成功（無 ClassCastException）
- ✓ 代理分數逐次改善
- ✓ PT 代理使用公共運輸
- ✓ Via 導出成功

---

## 📂 詳細文檔位置

已為你創建兩份詳細文檔，可以下週直接參考：

| 文檔 | 路徑 | 用途 |
|------|------|------|
| **改進計劃** | `working_journal/2025-11-05-Population-Improvements.md` | 問題分析、根本原因、改進方案 |
| **執行 TODO** | `working_journal/2025-11-05-Population-Improvements-TODO.md` | 逐步 checklist、命令行、預期輸出 |

**推薦使用方式：**
1. **下週一早上：** 閱讀 `Population-Improvements.md` 瞭解全貌
2. **執行過程中：** 參考 `Population-Improvements-TODO.md` 逐步操作
3. **卡住時：** 檢查「預期輸出」部分找出問題

---

## ✅ 成功標準 (Success Criteria)

完成後應該達到：

| 指標 | 目標 | 當前 | 改進後 |
|------|------|------|--------|
| 走路腿時間上限 | < 20 min | 30 min | ✓ 20 min |
| 汽車代理邊界 | 100% 在內 | ? | ✓ 100% |
| PT 停靠點格式 | link ID | x,y 座標 | ✓ link ID |
| 轉運代理 | 10 個 | 6 個 | ✓ 10 個 |
| 驗證錯誤 | 0 | ? | ✓ 0 |
| 模擬成功 | ✓ | 未測 | ✓ 通過 |
| PT 使用率 | 高 | 低（走路） | ✓ 高 |

---

## ⏰ 時間規劃

```
Monday   (11-05): 分析完成 ✓ 這就是今天的工作
Tuesday  (11-06): Phase 1 + Phase 2 (2-4 小時)
Wednesday(11-07): Phase 3 (2-4 小時) - 可能最複雜
Thursday (11-08): Phase 3 完成 + Phase 4 (1-2 小時)
Friday   (11-09): 完成驗證，提交最終版本
```

---

## 🚨 關鍵風險與注意

### ⚠️ Risk 1: PT 停靠點 ID 映射
- **風險：** 48 個站點的 link ID 映射容易出錯
- **緩解：** 逐個驗證，使用 grep 檢查 XML 格式
- **測試：** 驗證至少 5 個不同的 PT 代理

### ⚠️ Risk 2: 轉運時間估計
- **風險：** 調整速度模型後轉運代理數可能仍不足
- **緩解：** 有備用方案（降低等待時間或提高時間上限）
- **測試：** 檢查所有 10 個轉運路由的時間

### ⚠️ Risk 3: 模擬失敗
- **風險：** 新的 link ID 格式可能與配置不兼容
- **緩解：** Phase 4 中有短期模擬測試
- **恢復：** 如果失敗，可回退到上一個提交

---

## 📝 提交消息範本

已為每個 phase 準備好提交消息，直接在 TODO 文檔中找到。格式統一：

```
Phase X: [簡短描述]

Changes:
- [修改 1]
- [修改 2]

Result:
- [結果 1] ✓
- [結果 2] ✓
- [數字統計]

🤖 Generated with Claude Code
```

---

## 🎓 學習要點

完成這個計劃後，你會學到：

1. **MATSim 人口格式** - 代理活動、路由、轉運結構
2. **PT 停靠點映射** - 如何連接人口到轉運網絡
3. **空間約束驗證** - OSM 邊界、座標系統
4. **時間估計模型** - 距離、速度、開銷時間
5. **模擬除錯** - 日誌分析、統計檢查

---

## 🎯 最終檢查清單

下週開始執行時：

- [ ] 閱讀 `2025-11-05-Population-Improvements.md`
- [ ] 準備終端機環境
- [ ] 打開 `2025-11-05-Population-Improvements-TODO.md`
- [ ] Phase 1 開始執行
- [ ] 每個 phase 後提交一次
- [ ] 遇到問題時參考「預期輸出」部分
- [ ] Friday 提交最終版本

---

**Ready for Next Week! 💪**

*Analysis completed: 2025-11-05*
*Execution window: 2025-11-05 ~ 2025-11-09*
*Estimated completion: Friday 2025-11-09*

---

💾 **All files committed to git** (commit 9b28bfd)
📚 **Full documentation available** in working_journal/
🚀 **Ready to execute anytime!**
