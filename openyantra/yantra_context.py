"""
yantra_context.py -- OpenYantra Copy Context v3.0

Formats your full memory as a clean Markdown block.
Copies to clipboard automatically.
Paste into Claude.ai, ChatGPT, or any web AI chat.

Bridges your local OpenYantra memory to the AI tools you already use
without requiring any integration or API key.

Usage:
    yantra context                       # copies to clipboard + prints preview
    yantra context --output file.md      # save to file instead
    yantra context --sections loops,projects  # selective export
    python yantra_context.py --file ~/openyantra/chitrapat.ods
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from openyantra import (
        OpenYantra,
        SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS, SHEET_PEOPLE,
        SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS,
        SHEET_OPEN_LOOPS, SHEET_AGENT_CONFIG,
    )
    _OY_AVAILABLE = True
except ImportError:
    _OY_AVAILABLE = False

VERSION = "3.0.0"

ALL_SECTIONS = [
    "identity", "goals", "projects", "people",
    "preferences", "beliefs", "tasks", "loops", "instructions",
]


def build_context_markdown(oy: "OpenYantra",
                            sections: list[str] = None) -> str:
    """
    Build a Markdown context block from the Chitrapat.
    Suitable for pasting into any AI chat interface.
    """
    if sections is None:
        sections = ALL_SECTIONS

    ctx   = oy.load_session_context()
    lines = [
        f"<!-- OpenYantra Context Block v{VERSION} | {datetime.utcnow().isoformat()[:10]} -->",
        "",
        "## My AI Memory Context",
        "",
    ]

    # Identity
    if "identity" in sections and ctx.get("identity"):
        identity = ctx["identity"]
        name     = (identity.get("Preferred Name") or identity.get("Full Name") or "")
        occ      = identity.get("Occupation", "")
        loc      = identity.get("Location", "")
        lang     = identity.get("Primary Language", "")
        hours    = identity.get("Working Hours", "")

        lines.append("### Identity")
        if name: lines.append(f"- **Name:** {name}")
        if occ:  lines.append(f"- **Role:** {occ}")
        if loc:  lines.append(f"- **Location:** {loc}")
        if lang and lang.lower() != "english":
            lines.append(f"- **Language:** {lang}")
        if hours:
            lines.append(f"- **Working Hours:** {hours}")
        lines.append("")

    # Active projects
    if "projects" in sections and ctx.get("active_projects"):
        lines.append("### Active Projects")
        for p in ctx["active_projects"][:8]:
            proj = p.get("Project", "?")
            ns   = p.get("Next Step", "")
            dom  = p.get("Domain", "")
            pri  = p.get("Priority", "")
            line = f"- **{proj}**"
            if pri:
                line += f" [{pri}]"
            if dom:
                line += f" ({dom})"
            if ns:
                line += f" -- next: {ns}"
            lines.append(line)
        lines.append("")

    # Open loops
    if "loops" in sections and ctx.get("open_loops"):
        lines.append("### Open Loops (Unresolved)")
        for loop in ctx["open_loops"][:10]:
            topic   = loop.get("Topic", "?")
            context = loop.get("Context / What's Unresolved", "")
            pri     = loop.get("Priority", "?")
            imp     = loop.get("Importance", 5)
            line    = f"- [{pri}] **{topic}**"
            if context:
                line += f": {context[:100]}"
            lines.append(line)
        lines.append("")

    # Goals
    if "goals" in sections and ctx.get("active_goals"):
        lines.append("### Goals")
        for g in ctx["active_goals"][:6]:
            goal = g.get("Goal", "?")
            gtype = g.get("Type", "")
            lines.append(f"- {goal}" + (f" ({gtype})" if gtype else ""))
        lines.append("")

    # Pending tasks
    if "tasks" in sections and ctx.get("pending_tasks"):
        lines.append("### Pending Tasks")
        for t in ctx["pending_tasks"][:8]:
            task = t.get("Task", "?")
            proj = t.get("Project", "")
            pri  = t.get("Priority", "Medium")
            line = f"- [{pri}] {task}"
            if proj:
                line += f" ({proj})"
            lines.append(line)
        lines.append("")

    # Preferences
    if "preferences" in sections:
        prefs = oy._read_sheet(SHEET_PREFERENCES)
        strong_prefs = [p for p in prefs if p.get("Strength") == "Strong"]
        if strong_prefs:
            lines.append("### Preferences")
            for p in strong_prefs[:6]:
                cat  = p.get("Category", "?")
                pref = p.get("Preference", "?")
                lines.append(f"- **{cat}:** {pref}")
            lines.append("")

    # Beliefs (values / principles)
    if "beliefs" in sections:
        beliefs = oy._read_sheet(SHEET_BELIEFS)
        key_beliefs = [b for b in beliefs
                       if int(b.get("Importance", 5) or 5) >= 7][:5]
        if key_beliefs:
            lines.append("### Key Beliefs & Principles")
            for b in key_beliefs:
                topic    = b.get("Topic", "?")
                position = b.get("Position", "?")
                lines.append(f"- **{topic}:** {position}")
            lines.append("")

    # People
    if "people" in sections:
        people = oy._read_sheet(SHEET_PEOPLE)
        key_people = [p for p in people
                      if int(p.get("Importance", 5) or 5) >= 7][:6]
        if key_people:
            lines.append("### Key People")
            for p in key_people:
                name = p.get("Name", "?")
                rel  = p.get("Relationship", "")
                ctx_text = p.get("Context", "")
                line = f"- **{name}**"
                if rel:
                    line += f" ({rel})"
                if ctx_text:
                    line += f": {ctx_text[:80]}"
                lines.append(line)
            lines.append("")

    # Agent instructions
    if "instructions" in sections and ctx.get("agent_instructions"):
        lines.append("### Instructions for This Session")
        for instr in ctx["agent_instructions"][:5]:
            lines.append(f"- {instr}")
        lines.append("")

    # Alerts
    alerts = []
    if ctx.get("inbox_pending", 0) > 0:
        alerts.append(f"📥 {ctx['inbox_pending']} unrouted Inbox items")
    if ctx.get("pending_corrections"):
        alerts.append(f"✏️ {len(ctx['pending_corrections'])} corrections pending")
    if alerts:
        lines.append("### Alerts")
        for a in alerts:
            lines.append(f"- {a}")
        lines.append("")

    lines.append(
        f"<!-- Generated by OpenYantra v{VERSION} | "
        f"github.com/revanthlevaka/OpenYantra -->")

    return "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True if successful."""
    import subprocess
    import platform

    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return proc.returncode == 0
        elif system == "Linux":
            # Try xclip first, then xsel
            for cmd in [["xclip", "-selection", "clipboard"],
                        ["xsel", "--clipboard", "--input"]]:
                try:
                    proc = subprocess.run(cmd, input=text.encode(), check=True)
                    return proc.returncode == 0
                except FileNotFoundError:
                    continue
        elif system == "Windows":
            proc = subprocess.run(["clip"], input=text.encode(), check=True)
            return proc.returncode == 0
    except Exception:
        pass
    return False


def run_context(oy_path: str, output_file: str = None,
                sections: list[str] = None) -> str:
    """
    Run the context command. Copies to clipboard and prints preview.
    Optionally saves to file.
    Returns the markdown string.
    """
    if not _OY_AVAILABLE:
        print("[yantra context] openyantra.py not found.")
        return ""

    path = Path(oy_path).expanduser()
    if not path.exists():
        print(f"[yantra context] Chitrapat not found at {path}")
        print("Run: yantra bootstrap")
        return ""

    oy       = OpenYantra(str(path), agent_name="Context")
    markdown = build_context_markdown(oy, sections)

    if output_file:
        out = Path(output_file).expanduser()
        out.write_text(markdown, encoding="utf-8")
        print(f"[yantra context] Saved to {out}")
    else:
        copied = copy_to_clipboard(markdown)
        if copied:
            print("[yantra context] Context copied to clipboard.")
            print("[yantra context] Paste into Claude.ai, ChatGPT, or any AI chat.\n")
        else:
            print("[yantra context] Could not copy automatically.\n")
            print(markdown)

    # Print a short preview
    lines  = markdown.split("\n")
    print("\n".join(lines[:20]))
    if len(lines) > 20:
        print(f"\n... ({len(lines) - 20} more lines)")

    return markdown


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="OpenYantra Copy Context v3.0")
    parser.add_argument("--file", "-f",
                        default=str(Path.home() / "openyantra" / "chitrapat.ods"))
    parser.add_argument("--output", "-o", default=None,
                        help="Save to file instead of clipboard")
    parser.add_argument("--sections", "-s", default=None,
                        help=f"Comma-separated sections: {','.join(ALL_SECTIONS)}")
    args = parser.parse_args()

    sections = args.sections.split(",") if args.sections else None
    run_context(args.file, output_file=args.output, sections=sections)


if __name__ == "__main__":
    main()
