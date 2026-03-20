---
name: openyantra
version: "2.12"
description: >
  OpenYantra v2.12 -- The Sacred Memory Machine. Persistent, structured,
  human-readable memory for personal agentic AI. Single .ods file
  (chitrapat.ods) as canonical store alongside SQLite sync, single trusted
  writer (Chitragupta/LedgerAgent), hybrid semantic search (VidyaKosha),
  prompt injection protection (Raksha), and a v3 Briefing Room dashboard.
  Use whenever an agent needs to load, write, or search personal memory
  across sessions. Works with OpenClaw, LangChain, AutoGen, and Claude.
triggers:
  - "the AI keeps forgetting"
  - "I have to repeat myself every session"
  - "how do I give my agent persistent memory"
  - "remember this across sessions"
  - "load my context"
  - "flush open loops"
  - "chitrapat"
do_not_use_when:
  - Request is for multi-user or team memory (OpenYantra is single-human)
  - Request needs cloud infrastructure or SaaS
  - Request is for enterprise databases
---

# OpenYantra v2.12 -- Agent Skill Reference

> *Inspired by Chitragupta (चित्रगुप्त), the Hindu God of Data*

---

## Sanskrit Quick Reference (15 terms)

| Sanskrit | English | Component |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer -- all writes go through this |
| Agrasandhanī | Ledger | Immutable SHA-256-signed audit trail |
| Chitrapat | Memory file | `chitrapat.ods` -- canonical file (non-negotiable) |
| Karma-Lekha | WriteRequest | A write submitted to Chitragupta |
| Sanchitta | WriteQueue | Crash-safe queue (`sanchitta.json`) |
| Smarana | Session Load | Load context at session start |
| Anishtha | Open Loops | Unresolved threads -- compaction safety net |
| Mudra | Signature | SHA-256 seal on every write |
| Vivada | Conflict | Write conflict escalated to user |
| Dharma-Adesh | User Override | User edits always win |
| VidyaKosha | Semantic Index | BM25 + TF-IDF hybrid search sidecar |
| Pratibimba | Snapshot | Per-agent frozen index view |
| Raksha | Security Engine | Injection scanner + trust tiers |
| Nirodh | Quarantine | Blocked injection attempts sheet |
| Avagraha | Inbox | Quick capture before categorisation |

---

## Storage Architecture (Non-Negotiable)

```
chitrapat.ods  ← canonical human-readable store (always exists, never replaced)
      ↕  bidirectional sync
chitrapat.db   ← SQLite sidecar (fast writes, query power, sub-ms reads)
```

**Rules:**
- `.ods` is the source of truth visible to the human
- SQLite is the operational store for agent writes and VidyaKosha indexing
- Every Chitragupta commit writes to SQLite first, then syncs `.ods`
- Every time the user edits `.ods` in LibreOffice, `yantra sync` re-imports to SQLite
- `yantra sync --watch` watches the `.ods` file and re-imports on change automatically
- Neither store can be deleted or made optional

---

## Install and Bootstrap

```bash
# Mac / Linux
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash

# Windows PowerShell
irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex

# First run
yantra bootstrap   # 12-question interview, populates all key sheets
yantra ui          # Briefing Room dashboard at http://localhost:7331
```

```python
pip install odfpy pandas scikit-learn faiss-cpu fastapi uvicorn
from openyantra import OpenYantra
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")
```

---

## Session Lifecycle

### Phase 1 -- Smarana (Session Start)

```python
system_prompt = oy.build_system_prompt_block()
oy.take_pratibimba()      # optional: freeze VidyaKosha snapshot
oy.morning_brief_auto()   # fires once per day automatically
```

**Smarana load order:**
1. Identity + Agent Config
2. Active Projects (Status = Active)
3. Open Loops (Resolved? = No) -- sorted by Importance x recency, max 15
4. Active Goals, Pending Tasks
5. Count: inbox_pending, pending_corrections
6. Oracle cross-reference insights (v2.12)

### Phase 2 -- Active Session

```python
oy.add_project("My Film", domain="Creative", status="Active",
               priority="High", next_step="Write act 2", importance=9)
oy.flush_open_loop("Structure decision", "3-act vs 5-act undecided",
                   priority="High", ttl_days=30, importance=8)
oy.inbox("Priya mentioned budget revision needed by Friday")
oy.add_task("Research 5-act structure", project="My Film", priority="High")
oy.add_person("Priya", relationship="Producer", context="Budget approval needed")

# Semantic search -- score = relevance x importance x recency
results = oy.search("screenplay structure")

# Oracle -- cross-reference engine, read-only, never writes (v2.12)
insights = oy.oracle()
text     = oy.oracle_text()

# Export (v2.12)
md = oy.export()
md = oy.export(sheet="loops", fmt="json")
oy.export(since="2026-01-01", output_path="~/ctx.md")
```

### Phase 3 -- Pre-Compaction

```python
# Flush unresolved threads before context window compresses
oy.flush_open_loop("Unresolved topic", "Context", priority="High")
# After compaction: re-inject via build_system_prompt_block()
```

### Phase 4 -- Session End

```python
oy.log_session(
    topics=["screenplay structure"],
    decisions=["Will test 5-act structure this week"],
    new_memory=["Priya: budget approval by Friday"],
    open_loops_created=2,
)
oy.resolve_open_loop("Topic resolved", "Resolution text")
oy.release_pratibimba()
```

---

## The 14-Sheet Schema

| Sheet | Sanskrit | Purpose | Load Timing |
|---|---|---|---|
| 👤 Identity | Svarupa | Name, occupation, location, style | Session start |
| 🎯 Goals | Sankalpa | Long and short-term aims | Session start |
| 🚀 Projects | Karma | Active work + next step | Session start |
| 👥 People | Sambandha | Relationships, context | On person mention |
| 💡 Preferences | Ruchi | Tools, habits, anti-goals | Before recommendations |
| 🧠 Beliefs | Vishwas | Values, worldview, evolution | Before advice |
| ✅ Tasks | Kartavya | Action items | Session start |
| 🔓 Open Loops | Anishtha | Unresolved threads (flush before compaction) | Session start -- critical |
| 📅 Session Log | Dinacharya | Per-session summaries | On-demand |
| ⚙️ Agent Config | Niyama | Per-agent instructions + VidyaKosha mode | Session start |
| 📒 Agrasandhanī | -- | Immutable SHA-256-signed audit trail | Read-only |
| 📥 Inbox | Avagraha | Quick capture before routing | Check count at start |
| ✏️ Corrections | Sanshodhan | Agent-proposed edits pending approval | Check count at start |
| 🔒 Quarantine | Nirodh | Blocked prompt injection attempts | On-demand |

**Universal columns on every sheet:** Confidence · Source · Last Updated · Importance (1–10)

---

## Write Rules

1. All writes via `request_write()` -- never open `.ods` directly from agent code
2. Dharma-Adesh -- `User-stated` always overrides `Agent-inferred`
3. Anishtha and Tasks only grow -- mark Resolved? = Yes, never delete rows
4. Mark Source -- `User-stated` / `Agent-observed` / `Agent-inferred` / `System`
5. Set Importance 1–10 -- affects retrieval ranking and loop ordering
6. Oracle never writes -- reads, cross-references, proposes only

---

## CLI Reference

```bash
# Setup
yantra bootstrap          # 12-question interview -- cold start
yantra doctor             # system check: Python, packages, port, ODS integrity

# Daily
yantra morning            # morning brief (auto on first command of day)
yantra ui [port]          # Briefing Room at http://localhost:7331
yantra context            # copy context markdown to clipboard
yantra inbox "text"       # quick capture to Inbox
yantra oracle             # cross-reference insights (v2.12)
yantra export             # export all sheets to markdown (v2.12)
yantra export --sheet loops
yantra export --format json
yantra export --since 2026-01-01
yantra export --output ~/ctx.md
yantra digest             # daily summary

# Memory
yantra health             # sheet counts and system status
yantra stats              # memory growth analytics
yantra route              # auto-route Inbox items
yantra loops              # list unresolved Open Loops
yantra diff               # belief contradiction check
yantra ttl                # loops past TTL

# Capture
yantra telegram           # Telegram bot (any message to Inbox)
yantra shortcut           # iOS Shortcut HTTP server (port 7332)

# Sync (v3.0 -- bidirectional .ods / SQLite)
yantra sync               # sync .ods changes to SQLite
yantra sync --watch       # watch .ods file and sync on change

# Maintenance
yantra integrity          # verify all Agrasandhanī signatures
yantra archive            # rotate old session logs
yantra migrate            # upgrade Chitrapat schema
yantra security           # full Raksha security audit
yantra open               # open Chitrapat in LibreOffice
yantra version            # show version
```

---

## Python API -- Core Methods

```python
# Session
oy.build_system_prompt_block()
oy.build_context_markdown()
oy.load_session_context()
oy.morning_brief(format="terminal")
oy.morning_brief_auto()

# Writes (all through Chitragupta)
oy.add_project(project, domain, status, priority, next_step, importance)
oy.add_task(task, project, priority, deadline, status)
oy.add_person(name, relationship, context, sentiment)
oy.flush_open_loop(topic, context, priority, ttl_days, importance)
oy.resolve_open_loop(topic, resolution)
oy.update_identity(attribute, value)
oy.inbox(text, source, importance)
oy.log_session(topics, decisions, new_memory, open_loops_created)

# Search
oy.search(query, top_k, sheets, hybrid_alpha, importance_weight)
oy.search_open_loops(query)
oy.search_projects(query)
oy.search_people(query)
oy.take_pratibimba()
oy.release_pratibimba()

# Oracle (v2.12 -- read-only)
oy.oracle(max_insights)
oy.oracle_text()

# Export (v2.12)
oy.export(sheet, fmt, since, output_path)

# Health
oy.health_check()
oy.stats()
oy.diff_beliefs()
oy.check_anishtha_ttl()
oy.route_inbox()
oy.security_scan()
```

---

## VidyaKosha Search Semantics

```
score = (α × vector_score + (1-α) × bm25_score)
      × (1 + importance_weight × normalised_importance)
      × (1 + 0.1 × recency_factor)
```

- Default α = 0.7 (70% vector, 30% BM25)
- BM25 handles proper nouns reliably
- Importance weight: Importance=9 surfaces before Importance=3 at equal relevance
- Recency decays linearly over 365 days

---

## Raksha Security Model

| Tier | Agents | Treatment |
|---|---|---|
| 5 -- User | Human | Never blocked -- Dharma-Adesh |
| 4 -- Chitragupta | System, LedgerAgent | Full trust |
| 3 -- Known | Claude, OpenClaw, LangChain, AutoGen | Standard scan |
| 2 -- Unknown | Unregistered agents | Stricter scan |
| 1 -- External | Telegram bot, iOS Shortcut | Suspicious = confirmed block |
| 0 -- Untrusted | Explicitly flagged | Any flag blocks |

Blocked writes go to 🔒 Quarantine. Release via `yantra ui` Security tab or `oy.release_quarantine(request_id)`.

---

## System Prompt Block Format

```
[OPENYANTRA CONTEXT -- v2.12 | Chitragupta-secured]
User: {Name} | {Occupation} | {Location}
Active Projects (Karma): {Project} → {NextStep} ({Priority})
Open Loops (Anishtha, top 15): [{Priority}] {Topic} -- {Context}
Goals (Sankalpa): {Goal}
Tasks (Kartavya): {Task}
Alerts: 📥 {N} unrouted · ✏️ {N} corrections pending
Agent Instructions (Niyama): {Instruction}
[/OPENYANTRA CONTEXT]
```

---

## Controlled Vocabulary

| Column | Allowed Values |
|---|---|
| Project Status | `Active` / `Paused` / `Completed` / `Cancelled` |
| Task Status | `Pending` / `In Progress` / `Done` / `Blocked` |
| Goal Status | `Active` / `In Progress` / `Achieved` / `Abandoned` |
| Resolved? | `Yes` / `No` |
| Priority | `Critical` / `High` / `Medium` / `Low` |
| Confidence | `High` / `Medium` / `Low` / `Inferred` |
| Source | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| Importance | Integer 1–10 |

---

## File Layout

```
openyantra/
├── openyantra.py          Core library v2.12
├── vidyakosha.py          Semantic index
├── yantra_ui.py           Briefing Room dashboard (port 7331)
├── yantra_security.py     Raksha security engine
├── yantra_digest.py       Daily digest
├── telegram_bot.py        Telegram capture
├── ios_shortcut.py        iOS Shortcut HTTP capture
├── yantra_migrate.py      Schema migration tool
├── install.sh / install.ps1
├── chitrapat_template.ods Blank 14-sheet memory file
├── SKILL.md               This file
├── PROTOCOL.md            Open spec (CC0)
├── MYTHOLOGY.md           Chitragupta origin
├── WHITEPAPER.md          Research document
├── UI/v3/dashboard.html   Briefing Room HTML
├── docs/
│   ├── DEPLOYMENT.md      Framework integration guide
│   ├── brand-manual.html    Design system
│   └── visual-guide.html    Architecture diagrams
├── assets/                SVG brand assets
├── openclaw/              OpenClaw hooks + plugin
└── examples/              Quickstart + LangChain adapter
```

---

*Protocol: CC0 1.0 Universal · Library: MIT*
*github.com/revanthlevaka/OpenYantra*
