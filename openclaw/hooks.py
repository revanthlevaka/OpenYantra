"""
openclaw/hooks.py — Pre/post compaction hooks for OpenYantra + OpenClaw

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
    payload["system_prompt"] = block + "\n\n" + payload.get("system_prompt","")
    return payload

def pre_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    print(f"[OpenYantra pre-compact] Scanning for Anishtha (open loops)...")
    # Add loop extraction from payload["conversation"] here
    return payload

def post_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    try:
        ctx = oy.load_session_context()
        if ctx["open_loops"]:
            loops_text = "\n".join(
                f"- [{l.get('Priority','?')}] {l.get('Topic','?')}:"
                f" {l.get('Context / What\'s Unresolved','')}"
                for l in ctx["open_loops"]
            )
            payload["new_context"] = payload.get("new_context","") + (
                f"\n\n[OpenYantra: Anishtha restored]\n{loops_text}"
            )
    except Exception as e:
        print(f"[OpenYantra post-compact] Warning: {e}")
    return payload

def session_end_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name=AGENT_NAME)
    try:
        oy.log_session(
            topics=payload.get("topics", ["(auto-logged)"]),
            decisions=payload.get("decisions", []),
            new_memory=payload.get("new_memory", []),
            agent=AGENT_NAME,
        )
        oy.release_pratibimba()
    except Exception as e:
        print(f"[OpenYantra session-end] Warning: {e}")
    return payload
