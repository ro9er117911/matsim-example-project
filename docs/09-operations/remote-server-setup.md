# MATSim 遠端伺服器環境建置教學

本文件說明在 Ubuntu 24.04 LTS 伺服器上建置完整的 MATSim 模擬環境。

---

## 📋 目錄

1. [系統需求](#1-系統需求)
2. [基礎工具安裝](#2-基礎工具安裝)
3. [Java 21 安裝](#3-java-21-安裝)
4. [Maven 安裝](#4-maven-安裝)
5. [pyenv 安裝與設定](#5-pyenv-安裝與設定)
6. [Poetry 安裝與設定](#6-poetry-安裝與設定)
7. [專案下載與建置](#7-專案下載與建置)
8. [Python 環境建置](#8-python-環境建置)
9. [測試執行](#9-測試執行)
10. [常見問題排除](#10-常見問題排除)

---

## 1. 系統需求

### 目標伺服器
```
DataServer01
Ubuntu 24.04 LTS
Kernel: 6.8.0-88-generic
Architecture: x86_64
```

### 硬體需求
| 項目 | 最低需求 | 建議配置 |
|------|---------|---------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB |

### 軟體需求
- 網路連線 (用於下載套件)
- sudo 權限

---

## 2. 基礎工具安裝

首先更新系統並安裝必要的基礎工具：

```bash
# 更新套件列表
sudo apt update && sudo apt upgrade -y

# 安裝基礎編譯工具
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    build-essential \
    ca-certificates

# 安裝 pyenv 編譯所需依賴
sudo apt install -y \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev

# 安裝 GIS 相關依賴 (geopandas 需要)
sudo apt install -y \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev
```

> **注意**: Ubuntu 24.04 的套件都是最新版本，安裝應該不會遇到問題。

---

## 3. Java 21 安裝

MATSim 2025.0 需要 Java 21。Ubuntu 24.04 可以直接從官方倉庫安裝。

### 方法一：使用 APT (最簡單，推薦)

```bash
# 安裝 OpenJDK 21
sudo apt install -y openjdk-21-jdk

# 設定 JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 驗證安裝
java -version
```

預期輸出：
```
openjdk version "21.0.x" 2024-xx-xx
OpenJDK Runtime Environment (build 21.0.x+xx-Ubuntu-xxxxx.04)
OpenJDK 64-Bit Server VM (build 21.0.x+xx-Ubuntu-xxxxx.04, mixed mode, sharing)
```

### 方法二：使用 SDKMAN! (可管理多版本)

```bash
# 安裝 SDKMAN!
curl -s "https://get.sdkman.io" | bash

# 重新載入 shell
source "$HOME/.sdkman/bin/sdkman-init.sh"

# 安裝 Java 21 (Eclipse Temurin)
sdk install java 21.0.5-tem

# 驗證安裝
java -version
```

---

## 4. Maven 安裝

### 方法一：使用 APT (最簡單，推薦)

```bash
# 安裝 Maven
sudo apt install -y maven

# 驗證安裝
mvn -version
```

### 方法二：使用 SDKMAN!

```bash
# 安裝 Maven
sdk install maven 3.9.9

# 驗證安裝
mvn -version
```

預期輸出：
```
Apache Maven 3.9.x
Maven home: /usr/share/maven
Java version: 21.0.x, vendor: Ubuntu
```

---

## 5. pyenv 安裝與設定

pyenv 用於管理多個 Python 版本，避免與系統 Python 衝突。

### 安裝 pyenv

```bash
# 使用官方安裝腳本
curl https://pyenv.run | bash
```

### 設定環境變數

```bash
# 加入 pyenv 設定到 bashrc
cat << 'EOF' >> ~/.bashrc

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOF

# 重新載入設定
source ~/.bashrc
```

### 安裝 Python 3.11

```bash
# 安裝 Python 3.11.10 (穩定版本，與 geopandas 相容)
pyenv install 3.11.10

# 設定為全域預設版本
pyenv global 3.11.10

# 驗證安裝
python --version
# 預期輸出: Python 3.11.10

which python
# 預期輸出: /home/<user>/.pyenv/shims/python
```

---

## 6. Poetry 安裝與設定

Poetry 用於管理 Python 專案依賴。

### 安裝 Poetry

```bash
# 使用官方安裝腳本
curl -sSL https://install.python-poetry.org | python3 -

# 加入 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 驗證安裝
poetry --version
# 預期輸出: Poetry (version 1.8.x)
```

### Poetry 設定

```bash
# 設定虛擬環境在專案目錄內建立 (.venv)
poetry config virtualenvs.in-project true

# 設定使用 pyenv 的 Python
poetry config virtualenvs.prefer-active-python true
```

---

## 7. 專案下載與建置

### Clone 專案

```bash
# 建立工作目錄
mkdir -p ~/projects
cd ~/projects

# Clone 專案 (請替換成正確的 repository URL)
git clone https://github.com/ro9er117911/matsim-example-project.git
cd matsim-example-project
```

**或者使用 SCP 從本機上傳：**

```bash
# 在本機執行 (將專案上傳到伺服器)
scp -r /Users/ro9air/matsim-example-project user@DataServer01:~/projects/
```

### 建置 Java 專案

```bash
cd ~/projects/matsim-example-project

# 使用 Maven Wrapper 建置 (推薦)
./mvnw clean package -DskipTests

# 或使用系統 Maven
# mvn clean package -DskipTests
```

> **注意**: 首次建置需要下載大量依賴 (~500MB)，可能需要 10-20 分鐘。

建置成功後會產生：
```
matsim-example-project-0.0.1-SNAPSHOT.jar  (約 200MB)
```

---

## 8. Python 環境建置

### 確認 Python 版本

```bash
cd ~/projects/matsim-example-project

# 設定專案使用的 Python 版本
pyenv local 3.11.10

# 確認版本
python --version
# 預期輸出: Python 3.11.10
```

### 安裝 Python 依賴

```bash
# 安裝所有依賴
poetry install

# 檢視虛擬環境資訊
poetry env info
```

預期會安裝：
- pandas >= 2.2.0
- geopandas >= 0.14.0
- shapely >= 2.0.0
- pyproj >= 3.6.0
- pyyaml >= 6.0
- numpy >= 1.26.0
- matplotlib >= 3.8.0

### 驗證安裝

```bash
# 測試所有模組是否正確安裝
poetry run python -c "
import pandas
import geopandas
import shapely
import pyproj
import yaml
import numpy
import matplotlib
print('✓ pandas:', pandas.__version__)
print('✓ geopandas:', geopandas.__version__)
print('✓ shapely:', shapely.__version__)
print('✓ pyproj:', pyproj.__version__)
print('✓ numpy:', numpy.__version__)
print('✓ matplotlib:', matplotlib.__version__)
print()
print('All imports successful!')
"
```

---

## 9. 測試執行

### 9.1 測試 Java/MATSim 環境

使用指定的測試案例執行模擬：

```bash
cd ~/projects/matsim-example-project

# 執行測試模擬 (10 次迭代)
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

> **參數說明**:
> - `-Xmx4g`: 分配 4GB 記憶體給 JVM (根據伺服器記憶體調整，建議使用 `-Xmx8g`)
> - 輸出會寫入 `5000_disatar/05_combined_evac/output_optimized_iter10/`

### 9.2 Headless 模式執行 (背景執行)

```bash
# 使用 nohup 在背景執行
nohup java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    5000_disatar/05_combined_evac/config_optimized_iter10.xml \
    > simulation.log 2>&1 &

# 查看 PID
echo $!

# 監控日誌
tail -f simulation.log
```

### 9.3 測試 Python 分析工具

```bash
# 測試分析腳本 (需要先完成模擬)
poetry run python 5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py \
    --events 5000_disatar/05_combined_evac/output_optimized_iter10/output_events.xml.gz \
    --network 5000_disatar/05_combined_evac/output_optimized_iter10/output_network.xml.gz \
    --out slow_links_analysis.csv
```

### 9.4 完整測試流程

```bash
#!/bin/bash
# 完整測試腳本

cd ~/projects/matsim-example-project

echo "=== Step 1: 執行模擬 ==="
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    5000_disatar/05_combined_evac/config_optimized_iter10.xml

echo "=== Step 2: 分析結果 ==="
poetry run python 5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py \
    --events 5000_disatar/05_combined_evac/output_optimized_iter10/output_events.xml.gz \
    --network 5000_disatar/05_combined_evac/output_optimized_iter10/output_network.xml.gz \
    --out 5000_disatar/05_combined_evac/output_optimized_iter10/slow_links_analysis.csv

echo "=== Step 3: 生成 Dashboard ==="
poetry run python 5000_disatar/05_scripts/07_analysis/generate_dashboard_yamls.py \
    --output_dir 5000_disatar/05_combined_evac/output_optimized_iter10

echo "=== 完成! ==="
```

---

## 10. 常見問題排除

### Q1: pyenv install 失敗

**錯誤訊息**: `BUILD FAILED` 或 `missing library`

**解決方案**:
```bash
# 確認所有編譯依賴已安裝
sudo apt install -y \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# 重新安裝
pyenv install 3.11.10
```

### Q2: geopandas 安裝失敗

**錯誤訊息**: `GEOS, PROJ, GDAL not found`

**解決方案**:
```bash
# 安裝 GIS 依賴
sudo apt install -y libgeos-dev libproj-dev libgdal-dev gdal-bin

# 刪除並重建虛擬環境
poetry env remove --all
poetry install
```

### Q3: Java OutOfMemoryError

**錯誤訊息**: `java.lang.OutOfMemoryError: Java heap space`

**解決方案**:
```bash
# 增加 JVM 記憶體分配
java -Xmx16g -Xms8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml
```

### Q4: Maven 下載超時

**錯誤訊息**: `Connection timed out`

**解決方案**:
```bash
# 使用 Maven 鏡像 (阿里雲)
mkdir -p ~/.m2
cat << 'EOF' > ~/.m2/settings.xml
<settings>
  <mirrors>
    <mirror>
      <id>aliyun</id>
      <mirrorOf>central</mirrorOf>
      <url>https://maven.aliyun.com/repository/public</url>
    </mirror>
  </mirrors>
</settings>
EOF

# 清除快取並重新建置
rm -rf ~/.m2/repository
./mvnw clean package -DskipTests
```

### Q5: Poetry 虛擬環境問題

**問題**: 虛擬環境使用錯誤的 Python 版本

**解決方案**:
```bash
# 確認 pyenv 版本
pyenv local 3.11.10
python --version  # 應顯示 3.11.10

# 刪除現有虛擬環境
rm -rf .venv
poetry env remove --all

# 重新設定並安裝
poetry config virtualenvs.in-project true
poetry install

# 驗證
poetry run python --version
```

### Q6: 權限問題

**錯誤訊息**: `Permission denied`

**解決方案**:
```bash
# 修復 mvnw 執行權限
chmod +x ./mvnw

# 確保專案目錄權限正確
sudo chown -R $USER:$USER ~/projects/matsim-example-project
```

---

## 🎉 環境驗證清單

完成以上步驟後，請確認以下項目：

```bash
echo "=== 環境驗證 ==="

# Java
java -version 2>&1 | head -1
# ✓ 預期: openjdk version "21.x.x"

# Maven
mvn -version 2>&1 | head -1
# ✓ 預期: Apache Maven 3.x.x

# Python (pyenv)
python --version
# ✓ 預期: Python 3.11.10

# Poetry
poetry --version
# ✓ 預期: Poetry (version 1.8.x)

# 專案建置
ls -lh matsim-example-project-0.0.1-SNAPSHOT.jar
# ✓ 預期: 檔案大小約 200MB

# Python 依賴
poetry run python -c "import pandas, geopandas, pyproj; print('All imports OK')"
# ✓ 預期: All imports OK
```

---

## 📁 專案結構概覽

```
matsim-example-project/
├── 5000_disatar/                    # 災難模擬情境
│   └── 05_combined_evac/
│       ├── config_optimized_iter10.xml  ← 測試配置檔
│       ├── input/
│       └── output_optimized_iter10/
├── scenarios/                       # 其他情境
├── 5000_disatar/05_scripts/        # Python/Shell 腳本（依專案階段分類）
├── src/                           # Java 原始碼
├── pom.xml                        # Maven 配置
├── pyproject.toml                 # Poetry 配置
└── matsim-example-project-0.0.1-SNAPSHOT.jar  # 建置產物
```

---

## 🚀 快速開始 (TL;DR)

如果你想快速設定，可以執行自動安裝腳本：

```bash
# 下載並執行自動安裝腳本
cd ~/projects/matsim-example-project
./5000_disatar/05_scripts/09_operations/setup_remote_server.sh
```

或者複製貼上以下指令：

```bash
# === 一鍵設定 (Ubuntu 24.04) ===

# 1. 系統依賴
sudo apt update && sudo apt install -y curl wget git unzip build-essential \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev libgeos-dev libproj-dev gdal-bin libgdal-dev \
    openjdk-21-jdk maven

# 2. 設定 JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc

# 3. pyenv
curl https://pyenv.run | bash
cat << 'EOF' >> ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
source ~/.bashrc
pyenv install 3.11.10
pyenv global 3.11.10

# 4. Poetry
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
poetry config virtualenvs.in-project true

# 5. 建置專案
cd ~/projects/matsim-example-project
./mvnw clean package -DskipTests
poetry install

# 6. 測試
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

---

## 📚 延伸閱讀

- [MATSim 官方文件](https://www.matsim.org/docs)
- [pyenv 使用指南](https://github.com/pyenv/pyenv)
- [Poetry 官方文件](https://python-poetry.org/docs/)
- [SDKMAN! 使用指南](https://sdkman.io/usage)

---

*文件最後更新: 2025-12-22*  
*目標系統: Ubuntu 24.04 LTS (DataServer01)*
