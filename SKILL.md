---
name: openyantra
version: 3.0.0
description: >
  Implements OpenYantra v3.0.0 -- The Sacred Memory Machine -- persistent,
  structured, human-readable memory for personal agentic AI, inspired by
  Chitragupta (the Hindu God of Data). Uses open-standard .ods files,
  SQLite WAL operational backend, Chitragupta/LedgerAgent single-writer,
  VidyaKosha hybrid semantic search, Inbox quick capture, Morning Briefing,
  Copy Context, browser dashboard, and one-command CLI installer.
  Use whenever the user wants an AI agent to remember things across sessions,
  building agentic tools needing persistent context, setting up memory for
  OpenClaw / LangChain / AutoGen, or saying "the AI keeps forgetting",
  "I have to repeat myself", "how do I give my agent memory".
---

# OpenYantra v3.0.0 -- The Sacred Memory Machine

> *Inspired by Chitragupta, the Hindu God of Data*

---

## Sanskrit Reference

| Sanskrit | English | Component |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer |
| Agrasandhanī | Ledger | Audit trail |
| Chitrapat | Memory file | `chitrapat.ods` |
| Karma-Lekha | WriteRequest | Write to Chitragupta |
| Sanchitta | WriteQueue | Crash-safe queue |
| Setu | SyncEngine | SQLite-to-ODS bridge (v3.0) |
| Smarana | Session Load | Load at session start |
| Anishtha | Open Loops | Unresolved threads |
| Mudra | Signature | SHA-256 seal |
| Vivada | Conflict | Escalated to user |
| Dharma-Adesh | User Override | User always wins |
| VidyaKosha | Sidecar Index | Semantic search |
| Pratibimba | Snapshot | Per-agent frozen index |
| Avagraha | Inbox | Quick capture |
| Sanshodhan | Corrections | Pending edits |

---

## Quick Start

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Smarana -- inject into system prompt
print(oy.build_system_prompt_block())

# Writes via Chitragupta
oy.add_project("My Film", domain="Creative", status="Active",
               priority="High", next_step="Write act 2", importance=9)
oy.flush_open_loop("3-act vs 5-act", "Undecided", "High", ttl_days=30)

# Quick capture (Inbox)
oy.inbox("Priya mentioned budget revision needed")

# Copy context for web AI tools
md = oy.build_context_markdown()

# Semantic search (VidyaKosha)
results = oy.search("screenplay structure decisions")

# Session end
oy.log_session(topics=["screenplay"], decisions=["Use 3-act"])
```

---

## CLI

```bash
# Install
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash

# Daily commands
yantra bootstrap     # interview-based cold start
yantra morning       # daily brief -- auto-runs on first command
yantra ui            # browser dashboard -> http://localhost:7331
yantra inbox "text"  # quick capture
yantra context       # copy memory to clipboard, paste into any AI
yantra health        # system status
yantra loops         # list open loops
yantra corrections   # list and apply pending corrections
yantra sync          # import ODS edits back to SQLite
yantra stats         # memory growth analytics
```

---

## 14-Sheet Schema

| Sheet | Sanskrit | English | Load timing |
|---|---|---|---|
| `👤 Identity` | Svarupa | Identity | Session start |
| `🎯 Goals` | Sankalpa | Goals | Session start |
| `🚀 Projects` | Karma | Projects | Session start |
| `👥 People` | Sambandha | People | On person mention |
| `💡 Preferences` | Ruchi | Preferences | Before recommendations |
| `🧠 Beliefs` | Vishwas | Beliefs | Before advice |
| `✅ Tasks` | Kartavya | Tasks | Session start |
| `🔓 Open Loops` | Anishtha | Open Loops | **Session start -- critical** |
| `📅 Session Log` | Dinacharya | Session Log | On-demand |
| `⚙️ Agent Config` | Niyama | Agent Config | Session start |
| `📒 Agrasandhanī` | Agrasandhanī | Ledger | Read-only audit |
| `📥 Inbox` | Avagraha | Inbox | Check count at start |
| `✏️ Corrections` | Sanshodhan | Corrections | Check count at start |
| `🔒 Quarantine` | Nirodh | Quarantine | Security review |

Universal columns: `Confidence` · `Source` · `Last Updated` · `Importance` (1-10)

---

## v3.0 Architecture: SQLite + ODS

```
Agent -> WriteRequest -> Chitragupta (LedgerAgent)
                              |
                    Raksha security scan
                              |
                    Admission gate + validate
                              |
                    SHA-256 Mudra seal
                              |
                    SQLite WAL write (2ms)
                              |
                    Ledger audit log
                              |
                    Async ODS export (atomic)
                              |
                    VidyaKosha index sync

SQLite = operational source of truth (fast reads/writes)
ODS    = human-readable canonical export (open in LibreOffice)
Sync   = bidirectional: yantra sync imports ODS edits back
```

**Performance (Round 5 measured):**
- SQLite WAL write: 2ms flat at any row count
- ODS export: 78ms@200 rows, 366ms@1000 rows (off hot path)
- Concurrent reads: portalocker prevents file corruption
- Write idempotency: request_id dedup prevents double-writes

---

## Session Load (Smarana)

```
1. LOAD  Identity, Agent Config
2. LOAD  Projects (Active), Open Loops (Unresolved, top 15 by Importance)
3. LOAD  Goals (Active), Tasks (Pending)
4. CHECK Inbox count, Corrections pending
5. take_pratibimba() if per-session mode
```

### System Prompt Block

```
[OPENYANTRA CONTEXT -- v3.0.0 | Chitragupta-secured]
User: {Name} | {Occupation} | {Location}
Active Projects (Karma): {Project} -> {NextStep}
Open Loops (Anishtha, top 15): [{Priority}] {Topic} -- {Context}
Goals (Sankalpa): {Goal}
Tasks (Kartavya): {Task}
Alerts: 📥 {N} unrouted · ✏️ {N} corrections pending
Agent Instructions (Niyama): {Instruction}
[/OPENYANTRA CONTEXT]
```

---

## Session End

```
1. FLUSH  Anishtha -> flush_open_loop()
2. WRITE  Dinacharya -> log_session()
3. UPDATE changed facts -> request_write()
4. RESOLVE closed loops -> resolve_open_loop()
5. RELEASE Pratibimba -> release_pratibimba()
```

---

## VidyaKosha Search

```python
oy.search("query", top_k=5)          # all sheets, importance-weighted
oy.search_open_loops("query")        # Anishtha only
oy.search_projects("query")          # Karma only
oy.search_people("query")            # Sambandha only
oy.take_pratibimba()                 # freeze snapshot
oy.release_pratibimba()              # release
```

---

## Write Rules

1. All writes via `request_write()` -- never open `.ods` directly
2. Dharma-Adesh -- User-stated overrides Agent-*
3. Append never delete -- Anishtha, Kartavya, Sambandha only grow
4. Set Source -- User-stated/observed vs Agent-inferred
5. Set Importance 1-10 -- affects retrieval weighting
6. ODS edits via LibreOffice -> `yantra sync` to import back
7. Never sort columns in LibreOffice -- Sort Catastrophe warning

---

## Controlled Vocabulary

| English | Sanskrit | Values |
|---|---|---|
| Project Status | Karma-Sthiti | `Active` / `Paused` / `Completed` / `Cancelled` |
| Task Status | Kartavya-Sthiti | `Pending` / `In Progress` / `Done` / `Blocked` |
| Resolved? | Nishpanna | `Yes` / `No` |
| Priority | Pradhanta | `Critical` / `High` / `Medium` / `Low` |
| Confidence | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| Source | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| Importance | Pradhanta-Ank | 1-10 |

---

## Key Files

```
openyantra.py         <- Core library (Chitragupta pattern)
yantra_sqlite.py      <- SyncEngine (v3.0 SQLite WAL + atomic ODS export)
yantra_morning.py     <- Morning Briefing
yantra_context.py     <- Copy Context (paste into any AI)
vidyakosha.py         <- Semantic index
yantra_ui.py          <- Browser dashboard
yantra_security.py    <- Raksha engine
install.sh            <- One-command Mac/Linux installer
visual-guide.html     <- Interactive architecture guide
openyantra-brand-manual.html <- Brand design system
```
