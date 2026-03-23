#!/usr/bin/env bash
# ============================================================
#  CyberMind AI - Full Installer
#  Works on: Kali Linux, Ubuntu/Debian, macOS
# ============================================================

set -e

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Banner ─────────────────────────────────────────────────────
clear
echo -e "${CYAN}${BOLD}"
echo "  ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██████╗ "
echo " ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗"
echo " ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║  ██║"
echo " ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║  ██║"
echo " ╚██████╗   ██║   ██████╔╝███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██████╔╝"
echo "  ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ "
echo -e "${RESET}"
echo -e "${MAGENTA}  AI-Powered CTF & Penetration Testing Assistant${RESET}"
echo -e "${YELLOW}  ⚠️  For authorized testing only${RESET}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# ── Helper Functions ───────────────────────────────────────────
ok()   { echo -e "  ${GREEN}✅ $1${RESET}"; }
info() { echo -e "  ${CYAN}ℹ️  $1${RESET}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${RESET}"; }
err()  { echo -e "  ${RED}❌ $1${RESET}"; }
step() { echo -e "\n${BOLD}${BLUE}[$1]${RESET} ${BOLD}$2${RESET}"; echo -e "  ${BLUE}────────────────────────────────${RESET}"; }

command_exists() { command -v "$1" &>/dev/null; }

# ── Detect OS ─────────────────────────────────────────────────
step "1/7" "Detecting System"

OS="unknown"
PKG_MANAGER=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    info "macOS detected"
elif [[ -f /etc/os-release ]]; then
    source /etc/os-release
    DISTRO="${ID,,}"
    if [[ "$DISTRO" == "kali" ]]; then
        OS="kali"
        PKG_MANAGER="apt"
        ok "Kali Linux detected 🐉 — full pentesting tools will be installed"
    elif [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" =~ "kali" ]]; then
        OS="debian"
        PKG_MANAGER="apt"
        info "Debian/Ubuntu detected"
    elif [[ "$DISTRO" == "fedora" || "$DISTRO" == "rhel" || "$DISTRO" == "centos" ]]; then
        OS="fedora"
        PKG_MANAGER="dnf"
        info "Fedora/RHEL detected"
    elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
        OS="arch"
        PKG_MANAGER="pacman"
        info "Arch Linux detected"
    else
        OS="linux"
        warn "Unknown Linux distro: $DISTRO"
    fi
else
    warn "Could not detect OS — continuing with best effort"
fi

# ── Check Python ───────────────────────────────────────────────
step "2/7" "Checking Python"

PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command_exists "$cmd"; then
        VER=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        if [[ $MAJOR -ge 3 && $MINOR -ge 10 ]]; then
            PYTHON="$cmd"
            ok "Python $VER found ($cmd)"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    err "Python 3.10+ not found!"
    if [[ "$OS" == "kali" || "$OS" == "debian" ]]; then
        info "Installing Python 3.11..."
        sudo apt update -qq && sudo apt install -y python3.11 python3.11-venv python3-pip
        PYTHON="python3.11"
    elif [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install python@3.11
            PYTHON="python3"
        else
            err "Install Python 3.10+ from python.org"
            exit 1
        fi
    else
        err "Please install Python 3.10+ manually"
        exit 1
    fi
fi

# ── Create Virtual Environment ────────────────────────────────
step "3/7" "Setting Up Python Environment"

VENV_DIR="$(pwd)/venv"

if [[ -d "$VENV_DIR" ]]; then
    info "Virtual environment already exists"
else
    info "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    ok "Virtual environment created"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
ok "Virtual environment activated"

# Upgrade pip silently
pip install --upgrade pip -q
ok "pip upgraded"

# ── Install Python Dependencies ───────────────────────────────
step "4/7" "Installing Python Packages"

info "Installing from requirements.txt..."
echo ""

# Install with progress visible
pip install \
    ollama \
    customtkinter \
    chromadb \
    sentence-transformers \
    beautifulsoup4 \
    requests \
    lxml \
    python-dotenv \
    Pillow \
    pycryptodome \
    pyperclip \
    psutil \
    packaging \
    aiohttp \
    --progress-bar on

echo ""
ok "All Python packages installed"

# ── Install System Pentesting Tools ───────────────────────────
step "5/7" "Installing Pentesting Tools"

if [[ "$OS" == "kali" ]]; then
    ok "Kali Linux — installing full pentesting toolkit"
    info "Updating package lists..."
    sudo apt update -qq 2>/dev/null

    TOOLS=(
        nmap
        gobuster
        dirb
        nikto
        sqlmap
        binwalk
        exiftool
        steghide
        foremost
        hydra
        netcat-traditional
        curl
        wget
        xxd
        ltrace
        strace
        gdb
    )

    INSTALL_LIST=()
    for tool in "${TOOLS[@]}"; do
        if ! command_exists "$tool"; then
            INSTALL_LIST+=("$tool")
        else
            ok "$tool already installed"
        fi
    done

    if [[ ${#INSTALL_LIST[@]} -gt 0 ]]; then
        info "Installing: ${INSTALL_LIST[*]}"
        sudo apt install -y "${INSTALL_LIST[@]}" -qq
        ok "Tools installed"
    else
        ok "All tools already installed"
    fi

elif [[ "$OS" == "debian" ]]; then
    info "Debian/Ubuntu — installing basic tools"
    sudo apt update -qq 2>/dev/null
    sudo apt install -y nmap curl wget netcat-openbsd exiftool -qq 2>/dev/null || true
    ok "Basic tools installed"
    warn "For full toolkit, use Kali Linux"

elif [[ "$OS" == "macos" ]]; then
    if command_exists brew; then
        info "Homebrew found — installing tools"
        brew install nmap exiftool wget curl binwalk 2>/dev/null || true
        ok "macOS tools installed"
    else
        warn "Homebrew not found. Install from brew.sh for pentesting tools"
    fi

elif [[ "$OS" == "arch" ]]; then
    sudo pacman -S --noconfirm nmap gobuster nikto sqlmap exiftool 2>/dev/null || true
    ok "Arch tools installed"

else
    warn "Skipping system tools for unknown OS"
    warn "Manually install: nmap, gobuster, nikto, sqlmap, exiftool"
fi

# ── Install & Setup Ollama ─────────────────────────────────────
step "6/7" "Setting Up Ollama (Local AI)"

if command_exists ollama; then
    ok "Ollama already installed"
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    info "Version: $OLLAMA_VERSION"
else
    info "Installing Ollama..."
    if [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install ollama
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    ok "Ollama installed"
fi

# Start Ollama service
info "Starting Ollama service..."
if [[ "$OS" == "macos" ]]; then
    brew services start ollama 2>/dev/null || ollama serve &>/dev/null &
else
    # Linux
    if command_exists systemctl; then
        sudo systemctl enable ollama 2>/dev/null || true
        sudo systemctl start ollama 2>/dev/null || ollama serve &>/dev/null &
    else
        ollama serve &>/dev/null &
    fi
fi

# Wait for Ollama to be ready
info "Waiting for Ollama to start..."
MAX_WAIT=15
WAITED=0
while ! curl -s http://localhost:11434/api/tags &>/dev/null; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [[ $WAITED -ge $MAX_WAIT ]]; then
        warn "Ollama didn't start in time — you can start it manually: ollama serve"
        break
    fi
done

if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama is running"
else
    warn "Ollama not responding yet — it may need a moment after install"
fi

# Download AI model
echo ""
echo -e "  ${BOLD}Choose AI model to download:${RESET}"
echo ""
echo -e "  ${GREEN}1)${RESET} llama3.1:8b        — Best for CTF       (4.7 GB) ${GREEN}[Recommended]${RESET}"
echo -e "  ${GREEN}2)${RESET} qwen2.5-coder:7b   — Best for code       (4.7 GB)"
echo -e "  ${GREEN}3)${RESET} mistral:7b         — Fast & smart        (4.1 GB)"
echo -e "  ${GREEN}4)${RESET} llama3.2:3b        — Lightweight         (2.0 GB)"
echo -e "  ${GREEN}5)${RESET} Skip (I'll download later)"
echo ""
read -p "  Enter choice [1-5] (default: 1): " MODEL_CHOICE
MODEL_CHOICE=${MODEL_CHOICE:-1}

case $MODEL_CHOICE in
    1) SELECTED_MODEL="llama3.1:8b" ;;
    2) SELECTED_MODEL="qwen2.5-coder:7b" ;;
    3) SELECTED_MODEL="mistral:7b" ;;
    4) SELECTED_MODEL="llama3.2:3b" ;;
    5) SELECTED_MODEL="" ;;
    *) SELECTED_MODEL="llama3.1:8b" ;;
esac

if [[ -n "$SELECTED_MODEL" ]]; then
    # Check if model already exists
    if ollama list 2>/dev/null | grep -q "${SELECTED_MODEL%%:*}"; then
        ok "Model $SELECTED_MODEL already downloaded"
    else
        info "Downloading $SELECTED_MODEL (this may take a while)..."
        echo ""
        ollama pull "$SELECTED_MODEL"
        echo ""
        ok "Model $SELECTED_MODEL ready!"
    fi
else
    warn "Skipped model download"
    info "Download later with:  ollama pull llama3.1:8b"
fi

# ── Configure Project ──────────────────────────────────────────
step "7/7" "Configuring CyberMind"

# Create .env if not exists
if [[ ! -f ".env" ]]; then
    cp .env.example .env
    ok "Created .env config file"

    # Write selected model to .env
    if [[ -n "$SELECTED_MODEL" ]]; then
        if grep -q "^AI_MODEL=" .env; then
            sed -i.bak "s|^AI_MODEL=.*|AI_MODEL=$SELECTED_MODEL|" .env
            rm -f .env.bak
        else
            echo "AI_MODEL=$SELECTED_MODEL" >> .env
        fi
        ok "AI model set to: $SELECTED_MODEL"
    fi
else
    ok ".env already exists"
fi

# Ensure data directories exist
mkdir -p data/{chroma_db,writeups,sessions,logs}
ok "Data directories ready"

# Create launch scripts
cat > run.sh << 'RUNSCRIPT'
#!/usr/bin/env bash
# CyberMind AI Launcher
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "Starting Ollama..."
    ollama serve &>/dev/null &
    sleep 3
fi

# Launch CyberMind
python3 main.py
RUNSCRIPT

chmod +x run.sh
ok "Created run.sh launcher"

# ── Summary ────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${GREEN}${BOLD}  ✅ Installation Complete!${RESET}"
echo ""

# Show installed tools summary
echo -e "  ${BOLD}Installed Tools:${RESET}"
TOOL_LIST=(nmap gobuster nikto sqlmap binwalk exiftool hydra)
for tool in "${TOOL_LIST[@]}"; do
    if command_exists "$tool"; then
        echo -e "    ${GREEN}✓${RESET} $tool"
    else
        echo -e "    ${YELLOW}–${RESET} $tool (not found)"
    fi
done

echo ""
echo -e "  ${BOLD}AI Model:${RESET}"
if [[ -n "$SELECTED_MODEL" ]]; then
    echo -e "    ${GREEN}✓${RESET} $SELECTED_MODEL"
else
    echo -e "    ${YELLOW}–${RESET} Not downloaded yet"
fi

echo ""
echo -e "  ${BOLD}Knowledge Base:${RESET}"
echo -e "    ${GREEN}✓${RESET} 29 HTB writeups (Easy + Medium Windows)"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${BOLD}  🚀 To launch CyberMind:${RESET}"
echo ""
echo -e "  ${CYAN}  ./run.sh${RESET}          ← Recommended"
echo -e "  ${CYAN}  python3 main.py${RESET}   ← Alternative"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
