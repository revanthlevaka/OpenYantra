"""
desktop.py -- OpenYantra Desktop App Launcher v1.0.0
Launches OpenYantra as a native desktop application or floating HUD palette
using pywebview (WebKit/Edge WebView2) with zero Electron bloat.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a local TCP port is already open and accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def ensure_server_running(oy_file: str, port: int = 7331) -> subprocess.Popen | None:
    """Ensures the OpenYantra FastAPI server is active in background."""
    if is_port_open(port):
        return None

    script_dir = Path(__file__).resolve().parent
    ui_script = script_dir / "yantra_ui.py"

    proc = subprocess.Popen(
        [sys.executable, str(ui_script), "--file", oy_file, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait up to 4 seconds for server to be ready
    for _ in range(20):
        if is_port_open(port):
            break
        time.sleep(0.2)

    return proc


def launch_desktop(
    oy_file: Optional[str] = None,
    mode: str = "hud",
    port: int = 7331,
    title: str = "OpenYantra",
    daemon: bool = False,
    provider: str = "auto",
):
    """
    Launches native desktop window (Dashboard or HUD) using pywebview or browser app mode.
    Optionally starts the background Soul-Engine daemon alongside the window.
    """
    chitrapat = oy_file or os.environ.get("OPENYANTRA_FILE", str(Path.home() / "openyantra" / "chitrapat.ods"))
    ensure_server_running(chitrapat, port=port)

    if daemon:
        try:
            import threading
            from openyantra.core import OpenYantra
            from openyantra.yantra_nidra import NidraDaemon
            oy = OpenYantra(chitrapat)
            nidra_worker = NidraDaemon(
                oy,
                interval_seconds=60,
                idle_threshold_seconds=300,
                provider=provider,
                logger_func=lambda msg: print(f"  [Desktop Soul-Engine] {msg}")
            )
            resolved_p, _, _ = nidra_worker._consolidator.resolve_provider(provider)
            t = threading.Thread(target=nidra_worker.run_loop, daemon=True)
            t.start()
            print(f"  👁️ Background Soul-Engine daemon started ({resolved_p}) alongside Desktop HUD.")
        except Exception as e:
            print(f"  [Desktop Warning] Could not spawn background daemon: {e}")

    target_url = f"http://127.0.0.1:{port}/" if mode == "dashboard" else f"http://127.0.0.1:{port}/hud"

    try:
        import webview  # pywebview

        if mode == "hud":
            # Floating palette mode
            webview.create_window(
                title="OpenYantra HUD",
                url=target_url,
                width=640,
                height=380,
                resizable=False,
                frameless=True,
                easy_drag=True,
                on_top=True
            )
            webview.start()
        else:
            # Full dashboard mode
            webview.create_window(
                title=title,
                url=target_url,
                width=1200,
                height=800,
                resizable=True
            )
            webview.start()
    except ImportError:
        print("\n  [OpenYantra Desktop]")
        print("  Notice: 'pywebview' not installed. For native borderless HUD:")
        print("  Run: pip install pywebview\n")
        print(f"  Opening {mode.upper()} in your system browser at: {target_url}\n")
        webbrowser.open(target_url)


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Desktop App v1.0.0")
    parser.add_argument("--file", "-f", default=str(Path.home() / "openyantra" / "chitrapat.ods"))
    parser.add_argument("--port", "-p", type=int, default=7331)
    parser.add_argument("--mode", "-m", choices=["hud", "dashboard"], default="hud", help="Desktop mode: floating 'hud' or full 'dashboard'")
    parser.add_argument("--daemon", "-d", action="store_true", help="Spawn autonomous background soul-engine consolidator with desktop window")
    args = parser.parse_args()

    launch_desktop(oy_file=args.file, mode=args.mode, port=args.port, daemon=args.daemon)


if __name__ == "__main__":
    main()
