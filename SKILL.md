---
name: openyantra
description: >
  Implements OpenYantra v2.0 — The Sacred Memory Machine — persistent,
  structured, human-readable memory for agentic AI, inspired by Chitragupta
  (the Hindu God of Data). Uses open-standard .ods files, Chitragupta/LedgerAgent
  single-writer pattern, and VidyaKosha hybrid semantic search. Use whenever
  the user wants an AI agent to remember things across sessions, when building
  agentic tools that need persistent context, when setting up memory for
  OpenClaw / LangChain / AutoGen / CrewAI, when the user says "the AI keeps
  forgetting", "I have to repeat myself", "how do I give my agent memory",
  or "persist context across sessions". Also trigger for semantic memory search,
  Anishtha (open loop) flushing before compaction, multi-agent Vivada (conflict)
  handling, Pratibimba (snapshot) management, or Agrasandhanī (audit) queries.
---

# OpenYantra v2.0 — The Sacred Memory Machine

> *Inspired by Chitragupta, the Hindu God of Data*

Memory protocol using `.ods` (ISO open standard — free on all platforms).
Only **Chitragupta (LedgerAgent)** writes. Any agent reads.
**VidyaKosha** (v2.0) adds hybrid semantic + keyword search.

---

## Sanskrit ↔ English Reference

| Sanskrit | English | What it is |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer |
| Agrasandhanī | Ledger | Audit trail sheet |
| Chitrapat | Memory file | `chitrapat.ods` |
| Karma-Lekha | WriteRequest | Write to Chitragupta |
| Sanchitta | WriteQueue | `sanchitta.json` crash queue |
| Smarana | Session Load | Load at session start |
| Anishtha | Open Loops | Unresolved threads |
| Mudra | Signature | SHA-256 seal |
| Vivada | Conflict | Escalated to user |
| Dharma-Adesh | User Override | User always wins |
| VidyaKosha | Sidecar Index | Semantic search (v2.0) |
| Pratibimba | Snapshot | Frozen index per agent (v2.0) |

---

## Quick Start

```python
from openyantra import OpenYantra

# Chitragupta Puja — bootstrap
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Smarana — inject context into system prompt
print(oy.build_system_prompt_block())

# Writes via Chitragupta
oy.add_project("My Feature Film", domain="Creative", status="Active",
               priority="High", next_step="Finish act 2")
oy.flush_open_loop("3-act vs 5-act", "Undecided on structure", "High")
oy.log_session(topics=["screenplay"], decisions=["Use 3-act"])

# v2.0 — VidyaKosha semantic search
results = oy.search("screenplay structure decisions")
for r in results:
    print(r["sheet"], r["primary_value"], f"score={r['score']:.3f}")
```

---

## VidyaKosha — Semantic Search (v2.0)

Finds memory rows by meaning, not just exact keywords.
Requires `vidyakosha.py` in same directory.

```python
# Search all sheets
oy.search("screenplay structure film")

# Scoped searches
oy.search_open_loops("unresolved decisions")
oy.search_projects("creative work active")
oy.search_people("producer collaborator")

# Multi-agent snapshot (Pratibimba)
oy.take_pratibimba()                          # freeze at session start
oy.search("query", snapshot_mode="per-session")  # reads frozen snapshot
oy.release_pratibimba()                       # release at session end
```

**Embedder upgrade:**
```bash
pip install sentence-transformers  # auto-detected, better quality
```

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

Universal columns on every sheet: `Confidence` · `Source` · `Last Updated`

---

## Smarana — Session Load Sequence

```
1. LOAD  👤 Svarupa (Identity)       → system prompt
2. LOAD  ⚙️ Niyama (Agent Config)    → filter Agent = this OR "ALL"
3. LOAD  🚀 Karma (Projects)         → Status = "Active"
4. LOAD  🔓 Anishtha (Open Loops)    → Resolved? = "No" ← critical
5. LOAD  🎯 Sankalpa (Goals)         → Status = "Active"
6. LOAD  ✅ Kartavya (Tasks)         → Status != "Done"
7. (v2.0) take_pratibimba()          → if snapshot_mode = per-session
```

### System Prompt Block
```
[OPENYANTRA CONTEXT — v2.0 | Chitragupta-secured]
User: {Svarupa.PreferredName} | {Svarupa.Occupation} | {Svarupa.Location}
Active Projects (Karma): {Karma[Active].Project} → {Karma.NextStep}
Open Loops (Anishtha): {Anishtha[Unresolved].Topic} — {Anishtha.Context}
Goals (Sankalpa): {Sankalpa[Active].Goal}
Tasks (Kartavya): {Kartavya[Pending].Task}
Instructions (Niyama): {Niyama[this OR ALL].Instruction}
[/OPENYANTRA CONTEXT]
```

---

## Session End Sequence

```
1. FLUSH  Anishtha (open loops)    → Karma-Lekha
2. WRITE  Dinacharya (session log) → Karma-Lekha
3. UPDATE changed facts            → Karma-Lekha
4. RESOLVE closed Anishtha        → Resolved? = "Yes"
5. (v2.0) release_pratibimba()    → release snapshot
```

---

## Write Rules

1. All writes via `request_write()` — never open chitrapat.ods directly
2. Dharma-Adesh inviolable — User-stated overrides Agent-*
3. Append, never delete — Anishtha, Kartavya, Sambandha only grow
4. Mark Source: Chitra (User-stated/observed) vs Gupta (Agent-inferred)
5. Controlled vocabulary — Chitragupta rejects invalid values

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
├── PROTOCOL.md            ← full spec v2.0 (CC0)
├── MYTHOLOGY.md           ← Chitragupta origin
├── PRIVACY.md             ← four regional profiles
├── openyantra.py          ← core library v2.0
├── vidyakosha.py          ← semantic index v2.0
├── docs/DEPLOYMENT.md     ← framework integration guide
└── chitrapat_template.ods ← blank Chitrapat
```
