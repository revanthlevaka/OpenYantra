"""
openclaw/hooks.py -- OpenYantra hooks for OpenClaw v2.2

Register in openclaw config.toml:
    [hooks]
    session_start = "openyantra.openclaw.hooks:session_start_hook"
    pre_compact   = "openyantra.openclaw.hooks:pre_compact_hook"
    post_compact  = "openyantra.openclaw.hooks:post_compact_hook"
    session_end   = "openyantra.openclaw.hooks:session_end_hook"
"""
import os
from pathlib import Path
from openyantra import OpenYantra

OY_FILE    = Path(os.getenv("OPENYANTRA_FILE", "~/openyantra/chitrapat.ods")).expanduser()
AGENT_NAME = "OpenClaw"

def session_start_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    if not OY_FILE.exists():
        oy.bootstrap()
    oy.take_pratibimba()
    block = oy.build_system_prompt_block()
    payload["system_prompt"] = block + "\n\n" + payload.get("system_prompt", "")
    return payload

def pre_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    # Extract open loops from conversation and flush
    # Implement: loops = extract_loops(payload["conversation"])
    # for loop in loops: oy.flush_open_loop(**loop)
    return payload

def post_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    ctx = oy.load_session_context()
    if ctx["open_loops"]:
        loops_text = "\n".join(
            f"- [{l.get('Priority','?')}] {l.get('Topic','?')}: {l.get('Context / What\'s Unresolved','')}"
            for l in ctx["open_loops"]
        )
        payload["new_context"] = payload.get("new_context","") + (
            f"\n\n[OpenYantra: Anishtha restored after compaction]\n{loops_text}"
        )
    return payload

def session_end_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    oy.log_session(
        topics=payload.get("topics", ["(auto-logged)"]),
        decisions=payload.get("decisions", []),
        new_memory=payload.get("new_memory", []),
    )
    oy.release_pratibimba()
    return payload
