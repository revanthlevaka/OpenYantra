# ═══════════════════════════════════════════════════════════════
#  OpenYantra v2.12 Installer -- Windows (PowerShell)
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
$VERSION = "4.1.0"
$INSTALL_DIR = "$env:USERPROFILE\openyantra"
$VENV_DIR    = "$INSTALL_DIR\.venv"
$RAW         = "https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main"
$PORT        = 7331

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════╗" -ForegroundColor DarkYellow
    Write-Host "  ║  OpenYantra v$VERSION -- The Sacred Memory Machine    ║" -ForegroundColor Yellow
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
        Write-Warn "Could not set execution policy -- continuing anyway"
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

    # Python not found -- install via winget
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

    $dirs = @("openclaw", "examples", "references", "docs", "assets")
    foreach ($d in $dirs) {
        New-Item -ItemType Directory -Path "$INSTALL_DIR\$d" -Force | Out-Null
    }

    $files = @(
        "openyantra/__init__.py", "openyantra/core.py", "openyantra/cli.py",
        "openyantra/vidyakosha.py", "openyantra/yantra_ui.py",
        "openyantra/yantra_digest.py", "openyantra/telegram_bot.py",
        "openyantra/ios_shortcut.py", "openyantra/yantra_mail.py",
        "openyantra/yantra_migrate.py", "openyantra/yantra_security.py",
        "openyantra/yantra_morning.py", "openyantra/yantra_context.py",
        "openyantra/yantra_sqlite.py", "openyantra/cognitive_mcp.py",
        "openyantra/cognitive_db.py", "openyantra/chitrapat_template.ods",
        "openclaw/hooks.py", "openclaw/plugin.py", "openclaw/__init__.py",
        "examples/bootstrap.py", "examples/langchain_adapter.py",
        "examples/__init__.py", "references/controlled-vocab.md",
        "docs/DEPLOYMENT.md", "PROTOCOL.md", "SKILL.md",
        "MYTHOLOGY.md", "WHITEPAPER.md"
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
# yantra.ps1 -- OpenYantra v$VERSION CLI for Windows
`$INSTALL_DIR = "$INSTALL_DIR"
`$VENV = "$VENV_DIR"
`$PYTHON = "`$VENV\Scripts\python.exe"
`$OY_FILE = if (`$env:OPENYANTRA_FILE) { `$env:OPENYANTRA_FILE } else { "`$env:USERPROFILE\openyantra\chitrapat.ods" }

# Pass all arguments to the Python CLI
& `$PYTHON -m openyantra.cli `$args
"@

    $ps1 | Out-File -FilePath "$INSTALL_DIR\yantra.ps1" -Encoding UTF8

    # .bat wrapper -- no execution policy issues
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
    $Shortcut.Description      = "OpenYantra -- The Sacred Memory Machine"
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
