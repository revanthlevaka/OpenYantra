# ═══════════════════════════════════════════════════════════════
#  OpenYantra v2.11 Installer — Windows (PowerShell)
#  The Sacred Memory Machine
#  Inspired by Chitragupta, the Hindu God of Data
#
#  Fully self-contained:
#  Installs Python, LibreOffice, all deps, venv, CLI, shortcut
#
#  Usage:
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#    irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex
#  Or:
#    .\install.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$VERSION = "2.11"
$INSTALL_DIR = "$env:USERPROFILE\openyantra"
$VENV_DIR    = "$INSTALL_DIR\.venv"
$RAW         = "https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main"
$PORT        = 7331

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════╗" -ForegroundColor DarkYellow
    Write-Host "  ║  OpenYantra v$VERSION — The Sacred Memory Machine    ║" -ForegroundColor Yellow
    Write-Host "  ║  Inspired by Chitragupta, Hindu God of Data     ║" -ForegroundColor Yellow
    Write-Host "  ╚════════════════════════════════════════════════╝" -ForegroundColor DarkYellow
    Write-Host ""
}

function Write-Step  { param($m) Write-Host "`n  ▶ $m" -ForegroundColor Yellow }
function Write-OK    { param($m) Write-Host "  ✓ $m" -ForegroundColor Green }
function Write-Warn  { param($m) Write-Host "  ⚠ $m" -ForegroundColor DarkYellow }
function Write-Info  { param($m) Write-Host "  $m" -ForegroundColor DarkGray }
function Write-Err   { param($m) Write-Host "  ✗ $m" -ForegroundColor Red; exit 1 }

# ── Enable script execution ───────────────────────────────────────────────────

function Enable-Scripts {
    Write-Step "Enabling PowerShell script execution"
    try {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-OK "Script execution enabled"
    } catch {
        Write-Warn "Could not set execution policy — continuing anyway"
    }
}

# ── Check / Install Python ────────────────────────────────────────────────────

function Install-Python {
    Write-Step "Checking Python 3.9+"

    $pythonCmds = @("python", "python3", "py")
    $PYTHON = $null

    foreach ($cmd in $pythonCmds) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -ge 9) {
                    $script:PYTHON = $cmd
                    Write-OK "Python $major.$minor found ($cmd)"
                    return
                }
            }
        } catch {}
    }

    # Python not found — install via winget
    Write-Warn "Python 3.11 not found. Installing via winget..."

    # Install winget if not present
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Info "Installing winget (App Installer)..."
        $url = "https://aka.ms/getwinget"
        $tmp = "$env:TEMP\AppInstaller.msixbundle"
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        Add-AppxPackage -Path $tmp
    }

    winget install --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $script:PYTHON = "python"
    Write-OK "Python 3.11 installed via winget"
}

# ── Install LibreOffice ───────────────────────────────────────────────────────

function Install-LibreOffice {
    Write-Step "Checking LibreOffice"

    $lo = Get-Command soffice -ErrorAction SilentlyContinue
    if ($lo) {
        Write-OK "LibreOffice already installed"
        return
    }

    Write-Warn "LibreOffice not found. Installing via winget..."
    try {
        winget install --id TheDocumentFoundation.LibreOffice --silent `
              --accept-source-agreements --accept-package-agreements
        Write-OK "LibreOffice installed"
    } catch {
        Write-Warn "Could not auto-install LibreOffice. Get it from: https://libreoffice.org"
    }
}

# ── Create virtualenv ─────────────────────────────────────────────────────────

function Create-Venv {
    Write-Step "Creating isolated Python environment"

    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

    if (Test-Path $VENV_DIR) {
        Write-OK "Virtual environment already exists"
    } else {
        & $script:PYTHON -m venv $VENV_DIR
        Write-OK "Virtual environment created"
    }

    $script:PYTHON = "$VENV_DIR\Scripts\python.exe"
    $script:PIP    = "$VENV_DIR\Scripts\pip.exe"

    & $script:PIP install --quiet --upgrade pip
    Write-OK "pip upgraded"
}

# ── Install dependencies ──────────────────────────────────────────────────────

function Install-Deps {
    Write-Step "Installing Python dependencies"

    $deps = @(
        "odfpy", "pandas", "scikit-learn", "faiss-cpu",
        "fastapi", "uvicorn[standard]", "python-telegram-bot",
        "requests", "schedule"
    )

    Write-Info "Installing: $($deps -join ', ')"
    & $script:PIP install --quiet $deps
    Write-OK "All dependencies installed"
    Write-Info "Using TF-IDF embedder (fast). For better search: pip install sentence-transformers"
}

# ── Download files ────────────────────────────────────────────────────────────

function Download-Files {
    Write-Step "Downloading OpenYantra v$VERSION files"

    $dirs = @("openclaw", "examples", "references", "docs", "assets", "UI\v3")
    foreach ($d in $dirs) {
        New-Item -ItemType Directory -Path "$INSTALL_DIR\$d" -Force | Out-Null
    }

    $files = @(
        "openyantra.py", "vidyakosha.py", "yantra_ui.py",
        "yantra_digest.py", "telegram_bot.py", "ios_shortcut.py",
        "UI/v3/dashboard.html",
        "openclaw/hooks.py", "openclaw/plugin.py", "openclaw/__init__.py",
        "examples/bootstrap.py", "examples/langchain_adapter.py",
        "examples/__init__.py", "references/controlled-vocab.md",
        "docs/DEPLOYMENT.md", "docs/BRAND_MANUAL.md", "docs/VISUAL_GUIDE.md",
        "PROTOCOL.md", "SKILL.md", "MYTHOLOGY.md", "WHITEPAPER.md",
        "openyantra-brand-manual.html", "visual-guide.html"
    )

    foreach ($file in $files) {
        $url  = "$RAW/$file"
        $dest = "$INSTALL_DIR\$($file.Replace('/', '\'))"
        $dir  = Split-Path $dest
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        try {
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
            Write-OK "Downloaded $file"
        } catch {
            Write-Warn "Could not download $file"
        }
    }
}

# ── Create yantra CLI ─────────────────────────────────────────────────────────

function Create-CLI {
    Write-Step "Creating yantra CLI"

    $ps1 = @"
# yantra.ps1 — OpenYantra v$VERSION CLI for Windows
`$INSTALL_DIR = "$INSTALL_DIR"
`$VENV = "$VENV_DIR"
`$PYTHON = "`$VENV\Scripts\python.exe"
`$OY_FILE = if (`$env:OPENYANTRA_FILE) { `$env:OPENYANTRA_FILE } else { "`$env:USERPROFILE\openyantra\chitrapat.ods" }

switch (`$args[0]) {
    "bootstrap" { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import run_bootstrap_interview; run_bootstrap_interview('`$OY_FILE')" }
    "ui" {
        `$port = if (`$args[1]) { `$args[1] } else { "$PORT" }
        Start-Process `$PYTHON -ArgumentList "`$INSTALL_DIR\yantra_ui.py --file `$OY_FILE --port `$port" -NoNewWindow
        Start-Sleep 2
        Start-Process "http://localhost:`$port"
    }
    "doctor" {
        & `$PYTHON -c "
import sys, importlib, socket
sys.path.insert(0,'`$INSTALL_DIR')
print('OpenYantra Doctor v$VERSION'); print('='*45)
pv = sys.version_info
print(f'  Python {pv.major}.{pv.minor}  {chr(10003) if pv.major==3 and pv.minor>=9 else chr(10007)+\" Need 3.9+\"}')
for pkg in ['odfpy','pandas','sklearn','faiss','fastapi','uvicorn']:
    try: importlib.import_module(pkg); print(f'  {pkg:20} {chr(10003)}')
    except: print(f'  {pkg:20} {chr(10007)} missing')
try:
    s=socket.socket(); s.bind(('127.0.0.1',$PORT)); s.close(); print('  Port $PORT           {chr(10003)} available')
except: print('  Port $PORT           {chr(10007)} in use')
import os; f=os.path.expanduser('`$OY_FILE')
print(f'  Chitrapat  {chr(10003) if os.path.exists(f) else chr(10007)+\" run: yantra bootstrap\"}')"
    }
    "health"  { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; oy=OpenYantra('`$OY_FILE'); h=oy.health_check(); [print(f'  {k}: {v}') for k,v in h.items() if k!='rows']" }
    "inbox"   {
        `$text = `$args[1..`$args.Length] -join ' '
        if (-not `$text) { `$text = Read-Host "Capture" }
        & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; oy=OpenYantra('`$OY_FILE'); r=oy.inbox('`$text'); print('Captured' if r.get('status')=='written' else r.get('status'))"
    }
    "digest"  { & `$PYTHON "`$INSTALL_DIR\yantra_digest.py" --file `$OY_FILE }
    "route"   { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; oy=OpenYantra('`$OY_FILE'); d=oy.route_inbox(); r=sum(1 for x in d if x.get('routed')); print(f'Routed {r}/{len(d)} inbox items')" }
    "loops"   { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra,SHEET_OPEN_LOOPS; oy=OpenYantra('`$OY_FILE'); loops=[r for r in oy._read_sheet(SHEET_OPEN_LOOPS) if r.get('Resolved?')=='No']; print(f'Open Loops ({len(loops)}):'); [print(f'  [{l.get(\"Priority\",\"?\"):8}] {l.get(\"Topic\",\"\")[:55]}') for l in loops]" }
    "telegram"{ & `$PYTHON "`$INSTALL_DIR\telegram_bot.py" --file `$OY_FILE }
    "shortcut"{ & `$PYTHON "`$INSTALL_DIR\ios_shortcut.py" --file `$OY_FILE }
    "morning" { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; oy=OpenYantra('`$OY_FILE'); print(oy.morning_brief())" }
    "context" { & `$PYTHON -c "import sys; sys.path.insert(0,'`$INSTALL_DIR'); from openyantra import OpenYantra; oy=OpenYantra('`$OY_FILE'); print(oy.copy_context())" }
    "open"    { Start-Process soffice -ArgumentList `$OY_FILE }
    "version" { Write-Host "OpenYantra v$VERSION" }
    default   {
        Write-Host "`n  OpenYantra v$VERSION — The Sacred Memory Machine"
        Write-Host "`n  COMMANDS:"
        @("bootstrap","ui [port]","morning","context","doctor","health","inbox [text]","route","digest","loops","telegram","shortcut","open","version") | ForEach-Object { Write-Host "    yantra $_" }
        Write-Host ""
    }
}
"@

    $ps1 | Out-File -FilePath "$INSTALL_DIR\yantra.ps1" -Encoding UTF8

    # .bat wrapper — no execution policy issues
    @"
@echo off
PowerShell -ExecutionPolicy Bypass -File "$INSTALL_DIR\yantra.ps1" %*
"@ | Out-File -FilePath "$INSTALL_DIR\yantra.bat" -Encoding ASCII

    Write-OK "yantra.bat + yantra.ps1 created"
}

# ── Desktop shortcut ──────────────────────────────────────────────────────────

function Create-Shortcut {
    Write-Step "Creating desktop shortcut"

    $WshShell   = New-Object -ComObject WScript.Shell
    $Shortcut   = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OpenYantra.lnk")
    $Shortcut.TargetPath       = "cmd.exe"
    $Shortcut.Arguments        = "/c `"$INSTALL_DIR\yantra.bat`" ui"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.Description      = "OpenYantra — The Sacred Memory Machine"
    try {
        $icon = "$INSTALL_DIR\assets\icon_512.png"
        if (Test-Path $icon) { $Shortcut.IconLocation = $icon }
    } catch {}
    $Shortcut.Save()
    Write-OK "Desktop shortcut created"
}

# ── Add to PATH ───────────────────────────────────────────────────────────────

function Setup-Path {
    Write-Step "Configuring PATH"

    $cur = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($cur -notlike "*openyantra*") {
        [Environment]::SetEnvironmentVariable("PATH", "$cur;$INSTALL_DIR", "User")
        $env:PATH = "$env:PATH;$INSTALL_DIR"
        Write-OK "Added $INSTALL_DIR to PATH"
    } else {
        Write-OK "PATH already configured"
    }
    [Environment]::SetEnvironmentVariable("OPENYANTRA_FILE",
        "$env:USERPROFILE\openyantra\chitrapat.ods", "User")
    Write-OK "OPENYANTRA_FILE environment variable set"
}

# ── Doctor ────────────────────────────────────────────────────────────────────

function Run-Doctor {
    Write-Step "Running yantra doctor"
    try { & "$INSTALL_DIR\yantra.bat" doctor } catch { Write-Warn "Doctor check skipped" }
}

# ── Bootstrap ─────────────────────────────────────────────────────────────────

function Run-Bootstrap {
    Write-Host ""
    Write-Host "  Setup complete! Ready to meet Chitragupta." -ForegroundColor Yellow
    $yn = Read-Host "  Start Bootstrap Interview now? [Y/n]"
    if ($yn -notmatch "^[Nn]") {
        & "$INSTALL_DIR\yantra.bat" bootstrap
    } else {
        Write-Warn "Skipped. Run 'yantra bootstrap' when ready."
    }
}

# ── Open dashboard ────────────────────────────────────────────────────────────

function Open-Dashboard {
    $yn = Read-Host "  Open dashboard in browser now? [Y/n]"
    if ($yn -notmatch "^[Nn]") {
        & "$INSTALL_DIR\yantra.bat" ui
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────

function Print-Summary {
    Write-Host ""
    Write-Host "  ══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  OpenYantra v$VERSION installed successfully!" -ForegroundColor Green
    Write-Host "  ══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor Yellow
    Write-Host "    yantra bootstrap    ← first-time setup"
    Write-Host "    yantra ui           ← browser dashboard"
    Write-Host "    yantra doctor       ← system health check"
    Write-Host "    yantra inbox 'text' ← quick capture"
    Write-Host "    yantra digest       ← daily summary"
    Write-Host "    yantra shortcut     ← iOS Shortcut capture"
    Write-Host ""
    Write-Host "  Note: Restart terminal for PATH changes to take effect" -ForegroundColor DarkGray
    Write-Host "  Desktop shortcut: OpenYantra.lnk on your Desktop" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  GitHub: https://github.com/revanthlevaka/OpenYantra"
    Write-Host ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Banner
Enable-Scripts
Install-Python
Install-LibreOffice
Create-Venv
Install-Deps
Download-Files
Create-CLI
Create-Shortcut
Setup-Path
Run-Doctor
Run-Bootstrap
Open-Dashboard
Print-Summary
