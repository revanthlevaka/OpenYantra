"""
openyantra.adapters.openclaw -- OpenYantra Adapter for OpenClaw v6.2.2

Register in openclaw config.toml:
    [hooks]
    session_start = "openyantra.adapters.openclaw:session_start_hook"
    pre_compact   = "openyantra.adapters.openclaw:pre_compact_hook"
    post_compact  = "openyantra.adapters.openclaw:post_compact_hook"
    session_end   = "openyantra.adapters.openclaw:session_end_hook"
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from openyantra.core import OpenYantra

OY_FILE = Path(os.getenv("OPENYANTRA_FILE", "~/openyantra/chitrapat.ods")).expanduser()
AGENT_NAME = "OpenClaw"


def _get_oy(file_path: Optional[Path] = None) -> OpenYantra:
    target = file_path or OY_FILE
    return OpenYantra(target, agent_name=AGENT_NAME)


def session_start_hook(payload: Dict[str, Any], file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Called when an OpenClaw agent session begins. Injects active context."""
    oy = _get_oy(file_path)
    target = file_path or OY_FILE
    if not target.exists():
        oy.bootstrap()
    oy.take_pratibimba()
    block = oy.build_system_prompt_block()
    payload["system_prompt"] = block + "\n\n" + payload.get("system_prompt", "")
    return payload


def pre_compact_hook(payload: Dict[str, Any], file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Called before OpenClaw compacts conversation context."""
    # Preserves open loops before compaction loses them
    return payload


def post_compact_hook(payload: Dict[str, Any], file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Called after OpenClaw context compaction. Restores open loops (Anishtha)."""
    oy = _get_oy(file_path)
    ctx = oy.load_session_context()
    loops = ctx.get("open_loops", [])
    if loops:
        loop_lines = []
        for item in loops:
            prio = item.get("Priority", "?")
            topic = item.get("Topic", "?")
            unresolved = item.get("Context / What's Unresolved", "")
            loop_lines.append(f"- [{prio}] {topic}: {unresolved}")
        loops_text = "\n".join(loop_lines)
        payload["new_context"] = payload.get("new_context", "") + (
            f"\n\n[OpenYantra: Anishtha restored after compaction]\n{loops_text}"
        )
    return payload


def session_end_hook(payload: Dict[str, Any], file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Called when an OpenClaw session terminates. Flushes session log."""
    oy = _get_oy(file_path)
    oy.log_session(
        topics=payload.get("topics", ["(auto-logged)"]),
        decisions=payload.get("decisions", []),
        new_memory=payload.get("new_memory", []),
    )
    oy.release_pratibimba()
    return payload
