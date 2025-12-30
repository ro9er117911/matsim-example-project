# 快速開始

## 建置與執行

```bash
./mvnw clean package

# GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# 指定場景
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/corridor/taipei_test/config.xml
```

## 測試

```bash
./mvnw test
./mvnw test -Dtest=RunMatsimTest
```

## 專案結構

```
matsim-example-project/
├── src/main/java/               # Java 主程式與工具
├── src/main/python/             # Python 工具
├── scenarios/                   # 場景設定檔
├── pt2matsim/                   # GTFS 轉換工具
├── docs/                        # 文件
└── output/                      # 模擬輸出
```

## 延伸閱讀

- `docs/01-getting-started/architecture-overview.md`
- `docs/02-osm-network/network-guide.md`
- `docs/03-gtfs-public-transit/public-transit-guide.md`
- `docs/04-population/population-guide.md`
- `docs/08-configuration/configuration-reference.md`
