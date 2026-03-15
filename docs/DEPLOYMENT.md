# OpenYantra Deployment Guide — v2.0

> Implementation guide for agentic AI systems
> Primary example: **OpenClaw** · also LangChain · AutoGen · Raw API

---

## What's New in v2.0

Every integration now has access to VidyaKosha semantic search:

```python
# Instead of filtering sheets manually:
loops = [r for r in ctx["open_loops"] if "screenplay" in str(r).lower()]

# Use semantic search:
loops = oy.search_open_loops("screenplay structure decisions")
```

---

## Installation

```bash
# Core (required)
pip install odfpy pandas scikit-learn faiss-cpu

# Optional — better semantic search quality
pip install sentence-transformers
```

---

## Session Lifecycle (v2.0)

```
Startup
  └── sanchitta replay          ← crash recovery
Session Start (Smarana)
  └── load_session_context()    ← read 6 sheets
  └── take_pratibimba()         ← freeze index (if per-session mode)
Conversation
  └── request_write()           ← all writes via Chitragupta
  └── search()                  ← semantic queries via VidyaKosha
Pre-Compaction
  └── flush_open_loop()         ← Anishtha protection
Post-Compaction
  └── re-inject Anishtha        ← restore from file
Session End
  └── log_session()             ← Dinacharya
  └── release_pratibimba()      ← release snapshot
```

---

## Part 1 — OpenClaw (Primary)

### Step 1 — config.toml

```toml
[memory]
enabled    = true
backend    = "openyantra"
file_path  = "~/openyantra/chitrapat.ods"
agent_name = "OpenClaw"

[hooks]
session_start = "openyantra.openclaw.hooks:session_start_hook"
pre_compact   = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact  = "openyantra.openclaw.hooks:post_compact_hook"
session_end   = "openyantra.openclaw.hooks:session_end_hook"
```

### Step 2 — Bootstrap

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")
if not oy.path.exists():
    oy.bootstrap(user_name="Revanth", occupation="Filmmaker",
                 location="Hyderabad, IN")
```

### Step 3 — Full session example with VidyaKosha

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")

# SESSION START
ctx = oy.load_session_context()
oy.take_pratibimba()                    # v2.0 — freeze index snapshot
system_prompt = oy.build_system_prompt_block()

# DURING SESSION — semantic search
results = oy.search("screenplay structure film")
for r in results:
    print(f"[{r['sheet']}] {r['primary_value']} score={r['score']:.3f}")

# Find relevant open loops semantically
loops = oy.search_open_loops("unresolved narrative decisions", top_k=3)

# Find relevant people
people = oy.search_people("producer film collaborator", top_k=2)

# WRITE new facts
oy.add_project("Feature Screenplay", domain="Creative", status="Active",
               priority="High", next_step="Decide structure")
oy.add_task("Research 5-act examples", project="Feature Screenplay",
            priority="High")

# PRE-COMPACTION
oy.flush_open_loop("3-act vs 5-act structure",
                   "Undecided — 5-act more depth, 3-act safer for debut",
                   priority="High", related_project="Feature Screenplay")

# SESSION END
oy.log_session(
    topics=["screenplay structure", "project setup"],
    decisions=["Research 5-act structure before deciding"],
    open_loops_created=1
)
oy.release_pratibimba()                 # v2.0 — release snapshot

# Audit
ledger = oy.get_agrasandhani()
print(f"Session wrote {len(ledger)} entries to Agrasandhanī")
```

### Hook implementations

```python
# openclaw/hooks.py

from openyantra import OpenYantra
OY_FILE = "~/openyantra/chitrapat.ods"

def session_start_hook(session_context: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    if not oy.path.exists():
        oy.bootstrap()
    oy.take_pratibimba()                # v2.0
    block = oy.build_system_prompt_block()
    session_context["system_prompt"] = block + "\n\n" + \
        session_context.get("system_prompt", "")
    return session_context

def pre_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    # Use VidyaKosha to find related open loops
    existing = oy.search_open_loops("unresolved pending", top_k=10)
    existing_topics = {r["primary_value"] for r in existing}
    # Flush new ones from conversation
    loops = _extract_open_loops(payload.get("conversation", []))
    for loop in loops:
        if loop["topic"] not in existing_topics:
            oy.flush_open_loop(**loop)
    return payload

def post_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    ctx = oy.load_session_context()
    if ctx["open_loops"]:
        loops_text = "\n".join(
            f"- [{l['Priority']}] {l['Topic']}: "
            f"{l.get('Context / What\\'s Unresolved', '')}"
            for l in ctx["open_loops"]
        )
        payload["new_context"] += (
            f"\n\n[OpenYantra: Anishtha restored after compaction]\n{loops_text}"
        )
    return payload

def session_end_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    oy.log_session(
        topics=payload.get("topics", ["(session)"]),
        decisions=payload.get("decisions", []),
        new_memory=payload.get("new_memory", []),
    )
    oy.release_pratibimba()             # v2.0
    return payload

def _extract_open_loops(conversation: list) -> list[dict]:
    # Replace with your model call to extract unresolved threads
    return []
```

---

## Part 2 — LangChain

```python
from openyantra.examples.langchain_adapter import OpenYantraChatMemory
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatAnthropic

memory = OpenYantraChatMemory(
    path="~/openyantra/chitrapat.ods",
    agent_name="LangChain"
)
llm   = ChatAnthropic(model="claude-sonnet-4-20250514")
agent = initialize_agent(tools=[], llm=llm,
                         agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                         memory=memory, verbose=True)

# v2.0 — semantic search available on the underlying OpenYantra instance
oy      = memory._get_oy()
results = oy.search("unresolved decisions from previous sessions")
```

---

## Part 3 — AutoGen

```python
import autogen
from openyantra import OpenYantra

oy        = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")
oy_block  = oy.build_system_prompt_block()
oy.take_pratibimba()                    # v2.0

assistant = autogen.AssistantAgent(
    name="assistant",
    system_message=f"{oy_block}\n\nYou are a helpful AI assistant.",
    llm_config={"config_list": [{"model": "claude-sonnet-4-20250514"}]}
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False
)

def on_conversation_end(chat_result):
    # v2.0 — search for unresolved threads before ending
    loops = oy.search("unresolved undecided unclear", top_k=5)
    for loop in loops:
        if loop.get("sheet") not in ("🔓 Open Loops",):
            oy.flush_open_loop(
                topic=str(loop["primary_value"]),
                context="Identified via VidyaKosha end-of-session scan",
                priority="Medium"
            )
    oy.log_session(topics=["AutoGen session"], agent="AutoGen")
    oy.release_pratibimba()             # v2.0

user_proxy.initiate_chat(assistant, message="Help me with my project")
on_conversation_end(None)
```

---

## Part 4 — Raw Anthropic API

```python
import anthropic
from openyantra import OpenYantra

oy     = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
client = anthropic.Anthropic()

# Session start
oy_context = oy.build_system_prompt_block()
oy.take_pratibimba()                    # v2.0

# v2.0 — search before responding
relevant = oy.search("film screenplay structure", top_k=3)
extra_context = "\n".join(
    f"[Memory] {r['sheet']}: {r['primary_value']}"
    for r in relevant
)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    system=f"{oy_context}\n\nRelevant memory:\n{extra_context}\n\n"
           "You are a helpful creative assistant.",
    messages=[{"role": "user", "content": "Help me plan my film"}]
)

# Write new facts
oy.add_project("Feature Film 2025", domain="Creative",
               status="Active", priority="High")
oy.log_session(topics=["film planning"], decisions=["Start with logline"])
oy.release_pratibimba()                 # v2.0
```

---

## Part 5 — Multi-Agent Setup

```python
from openyantra import OpenYantra

# Each agent gets its own OpenYantra instance — same Chitrapat
claude  = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
autogen = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")

# Configure snapshot modes in Agent Config sheet:
# Claude  → "Use per-session snapshot mode" → frozen during session
# AutoGen → "Use live index mode"            → sees real-time writes

claude.take_pratibimba()   # Claude's view is frozen

# Claude writes
claude.add_project("Feature Film", status="Active", priority="High")

# AutoGen reads updated index (live mode)
results = autogen.search("film project active")  # sees the new project

# Claude's search still uses frozen snapshot
results = claude.search("film project", snapshot_mode="per-session")

claude.release_pratibimba()
```

---

## Part 6 — Viewing and Managing

```bash
# Open in LibreOffice
libreoffice ~/openyantra/chitrapat.ods

# View VidyaKosha index files
ls ~/openyantra/vidyakosha*
ls ~/openyantra/pratibimba/
```

```python
# Audit trail
for e in oy.get_agrasandhani()[-10:]:
    print(f"[{e.get('Status')}] {e.get('Agent')} → "
          f"{e.get('Sheet')} / {e.get('Operation')} | "
          f"{str(e.get('Signature',''))[:20]}")

# VidyaKosha stats
print(oy.get_vidyakosha_stats())
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "VidyaKosha not available" | Ensure `vidyakosha.py` is in same directory |
| Search returns empty | Call `oy._vidyakosha.sync(oy.path)` to rebuild index |
| "Chitrapat not found" | Run `oy.bootstrap()` |
| "Sanchitta replayed on startup" | Normal — crashed writes auto-recovered |
| "Vivada — conflict escalated" | Check `receipt["existing_value"]` vs `receipt["requested_value"]`, ask user |

---

## Production Checklist (v2.0)

- [ ] `vidyakosha.py` in same directory as `openyantra.py`
- [ ] `scikit-learn` and `faiss-cpu` installed
- [ ] Chitrapat in reliable location (not `/tmp`)
- [ ] Daily backup configured
- [ ] `take_pratibimba()` / `release_pratibimba()` called at session boundaries
- [ ] `search()` used for semantic retrieval (not just filter loops)
- [ ] Regional profile applied (IN / EU / US / CN)
- [ ] Agrasandhanī reviewed after first week
