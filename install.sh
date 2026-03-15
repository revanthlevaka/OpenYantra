#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  OpenYantra v2.1 Installer — Mac + Linux
#  The Sacred Memory Machine
#  Inspired by Chitragupta, the Hindu God of Data
#
#  Usage:
#    curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash
#
#  Or locally:
#    chmod +x install.sh && ./install.sh
# ═══════════════════════════════════════════════════════════════

set -e

REPO="https://github.com/revanthlevaka/OpenYantra"
RAW="https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main"
INSTALL_DIR="$HOME/openyantra"
VERSION="2.1"

# ── Colours ──────────────────────────────────────────────────────────────────

SAFFRON='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
DIM='\033[0;90m'
RESET='\033[0m'
BOLD='\033[1m'

banner() {
  echo ""
  echo -e "${SAFFRON}${BOLD}  ╔═══════════════════════════════════════════╗${RESET}"
  echo -e "${SAFFRON}${BOLD}  ║  OpenYantra v${VERSION} — The Sacred Memory Machine  ║${RESET}"
  echo -e "${SAFFRON}${BOLD}  ║  Inspired by Chitragupta, Hindu God of Data ║${RESET}"
  echo -e "${SAFFRON}${BOLD}  ╚═══════════════════════════════════════════╝${RESET}"
  echo ""
}

log()  { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${SAFFRON}⚠${RESET}  $1"; }
err()  { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
step() { echo -e "\n  ${SAFFRON}▶${RESET} ${BOLD}$1${RESET}"; }

# ── OS detection ─────────────────────────────────────────────────────────────

detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    log "macOS detected"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    log "Linux detected"
  else
    err "Unsupported OS: $OSTYPE. Use install.ps1 for Windows."
  fi
}

# ── Python check ─────────────────────────────────────────────────────────────

check_python() {
  step "Checking Python"

  if command -v python3 &>/dev/null; then
    PY=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$(echo $PY | cut -d. -f1)
    MINOR=$(echo $PY | cut -d. -f2)
    if [[ $MAJOR -lt 3 || ($MAJOR -eq 3 && $MINOR -lt 9) ]]; then
      err "Python 3.9+ required. You have $PY. Please upgrade."
    fi
    log "Python $PY found"
    PYTHON="python3"
  else
    err "Python 3 not found. Install from https://python.org"
  fi
}

# ── pip deps ─────────────────────────────────────────────────────────────────

install_deps() {
  step "Installing Python dependencies"

  DEPS="odfpy pandas scikit-learn faiss-cpu fastapi uvicorn"

  echo -e "  ${DIM}Installing: $DEPS${RESET}"
  $PYTHON -m pip install --quiet --upgrade pip
  $PYTHON -m pip install --quiet $DEPS

  log "Core dependencies installed"

  # Optional: sentence-transformers
  echo ""
  echo -e "  ${DIM}Optional: sentence-transformers improves semantic search quality${RESET}"
  read -p "  Install sentence-transformers? (~300MB) [y/N]: " install_st
  if [[ "$install_st" =~ ^[Yy]$ ]]; then
    $PYTHON -m pip install --quiet sentence-transformers
    log "sentence-transformers installed — VidyaKosha will use all-MiniLM-L6-v2"
  else
    warn "Skipped — using TF-IDF embedder (still works great for personal scale)"
  fi
}

# ── Download files ────────────────────────────────────────────────────────────

download_files() {
  step "Downloading OpenYantra files"

  mkdir -p "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR/openclaw"
  mkdir -p "$INSTALL_DIR/docs"

  FILES=(
    "openyantra.py"
    "vidyakosha.py"
    "yantra_ui.py"
    "openclaw/hooks.py"
    "openclaw/plugin.py"
    "docs/DEPLOYMENT.md"
  )

  for file in "${FILES[@]}"; do
    URL="$RAW/$file"
    DEST="$INSTALL_DIR/$file"
    mkdir -p "$(dirname $DEST)"
    if curl -sSL "$URL" -o "$DEST" 2>/dev/null; then
      log "Downloaded $file"
    else
      warn "Could not download $file from $URL"
    fi
  done
}

# ── Create yantra CLI ─────────────────────────────────────────────────────────

create_cli() {
  step "Creating yantra CLI command"

  YANTRA_BIN="$INSTALL_DIR/yantra"

  cat > "$YANTRA_BIN" << 'SCRIPT'
#!/usr/bin/env bash
# yantra — OpenYantra CLI
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
OY_FILE="${OPENYANTRA_FILE:-$HOME/openyantra/chitrapat.ods}"
PYTHON="${PYTHON:-python3}"

case "$1" in
  bootstrap|init)
    echo "Starting Bootstrap Interview..."
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import run_bootstrap_interview
run_bootstrap_interview('$OY_FILE')
"
    ;;
  ui|dashboard)
    PORT="${2:-7331}"
    echo "Starting OpenYantra Dashboard on http://localhost:$PORT"
    $PYTHON "$INSTALL_DIR/yantra_ui.py" --file "$OY_FILE" --port "$PORT"
    ;;
  health|status)
    $PYTHON -c "
import sys, json; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('$OY_FILE')
h = oy.health_check()
print('OpenYantra Health Check')
print('='*40)
for k,v in h.items():
    if k != 'rows': print(f'  {k:25} {v}')
if 'rows' in h:
    print('  Row counts:')
    for s,n in h['rows'].items():
        print(f'    {s}: {n}')
"
    ;;
  inbox)
    shift
    TEXT="$*"
    if [[ -z "$TEXT" ]]; then
      read -p "Capture: " TEXT
    fi
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('$OY_FILE')
r = oy.inbox('$TEXT')
print('✓ Captured to Inbox' if r.get('status')=='written' else f'Status: {r.get(\"status\")}')
"
    ;;
  route)
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('$OY_FILE')
decisions = oy.route_inbox()
routed = sum(1 for d in decisions if d.get('routed'))
print(f'✓ Routed {routed}/{len(decisions)} inbox items')
for d in decisions:
    print(f'  {d[\"content\"][:50]:50} → {d.get(\"target\",\"unrouted\")}')
"
    ;;
  loops)
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra, SHEET_OPEN_LOOPS
oy = OpenYantra('$OY_FILE')
loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS) if r.get('Resolved?')=='No']
print(f'Open Loops ({len(loops)}):')
for l in loops:
    print(f'  [{l.get(\"Priority\",\"?\"):6}] {l.get(\"Topic\",\"\")[:60]}')
"
    ;;
  diff|beliefs)
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('$OY_FILE')
diffs = oy.diff_beliefs()
if diffs:
    print(f'Potential belief contradictions ({len(diffs)}):')
    for d in diffs: print(f'  {d[\"message\"]}')
else:
    print('✓ No belief contradictions detected')
"
    ;;
  ttl|expire)
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('$OY_FILE')
expired = oy.check_anishtha_ttl()
if expired:
    print(f'Expired open loops ({len(expired)}):')
    for e in expired: print(f'  {e[\"message\"]}')
else:
    print('✓ No expired open loops')
"
    ;;
  version)
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import OpenYantra
print(f'OpenYantra v{OpenYantra.VERSION}')
"
    ;;
  help|--help|-h|"")
    echo ""
    echo "  OpenYantra v2.1 — The Sacred Memory Machine"
    echo "  Inspired by Chitragupta, the Hindu God of Data"
    echo ""
    echo "  COMMANDS:"
    echo "    yantra bootstrap    Interview-based cold start (populates memory)"
    echo "    yantra ui [port]    Open browser dashboard (default: 7331)"
    echo "    yantra health       System status and stats"
    echo "    yantra inbox [text] Quick capture to Inbox"
    echo "    yantra route        Route Inbox items to correct sheets"
    echo "    yantra loops        List open loops (Anishtha)"
    echo "    yantra diff         Check for belief contradictions"
    echo "    yantra ttl          Check for expired open loops"
    echo "    yantra version      Show version"
    echo ""
    echo "  FILE:  $OY_FILE"
    echo "  Set OPENYANTRA_FILE env var to change location"
    echo ""
    ;;
  *)
    echo "Unknown command: $1. Run 'yantra help' for usage."
    exit 1
    ;;
esac
SCRIPT

  chmod +x "$YANTRA_BIN"
  log "yantra CLI created at $YANTRA_BIN"
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
  OPENYANTRA_LINE="export OPENYANTRA_FILE=\"\$HOME/openyantra/chitrapat.ods\""

  if [[ -n "$SHELL_RC" ]]; then
    if ! grep -q "openyantra" "$SHELL_RC" 2>/dev/null; then
      echo "" >> "$SHELL_RC"
      echo "# OpenYantra" >> "$SHELL_RC"
      echo "$PATH_LINE" >> "$SHELL_RC"
      echo "$OPENYANTRA_LINE" >> "$SHELL_RC"
      log "Added to $SHELL_RC"
    else
      log "PATH already configured in $SHELL_RC"
    fi
  else
    warn "Could not detect shell config. Add manually:"
    echo "    $PATH_LINE"
    echo "    $OPENYANTRA_LINE"
  fi

  export PATH="$PATH:$INSTALL_DIR"
}

# ── Bootstrap question ────────────────────────────────────────────────────────

ask_bootstrap() {
  echo ""
  echo -e "  ${SAFFRON}Would you like to set up your memory file now?${RESET}"
  read -p "  Run bootstrap interview? [Y/n]: " do_bootstrap
  if [[ ! "$do_bootstrap" =~ ^[Nn]$ ]]; then
    echo ""
    $PYTHON -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from openyantra import run_bootstrap_interview
run_bootstrap_interview('$HOME/openyantra/chitrapat.ods')
"
  else
    warn "Skipped. Run 'yantra bootstrap' whenever you're ready."
  fi
}

# ── Summary ───────────────────────────────────────────────────────────────────

print_summary() {
  echo ""
  echo -e "${GREEN}${BOLD}  ═══════════════════════════════════════════${RESET}"
  echo -e "${GREEN}${BOLD}  OpenYantra v${VERSION} installed successfully!${RESET}"
  echo -e "${GREEN}${BOLD}  ═══════════════════════════════════════════${RESET}"
  echo ""
  echo -e "  ${SAFFRON}Quick start:${RESET}"
  echo "    yantra bootstrap     ← set up your memory (first time)"
  echo "    yantra ui            ← open browser dashboard"
  echo "    yantra inbox 'text'  ← quick capture"
  echo "    yantra health        ← system status"
  echo ""
  echo -e "  ${DIM}Restart terminal or run: source ~/.zshrc (or ~/.bashrc)${RESET}"
  echo ""
  echo -e "  GitHub: https://github.com/revanthlevaka/OpenYantra"
  echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
  banner
  detect_os
  check_python
  install_deps
  download_files
  create_cli
  setup_path
  ask_bootstrap
  print_summary
}

main "$@"
