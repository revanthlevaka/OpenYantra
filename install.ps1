# ═══════════════════════════════════════════════════════════════
#  OpenYantra v2.1 Installer — Windows (PowerShell)
#  The Sacred Memory Machine
#  Inspired by Chitragupta, the Hindu God of Data
#
#  Usage (run as Administrator or with execution policy set):
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#    irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex
#
#  Or locally:
#    .\install.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$VERSION    = "2.1"
$INSTALL_DIR = "$env:USERPROFILE\openyantra"
$RAW        = "https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main"

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════╗" -ForegroundColor DarkYellow
    Write-Host "  ║  OpenYantra v$VERSION — The Sacred Memory Machine  ║" -ForegroundColor Yellow
    Write-Host "  ║  Inspired by Chitragupta, Hindu God of Data  ║" -ForegroundColor Yellow
    Write-Host "  ╚════════════════════════════════════════════╝" -ForegroundColor DarkYellow
    Write-Host ""
}

function Write-Step  { param($msg) Write-Host "`n  ▶ $msg" -ForegroundColor Yellow }
function Write-OK    { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  ⚠ $msg" -ForegroundColor DarkYellow }
function Write-Err   { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# ── Check Python ──────────────────────────────────────────────────────────────

function Check-Python {
    Write-Step "Checking Python"
    try {
        $ver = python --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
                Write-Err "Python 3.9+ required. You have $ver. Install from https://python.org"
            }
            Write-OK "$ver found"
            return $true
        }
    } catch {}
    Write-Err "Python not found. Install from https://python.org"
}

# ── Install deps ──────────────────────────────────────────────────────────────

function Install-Deps {
    Write-Step "Installing Python dependencies"
    $deps = "odfpy pandas scikit-learn faiss-cpu fastapi uvicorn"
    Write-Host "  Installing: $deps" -ForegroundColor DarkGray
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet $deps.Split(" ")
    Write-OK "Core dependencies installed"

    Write-Host ""
    Write-Host "  Optional: sentence-transformers improves semantic search" -ForegroundColor DarkGray
    $yn = Read-Host "  Install sentence-transformers? (~300MB) [y/N]"
    if ($yn -match "^[Yy]") {
        python -m pip install --quiet sentence-transformers
        Write-OK "sentence-transformers installed"
    } else {
        Write-Warn "Skipped — using TF-IDF embedder (works great at personal scale)"
    }
}

# ── Download files ────────────────────────────────────────────────────────────

function Download-Files {
    Write-Step "Downloading OpenYantra files"

    $dirs = @("$INSTALL_DIR", "$INSTALL_DIR\openclaw", "$INSTALL_DIR\docs")
    foreach ($d in $dirs) {
        if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
    }

    $files = @(
        "openyantra.py",
        "vidyakosha.py",
        "yantra_ui.py",
        "openclaw/hooks.py",
        "openclaw/plugin.py",
        "docs/DEPLOYMENT.md"
    )

    foreach ($file in $files) {
        $url  = "$RAW/$file"
        $dest = "$INSTALL_DIR\$($file.Replace('/', '\'))"
        $dir  = Split-Path $dest
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        try {
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
            Write-OK "Downloaded $file"
        } catch {
            Write-Warn "Could not download $file"
        }
    }
}

# ── Create yantra.ps1 CLI ─────────────────────────────────────────────────────

function Create-CLI {
    Write-Step "Creating yantra CLI"

    $script = @"
# yantra.ps1 — OpenYantra CLI for Windows
`$INSTALL_DIR = "$INSTALL_DIR"
`$OY_FILE = if (`$env:OPENYANTRA_FILE) { `$env:OPENYANTRA_FILE } else { "`$env:USERPROFILE\openyantra\chitrapat.ods" }

switch (`$args[0]) {
    "bootstrap" {
        python -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import run_bootstrap_interview; run_bootstrap_interview('`$OY_FILE')"
    }
    "ui" {
        `$port = if (`$args[1]) { `$args[1] } else { "7331" }
        Write-Host "Opening http://localhost:`$port"
        python "`$INSTALL_DIR\yantra_ui.py" --file "`$OY_FILE" --port `$port
    }
    "health" {
        python -c "
import sys; sys.path.insert(0,'`$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('`$OY_FILE')
h = oy.health_check()
print('OpenYantra Health'); print('='*40)
for k,v in h.items():
    if k != 'rows': print(f'  {k:25} {v}')
"
    }
    "inbox" {
        `$text = `$args[1..`$args.Length] -join ' '
        if (-not `$text) { `$text = Read-Host "Capture" }
        python -c "
import sys; sys.path.insert(0,'`$INSTALL_DIR')
from openyantra import OpenYantra
oy = OpenYantra('`$OY_FILE')
r = oy.inbox('`$text')
print('✓ Captured' if r.get('status')=='written' else r.get('status'))
"
    }
    "loops" {
        python -c "
import sys; sys.path.insert(0,'`$INSTALL_DIR')
from openyantra import OpenYantra, SHEET_OPEN_LOOPS
oy = OpenYantra('`$OY_FILE')
loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS) if r.get('Resolved?')=='No']
print(f'Open Loops ({len(loops)}):')
for l in loops: print(f'  [{l.get(\"Priority\",\"?\"):6}] {l.get(\"Topic\",\"\")[:60]}')
"
    }
    "version" { python -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; print(f'OpenYantra v{OpenYantra.VERSION}')" }
    default {
        Write-Host ""
        Write-Host "  OpenYantra v2.1 — The Sacred Memory Machine"
        Write-Host ""
        Write-Host "  COMMANDS:"
        Write-Host "    yantra bootstrap    Interview-based cold start"
        Write-Host "    yantra ui [port]    Browser dashboard (default: 7331)"
        Write-Host "    yantra health       System status"
        Write-Host "    yantra inbox [text] Quick capture"
        Write-Host "    yantra loops        List open loops"
        Write-Host "    yantra version      Show version"
        Write-Host ""
    }
}
"@

    $script | Out-File -FilePath "$INSTALL_DIR\yantra.ps1" -Encoding UTF8
    Write-OK "yantra.ps1 created at $INSTALL_DIR\yantra.ps1"

    # Create yantra.bat wrapper
    @"
@echo off
powershell -ExecutionPolicy Bypass -File "$INSTALL_DIR\yantra.ps1" %*
"@ | Out-File -FilePath "$INSTALL_DIR\yantra.bat" -Encoding ASCII
    Write-OK "yantra.bat wrapper created"
}

# ── Add to PATH ───────────────────────────────────────────────────────────────

function Setup-Path {
    Write-Step "Setting up PATH"
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*openyantra*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$INSTALL_DIR", "User")
        $env:PATH = "$env:PATH;$INSTALL_DIR"
        Write-OK "Added $INSTALL_DIR to user PATH"
    } else {
        Write-OK "PATH already configured"
    }

    # Set OPENYANTRA_FILE env var
    [Environment]::SetEnvironmentVariable("OPENYANTRA_FILE",
        "$env:USERPROFILE\openyantra\chitrapat.ods", "User")
    Write-OK "OPENYANTRA_FILE environment variable set"
}

# ── Bootstrap question ────────────────────────────────────────────────────────

function Ask-Bootstrap {
    Write-Host ""
    Write-Host "  Would you like to set up your memory file now?" -ForegroundColor Yellow
    $yn = Read-Host "  Run bootstrap interview? [Y/n]"
    if ($yn -notmatch "^[Nn]") {
        python -c "
import sys; sys.path.insert(0,'$INSTALL_DIR')
from openyantra import run_bootstrap_interview
run_bootstrap_interview('$env:USERPROFILE\openyantra\chitrapat.ods')
"
    } else {
        Write-Warn "Skipped. Run 'yantra bootstrap' whenever ready."
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────

function Print-Summary {
    Write-Host ""
    Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  OpenYantra v$VERSION installed successfully!" -ForegroundColor Green
    Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Quick start:" -ForegroundColor Yellow
    Write-Host "    yantra bootstrap    ← set up your memory"
    Write-Host "    yantra ui           ← open browser dashboard"
    Write-Host "    yantra inbox 'text' ← quick capture"
    Write-Host "    yantra health       ← system status"
    Write-Host ""
    Write-Host "  Note: Restart your terminal for PATH changes to take effect" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  GitHub: https://github.com/revanthlevaka/OpenYantra"
    Write-Host ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Banner
Check-Python
Install-Deps
Download-Files
Create-CLI
Setup-Path
Ask-Bootstrap
Print-Summary
