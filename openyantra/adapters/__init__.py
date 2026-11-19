"""
OpenYantra Framework Adapters (v6.2.2).
First-class drop-in bindings for LangChain, CrewAI, OpenClaw, AutoGen, and custom LLM agent pipelines.
"""

from openyantra.adapters.langchain import OpenYantraChatMessageHistory, OpenYantraRetriever
from openyantra.adapters.crewai import OpenYantraCrewMemory
from openyantra.adapters.openclaw import (
    session_start_hook,
    pre_compact_hook,
    post_compact_hook,
    session_end_hook,
)

__all__ = [
    "OpenYantraChatMessageHistory",
    "OpenYantraRetriever",
    "OpenYantraCrewMemory",
    "session_start_hook",
    "pre_compact_hook",
    "post_compact_hook",
    "session_end_hook",
]
