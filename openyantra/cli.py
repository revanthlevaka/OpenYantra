#!/usr/bin/env python3
"""
OpenYantra CLI v4.1.0
Command-line interface for The Sacred Memory Machine.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# Setup paths so subprocesses can find the package
script_dir = Path(__file__).resolve().parent
pkg_dir = script_dir.parent
if str(pkg_dir) not in sys.path:
    sys.path.insert(0, str(pkg_dir))

from openyantra.core import OpenYantra, run_bootstrap_interview, __version__

def get_oy_file(args):
    return os.environ.get("OPENYANTRA_FILE", args.file)

def print_banner():
    print(f"\n  \033[38;2;255;153;51mOpenYantra v{__version__} -- The Sacred Memory Machine\033[0m")
    print(f"  Inspired by Chitragupta, Hindu God of Data\n")

def check_dependencies():
    deps = {
        "odfpy": "odf",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
        "faiss-cpu": "faiss",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "aiosmtpd": "aiosmtpd"
    }
    missing = []
    for pkg, mod in deps.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing

def stop_background_servers():
    import signal
    targets = ["yantra_ui.py", "yantra_mail.py", "cognitive_mcp.py", "telegram_bot.py"]
    stopped = []
    
    if sys.platform != "win32":
        try:
            out = subprocess.check_output(["ps", "-eo", "pid,args"], text=True)
            for line in out.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                pid_str, cmdline = parts[0], parts[1]
                try:
                    pid = int(pid_str)
                except ValueError:
                    continue
                if pid == os.getpid():
                    continue
                for target in targets:
                    if target in cmdline and "python" in cmdline.lower():
                        try:
                            os.kill(pid, signal.SIGTERM)
                            stopped.append(f"{target} (PID {pid})")
                        except Exception as e:
                            print(f"Failed to stop {target} (PID {pid}): {e}")
        except Exception as e:
            print(f"Error listing processes: {e}")
    else:
        try:
            out = subprocess.check_output(["wmic", "process", "get", "processid,commandline"], text=True)
            for line in out.splitlines():
                if not line.strip() or "CommandLine" in line:
                    continue
                parts = line.strip().rsplit(None, 1)
                if len(parts) < 2:
                    continue
                cmdline, pid_str = parts[0], parts[1]
                try:
                    pid = int(pid_str)
                except ValueError:
                    continue
                if pid == os.getpid():
                    continue
                for target in targets:
                    if target in cmdline and "python" in cmdline.lower():
                        try:
                            subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            stopped.append(f"{target} (PID {pid})")
                        except Exception as e:
                            print(f"Failed to stop {target} (PID {pid}): {e}")
        except Exception:
            try:
                out = subprocess.check_output(["tasklist", "/v", "/fo", "csv"], text=True)
                import csv
                import io
                reader = csv.reader(io.StringIO(out))
                for row in reader:
                    if len(row) < 9:
                        continue
                    image_name, pid_str, window_title = row[0], row[1], row[8]
                    try:
                        pid = int(pid_str)
                    except ValueError:
                        continue
                    if pid == os.getpid():
                        continue
                    if "python" in image_name.lower():
                        for target in targets:
                            if target in window_title or target in row[6]:
                                try:
                                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    stopped.append(f"{target} (PID {pid})")
                                except Exception:
                                    pass
            except Exception as e:
                print(f"Error listing processes: {e}")

    if stopped:
        print("Stopped background services:")
        for item in stopped:
            print(f"- {item}")
    else:
        print("No running OpenYantra background services found.")

def main():
    parser = argparse.ArgumentParser(description="OpenYantra CLI", usage="yantra <command> [options]")
    parser.add_argument("--file", default="chitrapat.ods", help="Path to Chitrapat ODS file")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup
    subparsers.add_parser("bootstrap", help="12-question interview to create a new Chitrapat")
    subparsers.add_parser("doctor", help="System check: Python, packages, port, ODS integrity")
    
    # Daily use
    subparsers.add_parser("morning", help="Daily brief")
    ui_parser = subparsers.add_parser("ui", help="Browser dashboard")
    ui_parser.add_argument("--port", type=int, default=7331, help="Port to run UI on")
    subparsers.add_parser("context", help="Copy full context to clipboard")
    inbox_parser = subparsers.add_parser("inbox", help="Quick capture to Inbox")
    inbox_parser.add_argument("text", nargs="+", help="Text to save to inbox")
    subparsers.add_parser("digest", help="Daily summary")
    subparsers.add_parser("stats", help="Memory growth analytics")
    
    # Memory management
    subparsers.add_parser("health", help="Stats overview")
    subparsers.add_parser("route", help="Auto-route all unprocessed Inbox items")
    subparsers.add_parser("loops", help="List all unresolved Open Loops")
    subparsers.add_parser("diff", help="Belief contradiction check")
    subparsers.add_parser("ttl", help="Check expired Open Loops")
    subparsers.add_parser("sync", help="Import ODS edits back into SQLite")
    subparsers.add_parser("corrections", help="List and apply pending agent corrections")
    
    # Mobile / Integrations
    subparsers.add_parser("telegram", help="Telegram bot")
    subparsers.add_parser("shortcut", help="iOS Shortcut server")
    mail_parser = subparsers.add_parser("mail", help="Email-to-Inbox SMTP")
    mail_parser.add_argument("--port", type=int, default=2525, help="SMTP port")
    subparsers.add_parser("schedule", help="Schedule daily digest")
    
    # MCP
    subparsers.add_parser("mcp", help="Start MCP JSON-RPC server")
    
    # Maintenance
    subparsers.add_parser("integrity", help="Verify SHA-256 signatures")
    subparsers.add_parser("archive", help="Rotate old session logs")
    subparsers.add_parser("migrate", help="Upgrade older Chitrapat")
    subparsers.add_parser("security", help="Full Chitrapat security audit")
    subparsers.add_parser("open", help="Open Chitrapat in LibreOffice")
    subparsers.add_parser("version", help="Show version")
    subparsers.add_parser("stop", aliases=["kill"], help="Stop running background servers")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)

    oy_file = get_oy_file(args)

    if args.command == "version":
        print(f"OpenYantra v{__version__}")
        sys.exit(0)
        
    if args.command == "bootstrap":
        print_banner()
        run_bootstrap_interview(oy_file)
        sys.exit(0)

    if args.command == "doctor":
        print_banner()
        print("[*] Running system checks...")
        print(f"[-] Python version: {sys.version.split()[0]}")
        missing = check_dependencies()
        if missing:
            print(f"[!] Missing packages: {', '.join(missing)}")
            print(f"    Run: pip install {' '.join(missing)}")
        else:
            print("[+] All Python dependencies installed")
        
        if os.path.exists(oy_file):
            print(f"[+] Found Chitrapat at: {oy_file}")
            try:
                oy = OpenYantra(oy_file)
                print("[+] Database integrity OK")
            except Exception as e:
                print(f"[!] Database error: {e}")
        else:
            print(f"[!] Chitrapat not found at: {oy_file}")
            print("    Run 'yantra bootstrap' to create one")
        sys.exit(0)

    # All commands below here need a valid chitrapat
    if not os.path.exists(oy_file) and args.command not in ["ui", "mcp", "mail", "shortcut", "telegram", "stop", "kill"]:
        print(f"Error: Could not find {oy_file}. Run 'yantra bootstrap' first.")
        sys.exit(1)

    oy = OpenYantra(oy_file) if args.command in [
        "health", "inbox", "stats", "route", "loops", "diff", "ttl", 
        "sync", "corrections", "integrity", "archive"
    ] else None

    # Routing commands
    if args.command == "health":
        oy.health_check()
    elif args.command == "inbox":
        text = " ".join(args.text)
        oy.inbox(text)
        print(f"[\033[38;2;255;153;51mINBOX\033[0m] Saved: {text}")
    elif args.command == "stats":
        oy.health_check()
    elif args.command == "route":
        oy.route_inbox()
    elif args.command == "loops":
        loops = oy.get_table("Open_Loops")
        open_loops = [r for r in loops if r.get("Status") == "Open"]
        print(f"\n--- Open Loops ({len(open_loops)}) ---")
        for loop in open_loops:
            print(f"[{loop.get('Priority', 'Medium')}] {loop.get('Description')}")
    elif args.command == "diff":
        oy.diff_beliefs()
    elif args.command == "ttl":
        oy.check_anishtha_ttl()
    elif args.command == "sync":
        oy.sync_from_ods()
        print("[+] Sync complete")
    elif args.command == "corrections":
        corrections = oy.get_table("Corrections")
        pending = [r for r in corrections if r.get("Status") == "Pending"]
        print(f"\n--- Pending Corrections ({len(pending)}) ---")
        for c in pending:
            print(f"- {c.get('Correction')}")
    elif args.command == "integrity":
        oy.verify_ledger_integrity()
    elif args.command == "archive":
        oy.archive_sessions()
        
    # Subprocess commands
    elif args.command == "ui":
        script = script_dir / "yantra_ui.py"
        cmd = [sys.executable, "-u", str(script), "--file", oy_file, "--port", str(args.port)]
        subprocess.run(cmd)
    elif args.command == "morning":
        script = script_dir / "yantra_morning.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "context":
        script = script_dir / "yantra_context.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "digest":
        script = script_dir / "yantra_digest.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "telegram":
        script = script_dir / "telegram_bot.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "shortcut":
        script = script_dir / "ios_shortcut.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "mail":
        script = script_dir / "yantra_mail.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file, "--port", str(args.port)])
    elif args.command == "migrate":
        script = script_dir / "yantra_migrate.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "security":
        script = script_dir / "yantra_security.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "mcp":
        script = script_dir / "cognitive_mcp.py"
        subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command == "open":
        if sys.platform == "darwin":
            subprocess.run(["open", oy_file])
        elif sys.platform == "win32":
            os.startfile(oy_file)
        else:
            subprocess.run(["xdg-open", oy_file])
    elif args.command == "schedule":
        print("To schedule the daily digest, add this to your crontab (crontab -e):")
        print(f"0 18 * * * {sys.executable} {script_dir}/yantra_digest.py --file {oy_file}")
    elif args.command in ["stop", "kill"]:
        stop_background_servers()

if __name__ == "__main__":
    main()
