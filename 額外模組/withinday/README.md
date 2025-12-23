# WithinDay Replanning 模組

## 概述

此模組包含 MATSim 的 WithinDay Replanning 功能，用於模擬中動態重新規劃 agent 路線。

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `RunEvacuationWithWithinDay.java` | WithinDay 模擬進入點 |
| `TsunamiWithinDayModule.java` | 海嘯 WithinDay 模組設定 |
| `TsunamiReplanningListener.java` | 重規劃事件監聽器 |
| `RunEvacuationWithReplan.java` | 重規劃模擬進入點 |

## 使用方式

若要啟用此模組，需將 java 檔案複製回 `src/main/java/org/matsim/project/evacuation/` 目錄後重新建置。

```bash
cp java/*.java ../src/main/java/org/matsim/project/evacuation/
./mvnw clean package
```

## 注意事項

- 此模組為實驗性功能
- WithinDay Replanning 會增加計算負擔
- 建議先用標準模式測試後再啟用
