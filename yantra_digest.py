"""
yantra_digest.py -- OpenYantra Daily Digest v2.12

Proactively surfaces what matters -- open loops, stale projects,
memory insights, and a random past memory for reflection.

Usage:
    yantra digest                        # terminal output
    python yantra_digest.py --file ~/openyantra/chitrapat.ods
    python yantra_digest.py --schedule   # run daily at 8am
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from openyantra import (
        OpenYantra,
        SHEET_OPEN_LOOPS, SHEET_PROJECTS, SHEET_TASKS,
        SHEET_INBOX, SHEET_SESSION_LOG, SHEET_BELIEFS,
        SHEET_GOALS
    )
except ImportError:
    print("openyantra.py not found. Ensure it's in the same directory.")
    sys.exit(1)


# ── Digest generator ──────────────────────────────────────────────────────────

def generate_digest(oy_path: str, format: str = "terminal") -> str:
    """
    Generate a daily digest from the Chitrapat.

    format: "terminal" | "telegram" | "email"
    """
    oy      = OpenYantra(oy_path, agent_name="Digest")
    today   = date.today().isoformat()
    health  = oy.health_check()

    sections = []

    # ── Header ────────────────────────────────────────────────────────────────

    if format == "terminal":
        sections.append(
            f"\n{'═'*55}\n"
            f"  🌅  OpenYantra Daily Digest -- {today}\n"
            f"{'═'*55}"
        )
    elif format == "telegram":
        sections.append(f"🌅 *OpenYantra Daily Digest*\n_{today}_")
    else:
        sections.append(f"OpenYantra Daily Digest -- {today}")

    # ── Open Loops needing attention ──────────────────────────────────────────

    all_loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS)
                 if r.get("Resolved?") == "No"]

    # Sort by importance desc, then by TTL asc
    def loop_priority(l):
        imp = int(l.get("Importance", 5) or 5)
        opened = str(l.get("Opened", ""))[:10]
        try:
            age = (datetime.utcnow() - datetime.fromisoformat(opened)).days
        except Exception:
            age = 0
        ttl = int(l.get("TTL_Days", 90) or 90)
        days_left = ttl - age
        return (-imp, days_left)

    urgent_loops = sorted(all_loops, key=loop_priority)[:5]

    if urgent_loops:
        if format == "terminal":
            sections.append(f"\n  🔓  Open Loops ({len(all_loops)} total):")
            for l in urgent_loops:
                topic     = l.get("Topic", "?")[:55]
                priority  = l.get("Priority", "?")
                opened    = str(l.get("Opened", ""))[:10]
                ttl       = int(l.get("TTL_Days", 90) or 90)
                try:
                    age      = (datetime.utcnow() - datetime.fromisoformat(opened)).days
                    days_left = ttl - age
                    ttl_str   = f"  ({days_left}d left)" if days_left < 14 else ""
                except Exception:
                    ttl_str = ""
                sections.append(f"     [{priority:8}] {topic}{ttl_str}")
        elif format == "telegram":
            lines = [f"\n🔓 *Open Loops* ({len(all_loops)} total):"]
            for l in urgent_loops:
                lines.append(f"• [{l.get('Priority','?')}] {l.get('Topic','?')[:50]}")
            sections.append("\n".join(lines))

    # ── Stale projects ────────────────────────────────────────────────────────

    active_projects = [r for r in oy._read_sheet(SHEET_PROJECTS)
                       if r.get("Status") == "Active"]
    stale = []
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()[:10]
    for p in active_projects:
        last = str(p.get("Last Updated", ""))[:10]
        if last and last < cutoff:
            stale.append(p)

    if stale:
        if format == "terminal":
            sections.append(f"\n  🚀  Stale Projects (no update in 7+ days):")
            for p in stale[:3]:
                name      = p.get("Project", "?")[:50]
                next_step = p.get("Next Step", "no next step set")[:50]
                sections.append(f"     {name} → {next_step}")
        elif format == "telegram":
            lines = [f"\n🚀 *Stale Projects* (7+ days):"]
            for p in stale[:3]:
                lines.append(f"• {p.get('Project','?')[:40]}")
            sections.append("\n".join(lines))

    # ── Inbox items pending routing ───────────────────────────────────────────

    inbox_pending = [r for r in oy._read_sheet(SHEET_INBOX)
                     if r.get("Routed?") == "No"]
    if inbox_pending:
        if format == "terminal":
            sections.append(f"\n  📥  Inbox ({len(inbox_pending)} unrouted):")
            for item in inbox_pending[:3]:
                content = str(item.get("Content", ""))[:60]
                sections.append(f"     {content}")
            if len(inbox_pending) > 3:
                sections.append(f"     ...and {len(inbox_pending)-3} more")
        elif format == "telegram":
            sections.append(
                f"\n📥 *Inbox:* {len(inbox_pending)} items need routing"
                f"\nRun `yantra route` to sort them")

    # ── Memory insight -- pattern detection ────────────────────────────────────

    sessions = oy._read_sheet(SHEET_SESSION_LOG)
    recent_sessions = [s for s in sessions
                       if str(s.get("Date",""))[:10] >= cutoff]

    if recent_sessions:
        word_freq: dict[str, int] = {}
        for s in recent_sessions:
            text = " ".join([
                str(s.get("Topics Discussed", "")),
                str(s.get("Decisions Made", "")),
                str(s.get("Notes", ""))
            ]).lower()
            for word in text.split():
                if len(word) > 4 and word not in {
                    "about", "their", "there", "would", "could", "should",
                    "which", "where", "these", "those", "after", "before",
                    "since", "while", "using", "added", "wrote", "noted"
                }:
                    word_freq[word] = word_freq.get(word, 0) + 1

        top = sorted(word_freq.items(), key=lambda x: -x[1])[:3]
        if top and top[0][1] >= 2:
            insight_words = ", ".join(f'"{w}"' for w, c in top if c >= 2)
            if insight_words:
                if format == "terminal":
                    sections.append(
                        f"\n  💡  Memory Insight:"
                        f"\n     You've mentioned {insight_words} repeatedly this week."
                    )
                elif format == "telegram":
                    sections.append(
                        f"\n💡 *Memory Insight:*\n"
                        f"You've mentioned {insight_words} repeatedly this week."
                    )

    # ── Tasks that may be done ────────────────────────────────────────────────

    pending_tasks = [r for r in oy._read_sheet(SHEET_TASKS)
                     if r.get("Status") in ("Pending", "In Progress")]
    old_tasks = [t for t in pending_tasks
                 if str(t.get("Last Updated",""))[:10] < cutoff]

    if old_tasks:
        if format == "terminal":
            sections.append(f"\n  ✅  Tasks to confirm:")
            for t in old_tasks[:3]:
                task = str(t.get("Task",""))[:55]
                sections.append(f"     Still pending? → {task}")
        elif format == "telegram":
            lines = [f"\n✅ *Tasks to confirm:*"]
            for t in old_tasks[:3]:
                lines.append(f"• {t.get('Task','?')[:50]}")
            sections.append("\n".join(lines))

    # ── On this day -- random past memory ─────────────────────────────────────

    all_goals    = oy._read_sheet(SHEET_GOALS)
    all_beliefs  = oy._read_sheet(SHEET_BELIEFS)
    past_pool    = [r for r in (all_goals + all_beliefs) if any(r.values())]

    if past_pool:
        memory = random.choice(past_pool)
        val    = (memory.get("Goal") or memory.get("Position") or
                  memory.get("Value") or "")
        if val and len(str(val)) > 5:
            if format == "terminal":
                sections.append(
                    f"\n  🕰️   On this day (past memory):\n"
                    f"     \"{str(val)[:100]}\""
                )
            elif format == "telegram":
                sections.append(
                    f"\n🕰️ *On this day:*\n_{str(val)[:100]}_"
                )

    # ── Footer ────────────────────────────────────────────────────────────────

    if format == "terminal":
        summary_parts = []
        if all_loops:
            summary_parts.append(f"{len(all_loops)} open loops")
        if stale:
            summary_parts.append(f"{len(stale)} stale projects")
        if inbox_pending:
            summary_parts.append(f"{len(inbox_pending)} inbox pending")

        summary = " · ".join(summary_parts) if summary_parts else "All clear"
        sections.append(
            f"\n  ─────────────────────────────────────────────────\n"
            f"  {summary}\n"
            f"  yantra ui → http://localhost:7331\n"
            f"{'═'*55}\n"
        )
    elif format == "telegram":
        sections.append(
            f"\n_Open `yantra ui` to take action._"
        )

    return "\n".join(sections)


# ── Scheduled runner ──────────────────────────────────────────────────────────

def run_scheduled(oy_path: str, time_str: str = "08:00"):
    """Run digest daily at the specified time."""
    try:
        import schedule
        import time

        def job():
            print(generate_digest(oy_path, format="terminal"))

        schedule.every().day.at(time_str).do(job)
        print(f"[OpenYantra] Digest scheduled daily at {time_str}")
        print("[OpenYantra] Press Ctrl+C to stop\n")

        while True:
            schedule.run_pending()
            time.sleep(60)

    except ImportError:
        print("pip install schedule")
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OpenYantra Daily Digest v2.3"
    )
    parser.add_argument(
        "--file", "-f",
        default=str(Path.home() / "openyantra" / "chitrapat.ods"),
        help="Path to chitrapat.ods"
    )
    parser.add_argument(
        "--schedule", "-s",
        action="store_true",
        help="Run daily on schedule"
    )
    parser.add_argument(
        "--time", "-t",
        default="08:00",
        help="Schedule time HH:MM (default 08:00)"
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "telegram", "email"],
        default="terminal"
    )
    args = parser.parse_args()

    oy_path = Path(args.file).expanduser()
    if not oy_path.exists():
        print(f"Chitrapat not found at {oy_path}. Run: yantra bootstrap")
        sys.exit(1)

    if args.schedule:
        run_scheduled(str(oy_path), args.time)
    else:
        print(generate_digest(str(oy_path), format=args.format))


if __name__ == "__main__":
    main()
