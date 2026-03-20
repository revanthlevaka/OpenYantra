"""
telegram_bot.py -- OpenYantra Telegram Bot v2.12
Mobile capture: message @YourBot → saved to Inbox

Setup:
  1. Message @BotFather on Telegram → /newbot → get your token
  2. Set token: export TELEGRAM_BOT_TOKEN="your_token_here"
     Or add to ~/.openyantra_config: TELEGRAM_BOT_TOKEN=your_token
  3. Run: yantra telegram
     Or:  python telegram_bot.py --file ~/openyantra/chitrapat.ods

Commands in Telegram:
  Any text           → saved to Inbox
  /loop [text]       → saved as Open Loop (Anishtha)
  /task [text]       → saved as Task (Kartavya)
  /goal [text]       → saved as Goal (Sankalpa)
  /health            → show system health
  /loops             → list open loops
  /digest            → show daily digest
  /help              → show commands
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes
    )
except ImportError:
    print("python-telegram-bot not installed.")
    print("Run: pip install python-telegram-bot")
    sys.exit(1)

try:
    from openyantra import (
        OpenYantra, WriteRequest,
        SHEET_OPEN_LOOPS, SHEET_TASKS, SHEET_GOALS
    )
except ImportError:
    print("openyantra.py not found in the same directory.")
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────────────────

def get_token() -> str:
    """Get Telegram bot token from env or config file."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if token:
        return token

    config_path = Path.home() / ".openyantra_config"
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
                if token:
                    return token

    return ""


def get_oy(oy_path: str) -> OpenYantra:
    return OpenYantra(oy_path, agent_name="TelegramBot")


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    await update.message.reply_text(
        "🪔 *Namaste. I am Chitragupta, your memory keeper.*\n\n"
        "Send me any text and I'll save it to your Inbox.\n\n"
        "*Commands:*\n"
        "Any text → 📥 Inbox\n"
        "/loop [text] → 🔓 Open Loop\n"
        "/task [text] → ✅ Task\n"
        "/goal [text] → 🎯 Goal\n"
        "/health → system status\n"
        "/loops → open loops\n"
        "/digest → daily summary\n"
        "/help → this message",
        parse_mode="Markdown"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    try:
        oy = get_oy(oy_path)
        h  = oy.health_check()
        msg = (
            f"*OpenYantra Health*\n"
            f"Status: {h.get('status','?')}\n"
            f"Open Loops: {h.get('open_loops', 0)}\n"
            f"Inbox Pending: {h.get('inbox_pending', 0)}\n"
            f"Corrections: {h.get('corrections_pending', 0)}\n"
            f"File Size: {h.get('chitrapat_size_kb', 0)}KB\n"
            f"VidyaKosha: {h.get('vidyakosha','?')}"
        )
    except Exception as e:
        msg = f"Health check failed: {e}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_loops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    try:
        oy    = get_oy(oy_path)
        loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS)
                 if r.get("Resolved?") == "No"]
        if not loops:
            msg = "✅ No open loops!"
        else:
            lines = [f"*Open Loops ({len(loops)}):*"]
            for l in loops[:10]:
                priority = l.get("Priority", "?")
                topic    = l.get("Topic", "?")
                lines.append(f"• [{priority}] {topic}")
            if len(loops) > 10:
                lines.append(f"_...and {len(loops)-10} more_")
            msg = "\n".join(lines)
    except Exception as e:
        msg = f"Could not load loops: {e}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    try:
        from yantra_digest import generate_digest
        msg = generate_digest(oy_path, format="telegram")
    except Exception as e:
        msg = f"Could not generate digest: {e}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    text    = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: /loop [describe the unresolved thread]")
        return
    try:
        oy = get_oy(oy_path)
        oy.flush_open_loop(
            topic    = text[:80],
            context  = text,
            priority = "Medium",
            ttl_days = 30,
            importance = 7,
        )
        await update.message.reply_text(
            f"🔓 *Open Loop saved:*\n_{text[:100]}_",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to save loop: {e}")


async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    text    = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /task [task description]")
        return
    try:
        oy = get_oy(oy_path)
        oy.add_task(task=text, priority="Medium", importance=6)
        await update.message.reply_text(
            f"✅ *Task saved:*\n_{text[:100]}_",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to save task: {e}")


async def cmd_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oy_path = context.bot_data.get("oy_path", "")
    text    = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /goal [goal description]")
        return
    try:
        oy = get_oy(oy_path)
        oy.request_write(WriteRequest(
            requesting_agent = "TelegramBot",
            sheet            = SHEET_GOALS,
            operation        = "add",
            fields           = {"Goal": text, "Type": "Short-term",
                                 "Priority": "Medium", "Status": "Active"},
            confidence       = "High",
            source           = "User-stated",
            importance       = 8,
        ))
        await update.message.reply_text(
            f"🎯 *Goal saved:*\n_{text[:100]}_",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to save goal: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Default handler -- any text goes to Inbox."""
    oy_path = context.bot_data.get("oy_path", "")
    text    = update.message.text or ""

    if not text.strip():
        return

    try:
        oy      = get_oy(oy_path)
        receipt = oy.inbox(text, source="User-stated", importance=6)

        if receipt.get("status") == "written":
            await update.message.reply_text(
                f"📥 *Captured to Inbox*\n_{text[:100]}_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"Saved ({receipt.get('status', 'ok')})")
    except Exception as e:
        await update.message.reply_text(f"Could not save: {e}")


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"[TelegramBot] Error: {context.error}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OpenYantra Telegram Bot v2.12"
    )
    parser.add_argument(
        "--file", "-f",
        default=str(Path.home() / "openyantra" / "chitrapat.ods"),
        help="Path to chitrapat.ods"
    )
    parser.add_argument(
        "--token", "-t",
        default="",
        help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)"
    )
    args = parser.parse_args()

    token = args.token or get_token()

    if not token:
        print("\n[OpenYantra Telegram Bot]")
        print("No bot token found. Get one from @BotFather on Telegram.")
        print("\nSetup:")
        print("  1. Message @BotFather → /newbot → copy the token")
        print("  2. export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("  3. Run: yantra telegram")
        print("\nOr add to ~/.openyantra_config:")
        print("  TELEGRAM_BOT_TOKEN=your_token_here\n")
        sys.exit(1)

    oy_path = Path(args.file).expanduser()
    if not oy_path.exists():
        print(f"[TelegramBot] Chitrapat not found at {oy_path}")
        print("Run: yantra bootstrap")
        sys.exit(1)

    print(f"\n[OpenYantra] Starting Telegram bot...")
    print(f"[OpenYantra] Chitrapat: {oy_path}")
    print(f"[OpenYantra] Send any message to your bot to capture to Inbox")
    print(f"[OpenYantra] Press Ctrl+C to stop\n")

    app = Application.builder().token(token).build()
    app.bot_data["oy_path"] = str(oy_path)

    # Commands
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("loops",  cmd_loops))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("loop",   cmd_loop))
    app.add_handler(CommandHandler("task",   cmd_task))
    app.add_handler(CommandHandler("goal",   cmd_goal))

    # Default -- any text to Inbox
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   handle_message))
    app.add_error_handler(handle_error)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
