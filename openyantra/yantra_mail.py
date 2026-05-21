#!/usr/bin/env python3
"""
OpenYantra Mail Server (v4.1.0)
A simple SMTP server that listens for incoming emails and routes them to the Inbox.
"""

import asyncio
import email
from email.message import Message
import argparse
import os
import sys

from aiosmtpd.controller import Controller
from openyantra.core import OpenYantra

class InboxHandler:
    def __init__(self, oy_file: str):
        self.oy_file = oy_file
        self.oy = OpenYantra(oy_file)

    async def handle_DATA(self, server, session, envelope):
        peer = session.peer
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content

        try:
            msg = email.message_from_bytes(data)
            subject = msg.get('Subject', '(No Subject)')
            
            # Extract plain text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition'))
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        body += part.get_payload(decode=True).decode(errors='replace')
            else:
                body = msg.get_payload(decode=True).decode(errors='replace')

            inbox_text = f"{subject}\n\n{body}".strip()
            print(f"[\033[38;2;255;153;51mMAIL\033[0m] Received email: {subject}")
            
            # Save to Inbox
            self.oy.inbox(inbox_text)
            print(f"[\033[38;2;255;153;51mINBOX\033[0m] Message saved to Chitrapat")
            
            return '250 Message accepted for delivery'
            
        except Exception as e:
            print(f"Error processing email: {e}")
            return f'500 Error processing email: {str(e)}'

def main():
    parser = argparse.ArgumentParser(description="OpenYantra Mail Server")
    parser.add_argument("--port", type=int, default=2525, help="SMTP port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--file", type=str, default="chitrapat.ods", help="Path to Chitrapat ODS file")
    args = parser.parse_args()

    oy_file = os.environ.get("OPENYANTRA_FILE", args.file)
    handler = InboxHandler(oy_file)
    controller = Controller(handler, hostname=args.host, port=args.port)
    
    print(f"\n  \033[38;2;255;153;51mOpenYantra Mail Server\033[0m")
    print(f"  Listening on {args.host}:{args.port}")
    print(f"  Routing emails to: {oy_file}\n")
    
    controller.start()
    
    try:
        # Keep running
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down mail server...")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
