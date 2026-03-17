# OpenYantra Deployment Guide — v2.11

> OpenClaw · LangChain · AutoGen · raw API clients

## Install

```bash
# Mac / Linux
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex

# Manual dependencies
pip install odfpy pandas scikit-learn faiss-cpu fastapi uvicorn
pip install sentence-transformers  # optional
```

## Session Lifecycle

```text
Startup         -> Sanchitta replay (crash recovery)
Session start   -> load_session_context() + take_pratibimba()
Conversation    -> request_write() + search() + inbox()
Pre-compaction  -> flush_open_loop()
Post-compaction -> re-inject open loops from file
Session end     -> log_session() + release_pratibimba()
```

## Browser Dashboard Architecture

The canonical dashboard for v2.11 lives at:

```text
UI/v3/dashboard.html
```

The UI server in `yantra_ui.py` now serves that file directly with `FileResponse` rather than embedding the dashboard as an inline HTML string.

Important v2.11 paths:

```text
UI/v3/dashboard.html   # canonical dashboard source
UI/v3/index.html       # canonical landing page source
index.html             # mirrored landing page for root deploys
yantra_ui.py           # FastAPI server and API surface
```

The dashboard keeps the v2.10 backend behaviors while presenting the new 7-tab v3 interface:

- Today
- Inbox
- Loops
- Projects
- Timeline
- Review
- System

The Today view exposes the stable `oracle-card` hook for Oracle work in v2.12.

## Capture Surfaces

Supported optional capture channels:

- Telegram bot
- iOS Shortcut

Email and SMTP capture are not part of OpenYantra.

## OpenClaw

```toml
# openclaw/config.toml
[hooks]
session_start = "openyantra.openclaw.hooks:session_start_hook"
pre_compact   = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact  = "openyantra.openclaw.hooks:post_compact_hook"
session_end   = "openyantra.openclaw.hooks:session_end_hook"

[env]
OPENYANTRA_FILE = "~/openyantra/chitrapat.ods"
```

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")
oy.take_pratibimba()
system_prompt = oy.build_system_prompt_block()

oy.add_project("My Film", status="Active", priority="High", importance=9)
oy.inbox("Quick thought captured mid-session")
oy.flush_open_loop("Unresolved decision", "Context here", "High", ttl_days=30)

results = oy.search("screenplay structure")
loops = oy.search_open_loops("unresolved film choices")

oy.log_session(topics=["film"], decisions=["Use 3-act"])
oy.release_pratibimba()
```

## LangChain

```python
from openyantra.examples.langchain_adapter import OpenYantraChatMemory
from langchain.agents import initialize_agent

memory = OpenYantraChatMemory(
    path="~/openyantra/chitrapat.ods",
    agent_name="LangChain",
)
agent = initialize_agent(tools=[], llm=llm, memory=memory)
```

## AutoGen

```python
import autogen
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")
oy_ctx = oy.build_system_prompt_block()
oy.take_pratibimba()

assistant = autogen.AssistantAgent(
    name="assistant",
    system_message=f"{oy_ctx}\n\nYou are a helpful assistant.",
    llm_config={"config_list": [{"model": "claude-sonnet-4-20250514"}]},
)

oy.log_session(topics=["session"])
oy.release_pratibimba()
```

## Raw API Client Pattern

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.take_pratibimba()

context = oy.build_system_prompt_block()
relevant = oy.search("topic of conversation", top_k=3)
extra = "\n".join(
    f"[Memory] {r['sheet']}: {r['primary_value']}"
    for r in relevant
)

system_prompt = f"{context}\n\nRelevant memory:\n{extra}"

# send system_prompt to your model client here

oy.log_session(topics=["session"])
oy.release_pratibimba()
```

## Local UI

```bash
yantra ui          # opens http://localhost:7331
yantra ui 8080     # custom port
```

## Troubleshooting

| Issue | Fix |
|---|---|
| `Chitrapat not found` | Run `yantra bootstrap` first |
| `Dashboard file missing` | Ensure `UI/v3/dashboard.html` exists in the install or checkout |
| `Sanchitta replayed` | Normal crash recovery; queued writes were re-applied |
| `VidyaKosha not available` | Ensure `vidyakosha.py` is present in the same install |
| Search returns empty | Rebuild the sidecar index with `oy._vidyakosha.sync(oy.path)` |
| Slow writes at scale | Expected in `.ods`; WAL-backed storage is planned for v3.0 |
