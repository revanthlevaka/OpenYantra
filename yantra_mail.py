"""
yantra_mail.py — OpenYantra Email-to-Inbox v2.8
Local SMTP server that accepts forwarded emails → saves to Inbox.

How it works:
  1. This script runs a local SMTP server on port 2525
  2. You forward emails to yantra@localhost (or via mail client rule)
  3. Subject + body land in your Chitrapat Inbox

Setup options:

  Option A — Forward from Gmail/Outlook:
    - Set up a filter: forward matching emails to yantra@localhost
    - Requires local mail relay (Postfix on Linux, or use Option B)

  Option B — Direct send from mail client:
    - SMTP server: localhost, port: 2525, no auth
    - Send any email → lands in Inbox

  Option C — Command line:
    python -c "
    import smtplib
    s = smtplib.SMTP('localhost', 2525)
    s.sendmail('me@me.com', 'yantra@localhost',
               'Subject: Meeting notes\\n\\nDiscussed budget with Priya.')
    s.quit()
    "

  Option D — iPhone Mail app:
    - Add SMTP account: localhost:2525
    - BCC yantra@localhost on any email you want to capture

Usage:
    yantra mail          # start SMTP listener
    yantra mail --port 2525 --file ~/openyantra/chitrapat.ods
"""

from __future__ import annotations

import argparse
import asyncio
import email
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from openyantra import OpenYantra
except ImportError:
    print("openyantra.py not found.")
    sys.exit(1)


# ── SMTP handler ──────────────────────────────────────────────────────────────


def _extract_text(msg) -> tuple[str, str]:
    """Extract subject and body text from email message."""
    subject = msg.get("Subject", "(no subject)").strip()

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                    break
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        except Exception:
            body = str(msg.get_payload())

    return subject.strip(), body.strip()


class YantraMailHandler:
    """Handles incoming SMTP messages → saves to Chitrapat Inbox."""

    def __init__(self, oy: OpenYantra):
        self.oy = oy

    async def handle_DATA(self, server, session, envelope):
        try:
            raw_msg = envelope.content.decode("utf-8", errors="replace")
            msg = email.message_from_string(raw_msg)
            subject, body = _extract_text(msg)
            sender = envelope.mail_from or "unknown"

            # Build capture text
            if body:
                capture = f"[Email from {sender}] {subject}\n\n{body[:500]}"
            else:
                capture = f"[Email from {sender}] {subject}"

            receipt = self.oy.inbox(
                capture,
                source="Agent-observed",
                importance=6,
            )
            ts = datetime.utcnow().strftime("%H:%M:%S")
            status = receipt.get("status", "unknown")
            print(f"[{ts}] Email captured: '{subject[:50]}' from {sender} → {status}")
            return "250 Message accepted"

        except Exception as e:
            print(f"[YantraMail] Error: {e}")
            return "500 Error processing message"


def run_smtp_server(oy_path: str, host: str = "localhost", port: int = 2525):
    """Run the local SMTP server."""
    try:
        from aiosmtpd.controller import Controller
    except ImportError:
        print("\n[YantraMail] aiosmtpd not installed.")
        print("Install: pip install aiosmtpd")
        print("\nFalling back to basic SMTP server...")
        _run_basic_smtp(oy_path, host, port)
        return

    path = Path(oy_path).expanduser()
    if not path.exists():
        print(f"Chitrapat not found at {path}. Run: yantra bootstrap")
        sys.exit(1)

    oy = OpenYantra(str(path), agent_name="YantraMail")
    handler = YantraMailHandler(oy)

    print(f"\n{'='*55}")
    print("  OpenYantra Email-to-Inbox v2.8")
    print(f"{'='*55}")
    print(f"\n  SMTP server: {host}:{port}")
    print("  Address:     yantra@localhost")
    print("\n  Send any email to yantra@localhost → saved to Inbox")
    print("\n  Quick test:")
    print('    python -c "')
    print("    import smtplib")
    print(f"    s = smtplib.SMTP('localhost', {port})")
    print("    s.sendmail('me@test.com', 'yantra@localhost',")
    print("               'Subject: My thought\\n\\nThis lands in Inbox.')")
    print('    s.quit()"')
    print("\n  Waiting for emails... (Ctrl+C to stop)\n")

    controller = Controller(handler, hostname=host, port=port)
    controller.start()

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n[YantraMail] Stopped.")
        controller.stop()


def _run_basic_smtp(oy_path: str, host: str, port: int):
    """Fallback basic SMTP server without aiosmtpd."""
    import smtpd
    import asyncore

    oy = OpenYantra(str(Path(oy_path).expanduser()), agent_name="YantraMail")

    class BasicHandler(smtpd.SMTPServer):
        def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
            try:
                msg = email.message_from_bytes(data)
                subject, body = _extract_text(msg)
                capture = f"[Email] {subject}" + (f"\n\n{body[:300]}" if body else "")
                receipt = oy.inbox(capture, source="Agent-observed", importance=6)
                print(f"Email captured: '{subject[:50]}' → {receipt.get('status')}")
            except Exception as e:
                print(f"Error: {e}")

    BasicHandler((host, port), None)
    print(f"  Basic SMTP server on {host}:{port}")
    print("  Waiting for emails... (Ctrl+C to stop)\n")
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        print("\n[YantraMail] Stopped.")


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Email-to-Inbox v2.8")
    parser.add_argument(
        "--file", "-f", default=str(Path.home() / "openyantra" / "chitrapat.ods")
    )
    parser.add_argument("--port", "-p", type=int, default=2525)
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    run_smtp_server(args.file, args.host, args.port)


if __name__ == "__main__":
    main()
