#!/bin/bash
# ============================================================
# MATSim Remote Server Environment Setup Script
# For Ubuntu 24.04 LTS (DataServer01)
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}MATSim Environment Auto-Setup Script${NC}"
echo -e "${GREEN}For Ubuntu 24.04 LTS${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}Error: Do not run this script as root!${NC}"
    echo "Please run as a regular user with sudo privileges."
    exit 1
fi

# Confirm Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "${BLUE}Detected OS: $PRETTY_NAME${NC}"
    if [[ "$ID" != "ubuntu" ]]; then
        echo -e "${YELLOW}Warning: This script is optimized for Ubuntu. Proceed with caution.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Cannot detect OS version.${NC}"
fi
echo ""

# ============================================================
# Step 1: Install system dependencies
# ============================================================
echo -e "${GREEN}[1/6] Installing system dependencies...${NC}"

sudo apt update
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    build-essential \
    ca-certificates

# pyenv build dependencies
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

# GIS dependencies for geopandas
sudo apt install -y \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

# ============================================================
# Step 2: Install Java 21 via APT
# ============================================================
echo -e "${GREEN}[2/6] Installing Java 21...${NC}"

sudo apt install -y openjdk-21-jdk

# Set JAVA_HOME
if ! grep -q 'JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' ~/.bashrc; then
    cat << 'EOF' >> ~/.bashrc

# Java 21
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
EOF
fi

export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo -e "${GREEN}✓ Java 21 installed${NC}"
java -version
echo ""

# ============================================================
# Step 3: Install Maven via APT
# ============================================================
echo -e "${GREEN}[3/6] Installing Maven...${NC}"

sudo apt install -y maven

echo -e "${GREEN}✓ Maven installed${NC}"
mvn -version
echo ""

# ============================================================
# Step 4: Install pyenv
# ============================================================
echo -e "${GREEN}[4/6] Installing pyenv...${NC}"

if [ ! -d "$HOME/.pyenv" ]; then
    curl https://pyenv.run | bash
else
    echo "pyenv already installed, skipping..."
fi

# Add to bashrc if not already present
if ! grep -q 'PYENV_ROOT' ~/.bashrc; then
    cat << 'EOF' >> ~/.bashrc

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOF
fi

# Source pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)" 2>/dev/null || true

echo -e "${GREEN}✓ pyenv installed${NC}"
echo ""

# ============================================================
# Step 5: Install Python 3.11
# ============================================================
echo -e "${GREEN}[5/6] Installing Python 3.11.10 via pyenv...${NC}"

pyenv install 3.11.10 -s  # -s means skip if already installed
pyenv global 3.11.10

echo -e "${GREEN}✓ Python 3.11.10 installed${NC}"
$HOME/.pyenv/shims/python --version
echo ""

# ============================================================
# Step 6: Install Poetry
# ============================================================
echo -e "${GREEN}[6/6] Installing Poetry...${NC}"

if [ ! -f "$HOME/.local/bin/poetry" ]; then
    curl -sSL https://install.python-poetry.org | $HOME/.pyenv/shims/python3 -
else
    echo "Poetry already installed, skipping..."
fi

# Add to PATH if not already present
if ! grep -q '.local/bin' ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

export PATH="$HOME/.local/bin:$PATH"

# Configure Poetry
$HOME/.local/bin/poetry config virtualenvs.in-project true
$HOME/.local/bin/poetry config virtualenvs.prefer-active-python true

echo -e "${GREEN}✓ Poetry installed${NC}"
$HOME/.local/bin/poetry --version
echo ""

# ============================================================
# Summary
# ============================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Installed versions:"
echo "  Java:   $(java -version 2>&1 | head -1)"
echo "  Maven:  $(mvn -version 2>&1 | head -1)"
echo "  Python: $($HOME/.pyenv/shims/python --version)"
echo "  Poetry: $($HOME/.local/bin/poetry --version)"
echo ""
echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}IMPORTANT: Please run the following command to reload shell:${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo -e "    ${GREEN}source ~/.bashrc${NC}"
echo ""
echo "After that, build and test the MATSim project:"
echo ""
echo "    cd ~/projects/matsim-example-project"
echo "    ./mvnw clean package -DskipTests"
echo "    poetry install"
echo ""
echo "    # Run test simulation"
echo "    java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \\"
echo "        5000_disatar/05_combined_evac/config_optimized_iter10.xml"
echo ""
echo -e "${GREEN}Happy simulating! 🚗${NC}"
