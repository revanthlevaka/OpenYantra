---
name: openyantra
description: >
  Implements OpenYantra v1.0 — The Sacred Memory Machine — a persistent,
  structured, human-readable memory system for agentic AI, inspired by
  Chitragupta (the Hindu God of Data). Uses open-standard .ods files and a
  Chitragupta/LedgerAgent single-writer pattern with a crash-safe
  Sanchitta/WriteQueue. Use this skill whenever the user wants an AI agent to
  remember things across sessions, when building agentic tools that need
  persistent user context, when setting up memory for OpenClaw / LangChain /
  AutoGen / CrewAI, when the user says "the AI keeps forgetting", "I have to
  repeat myself every session", "how do I give my agent memory", or "persist
  context across sessions". Also trigger when the user wants to bootstrap a new
  Chitrapat (memory file), flush Anishtha (open loops) before compaction,
  handle multi-agent Vivada (write conflicts), view the Agrasandhanī (audit
  ledger), or generate a Dinacharya (session summary). Use proactively any time
  persistent transparent user context would improve agent quality.
---

# OpenYantra — The Sacred Memory Machine

> *Inspired by Chitragupta, the Hindu God of Data*  
> *यन्त्र — a sacred diagram and a working instrument, simultaneously*

A vendor-neutral memory protocol storing a structured mind map of the user in a
`.ods` file (ISO/IEC 26300 — free on all platforms, forever). Any agent reads.
Only **Chitragupta (LedgerAgent)** writes. Every write is sealed with a
**Mudra** (SHA-256) and permanently recorded in the **Agrasandhanī** (audit
ledger). The user opens the **Chitrapat** (memory file) in LibreOffice at any
time and may issue a **Dharma-Adesh** (user override) on any cell.

---

## Sanskrit ↔ English Quick Reference

| Sanskrit | English | What it is |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer — the trusted recorder |
| Agrasandhanī | Ledger | Immutable audit trail sheet |
| Chitrapat | Memory file | `chitrapat.ods` |
| Karma-Lekha | WriteRequest | Write request to LedgerAgent |
| Sanchitta | WriteQueue | Crash-safe queue (`sanchitta.json`) |
| Smarana | Session Load | Load context at session start |
| Anishtha | Open Loops | Unresolved threads |
| Mudra | Signature | SHA-256 seal on every write |
| Vivada | Conflict | Escalated to user |
| Dharma-Adesh | User Override | User edits always win |

---

## Quick Start — The Chitragupta Puja

```python
from openyantra import OpenYantra, WriteRequest

# Bootstrap — the Chitragupta Puja (consecrating the memory)
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Smarana — load context into system prompt
print(oy.build_system_prompt_block())

# All writes route through Chitragupta (LedgerAgent) automatically
oy.add_project("My Feature Film", domain="Creative", status="Active",
               priority="High", next_step="Finish screenplay act 2")

# Anishtha — flush open loops before compaction
oy.flush_open_loop(
    topic="3-act vs 5-act structure",
    context="Deciding screenplay structure — undecided",
    priority="High",
    related_project="My Feature Film"
)

# Dinacharya — session summary at end
oy.log_session(
    topics=["screenplay", "OpenYantra setup"],
    decisions=["Use 3-act structure"],
    open_loops_created=1
)
```

---

## The Chitragupta / LedgerAgent Pattern

**Problem:** Multiple agents (OpenClaw, AutoGen, Claude) write simultaneously.
Schema drifts. Memory corrupts. No audit trail.

**Solution:** Only Chitragupta (LedgerAgent) writes. Others read-only.

```
    chitrapat.ods — READ by any agent (Smarana)
             ↑
    Chitragupta (LedgerAgent) — sole writer
      validates · seals with Mudra · records in Agrasandhanī
             ↑
    Karma-Lekha (WriteRequest) from any agent
    Claude · AutoGen · OpenClaw · CrewAI
             ↑
          User — Dharma-Adesh overrides all
```

**Sanchitta (WriteQueue):** every Karma-Lekha is written to `sanchitta.json`
on disk before commit. Crash → queue survives → auto-replays on next init.

---

## Sheet Schema — 12 Sheets

| Sheet | Sanskrit | English | Load timing |
|---|---|---|---|
| `👤 Identity` | Svarupa | Identity | Every session start |
| `🎯 Goals` | Sankalpa | Goals | Session start |
| `🚀 Projects` | Karma | Projects | Session start |
| `👥 People` | Sambandha | People | On person mention |
| `💡 Preferences` | Ruchi | Preferences | Before recommendations |
| `🧠 Beliefs` | Vishwas | Beliefs | Before advice |
| `✅ Tasks` | Kartavya | Tasks | Session start |
| `🔓 Open Loops` | Anishtha | Open Loops | **Session start — critical** |
| `📅 Session Log` | Dinacharya | Session Log | On-demand |
| `⚙️ Agent Config` | Niyama | Agent Config | Session start |
| `🗂 INDEX` | Soochi | Index | On-demand |
| `📒 Agrasandhanī` | Agrasandhanī | Ledger | Read-only audit |

### Universal columns — every sheet

- `Confidence` / Nishchaya — `High` / `Medium` / `Low` / `Inferred`
- `Source` / Strot — `User-stated` / `Agent-observed` / `Agent-inferred` / `System`
- `Last Updated` / Samay — ISO 8601 timestamp

**Chitra vs Gupta:** `User-stated` and `Agent-observed` are Chitra (explicit, higher trust). `Agent-inferred` is Gupta (hidden inference, lower trust). In Vivada, Chitra beats Gupta.

---

## Smarana — Session Load Sequence (MANDATORY)

```
1. LOAD  👤 Svarupa (Identity)       → system prompt
2. LOAD  ⚙️ Niyama (Agent Config)    → filter Agent = this OR "ALL"
3. LOAD  🚀 Karma (Projects)         → filter Status = "Active"
4. LOAD  🔓 Anishtha (Open Loops)    → filter Resolved? = "No" ← critical
5. LOAD  🎯 Sankalpa (Goals)         → filter Status = "Active"
6. LOAD  ✅ Kartavya (Tasks)         → filter Status != "Done"
```

Load Sambandha, Ruchi, Vishwas on-demand only.

### System Prompt Block
```
[OPENYANTRA CONTEXT — v1.0 | Chitragupta-secured]
User: {Svarupa.PreferredName} | {Svarupa.Occupation} | {Svarupa.Location}
Active Projects (Karma): {Karma[Active].Project} → {Karma.NextStep}
Open Loops (Anishtha): {Anishtha[Unresolved].Topic} — {Anishtha.Context}
Goals (Sankalpa): {Sankalpa[Active].Goal}
Tasks (Kartavya): {Kartavya[Pending].Task}
Instructions (Niyama): {Niyama[this OR ALL].Instruction}
[/OPENYANTRA CONTEXT]
```

---

## Session End Sequence (MANDATORY)

```
1. FLUSH  Anishtha (open loops)    → Karma-Lekha to Chitragupta
2. WRITE  Dinacharya (session log) → Karma-Lekha to Chitragupta
3. UPDATE changed facts            → Karma-Lekha to relevant sheets
4. RESOLVE closed Anishtha        → Resolved? = "Yes"
```

### What counts as Anishtha (Open Loop)
- Unresolved decisions (no conclusion reached)
- Mid-task threads (started, not finished)
- Promises made ("I'll help with X next session")
- New facts about user not yet in any sheet

---

## Write Rules

1. **All writes via `request_write()`** — never access chitrapat.ods directly
2. **Dharma-Adesh is inviolable** — User-stated data overrides all agents
3. **Append, never delete** — Sambandha, Kartavya, Anishtha only grow
4. **Mark Source** — Chitra vs Gupta matters
5. **Use controlled vocabulary** — Chitragupta rejects invalid values

### Vivada (Conflict) priority order
1. `User-stated` (Chitra) beats `Agent-*` (Gupta) — Dharma-Adesh
2. Higher Nishchaya (Confidence) beats lower
3. Newer Samay (Last Updated) beats older
4. If all equal → Vivada escalated to user

---

## Controlled Vocabulary

| English | Sanskrit | Values |
|---|---|---|
| Project Status | Karma-Sthiti | `Active` / `Paused` / `Completed` / `Cancelled` |
| Task Status | Kartavya-Sthiti | `Pending` / `In Progress` / `Done` / `Blocked` |
| Goal Status | Sankalpa-Sthiti | `Active` / `In Progress` / `Achieved` / `Abandoned` |
| Resolved? | Nishpanna | `Yes` / `No` |
| Priority | Pradhanta | `Critical` / `High` / `Medium` / `Low` |
| Confidence | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| Source | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |

---

## Regional Profiles

| Profile | Region | Law |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India | DPDP Act 2023 |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act |
| **OpenYantra-US** 🇺🇸 | USA | CCPA/CPRA, HIPAA |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL |

---

## File Layout

```
openyantra/
├── SKILL.md               ← this file
├── PROTOCOL.md            ← full spec v1.0 (CC0)
├── MYTHOLOGY.md           ← Chitragupta origin + Sanskrit naming
├── PRIVACY.md             ← four regional profiles
├── docs/DEPLOYMENT.md     ← implementation guide (OpenClaw + others)
├── openyantra.py          ← Lekhani — core library (MIT)
├── openclaw/
│   ├── plugin.py
│   └── hooks.py
├── examples/
│   ├── bootstrap.py       ← Chitragupta Puja quickstart
│   └── langchain_adapter.py
└── chitrapat_template.ods ← blank Chitrapat
```

For full multi-agent architecture, Vivada resolution, archival rotation, and
all four regional profiles: read `PROTOCOL.md`.  
For the Chitragupta origin, BDI mapping, Zeigarnik Effect, and Sanskrit naming:
read `MYTHOLOGY.md`.  
For OpenClaw, LangChain, AutoGen deployment: read `docs/DEPLOYMENT.md`.
