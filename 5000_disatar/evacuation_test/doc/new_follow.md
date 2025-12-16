TL;DR：以官方「海嘯溢淹潛勢圖」定義淡水危險區（溢淹水深 > 0 的所有區塊），裁切到淡水行政區後輸出一份 polygon（可含多面），再用同一份 polygon 算出中心點（centroid）、面積（km²）與受影響人口（疊村里人口或網格人口），最後把 polygon 丟進撤離 GUI 作為 evacuation area。

---

## 1) 海嘯撤離在 MATSim 該怎麼被「正確地」建模

### 1.1 災害本體（hazard）

採用「海嘯溢淹潛勢圖」而不是憑想像畫圈：該圖資是把多組海嘯模擬結果取最大溢淹水深，並以地形高程推得溢淹深度，用於產製潛勢地圖。 ([dmap.ncdr.nat.gov.tw][1])
圖上通常會分級（0–0.3m、0.3–1m、1–3m、>3m）。 ([dmap.ncdr.nat.gov.tw][2])

### 1.2 人的行為（demand）

海嘯撤離的關鍵不是「起終點」，而是「警報 → 反應延遲 → 出門時間分佈」。你要把出發時間當成分佈（包含不撤離者比例），否則只是在跑一個同時出發的交通指派。

### 1.3 路網與可用性（supply）

海嘯的道路失效是「時間敏感」：某些 link 在某個時間後變不可用（淹到/被封控/逆向車流）。如果你的 GUI 模組不支援 time-dependent closure，至少要用保守做法：把危險區內的 link 視為在某個 cut-off time 後不可通行（用 scenario copy 做兩段式，或在前處理把危險區內低洼路段直接排除，讓撤離路徑自然遠離）。

---

## 2) 危險區（Hazard Zone）要怎麼設定

### 2.1 定義（單一、可稽核）

危險區 = 官方海嘯溢淹潛勢圖中「溢淹水深 > 0」的所有面，裁切到「新北市淡水區」行政界。圖資可在 NCDR 的災害潛勢地圖/資料集體系查詢與下載（常見為 shp/kml）。 ([datahub.ncdr.nat.gov.tw][3])

### 2.2 你要的三個數字怎麼得到（中心點 / 範圍 / 人數）

這三個數字必須由「危險區 polygon」計算，禁止用主觀猜測，否則模型輸出不可用於任何決策溝通。

下面給一個可重現、可驗收的最小流程：你只要把下載到的圖資路徑填上，直接跑出你要的結果（含多面、多安全區支援）。

#### (A) 安裝

```bash
python -m pip install --upgrade pip
python -m pip install geopandas shapely pyproj rtree pandas
```

#### (B) 計算中心點/面積/受影響人口（可用村里人口做近似）

你需要三份資料：

1. 海嘯溢淹潛勢圖（shp；含水深分級欄位）
2. 淡水區行政界（shp）
3. 村里界 + 村里人口（shp + csv；用村里代碼 join）

```python
# tsunami_metrics.py
import geopandas as gpd
import pandas as pd

TSUNAMI_SHP = "data/tsunami_inundation.shp"      # 待補：NCDR 下載的 shp
ADMIN_SHP   = "data/admin_tamsui.shp"           # 待補：淡水區界 shp
VILL_SHP    = "data/village.shp"                # 待補：村里界 shp
VILL_POPCSV = "data/village_population.csv"     # 待補：欄位至少含 village_id,pop

# 1) 讀取並統一座標系（先轉到等積投影算面積；台灣常用 TWD97 / TM2 121 = EPSG:3826）
tsu = gpd.read_file(TSUNAMI_SHP)
adm = gpd.read_file(ADMIN_SHP).to_crs(epsg=3826)
tsu = tsu.to_crs(epsg=3826)

# 2) 過濾「溢淹水深 > 0」
# 待補：把 depth 欄位名改成你的 shp 真實欄位（例如 'depth_m' 或 'CLASS'）
# 這裡假設 'depth_m' 是連續值（公尺）；若是分級字串，改成用類別表達式
depth_col = "depth_m"  # 待補
tsu = tsu[tsu[depth_col] > 0].copy()

# 3) 裁切到淡水區、溶解成單一/多個面（危險區可為 MultiPolygon）
haz = gpd.overlay(tsu, adm, how="intersection")
haz = haz.dissolve()  # 變成一筆 MultiPolygon

# 4) 中心點（以 centroid；若要落在面內改 representative_point）
haz_centroid = haz.geometry.centroid.iloc[0]
# 轉回 WGS84 給 GUI/文件用
haz_wgs84 = gpd.GeoSeries([haz_centroid], crs=3826).to_crs(epsg=4326).iloc[0]

# 5) 面積（km^2）
haz_area_km2 = haz.geometry.area.iloc[0] / 1_000_000

# 6) 人口：村里疊圖，按「村里面積被淹比例」分攤人口（保守近似）
vill = gpd.read_file(VILL_SHP).to_crs(epsg=3826)
pop = pd.read_csv(VILL_POPCSV)
# 待補：村里代碼欄位名一致化
vill_id_col = "village_id"  # 待補
vill = vill.merge(pop, on=vill_id_col, how="left")

inter = gpd.overlay(vill, haz.reset_index(drop=True), how="intersection")
inter["inter_area"] = inter.geometry.area
vill["vill_area"] = vill.geometry.area
inter = inter.merge(vill[[vill_id_col, "vill_area", "pop"]], on=vill_id_col, how="left")
inter["pop_imp"] = inter["pop"] * (inter["inter_area"] / inter["vill_area"])
haz_pop_est = inter["pop_imp"].sum()

print("Hazard centroid (WGS84):", (haz_wgs84.y, haz_wgs84.x))  # (lat, lon)
print("Hazard area (km^2):", haz_area_km2)
print("Affected population (est.):", round(haz_pop_est))
```

驗收標準（跑完必須出現三行數字）：

* centroid 輸出為 (lat, lon) 且落在淡水區附近
* area_km2 > 0
* affected population 為非負整數（若為 NaN 表示村里人口 join 失敗）

---

## 3) 危險區中心點座標 / 範圍 / 人數：可用的「基準數」

你可以先把「淡水區總人口」當上限基準，用於 sanity check：淡水區戶籍人口在 114 年 11 月為 207,477。 ([新北市政府][4])
真正「海嘯危險區人口」以你上面疊圖結果為準（它會小於等於 207,477）。

---

## 4) 安全區怎麼設定、能不能多個

### 4.1 政策定義（你要拿來寫在文件裡的那句話）

安全區 = 「海拔 10 公尺以上」且「非海嘯潛勢區」的鄰近高地或建築量體（含大樓）。 ([dsc.ntpc.gov.tw][5])

### 4.2 工程落地（丟進 GUI 的資料形態）

* 可以設定多個安全區：做法是把多個安全 polygon 放在同一個 shapefile/geojson 裡（多筆 feature 或 MultiPolygon 都可）。
* GUI 模組若採「離開危險區即算完成撤離」，則安全區不必畫；以危險區邊界作為 completion boundary。
* GUI 模組若要求「指定 shelters」，就把每個安全區內的 shelter 點（或面）做成一個圖層，讓代理人目的地在這些 shelter 之間抽樣。

---

## 5) 你這張圖的情境化（淡水海嘯撤離到文山）

你的路網已涵蓋大台北盆地，但海嘯撤離的路網裁切不能用行政區矩形，要用「危險區 ∪（目的安全區）∪（兩者之間走廊）」的 union polygon 去切 OSM，否則你會遺失關鍵替代路徑、或保留大量無關路段導致計算與視覺化成本暴增。

[1]: https://dmap.ncdr.nat.gov.tw/1109/disaster-topics/%E6%B5%B7%E5%B2%B8%E7%81%BD%E5%AE%B3-%E6%B5%B7%E5%98%AF%E6%BA%A2%E6%B7%B9/?utm_source=chatgpt.com "海岸災害海嘯溢淹 - 3D災害潛勢地圖"
[2]: https://dmap.ncdr.nat.gov.tw/1109/map/?utm_source=chatgpt.com "3D災害潛勢地圖"
[3]: https://datahub.ncdr.nat.gov.tw/dataset/detail?pid=8a83d05a-27ac-42a7-ad17-ad0eca0e016a&utm_source=chatgpt.com "海嘯潛勢圖114年版| 災防中心資料服務平台"
[4]: https://www.ca.ntpc.gov.tw/home.jsp?id=88f142fb0f4a0762 "人口統計-新北市政府民政局"
[5]: https://www.dsc.ntpc.gov.tw/DRPI/ntcdmap?dist=%E6%B7%A1%E6%B0%B4%E5%8D%80&utm_source=chatgpt.com "新北市防災地圖-淡水區"
