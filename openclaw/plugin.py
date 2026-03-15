"""
openclaw/plugin.py — UAM Plugin for OpenClaw
Hooks into OpenClaw's session lifecycle to provide persistent memory.

Install:
    Copy this file into your OpenClaw plugins/ directory, or register
    via openclaw.config.toml:

    [plugins]
    uam = { path = "path/to/openclaw/plugin.py", enabled = true }

    Then set UAM_FILE in your environment:
    export UAM_FILE=~/uam/memory.xlsx
"""

import os
from pathlib import Path

try:
    from openyantra import OpenYantra
except ImportError:
    raise ImportError(
        "UAM library not found. Install it: pip install universal-agent-memory"
    )

# ── Config ─────────────────────────────────────────────────────────────────────

UAM_FILE    = Path(os.getenv("UAM_FILE", "~/uam/memory.xlsx")).expanduser()
AGENT_NAME  = "OpenClaw"


def _get_mem() -> OpenYantra:
    return OpenYantra(UAM_FILE, agent_name=AGENT_NAME)


# ── Lifecycle hooks ────────────────────────────────────────────────────────────

def on_session_start(session_context: dict) -> dict:
    """
    OpenClaw hook: called before the first message is processed.
    Injects UAM context into the system prompt.

    Register in openclaw config:
        session_start_hook = "openclaw.plugin:on_session_start"
    """
    mem = _get_mem()

    # Bootstrap if no file exists yet
    if not UAM_FILE.exists():
        print(f"[OpenYantra] No memory file found. Creating at {UAM_FILE}")
        mem.bootstrap()

    try:
        uam_block = mem.build_system_prompt_block(agent_name=AGENT_NAME)
        existing = session_context.get("system_prompt", "")
        session_context["system_prompt"] = uam_block + "\n\n" + existing
        print("[OpenYantra] Context injected into system prompt.")
    except Exception as e:
        print(f"[OpenYantra] Warning: could not load memory context — {e}")

    return session_context


def on_pre_compact(conversation_history: list, current_summary: str) -> str:
    """
    OpenClaw hook: called BEFORE context compaction.
    Scans conversation for open loops and flushes them to UAM.

    Register in openclaw config:
        pre_compact_hook = "openclaw.plugin:on_pre_compact"
    """
    mem = _get_mem()

    # Ask the model to identify open loops from conversation history
    # (In a real implementation, this would call the model with a structured prompt)
    open_loops = _extract_open_loops_from_history(conversation_history)

    for loop in open_loops:
        try:
            mem.flush_open_loop(
                topic=loop["topic"],
                context=loop["context"],
                priority=loop.get("priority", "Medium"),
                related_project=loop.get("project", ""),
            )
            print(f"[OpenYantra] Flushed open loop: {loop['topic']}")
        except Exception as e:
            print(f"[OpenYantra] Warning: could not flush loop '{loop['topic']}' — {e}")

    return current_summary


def on_session_end(session_data: dict):
    """
    OpenClaw hook: called when session ends.
    Writes session summary to UAM Session Log.

    Register in openclaw config:
        session_end_hook = "openclaw.plugin:on_session_end"
    """
    mem = _get_mem()

    try:
        mem.log_session(
            topics=session_data.get("topics", ["(session)"]),
            decisions=session_data.get("decisions", []),
            new_memory=session_data.get("new_facts", []),
            open_loops_created=session_data.get("open_loops_created", 0),
            notes=session_data.get("notes", ""),
            agent=AGENT_NAME,
        )
        print("[OpenYantra] Session logged.")
    except Exception as e:
        print(f"[OpenYantra] Warning: could not log session — {e}")


# ── Internal helpers ───────────────────────────────────────────────────────────

def _extract_open_loops_from_history(history: list) -> list[dict]:
    """
    Analyse conversation history and identify unresolved threads.

    In production: call the model with a structured extraction prompt.
    Here: placeholder that returns an empty list.
    Replace with your model call:

        response = model.complete(
            system="Extract unresolved threads as JSON array: "
                   "[{topic, context, priority, project}]",
            messages=history,
        )
        return json.loads(response)
    """
    # TODO: replace with real model call
    return []
