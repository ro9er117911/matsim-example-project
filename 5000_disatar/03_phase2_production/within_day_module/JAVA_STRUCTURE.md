# 預計 Java 類別結構

```
src/main/java/org/matsim/project/evacuation/
├── RunEvacuationSimulation.java      # 主入口
├── EvacuationWithinDayModule.java    # Guice 模組
├── DisasterAlertListener.java        # MobsimBeforeSimStepListener
├── EvacuationPlanModifier.java       # 計畫修改邏輯
├── SafeZoneManager.java              # 安全區域管理
└── NetworkDamageManager.java         # 路網損壞管理
```
