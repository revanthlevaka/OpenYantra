#!/usr/bin/env python3
"""
OpenYantra CLI v6.2.0
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
import logging as _oy_logging
_oy_log = _oy_logging.getLogger("openyantra")

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
        "webauthn": "webauthn",
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
                                    _oy_log.debug("ignored error", exc_info=True)
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
    context_parser = subparsers.add_parser("context", help="Copy full context to clipboard")
    context_parser.add_argument("--project", "-p", default=None, help="Scope context to specific workspace/project")
    inbox_parser = subparsers.add_parser("inbox", help="Quick capture to Inbox")
    inbox_parser.add_argument("text", nargs="+", help="Text to save to inbox")
    subparsers.add_parser("digest", help="Daily summary")
    subparsers.add_parser("stats", help="Memory growth analytics")
    
    # Memory management
    subparsers.add_parser("health", help="Stats overview")
    route_parser = subparsers.add_parser("route", help="Auto-route Inbox items or zero-retention prompt routing")
    route_parser.add_argument("prompt", nargs="?", default=None, help="Optional natural-language prompt to route to memory subspace centroids")
    route_parser.add_argument("--top-k", "-k", type=int, default=2, help="Number of top sheet subspaces to return")
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
    mcp_parser = subparsers.add_parser("mcp", help="Start or configure MCP JSON-RPC server")
    mcp_parser.add_argument("subcommand", nargs="?", default="serve", choices=["serve", "setup"], help="Subcommand: serve (default) or setup")
    mcp_parser.add_argument("--client", choices=["all", "claude", "cursor"], default="all", help="Target client for setup")

    # Nidra / Sleep Consolidation (v6.0)
    dream_parser = subparsers.add_parser("dream", aliases=["consolidate", "nidra"], help="Autonomous Sleep & Memory Consolidation (Nidra)")
    dream_parser.add_argument("--dry-run", action="store_true", help="Simulate consolidation without committing changes")
    dream_parser.add_argument("--provider", choices=["auto", "ollama", "heuristic"], default="auto", help="Consolidation engine provider")

    # Obsidian Vault (v6.0)
    vault_parser = subparsers.add_parser("vault", help="Bi-directional Obsidian Markdown Vault Sync")
    vault_parser.add_argument("action", choices=["export", "import", "sync"], help="Vault action: export, import, or sync")
    vault_parser.add_argument("path", nargs="?", default="~/openyantra_vault", help="Vault directory path")

    # Desktop App & HUD (v1.0.0 / v6.1.0)
    desktop_parser = subparsers.add_parser("desktop", aliases=["app", "hud"], help="Launch native Desktop App or floating HUD palette")
    desktop_parser.add_argument("--mode", "-m", choices=["hud", "dashboard"], default="hud", help="Desktop window mode: floating 'hud' or full 'dashboard'")
    desktop_parser.add_argument("--port", "-p", type=int, default=7331, help="Local server port")

    # Git Hook Auto-Ingest (v6.1.0)
    hook_parser = subparsers.add_parser("hook", help="Git post-commit auto-ingest hook")
    hook_parser.add_argument("action", choices=["install", "run"], help="Action: install (in target repo) or run (execute post-commit ingest)")
    hook_parser.add_argument("repo", nargs="?", default=".", help="Repository path")

    # Terminal TUI (v6.1.0)
    subparsers.add_parser("tui", help="Launch Cyberpunk Terminal TUI Dashboard")
    
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
                OpenYantra(oy_file)
                print("[+] Database integrity OK")
            except Exception as e:
                print(f"[!] Database error: {e}")
        else:
            print(f"[!] Chitrapat not found at: {oy_file}")
            print("    Run 'yantra bootstrap' to create one")
        sys.exit(0)

    # All commands below here need a valid chitrapat
    if not os.path.exists(oy_file) and args.command not in ["ui", "mcp", "mail", "shortcut", "telegram", "stop", "kill", "desktop", "app", "hud"]:
        print(f"Error: Could not find {oy_file}. Run 'yantra bootstrap' first.")
        sys.exit(1)

    oy = OpenYantra(oy_file) if args.command in [
        "health", "inbox", "stats", "route", "loops", "diff", "ttl", 
        "sync", "corrections", "integrity", "archive", "dream", "consolidate", "nidra", "vault",
        "hook", "tui"
    ] else None

    # Routing commands
    if args.command == "health":
        h = oy.health_check()
        print(f"\n  OpenYantra Health Status: {h.get('status', 'unknown').upper()}")
        print(f"  Chitrapat Size: {h.get('chitrapat_size_kb', 0)} KB")
        print(f"  Chitragupta: {'Alive' if h.get('chitragupta_alive') else 'Inactive'}")
        print(f"  VidyaKosha: {h.get('vidyakosha', 'not installed')}")
        print(f"  Open Loops: {h.get('open_loops', 0)}")
        print(f"  Inbox Pending: {h.get('inbox_pending', 0)}")
        print(f"  Corrections Pending: {h.get('corrections_pending', 0)}")
        print(f"  Stale Projects (>30d): {h.get('stale_projects', 0)}")
        if h.get("rows"):
            print("\n  Sheet Row Counts:")
            for s, count in h["rows"].items():
                print(f"    - {s}: {count} rows")
        print()
    elif args.command == "inbox":
        text = " ".join(args.text)
        oy.inbox(text)
        print(f"[\033[38;2;255;153;51mINBOX\033[0m] Saved: {text}")
    elif args.command == "stats":
        s = oy.stats() if hasattr(oy, "stats") else oy.health_check()
        print(f"\n--- OpenYantra Memory Statistics ---")
        print(f"Total Rows: {s.get('total_rows', 0)}")
        print(f"Open Loops: {s.get('open_loops_total', 0)} (Resolution Rate: {s.get('loop_resolution_rate', 0)}%)")
        print(f"High Importance Items: {s.get('high_importance_items', 0)}")
        print(f"Chitrapat Size: {s.get('chitrapat_size_kb', 0)} KB")
        if s.get("sheet_counts"):
            print("\nRow Counts by Sheet:")
            for sheet, count in s["sheet_counts"].items():
                print(f"  - {sheet}: {count}")
        print()
    elif args.command == "route":
        if getattr(args, "prompt", None):
            import time
            t0 = time.perf_counter()
            routes = oy.route(args.prompt, top_k=getattr(args, "top_k", 2))
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(f"\n--- Zero-Retention Memory Routing ({elapsed_ms:.2f}ms) ---")
            print(f"Prompt: \"{args.prompt}\"")
            if not routes:
                print("No active centroids matched (run `yantra health` or sync index).")
            else:
                print("Active Subspaces:")
                for i, r in enumerate(routes, 1):
                    print(f"  {i}. {r['sheet']} (similarity: {r['score']:.4f})")
            print()
        else:
            decisions = oy.route_inbox()
            if not decisions:
                print("\n[+] No unrouted inbox items found.")
            else:
                print(f"\n--- Routed {len(decisions)} Inbox Items ---")
                for d in decisions:
                    print(f"- '{d.get('content')}' -> {d.get('target', 'Unclassified')}")
    elif args.command == "loops":
        loops = oy.get_sheet("open_loops")
        open_loops = [r for r in loops if r.get("Resolved?") != "Yes"]
        print(f"\n--- Open Loops ({len(open_loops)}) ---")
        for loop in open_loops:
            topic = loop.get("Topic") or loop.get("Description") or "Untitled"
            prio = loop.get("Priority", "Medium")
            ctx = loop.get("Context / What's Unresolved", "")
            print(f"[{prio}] {topic}" + (f" - {ctx}" if ctx else ""))
    elif args.command == "diff":
        diffs = oy.diff_beliefs()
        if not diffs:
            print("\n[+] No belief or identity contradictions detected.")
        else:
            print(f"\n--- Belief Contradictions Detected ({len(diffs)}) ---")
            for d in diffs:
                print(f"- Topic '{d.get('topic')}': {d.get('positions')}")
    elif args.command == "ttl":
        expired = oy.check_anishtha_ttl()
        if not expired:
            print("\n[+] No expired open loops.")
        else:
            print(f"\n--- Expired Open Loops ({len(expired)}) ---")
            for item in expired:
                print(f"- {item.get('message', item)}")
    elif args.command == "sync":
        res = oy.sync_from_ods()
        print(f"[+] Sync complete: {res.get('status', 'OK')}")
    elif args.command == "corrections":
        corrections = oy.get_sheet("corrections")
        pending = [r for r in corrections if r.get("Status") == "Pending"]
        if not pending:
            print("\n[+] No pending corrections.")
        else:
            print(f"\n--- Pending Corrections ({len(pending)}) ---")
            for c in pending:
                sheet = c.get('Sheet', '')
                field = c.get('Field', '')
                old_v = c.get('Old Value', '')
                new_v = c.get('Proposed Value', '')
                reason = c.get('Reason', '')
                print(f"- [{sheet}] {field}: '{old_v}' -> '{new_v}' ({reason})")
    elif args.command == "integrity":
        res = oy.verify_ledger_integrity()
        print("\n--- Ledger Integrity Audit ---")
        print(f"Total entries: {res.get('total', 0)}")
        print(f"Valid SHA-256 signatures: {res.get('valid', 0)}")
        if res.get('invalid'):
            print(f"Invalid signatures: {len(res['invalid'])}")
        if res.get('missing'):
            print(f"Missing signatures: {len(res['missing'])}")
        print(f"Status: {res.get('status', 'OK')}\n")
    elif args.command == "archive":
        res = oy.archive_sessions()
        print(f"[+] Archive complete: status={res.get('status', 'OK')}, archived={res.get('archived', 0)} sessions")
        
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
        cmd = [sys.executable, str(script), "--file", oy_file]
        if getattr(args, "project", None):
            cmd.extend(["--project", args.project])
        subprocess.run(cmd)
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
        if getattr(args, "subcommand", "serve") == "setup":
            from openyantra.mcp_setup import auto_setup_clients
            results = auto_setup_clients(client_filter=args.client, oy_file=oy_file)
            print("\n  🚀 OpenYantra MCP Client Configuration:")
            for r in results:
                print(f"     • {r['client'].capitalize()}: {r['status']} at {r['config_path']}")
            print("\n  Restart your MCP client (Claude Desktop / Cursor) to start using OpenYantra memory tools!\n")
        else:
            script = script_dir / "cognitive_mcp.py"
            subprocess.run([sys.executable, str(script), "--file", oy_file])
    elif args.command in ["dream", "consolidate", "nidra"]:
        from openyantra.yantra_nidra import NidraConsolidator
        nidra = NidraConsolidator(oy)
        dry_run = getattr(args, "dry_run", False)
        provider = getattr(args, "provider", "auto")
        print(f"\n  🌙 Running Nidra Memory Consolidation (dry_run={dry_run}, provider={provider})...")
        report = nidra.consolidate(dry_run=dry_run, provider=provider)
        print(f"  ✨ Consolidation Complete ({report['provider_used']}):")
        print(f"     • Sessions Clustered: {report['sessions_clustered']}")
        print(f"     • Active Projects: {', '.join(report['projects_active']) or 'None'}")
        print(f"     • Open Loops Resolved: {len(report['loops_resolved'])}")
        for l in report["loops_resolved"]:
            print(f"       - {l['topic']} ({l['reason']})")
        print(f"     • Promoted Preferences: {len(report['promoted_preferences'])}")
        for p in report["promoted_preferences"]:
            print(f"       - {p['Belief / Principle']}")
        print(f"\n  Executive Digest:\n     {report['summary']}\n")
    elif args.command == "vault":
        from openyantra.yantra_vault import VaultSync
        v_dir = getattr(args, "path", "~/openyantra_vault")
        sync = VaultSync(oy, v_dir)
        action = getattr(args, "action", "export")
        if action == "export":
            res = sync.export_vault()
            print(f"\n  📓 Obsidian Vault Exported: {res['vault_dir']}")
            print(f"     • Total files exported: {res['files_exported']}\n")
        elif action == "import":
            res = sync.import_vault()
            print(f"\n  📥 Obsidian Vault Imported: {res['vault_dir']}")
            print(f"     • Loops resolved: {len(res['loops_resolved'])}")
            for l in res["loops_resolved"]:
                print(f"       - Resolved: {l}")
            print(f"     • New loops created: {len(res['new_loops_created'])}")
            for l in res["new_loops_created"]:
                print(f"       - Created: {l}")
            print(f"     • Inbox notes imported: {len(res['inbox_items_imported'])}\n")
        elif action == "sync":
            res_imp = sync.import_vault()
            res_exp = sync.export_vault()
            print(f"\n  🔄 Obsidian Vault Synced: {sync.vault_dir}")
            print(f"     • Loops resolved from Obsidian: {len(res_imp['loops_resolved'])}")
            print(f"     • Total files re-exported: {res_exp['files_exported']}\n")
    elif args.command in ["desktop", "app", "hud"]:
        from openyantra.desktop import launch_desktop
        mode = "hud" if args.command == "hud" else getattr(args, "mode", "hud")
        port = getattr(args, "port", 7331)
        launch_desktop(oy_file=oy_file, mode=mode, port=port)
    elif args.command == "hook":
        from openyantra.yantra_git import install_git_hook, ingest_last_commit
        action = getattr(args, "action", "run")
        repo = getattr(args, "repo", ".")
        if action == "install":
            res = install_git_hook(repo)
            if res.get("status") == "success":
                print(f"\n  ✓ Git post-commit auto-ingest hook installed at:")
                print(f"    {res['hook_path']}\n")
            else:
                print(f"\n  [!] Could not install git hook: {res.get('message')}\n")
        elif action == "run":
            res = ingest_last_commit(repo, oy=oy)
            if res.get("status") == "ingested":
                print(f"\n  ✓ Ingested git commit [{res['commit']}] ({res['subject']}) into Session Log.\n")
            else:
                print(f"\n  Notice: {res.get('message', 'No commit ingested')}\n")
    elif args.command == "tui":
        from openyantra.yantra_tui import run_tui
        run_tui(oy)
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
