"""
openclaw/plugin.py — OpenYantra plugin for OpenClaw v2.2
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
    block = oy.build_system_prompt_block()
    session_context["system_prompt"] = block + "\n\n" + session_context.get("system_prompt", "")
    return session_context

def on_session_end(session_data: dict):
    oy = _get_oy()
    oy.log_session(
        topics=session_data.get("topics", ["(session)"]),
        decisions=session_data.get("decisions", []),
        new_memory=session_data.get("new_facts", []),
    )
    oy.release_pratibimba()
