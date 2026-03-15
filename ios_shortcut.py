"""
ios_shortcut.py — OpenYantra iOS Shortcut Integration v2.8
Local HTTP endpoint that receives captures from iOS Shortcuts.

How it works:
  1. This script runs a tiny HTTP server on your Mac/Linux machine
  2. iOS Shortcut sends POST to http://your-mac-ip:7332/inbox
  3. Captured text lands in your Chitrapat Inbox instantly

Setup:
  1. Run: yantra shortcut
     Prints your Mac's local IP and the shortcut URL

  2. On iPhone — create a Shortcut:
     • Trigger: Share Sheet (any text/URL) OR Ask for Input
     • Action: Get Contents of URL
       URL: http://YOUR_MAC_IP:7332/inbox
       Method: POST
       Headers: Content-Type = application/json
       Body: {"text": "[Shortcut Input]", "source": "iOS"}
     • (Optional) Add to Home Screen

  3. From anywhere on iPhone:
     • Select text → Share → OpenYantra
     • Or: tap Home Screen shortcut → type thought → sent

  Tip: Use the same shortcut with "Ask for Input" as your
       quick capture widget on iPhone home screen.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from openyantra import OpenYantra
except ImportError:
    print("openyantra.py not found."); sys.exit(1)

# ── Request handler ───────────────────────────────────────────────────────────

class ShortcutHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging — we log our own

    def do_POST(self):
        if self.path not in ("/inbox", "/capture", "/"):
            self.send_response(404); self.end_headers()
            self.wfile.write(b'{"error": "Use /inbox"}')
            return

        try:
            length  = int(self.headers.get("Content-Length", 0))
            raw     = self.rfile.read(length)
            payload = json.loads(raw)
            text    = payload.get("text", "").strip()
            source  = payload.get("source", "iOS Shortcut")
            importance = int(payload.get("importance", 6))

            if not text:
                self.send_response(400); self.end_headers()
                self.wfile.write(b'{"error": "text required"}')
                return

            oy      = self.server.oy
            receipt = oy.inbox(text, source=source, importance=importance)
            status  = receipt.get("status", "unknown")

            ts = datetime.utcnow().strftime("%H:%M:%S")
            print(f"[{ts}] iOS capture: {text[:60]}{'...' if len(text)>60 else ''} → {status}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": status,
                "message": "Captured to Inbox" if status == "written" else status,
                "timestamp": datetime.utcnow().isoformat(),
            }).encode())

        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            oy = self.server.oy
            h  = oy.health_check()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(h).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OpenYantra iOS Shortcut Server v2.8 -- POST /inbox to capture")

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── Server ────────────────────────────────────────────────────────────────────

class ShortcutServer(HTTPServer):
    def __init__(self, *args, oy: OpenYantra, **kwargs):
        super().__init__(*args, **kwargs)
        self.oy = oy


def get_local_ip() -> str:
    """Get the machine's local network IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_shortcut_instructions(ip: str, port: int):
    print(f"\n{'='*60}")
    print(f"  OpenYantra iOS Shortcut Server v2.8")
    print(f"{'='*60}")
    print(f"\n  Server URL: http://{ip}:{port}/inbox")
    print(f"\n  iPhone Shortcut setup:")
    print(f"  ┌─────────────────────────────────────────────┐")
    print(f"  │ 1. Open Shortcuts app on iPhone              │")
    print(f"  │ 2. Tap + → New Shortcut                      │")
    print(f"  │ 3. Add action: Ask for Input                  │")
    print(f"  │    (or use Share Sheet for text selection)    │")
    print(f"  │ 4. Add action: Get Contents of URL           │")
    print(f"  │    URL:    http://{ip}:{port}/inbox  │")
    print(f"  │    Method: POST                               │")
    print(f"  │    Header: Content-Type = application/json    │")
    print(f"  │    Body:   {{\"text\": [Input]}}               │")
    print(f"  │ 5. Add to Home Screen as widget               │")
    print(f"  └─────────────────────────────────────────────┘")
    print(f"\n  Mac must be on the same WiFi as iPhone.")
    print(f"  Health check: http://{ip}:{port}/health")
    print(f"\n  Waiting for captures... (Ctrl+C to stop)\n")


def main():
    parser = argparse.ArgumentParser(
        description="OpenYantra iOS Shortcut Server v2.8"
    )
    parser.add_argument(
        "--file", "-f",
        default=str(Path.home() / "openyantra" / "chitrapat.ods")
    )
    parser.add_argument("--port", "-p", type=int, default=7332)
    parser.add_argument("--host", default="0.0.0.0",
                        help="0.0.0.0 = accessible from iPhone on same WiFi")
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.exists():
        print(f"Chitrapat not found at {path}. Run: yantra bootstrap")
        sys.exit(1)

    oy     = OpenYantra(str(path), agent_name="iOSShortcut")
    ip     = get_local_ip()
    server = ShortcutServer((args.host, args.port),
                             ShortcutHandler, oy=oy)

    print_shortcut_instructions(ip, args.port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OpenYantra] iOS Shortcut server stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
