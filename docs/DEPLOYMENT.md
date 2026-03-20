# OpenYantra Deployment Guide -- v2.12

> OpenClaw · LangChain · AutoGen · Raw Anthropic API

## Install

```bash
# Mac / Linux
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex

# Manual
pip install odfpy pandas scikit-learn faiss-cpu fastapi uvicorn
pip install sentence-transformers  # optional
```

## Morning Brief and Context Copy (v2.10+)

```python
# Morning brief -- runs automatically on first yantra command of the day
oy.morning_brief_auto()

# Full brief as string
brief = oy.morning_brief(format="terminal")   # or "telegram"

# Copy full context to clipboard for pasting into any AI chat
md = oy.build_context_markdown()
oy.copy_context()   # builds + copies to clipboard
```

CLI:
```bash
yantra morning    # print morning brief
yantra context    # build + copy context markdown to clipboard
```

## Session lifecycle

```
Startup        → sanchitta replay (crash recovery)
Session Start  → load_session_context() + take_pratibimba()
Conversation   → request_write() + search() + inbox()
Pre-Compaction → flush_open_loop()
Post-Compaction→ re-inject open loops from file
Session End    → log_session() + release_pratibimba()
```

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

# Writes
oy.add_project("My Film", status="Active", priority="High", importance=9)
oy.inbox("Quick thought captured mid-session")
oy.flush_open_loop("Unresolved decision", "Context here", "High", ttl_days=30)

# Semantic search
results = oy.search("screenplay structure")
loops   = oy.search_open_loops("unresolved film choices")

# Session end
oy.log_session(topics=["film"], decisions=["Use 3-act"])
oy.release_pratibimba()
```

## LangChain

```python
from openyantra.examples.langchain_adapter import OpenYantraChatMemory
from langchain.agents import initialize_agent

memory = OpenYantraChatMemory(path="~/openyantra/chitrapat.ods", agent_name="LangChain")
agent  = initialize_agent(tools=[], llm=llm, memory=memory)
```

## AutoGen

```python
import autogen
from openyantra import OpenYantra

oy      = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")
oy_ctx  = oy.build_system_prompt_block()
oy.take_pratibimba()

assistant = autogen.AssistantAgent(
    name="assistant",
    system_message=f"{oy_ctx}\n\nYou are a helpful assistant.",
    llm_config={"config_list": [{"model": "claude-sonnet-4-20250514"}]}
)
# ... run conversation ...
oy.log_session(topics=["session"]); oy.release_pratibimba()
```

## Raw Anthropic API

```python
import anthropic
from openyantra import OpenYantra

oy     = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
client = anthropic.Anthropic()

oy.take_pratibimba()
context  = oy.build_system_prompt_block()
relevant = oy.search("topic of conversation", top_k=3)
extra    = "\n".join(f"[Memory] {r['sheet']}: {r['primary_value']}" for r in relevant)

response = client.messages.create(
    model="claude-sonnet-4-20250514", max_tokens=2048,
    system=f"{context}\n\nRelevant memory:\n{extra}",
    messages=[{"role": "user", "content": "Help me"}]
)
oy.log_session(topics=["session"]); oy.release_pratibimba()
```

## Browser Dashboard

```bash
yantra ui          # opens http://localhost:7331
yantra ui 8080     # custom port
```

Tabs: Dashboard · Inbox · Projects · Open Loops · Tasks · Corrections · Ledger · Health

## Oracle and Export (v2.12)

```python
# Oracle -- cross-reference engine, read-only
insights = oy.oracle(max_insights=8)
# Returns list of dicts: type, title, detail, action
for ins in insights:
    print(f"[{ins['type']}] {ins['title']}")
    print(f"  {ins['detail']}")
    print(f"  Action: {ins['action']}")

# Plain text for terminal or morning brief
print(oy.oracle_text())

# Export -- markdown or JSON
md = oy.export()                                  # all sheets
md = oy.export(sheet="loops")                     # just open loops
md = oy.export(fmt="json", sheet="projects")      # JSON
oy.export(since="2026-01-01", output_path="~/ctx.md")
```

CLI:
```bash
yantra oracle
yantra export
yantra export --sheet loops
yantra export --format json
yantra export --since 2026-01-01 --output ~/ctx.md
```

## Troubleshooting

| Issue | Fix |
|---|---|
| "Chitrapat not found" | `yantra bootstrap` or `oy.bootstrap()` |
| "Sanchitta replayed" | Normal -- crashed writes auto-recovered |
| "VidyaKosha not available" | Ensure `vidyakosha.py` in same directory |
| Search returns empty | `oy._vidyakosha.sync(oy.path)` to rebuild index |
| Slow writes at scale | Expected -- full `.ods` rewrite; SQLite backend planned v3.0 |
