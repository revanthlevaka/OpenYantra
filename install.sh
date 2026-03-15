#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  OpenYantra v2.3 Installer — Mac + Linux
#  The Sacred Memory Machine
#  Inspired by Chitragupta, the Hindu God of Data
#
#  Fully self-contained — installs everything automatically:
#  Python, LibreOffice, all deps, venv, CLI, desktop shortcut
#
#  Usage:
#    curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash
#  Or:
#    chmod +x install.sh && ./install.sh
# ═══════════════════════════════════════════════════════════════

set -e

VERSION="2.9.1"
INSTALL_DIR="$HOME/openyantra"
VENV_DIR="$INSTALL_DIR/.venv"
RAW="https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main"
PORT=7331

# ── Colours ──────────────────────────────────────────────────────────────────

SAFFRON='\033[0;33m'; GREEN='\033[0;32m'; RED='\033[0;31m'
DIM='\033[0;90m';     RESET='\033[0m';    BOLD='\033[1m'

banner() {
  echo ""
  echo -e "${SAFFRON}${BOLD}  ╔══════════════════════════════════════════════╗${RESET}"
  echo -e "${SAFFRON}${BOLD}  ║  OpenYantra v${VERSION} — The Sacred Memory Machine  ║${RESET}"
  echo -e "${SAFFRON}${BOLD}  ║  Inspired by Chitragupta, Hindu God of Data   ║${RESET}"
  echo -e "${SAFFRON}${BOLD}  ╚══════════════════════════════════════════════╝${RESET}"
  echo ""
}

log()  { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${SAFFRON}⚠${RESET}  $1"; }
err()  { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
step() { echo -e "\n  ${SAFFRON}▶${RESET} ${BOLD}$1${RESET}"; }
info() { echo -e "  ${DIM}$1${RESET}"; }

# ── OS detection ─────────────────────────────────────────────────────────────

detect_os() {
  step "Detecting system"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    ARCH=$(uname -m)
    log "macOS detected ($ARCH)"
    [[ "$ARCH" == "arm64" ]] && ARCH_LABEL="Apple Silicon" || ARCH_LABEL="Intel"
    info "$ARCH_LABEL Mac"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if command -v apt-get &>/dev/null; then
      PKG="apt"
    elif command -v dnf &>/dev/null; then
      PKG="dnf"
    elif command -v pacman &>/dev/null; then
      PKG="pacman"
    else
      PKG="unknown"
    fi
    log "Linux detected (package manager: $PKG)"
  else
    err "Unsupported OS: $OSTYPE. Use install.ps1 for Windows."
  fi
}

# ── Python installation ───────────────────────────────────────────────────────

install_python() {
  step "Checking Python 3.9+"

  # Check for existing Python
  for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$cmd" &>/dev/null; then
      PY_VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
      MAJOR=$(echo $PY_VER | cut -d. -f1)
      MINOR=$(echo $PY_VER | cut -d. -f2)
      if [[ $MAJOR -eq 3 && $MINOR -ge 9 ]]; then
        PYTHON="$cmd"
        log "Python $PY_VER found ($cmd)"
        return
      fi
    fi
  done

  # Python not found or too old — install it
  warn "Python 3.9+ not found. Installing automatically..."

  if [[ "$OS" == "mac" ]]; then
    # Install Homebrew if missing
    if ! command -v brew &>/dev/null; then
      info "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      # Add brew to PATH for Apple Silicon
      if [[ "$ARCH" == "arm64" ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> "$HOME/.zprofile"
      fi
    fi
    brew install python@3.11
    PYTHON=$(brew --prefix python@3.11)/bin/python3.11
    log "Python 3.11 installed via Homebrew"

  elif [[ "$OS" == "linux" ]]; then
    if [[ "$PKG" == "apt" ]]; then
      sudo apt-get update -qq
      sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential
      PYTHON=$(command -v python3)
      log "Python installed via apt"
    elif [[ "$PKG" == "dnf" ]]; then
      sudo dnf install -y python3 python3-pip python3-devel gcc
      PYTHON=$(command -v python3)
      log "Python installed via dnf"
    elif [[ "$PKG" == "pacman" ]]; then
      sudo pacman -Sy --noconfirm python python-pip
      PYTHON=$(command -v python3)
      log "Python installed via pacman"
    else
      err "Could not auto-install Python. Please install Python 3.9+ from https://python.org"
    fi
  fi
}

# ── LibreOffice installation ──────────────────────────────────────────────────

install_libreoffice() {
  step "Checking LibreOffice (needed to view/edit Chitrapat)"

  if command -v libreoffice &>/dev/null || command -v soffice &>/dev/null; then
    log "LibreOffice already installed"
    return
  fi

  warn "LibreOffice not found. Installing..."

  if [[ "$OS" == "mac" ]]; then
    if command -v brew &>/dev/null; then
      brew install --cask libreoffice 2>/dev/null || warn "LibreOffice install failed — install manually from libreoffice.org"
      log "LibreOffice installed"
    else
      warn "Install LibreOffice manually: https://libreoffice.org"
    fi
  elif [[ "$OS" == "linux" ]]; then
    if [[ "$PKG" == "apt" ]]; then
      sudo apt-get install -y libreoffice-calc 2>/dev/null || warn "LibreOffice install failed"
      log "LibreOffice installed"
    elif [[ "$PKG" == "dnf" ]]; then
      sudo dnf install -y libreoffice-calc 2>/dev/null || warn "LibreOffice install failed"
      log "LibreOffice installed"
    else
      warn "Install LibreOffice manually: https://libreoffice.org"
    fi
  fi
}

# ── Create virtualenv ─────────────────────────────────────────────────────────

create_venv() {
  step "Creating isolated Python environment"

  mkdir -p "$INSTALL_DIR"

  if [[ -d "$VENV_DIR" ]]; then
    log "Virtual environment already exists"
  else
    $PYTHON -m venv "$VENV_DIR"
    log "Virtual environment created at $VENV_DIR"
  fi

  # Activate venv
  source "$VENV_DIR/bin/activate"
  PYTHON="$VENV_DIR/bin/python"
  PIP="$VENV_DIR/bin/pip"

  # Upgrade pip silently
  $PIP install --quiet --upgrade pip
  log "pip upgraded"
}

# ── Install Python dependencies ───────────────────────────────────────────────

install_deps() {
  step "Installing Python dependencies"

  # Core deps — always installed
  CORE_DEPS=(
    "odfpy"
    "pandas"
    "scikit-learn"
    "faiss-cpu"
    "fastapi"
    "uvicorn[standard]"
    "python-telegram-bot"
    "requests"
    "schedule"
  )

  info "Installing: ${CORE_DEPS[*]}"
  $PIP install --quiet "${CORE_DEPS[@]}"
  log "All core dependencies installed"

  # sentence-transformers — skipped (using TF-IDF, faster install)
  info "Using TF-IDF embedder (fast, zero extra deps)"
  info "For better search quality later: pip install sentence-transformers"
}

# ── Download project files ────────────────────────────────────────────────────

download_files() {
  step "Downloading OpenYantra v${VERSION} files"

  mkdir -p "$INSTALL_DIR"/{openclaw,examples,references,docs}

  FILES=(
    "openyantra.py"
    "vidyakosha.py"
    "yantra_ui.py"
    "yantra_digest.py"
    "telegram_bot.py"
    "ios_shortcut.py"
    "yantra_mail.py"
    "yantra_migrate.py"
    "openclaw/hooks.py"
    "openclaw/plugin.py"
    "openclaw/__init__.py"
    "examples/bootstrap.py"
    "examples/langchain_adapter.py"
    "examples/__init__.py"
    "references/controlled-vocab.md"
    "docs/DEPLOYMENT.md"
    "PROTOCOL.md"
    "SKILL.md"
    "MYTHOLOGY.md"
    "WHITEPAPER.md"
  )

  for file in "${FILES[@]}"; do
    URL="$RAW/$file"
    DEST="$INSTALL_DIR/$file"
    mkdir -p "$(dirname "$DEST")"
    if curl -sSL "$URL" -o "$DEST" 2>/dev/null; then
      log "Downloaded $file"
    else
      warn "Could not download $file (continuing)"
    fi
  done
}

# ── Create yantra CLI ─────────────────────────────────────────────────────────

create_cli() {
  step "Creating yantra CLI"

  BIN="$INSTALL_DIR/yantra"

  cat > "$BIN" << SCRIPT
#!/usr/bin/env bash
# yantra — OpenYantra v${VERSION} CLI
INSTALL_DIR="\$HOME/openyantra"
VENV="\$INSTALL_DIR/.venv"
OY_FILE="\${OPENYANTRA_FILE:-\$HOME/openyantra/chitrapat.ods}"
PYTHON="\$VENV/bin/python"

# Activate venv
if [[ -f "\$VENV/bin/activate" ]]; then
  source "\$VENV/bin/activate"
fi

case "\$1" in
  bootstrap|init)
    echo "Starting Bootstrap Interview..."
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import run_bootstrap_interview
run_bootstrap_interview('\$OY_FILE')
"
    ;;
  ui|dashboard)
    PORT="\${2:-7331}"
    echo "Opening OpenYantra Dashboard..."
    \$PYTHON "\$INSTALL_DIR/yantra_ui.py" --file "\$OY_FILE" --port "\$PORT" &
    sleep 1
    # Auto-open browser
    if command -v open &>/dev/null; then
      open "http://localhost:\$PORT"
    elif command -v xdg-open &>/dev/null; then
      xdg-open "http://localhost:\$PORT"
    fi
    wait
    ;;
  health|status)
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('\$OY_FILE')
h = oy.health_check()
print('OpenYantra Health Check v${VERSION}')
print('='*45)
for k,v in h.items():
    if k != 'rows': print(f'  {k:28} {v}')
if h.get('rows'):
    print('  Sheet row counts:')
    for s,n in h['rows'].items(): print(f'    {s}: {n}')
"
    ;;
  doctor)
    \$PYTHON -c "
import sys, importlib, socket
sys.path.insert(0, '\$INSTALL_DIR')
print('OpenYantra Doctor v${VERSION}')
print('='*45)
# Python version
pv = sys.version_info
ok = pv.major == 3 and pv.minor >= 9
print(f'  Python {pv.major}.{pv.minor}  {\"✓\" if ok else \"✗ Need 3.9+\"}')
# Required packages
for pkg in ['odfpy','pandas','sklearn','faiss','fastapi','uvicorn']:
    try:
        importlib.import_module(pkg.replace('sklearn','sklearn'))
        print(f'  {pkg:20} ✓')
    except ImportError:
        print(f'  {pkg:20} ✗ missing')
# Port check
try:
    s = socket.socket(); s.bind(('127.0.0.1', 7331)); s.close()
    print(f'  Port 7331           ✓ available')
except:
    print(f'  Port 7331           ✗ in use')
# File check
import os
f = os.path.expanduser('\$OY_FILE')
if os.path.exists(f):
    kb = os.path.getsize(f)//1024
    print(f'  Chitrapat           ✓ {kb}KB')
else:
    print(f'  Chitrapat           ✗ not found — run: yantra bootstrap')
print('='*45)
"
    ;;
  inbox)
    shift; TEXT="\$*"
    [[ -z "\$TEXT" ]] && read -p "Capture: " TEXT
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('\$OY_FILE')
r = oy.inbox('\$TEXT')
print('✓ Captured to Inbox' if r.get('status')=='written' else f'Status: {r.get(\"status\")}')
"
    ;;
  digest)
    \$PYTHON "\$INSTALL_DIR/yantra_digest.py" --file "\$OY_FILE"
    ;;
  route)
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('\$OY_FILE')
d = oy.route_inbox()
r = sum(1 for x in d if x.get('routed'))
print(f'✓ Routed {r}/{len(d)} inbox items')
for x in d: print(f'  {str(x.get(\"content\",\"\"))[:50]:50} → {x.get(\"target\",\"unrouted\")}')
"
    ;;
  loops)
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra, SHEET_OPEN_LOOPS
oy = OpenYantra('\$OY_FILE')
loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS) if r.get('Resolved?')=='No']
print(f'Open Loops ({len(loops)}):')
for l in loops:
    print(f'  [{l.get(\"Priority\",\"?\"):8}] {l.get(\"Topic\",\"\")[:55]}')
"
    ;;
  diff|beliefs)
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('\$OY_FILE')
d = oy.diff_beliefs()
if d:
    print(f'Belief contradictions ({len(d)}):')
    for x in d: print(f'  {x[\"message\"]}')
else: print('✓ No contradictions detected')
"
    ;;
  ttl|expire)
    \$PYTHON -c "
import sys; sys.path.insert(0, '\$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('\$OY_FILE')
e = oy.check_anishtha_ttl()
if e:
    print(f'Expired loops ({len(e)}):')
    for x in e: print(f'  {x[\"message\"]}')
else: print('✓ No expired loops')
"
    ;;
  telegram)
    echo "Starting Telegram bot..."
    \$PYTHON "\$INSTALL_DIR/telegram_bot.py" --file "\$OY_FILE"
    ;;
  open|edit)
    if command -v libreoffice &>/dev/null; then
      libreoffice "\$OY_FILE" &
    elif command -v soffice &>/dev/null; then
      soffice "\$OY_FILE" &
    else
      echo "LibreOffice not found. Install from: https://libreoffice.org"
    fi
    ;;
  version)
    echo "OpenYantra v${VERSION}"
    ;;
  help|--help|-h|"")
    echo ""
    echo "  OpenYantra v${VERSION} — The Sacred Memory Machine"
    echo "  Inspired by Chitragupta, the Hindu God of Data"
    echo ""
    echo "  COMMANDS:"
    echo "    yantra bootstrap    Interview-based setup (first time)"
    echo "    yantra ui [port]    Browser dashboard → http://localhost:7331"
    echo "    yantra doctor       System health check"
    echo "    yantra health       Memory stats"
    echo "    yantra inbox [text] Quick capture to Inbox"
    echo "    yantra route        Route Inbox items to correct sheets"
    echo "    yantra digest       Daily summary — loops, projects, insights"
    echo "    yantra loops        List open loops (Anishtha)"
    echo "    yantra diff         Belief contradiction check"
    echo "    yantra ttl          Check expired open loops"
    echo "    yantra telegram     Start Telegram bot capture"
    echo "    yantra open         Open Chitrapat in LibreOffice"
    echo "    yantra stats        Memory growth analytics
    yantra context      Copy full context to clipboard — paste into any AI chat
    yantra integrity    Verify Agrasandhani SHA-256 Mudra signatures
    yantra archive      Rotate session log (default: keep 90 days)
    yantra shortcut     Start iOS Shortcut server (port 7332)
    yantra mail         Start Email-to-Inbox SMTP server (port 2525)
    yantra migrate      Upgrade older Chitrapat to current schema
    yantra schedule     Schedule daily digest via cron/launchd
    yantra version      Show version"
    echo ""
    echo "  FILE: \$OY_FILE"
    echo "  Set OPENYANTRA_FILE to change location"
    echo ""
    ;;
  *)
    echo "Unknown command: \$1. Run 'yantra help'"
    exit 1
    ;;
esac
SCRIPT

  chmod +x "$BIN"
  log "yantra CLI created"
}

# ── Desktop shortcut ──────────────────────────────────────────────────────────

create_desktop_shortcut() {
  step "Creating desktop shortcut"

  if [[ "$OS" == "mac" ]]; then
    # Create .command file (double-clickable on Mac)
    SHORTCUT="$HOME/Desktop/OpenYantra.command"
    cat > "$SHORTCUT" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
"$INSTALL_DIR/yantra" ui &
sleep 1
open "http://localhost:$PORT"
EOF
    chmod +x "$SHORTCUT"
    # Remove quarantine flag so Mac doesn't block it
    xattr -d com.apple.quarantine "$SHORTCUT" 2>/dev/null || true
    log "Desktop shortcut created: ~/Desktop/OpenYantra.command"

  elif [[ "$OS" == "linux" ]]; then
    # Create .desktop file
    SHORTCUT="$HOME/Desktop/OpenYantra.desktop"
    APPS_DIR="$HOME/.local/share/applications"
    mkdir -p "$APPS_DIR"

    DESKTOP_CONTENT="[Desktop Entry]
Name=OpenYantra
Comment=The Sacred Memory Machine
Exec=bash -c 'source $VENV_DIR/bin/activate && $INSTALL_DIR/yantra ui'
Icon=$INSTALL_DIR/assets/icon_512.png
Terminal=false
Type=Application
Categories=Utility;Office;"

    echo "$DESKTOP_CONTENT" > "$SHORTCUT"
    echo "$DESKTOP_CONTENT" > "$APPS_DIR/openyantra.desktop"
    chmod +x "$SHORTCUT" "$APPS_DIR/openyantra.desktop"
    log "Desktop shortcut created"
  fi
}

# ── Add to PATH ───────────────────────────────────────────────────────────────

setup_path() {
  step "Setting up PATH"

  SHELL_RC=""
  if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
  elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    [[ "$OS" == "mac" ]] && SHELL_RC="$HOME/.bash_profile"
  fi

  PATH_LINE="export PATH=\"\$PATH:$INSTALL_DIR\""
  OY_LINE="export OPENYANTRA_FILE=\"\$HOME/openyantra/chitrapat.ods\""
  VENV_LINE="# OpenYantra venv — auto-activated by yantra CLI"

  if [[ -n "$SHELL_RC" ]]; then
    if ! grep -q "OPENYANTRA_FILE" "$SHELL_RC" 2>/dev/null; then
      { echo ""; echo "# OpenYantra v${VERSION}"; echo "$PATH_LINE"; echo "$OY_LINE"; } >> "$SHELL_RC"
      log "Added to $SHELL_RC"
    else
      log "PATH already configured"
    fi
  fi

  export PATH="$PATH:$INSTALL_DIR"
  export OPENYANTRA_FILE="$HOME/openyantra/chitrapat.ods"
}

# ── Run yantra doctor ─────────────────────────────────────────────────────────

run_doctor() {
  step "Running yantra doctor"
  source "$VENV_DIR/bin/activate"
  "$INSTALL_DIR/yantra" doctor || true
}

# ── Bootstrap ────────────────────────────────────────────────────────────────

run_bootstrap() {
  echo ""
  echo -e "  ${SAFFRON}Setup complete! Ready to meet Chitragupta.${RESET}"
  echo ""
  read -p "  Start the Bootstrap Interview now? [Y/n]: " do_bootstrap
  if [[ ! "$do_bootstrap" =~ ^[Nn]$ ]]; then
    source "$VENV_DIR/bin/activate"
    "$INSTALL_DIR/yantra" bootstrap
  else
    warn "Skipped. Run 'yantra bootstrap' when ready."
  fi
}

# ── Open browser ──────────────────────────────────────────────────────────────

open_dashboard() {
  echo ""
  read -p "  Open dashboard in browser now? [Y/n]: " do_open
  if [[ ! "$do_open" =~ ^[Nn]$ ]]; then
    source "$VENV_DIR/bin/activate"
    "$INSTALL_DIR/yantra" ui &
    sleep 2
    if command -v open &>/dev/null; then
      open "http://localhost:$PORT"
    elif command -v xdg-open &>/dev/null; then
      xdg-open "http://localhost:$PORT"
    fi
  fi
}

# ── Summary ───────────────────────────────────────────────────────────────────

print_summary() {
  echo ""
  echo -e "${GREEN}${BOLD}  ════════════════════════════════════════════${RESET}"
  echo -e "${GREEN}${BOLD}  OpenYantra v${VERSION} installed successfully!${RESET}"
  echo -e "${GREEN}${BOLD}  ════════════════════════════════════════════${RESET}"
  echo ""
  echo -e "  ${SAFFRON}Commands:${RESET}"
  echo "    yantra bootstrap     ← first-time setup"
  echo "    yantra ui            ← browser dashboard"
  echo "    yantra doctor        ← system health check"
  echo "    yantra inbox 'text'  ← quick capture"
  echo "    yantra digest        ← daily summary"
  echo "    yantra telegram      ← start Telegram bot"
  echo ""
  echo -e "  ${DIM}Restart terminal or run: source $([[ "$SHELL" == *zsh* ]] && echo ~/.zshrc || echo ~/.bashrc)${RESET}"
  echo -e "  ${DIM}Desktop shortcut: ~/Desktop/OpenYantra.command${RESET}"
  echo ""
  echo -e "  GitHub: https://github.com/revanthlevaka/OpenYantra"
  echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
  banner
  detect_os
  install_python
  install_libreoffice
  create_venv
  install_deps
  download_files
  create_cli
  create_desktop_shortcut
  setup_path
  run_doctor
  run_bootstrap
  open_dashboard
  print_summary
}

main "$@"
