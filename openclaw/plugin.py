"""
openclaw/plugin.py — OpenYantra plugin for OpenClaw
Register in openclaw config.toml:
    [plugins]
    openyantra = { path = "path/to/openclaw/plugin.py", enabled = true }

    [env]
    OPENYANTRA_FILE = "~/openyantra/chitrapat.ods"
"""
import os
from pathlib import Path
from openyantra import OpenYantra

OY_FILE    = Path(os.getenv("OPENYANTRA_FILE", "~/openyantra/chitrapat.ods")).expanduser()
AGENT_NAME = "OpenClaw"

def _get_oy() -> OpenYantra:
    return OpenYantra(OY_FILE, agent_name=AGENT_NAME)

def on_session_start(session_context: dict) -> dict:
    oy = _get_oy()
    if not OY_FILE.exists():
        oy.bootstrap()
    oy.take_pratibimba()
    try:
        block = oy.build_system_prompt_block()
        session_context["system_prompt"] = block + "\n\n" + session_context.get("system_prompt","")
        print("[OpenYantra] Context injected into system prompt.")
    except Exception as e:
        print(f"[OpenYantra] Warning: {e}")
    return session_context

def on_pre_compact(conversation_history: list, current_summary: str) -> str:
    oy = _get_oy()
    # Implement: extract open loops from conversation_history and flush them
    return current_summary

def on_session_end(session_data: dict):
    oy = _get_oy()
    try:
        oy.log_session(
            topics=session_data.get("topics", ["(session)"]),
            decisions=session_data.get("decisions", []),
            new_memory=session_data.get("new_facts", []),
            open_loops_created=session_data.get("open_loops_created", 0),
            agent=AGENT_NAME,
        )
        oy.release_pratibimba()
        print("[OpenYantra] Session logged.")
    except Exception as e:
        print(f"[OpenYantra] Warning: {e}")
