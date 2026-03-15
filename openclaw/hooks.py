"""
openclaw/hooks.py — Pre/Post compaction hooks for UAM + OpenClaw

These hooks solve the #1 memory failure mode in OpenClaw:
context compaction silently destroying active work context.

Usage in openclaw config.toml:
    [hooks]
    pre_compact  = "uam.openclaw.hooks:pre_compact_hook"
    post_compact = "uam.openclaw.hooks:post_compact_hook"
    session_end  = "uam.openclaw.hooks:session_end_hook"
"""

import json
import os
from pathlib import Path
from openyantra import OpenYantra

UAM_FILE   = Path(os.getenv("UAM_FILE", "~/uam/memory.xlsx")).expanduser()
AGENT_NAME = "OpenClaw"


def pre_compact_hook(payload: dict) -> dict:
    """
    Called immediately before OpenClaw compacts the context window.

    payload keys:
        conversation  - full message list
        summary_so_far - existing running summary string
        model         - model name being used

    Returns the payload unchanged (side effect: writes to UAM).
    """
    mem = OpenYantra(UAM_FILE, agent_name=AGENT_NAME)
    conversation = payload.get("conversation", [])

    # Build a quick extraction prompt
    extraction_prompt = _build_extraction_prompt(conversation)

    # In a live integration, call the model here.
    # For now, we demonstrate the structure.
    print(f"[UAM pre-compact] Scanning {len(conversation)} messages for open loops...")

    # Example: if model returns this structure, we flush it
    # loops = model.complete(extraction_prompt)
    # for loop in loops:
    #     mem.flush_open_loop(**loop)

    return payload


def post_compact_hook(payload: dict) -> dict:
    """
    Called immediately after compaction.
    Re-injects UAM open loops into the new context so they survive.

    payload keys:
        new_context - the freshly compacted context string
    """
    mem = OpenYantra(UAM_FILE, agent_name=AGENT_NAME)

    try:
        ctx = mem.load_session_context(agent_name=AGENT_NAME)
        open_loops = ctx.get("open_loops", [])

        if open_loops:
            loops_text = "\n".join(
                f"- [{l.get('Priority','?')}] {l.get('Topic','?')}: "
                f"{l.get('Context / What\\'s Unresolved','')}"
                for l in open_loops
            )
            injection = (
                f"\n\n[UAM: UNRESOLVED THREADS — restored after compaction]\n"
                f"{loops_text}\n[/UAM]"
            )
            payload["new_context"] = payload.get("new_context", "") + injection
            print(f"[UAM post-compact] Re-injected {len(open_loops)} open loop(s).")
    except Exception as e:
        print(f"[UAM post-compact] Warning: {e}")

    return payload


def session_end_hook(payload: dict) -> dict:
    """
    Called when OpenClaw ends a session (user closes, timeout, explicit exit).
    Writes final session log entry.
    """
    mem = OpenYantra(UAM_FILE, agent_name=AGENT_NAME)

    try:
        mem.log_session(
            topics=payload.get("topics", ["(auto-logged)"]),
            decisions=payload.get("decisions", []),
            new_memory=payload.get("new_memory", []),
            open_loops_created=payload.get("loops_flushed", 0),
            agent=AGENT_NAME,
        )
        print("[UAM session-end] Session logged to memory file.")
    except Exception as e:
        print(f"[UAM session-end] Warning: {e}")

    return payload


# ── Internal ───────────────────────────────────────────────────────────────────

def _build_extraction_prompt(conversation: list) -> str:
    messages_text = "\n".join(
        f"{m.get('role','?').upper()}: {m.get('content','')}"
        for m in conversation[-20:]  # last 20 messages
    )
    return f"""You are analysing a conversation to extract unresolved threads before context compaction.

Read the conversation below and return a JSON array of open loops.
Each loop must have: topic (str), context (str), priority (High/Medium/Low), project (str or "").
Only include genuinely unresolved items — skip anything that was concluded.
Return ONLY valid JSON, no other text.

CONVERSATION:
{messages_text}

JSON:"""
