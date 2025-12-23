# Within-Day Replanning Module (待實作)

## 目的
此模組將實作災難發生時的動態路線重規劃功能。

## 預計功能
1. 災難警報觸發器 (DisasterAlertListener)
2. 疏散計畫修改器 (EvacuationPlanModifier)
3. 動態路線計算 (TripRouter integration)
4. 受損路段管理 (NetworkChangeEvents)

## 使用方式
```java
// 未來實作
Controler controler = ...;
controler.addOverridingModule(new EvacuationWithinDayModule());
```

## 參考
- matsim-code-examples/withinday
- docs/06-disaster-evacuation/evacuation-guide.md (文件 3)
