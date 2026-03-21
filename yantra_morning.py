"""
yantra_morning.py -- OpenYantra Morning Briefing v3.0

Surfaces what matters before you open any other app.
Runs automatically on first yantra command each day.

Features:
    - Open loops sorted by importance x TTL urgency
    - Stale projects (no update in 7 days)
    - Unrouted inbox count
    - Proactive suggestion: cross-reference inbox with open loops
    - Past memory: random goal or belief for reflection
    - Streak counter: consecutive days with at least one write

Usage:
    yantra morning
    python yantra_morning.py --file ~/openyantra/chitrapat.ods
    generate_morning_brief(oy) -> returns dict for dashboard Daily Insight card
"""

from __future__ import annotations

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
        SHEET_GOALS, SHEET_IDENTITY,
    )
    _OY_AVAILABLE = True
except ImportError:
    _OY_AVAILABLE = False


VERSION = "3.0.0"
IMPORTANCE_THRESHOLD = 7    # Only show importance >= this in morning brief
STALE_DAYS           = 7    # Project counts as stale after this many days
MAX_LOOPS_SHOWN      = 5    # Max loops to surface in terminal output


def generate_morning_brief(oy: "OpenYantra") -> dict:
    """
    Generate the morning brief data structure.
    Returns a dict usable by both the terminal renderer and the
    browser dashboard Daily Insight card.
    """
    today = date.today().isoformat()
    cutoff_stale = (datetime.utcnow() - timedelta(days=STALE_DAYS)).isoformat()[:10]

    # Identity
    identity_rows = oy._read_sheet(SHEET_IDENTITY)
    identity = {r.get("Attribute"): r.get("Value")
                for r in identity_rows if r.get("Value")}
    user_name = (identity.get("Preferred Name") or
                 identity.get("Full Name") or "there")

    # Open loops -- sorted by importance desc, TTL urgency asc
    all_loops = [r for r in oy._read_sheet(SHEET_OPEN_LOOPS)
                 if r.get("Resolved?") == "No"]

    def loop_urgency(loop):
        imp  = -(int(loop.get("Importance", 5) or 5))
        ttl  = int(loop.get("TTL_Days", 90) or 90)
        opened = str(loop.get("Opened", ""))[:10]
        try:
            age = (datetime.utcnow() - datetime.fromisoformat(opened)).days
            days_left = ttl - age
        except Exception:
            days_left = ttl
        return (imp, days_left)

    urgent_loops = sorted(all_loops, key=loop_urgency)
    high_loops   = [l for l in urgent_loops
                    if int(l.get("Importance", 5) or 5) >= IMPORTANCE_THRESHOLD]
    shown_loops  = (high_loops or urgent_loops)[:MAX_LOOPS_SHOWN]

    # TTL days left for each shown loop
    loops_with_ttl = []
    for loop in shown_loops:
        ttl    = int(loop.get("TTL_Days", 90) or 90)
        opened = str(loop.get("Opened", ""))[:10]
        try:
            age       = (datetime.utcnow() - datetime.fromisoformat(opened)).days
            days_left = ttl - age
        except Exception:
            days_left = None
        loops_with_ttl.append({
            "topic":      loop.get("Topic", "?"),
            "priority":   loop.get("Priority", "?"),
            "importance": loop.get("Importance", 5),
            "days_left":  days_left,
        })

    # Stale projects
    active_projects  = [r for r in oy._read_sheet(SHEET_PROJECTS)
                        if r.get("Status") == "Active"]
    stale_projects   = [p for p in active_projects
                        if str(p.get("Last Updated", ""))[:10] < cutoff_stale]

    # Inbox
    inbox_items    = oy._read_sheet(SHEET_INBOX)
    inbox_unrouted = [i for i in inbox_items if i.get("Routed?") == "No"]

    # Proactive suggestion: inbox item cross-referenced with open loops
    suggestion = None
    for inbox_item in inbox_unrouted[:10]:
        content = str(inbox_item.get("Content", "")).lower()
        for loop in all_loops[:10]:
            topic = str(loop.get("Topic", "")).lower()
            # Simple overlap: any word > 4 chars in both
            words_content = {w for w in content.split() if len(w) > 4}
            words_topic   = {w for w in topic.split() if len(w) > 4}
            if words_content & words_topic:
                suggestion = {
                    "inbox_text": inbox_item.get("Content", "")[:60],
                    "loop_topic": loop.get("Topic", "")[:60],
                    "match_words": list(words_content & words_topic)[:3],
                }
                break
        if suggestion:
            break

    # Past memory -- random goal or belief for reflection
    goals   = oy._read_sheet(SHEET_GOALS)
    beliefs = oy._read_sheet(SHEET_BELIEFS)
    pool    = [r.get("Goal") for r in goals if r.get("Goal")]
    pool   += [r.get("Position") for r in beliefs if r.get("Position")]
    pool    = [p for p in pool if p and len(str(p)) > 10]
    past_memory = random.choice(pool) if pool else None

    # Streak counter: consecutive days with at least one session log entry
    sessions = oy._read_sheet(SHEET_SESSION_LOG)
    session_dates = sorted(
        {str(s.get("Date", ""))[:10] for s in sessions if s.get("Date")},
        reverse=True)
    streak = 0
    check  = today
    for d in session_dates:
        if d == check:
            streak += 1
            prev = datetime.fromisoformat(check) - timedelta(days=1)
            check = prev.isoformat()[:10]
        else:
            break

    return {
        "user_name":      user_name,
        "date":           today,
        "loops":          loops_with_ttl,
        "loops_total":    len(all_loops),
        "stale_projects": [
            {"project":   p.get("Project", "?"),
             "next_step": p.get("Next Step", "not set"),
             "days_stale": (datetime.utcnow() - datetime.fromisoformat(
                 str(p.get("Last Updated", today))[:10])).days
                 if str(p.get("Last Updated", ""))[:10] else None}
            for p in stale_projects[:3]
        ],
        "inbox_unrouted": len(inbox_unrouted),
        "suggestion":     suggestion,
        "past_memory":    past_memory,
        "streak":         streak,
    }


def render_terminal(brief: dict) -> str:
    """Render morning brief as terminal text (full ANSI-safe output)."""
    SEP  = "=" * 56
    DASH = "-" * 52
    lines = [
        "",
        SEP,
        f"  Good morning, {brief['user_name']}. OpenYantra v{VERSION}",
        f"  {brief['date']}",
        SEP,
        "",
    ]

    # Open loops
    if brief["loops"]:
        n = brief["loops_total"]
        lines.append(f"  🔓  Open Loops ({n} total):")
        for loop in brief["loops"]:
            priority = f"{loop['priority']:8}"
            topic    = loop["topic"][:48]
            ttl_part = ""
            if loop["days_left"] is not None:
                dl = loop["days_left"]
                if dl <= 0:
                    ttl_part = "  (EXPIRED)"
                elif dl <= 7:
                    ttl_part = f"  ({dl}d left)"
            lines.append(f"     [{priority}] {topic}{ttl_part}")
        lines.append("")

    # Stale projects
    if brief["stale_projects"]:
        lines.append("  🚀  Stale Projects:")
        for p in brief["stale_projects"]:
            days  = p.get("days_stale")
            label = f" -- no update in {days} days" if days else ""
            lines.append(f"     {p['project']}{label}")
            ns = p["next_step"]
            if ns and ns != "not set":
                lines.append(f"       -> {ns[:55]}")
        lines.append("")

    # Inbox
    if brief["inbox_unrouted"] > 0:
        n = brief["inbox_unrouted"]
        lines.append(f"  📥  Inbox: {n} item{'s' if n != 1 else ''} unrouted")
        lines.append("")

    # Proactive suggestion
    if brief["suggestion"]:
        s = brief["suggestion"]
        lines.append("  💡  Suggestion:")
        lines.append(f"     '{s['inbox_text']}' in Inbox may relate to:")
        lines.append(f"     '{s['loop_topic']}'")
        lines.append("")

    # Past memory
    if brief["past_memory"]:
        mem = str(brief["past_memory"])[:80]
        lines.append(f"  🕰️   Past memory:")
        lines.append(f'     "{mem}"')
        lines.append("")

    # Streak
    if brief["streak"] > 1:
        lines.append(f"  🔥  Streak: {brief['streak']} days")
        lines.append("")

    lines += [
        f"  {DASH}",
        "  yantra ui -> http://localhost:7331",
        SEP,
        "",
    ]

    return "\n".join(lines)


def has_run_today(oy: "OpenYantra") -> bool:
    """Check if morning brief has already run today."""
    sessions = oy._read_sheet(SHEET_SESSION_LOG)
    today    = date.today().isoformat()
    return any(str(s.get("Date", ""))[:10] == today and
               "morning" in str(s.get("Notes", "")).lower()
               for s in sessions)


def run_morning_brief(oy_path: str, force: bool = False) -> dict:
    """
    Run the morning brief. Prints to terminal and returns brief dict.
    Skips if already run today unless force=True.
    """
    if not _OY_AVAILABLE:
        print("[yantra morning] openyantra.py not found.")
        return {}

    path = Path(oy_path).expanduser()
    if not path.exists():
        print(f"[yantra morning] Chitrapat not found at {path}")
        print("Run: yantra bootstrap")
        return {}

    oy = OpenYantra(str(path), agent_name="Morning")

    if not force and has_run_today(oy):
        # Already ran today -- silent return for auto-trigger mode
        return {}

    brief = generate_morning_brief(oy)
    print(render_terminal(brief))
    return brief


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OpenYantra Morning Briefing v3.0")
    parser.add_argument("--file", "-f",
                        default=str(Path.home() / "openyantra" / "chitrapat.ods"))
    parser.add_argument("--force", action="store_true",
                        help="Run even if already ran today")
    args = parser.parse_args()
    run_morning_brief(args.file, force=args.force)


if __name__ == "__main__":
    main()
