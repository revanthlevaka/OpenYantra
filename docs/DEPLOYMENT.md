# OpenYantra Deployment Guide

> Implementation guide for agentic AI systems  
> **Primary example: OpenClaw** — with LangChain, AutoGen, and raw API examples

---

## Overview

This guide covers how to integrate OpenYantra into your agentic AI system as persistent memory. OpenYantra works by maintaining a structured `.ods` file — the **Chitrapat** (life scroll) — that agents read from and write to via the single trusted writer: **Chitragupta (LedgerAgent)**.

Every session follows the same lifecycle:

```
Startup
  └── replay_sanchitta()       ← replay any pending writes from crash
        ↓
Session Start (Smarana)
  └── load_session_context()   ← read 6 sheets, inject into system prompt
        ↓
Conversation
  └── request_write()          ← all writes routed through Chitragupta
        ↓
Pre-Compaction
  └── flush_open_loop()        ← Anishtha — protect context from compaction
        ↓
Session End
  └── log_session()            ← Dinacharya — write summary to Session Log
```

---

## Installation

```bash
pip install odfpy pandas
git clone https://github.com/yourusername/openyantra
cd openyantra
```

---

## Part 1 — OpenClaw (Primary Integration)

OpenClaw supports a hook system that maps perfectly onto OpenYantra's session lifecycle. This is the reference integration.

### Step 1 — Configure hooks

```toml
# ~/.openclaw/config.toml

[memory]
enabled   = true
backend   = "openyantra"
file_path = "~/openyantra/chitrapat.ods"
agent_name = "OpenClaw"

[hooks]
pre_compact  = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact = "openyantra.openclaw.hooks:post_compact_hook"
session_end  = "openyantra.openclaw.hooks:session_end_hook"
session_start = "openyantra.openclaw.hooks:session_start_hook"
```

### Step 2 — Install the plugin

```python
# openclaw/plugin.py (already included in OpenYantra)
# Drop it into your OpenClaw plugins/ directory or register via config.

# Or install programmatically:
from openyantra.openclaw.plugin import register_plugin
register_plugin()
```

### Step 3 — Bootstrap on first run

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")

if not oy.path.exists():
    oy.bootstrap(
        user_name  = "Revanth",
        occupation = "Filmmaker",
        location   = "Hyderabad, IN"
    )
    print(f"Chitrapat created at {oy.path}")
    print("Open it in LibreOffice to see and edit your memory.")
```

### Step 4 — Verify the integration

Run a test session:

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")

# Check what Chitragupta knows
ctx = oy.load_session_context()
print("Identity:", ctx["identity"])
print("Active projects:", len(ctx["active_projects"]))
print("Open loops:", len(ctx["open_loops"]))

# Check the Agrasandhanī (audit ledger)
ledger = oy.get_agrasandhani()
print(f"Ledger entries: {len(ledger)}")

# Full system prompt block
print(oy.build_system_prompt_block())
```

### How the hooks work

**`session_start_hook`** — called before first user message:
- Reads `chitrapat.ods` (Smarana)
- Builds the `[OPENYANTRA CONTEXT]` block
- Prepends it to the system prompt
- Replays any pending Sanchitta (WriteQueue) entries

```python
# openclaw/hooks.py
def session_start_hook(session_context: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    uam_block = oy.build_system_prompt_block()
    session_context["system_prompt"] = uam_block + "\n\n" + session_context.get("system_prompt", "")
    return session_context
```

**`pre_compact_hook`** — called BEFORE context compaction:
- Scans conversation for unresolved threads (Anishtha)
- Flushes them to `🔓 Open Loops` via Chitragupta
- These survive the compaction

```python
def pre_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    open_loops = extract_open_loops(payload["conversation"])
    for loop in open_loops:
        oy.flush_open_loop(**loop)
    return payload
```

**`post_compact_hook`** — called AFTER context compaction:
- Re-reads unresolved Anishtha from the file
- Re-injects them into the new compacted context
- Context survives compaction intact

```python
def post_compact_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    ctx = oy.load_session_context()
    if ctx["open_loops"]:
        loops_text = "\n".join(
            f"- [{l['Priority']}] {l['Topic']}: {l.get('Context / What\'s Unresolved', '')}"
            for l in ctx["open_loops"]
        )
        payload["new_context"] += f"\n\n[OpenYantra: Anishtha restored after compaction]\n{loops_text}"
    return payload
```

**`session_end_hook`** — called when session ends:
- Writes Dinacharya (session summary) to `📅 Session Log`

```python
def session_end_hook(payload: dict) -> dict:
    oy = OpenYantra(OY_FILE, agent_name="OpenClaw")
    oy.log_session(
        topics   = payload.get("topics", ["(session)"]),
        decisions= payload.get("decisions", []),
        new_memory= payload.get("new_memory", []),
    )
    return payload
```

### Complete OpenClaw session example

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="OpenClaw")

# --- SESSION START ---
ctx = oy.load_session_context()
system_prompt = oy.build_system_prompt_block() + "\n\nYou are a helpful assistant..."

# ... conversation with user ...
# User: "I'm working on my screenplay and stuck on the structure"

# --- DURING SESSION ---
# Agent recognises new fact — write via Chitragupta
oy.add_project(
    project    = "Feature Screenplay",
    domain     = "Creative",
    status     = "Active",
    priority   = "High",
    next_step  = "Decide between 3-act and 5-act structure"
)

# Agent writes a task
oy.add_task(
    task     = "Research 5-act structure examples",
    project  = "Feature Screenplay",
    priority = "High"
)

# --- PRE-COMPACTION (if context getting long) ---
oy.flush_open_loop(
    topic           = "3-act vs 5-act structure",
    context         = "User undecided — likes 5-act for complexity but worried about pacing",
    priority        = "High",
    related_project = "Feature Screenplay"
)

# --- SESSION END ---
oy.log_session(
    topics    = ["screenplay structure", "feature film project"],
    decisions = ["Will research 5-act examples before deciding"],
    open_loops_created = 1
)

# Verify Agrasandhanī (audit trail)
ledger = oy.get_agrasandhani()
print(f"This session wrote {len(ledger)} entries to Agrasandhanī")
```

---

## Part 2 — LangChain Integration

```python
from openyantra.examples.langchain_adapter import OpenYantraChatMemory
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatAnthropic

# Memory backed by OpenYantra
memory = OpenYantraChatMemory(
    path       = "~/openyantra/chitrapat.ods",
    agent_name = "LangChain"
)

# Initialise agent with OpenYantra memory
llm   = ChatAnthropic(model="claude-sonnet-4-20250514")
agent = initialize_agent(
    tools      = [],  # your tools here
    llm        = llm,
    agent      = AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory     = memory,
    verbose    = True
)

# The agent now has persistent memory across sessions
response = agent.run("Help me plan my film project")
```

### How the LangChain adapter works

```python
# openyantra/examples/langchain_adapter.py

class OpenYantraChatMemory(BaseChatMemory):
    path: str = "~/openyantra/chitrapat.ods"
    agent_name: str = "LangChain"

    def load_memory_variables(self, inputs):
        oy = OpenYantra(self.path, self.agent_name)
        block = oy.build_system_prompt_block()
        return {self.memory_key: block}

    def save_context(self, inputs, outputs):
        oy = OpenYantra(self.path, self.agent_name)
        oy.log_session(
            topics=[inputs.get("input", "")[:80]],
            agent=self.agent_name
        )
```

---

## Part 3 — AutoGen Integration

```python
import autogen
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")

# Build OpenYantra context block
oy_context = oy.build_system_prompt_block()

# Inject into agent system message
assistant = autogen.AssistantAgent(
    name           = "assistant",
    system_message = f"{oy_context}\n\nYou are a helpful AI assistant.",
    llm_config     = {"config_list": [{"model": "claude-sonnet-4-20250514"}]}
)

user_proxy = autogen.UserProxyAgent(
    name             = "user_proxy",
    human_input_mode = "NEVER",
    code_execution_config = False
)

# After each conversation, write summary
def on_conversation_end(chat_result):
    oy.log_session(
        topics    = ["AutoGen session"],
        decisions = [],
        agent     = "AutoGen"
    )

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

# Session start — load context
oy_context = oy.build_system_prompt_block()

# Build message history
messages = [
    {"role": "user", "content": "Help me plan my feature film"}
]

# Call API with OpenYantra context in system prompt
response = client.messages.create(
    model      = "claude-sonnet-4-20250514",
    max_tokens = 2048,
    system     = f"{oy_context}\n\nYou are a helpful creative assistant.",
    messages   = messages
)

print(response.content[0].text)

# Write any new facts from this session
oy.add_project("Feature Film 2025", domain="Creative", status="Active",
               priority="High", next_step="Develop logline")
oy.log_session(topics=["film planning"], decisions=["Start with logline"])
```

---

## Part 5 — CrewAI Integration (Planned)

```python
# Coming in OpenYantra v1.1
# from openyantra.examples.crewai_adapter import OpenYantraMemory
# crew = Crew(agents=[...], tasks=[...], memory=OpenYantraMemory(...))
```

---

## Part 6 — Viewing and Managing the Chitrapat

### Open in LibreOffice (recommended)

```bash
libreoffice ~/openyantra/chitrapat.ods
```

The file opens with all 12 sheets. You can edit any cell — your changes are respected as Dharma-Adesh (user override) next session.

### View the Agrasandhanī (audit trail)

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods")
ledger = oy.get_agrasandhani()

for entry in ledger[-10:]:  # last 10 entries
    print(f"[{entry['Status']}] {entry['Agent']} → {entry['Sheet']} "
          f"| {entry['Operation']} | Mudra: {str(entry['Signature'])[:20]}")
```

### View pending Sanchitta (write queue)

```python
from openyantra.openyantra import WriteQueue
from pathlib import Path

queue = WriteQueue(Path("~/openyantra/sanchitta.json").expanduser())
pending = queue.peek()
print(f"Pending writes: {len(pending)}")
for p in pending:
    print(f"  {p['requesting_agent']} → {p['sheet']} / {p['operation']}")
```

### Export to CSV for external analysis

```python
import pandas as pd

oy = OpenYantra("~/openyantra/chitrapat.ods")
sheets = ["🚀 Projects", "✅ Tasks", "🔓 Open Loops"]

for sheet in sheets:
    records = oy._read_sheet(sheet)
    df = pd.DataFrame(records)
    df.to_csv(f"{sheet.split()[-1].lower()}.csv", index=False)
    print(f"Exported {len(records)} rows from {sheet}")
```

---

## Part 7 — Multi-Agent Setup

When multiple agents (Claude + AutoGen + OpenClaw) share one Chitrapat:

```python
# Claude reads context at session start
claude_oy  = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
autogen_oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="AutoGen")

# All agents read freely
claude_ctx  = claude_oy.load_session_context()
autogen_ctx = autogen_oy.load_session_context()  # same data

# All writes go through Chitragupta — no conflict possible
claude_oy.add_project("Film Project", status="Active", priority="High")
autogen_oy.add_task("Research comp films", project="Film Project")

# Agrasandhanī records which agent wrote what
ledger = claude_oy.get_agrasandhani()
for e in ledger:
    print(f"{e['Agent']:12} → {e['Sheet']:20} | {e['Status']}")
```

**Key guarantee:** Because Chitragupta is the sole writer and uses file-level locking, no two agents can corrupt each other's data. Vivada (conflict) is only possible between an agent write and a human cell edit — and that is always escalated to the user.

---

## Part 8 — Production Checklist

Before deploying OpenYantra in production:

- [ ] Chitrapat stored in a reliable location (not `/tmp`)
- [ ] Daily backup configured (hook or cron job)
- [ ] File permissions restricted to the agent process user
- [ ] LibreOffice password protection enabled for sensitive deployments
- [ ] Regional profile applied (`-IN`, `-EU`, `-US`, or `-CN`)
- [ ] Digital will documented (see PRIVACY.md)
- [ ] Test crash recovery: verify `sanchitta.json` replay works
- [ ] Verify Agrasandhanī is being written on every session
- [ ] At least one human review of Chitrapat contents after first week

---

## Part 9 — Troubleshooting

**"Chitrapat not found"**
```python
oy.bootstrap()  # creates the file
```

**"Pending writes replayed on startup"**
```
[OpenYantra] Replayed 3 pending Karma-Lekha from previous session.
```
Normal behaviour — Sanchitta auto-replayed after crash. No action needed.

**"Vivada — conflict escalated"**
```python
receipt = oy.request_write(req)
if receipt["status"] == "conflict":
    print(f"Conflict: agent wants '{receipt['requested_value']}', "
          f"you have '{receipt['existing_value']}'")
    # Raise with user next session
```

**"LibreOffice not installed"**
```bash
# Ubuntu/Debian
sudo apt install libreoffice

# macOS
brew install --cask libreoffice

# Windows
# Download from https://libreoffice.org
```

**"Agrasandhanī has no entries"**
The Agrasandhanī sheet is written after each successful commit. If it's empty, check that `request_write()` is being called (not direct file writes).

---

## Summary

| Step | What to do | Sanskrit term |
|---|---|---|
| First run | `oy.bootstrap()` | Chitragupta Puja |
| Session start | `oy.build_system_prompt_block()` | Smarana |
| Any write | `oy.request_write()` or helpers | Karma-Lekha to Chitragupta |
| Pre-compaction | `oy.flush_open_loop()` | Anishtha flush |
| Session end | `oy.log_session()` | Dinacharya |
| Audit | `oy.get_agrasandhani()` | Read Agrasandhanī |
| User edit | Open file in LibreOffice, edit | Dharma-Adesh |
