# OpenYantra Protocol Specification — v2.0

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*
> — Brahma to Chitragupta

> **OpenYantra** — The Sacred Memory Machine
> Inspired by Chitragupta (चित्रगुप्त), the Hindu God of Data
> Protocol License: CC0 1.0 Universal (Public Domain)

---

## What Changed in v2.0

| | v1.0 | v2.0 |
|---|---|---|
| **Semantic search** | Keyword/filter only | VidyaKosha hybrid BM25 + vector |
| **Multi-agent snapshots** | Not available | Pratibimba per-agent frozen index |
| **Index sync** | Manual | Auto-sync on every Chitragupta write |
| **Search API** | None | `search()`, `search_open_loops()`, `search_projects()`, `search_people()` |
| **Embedder** | N/A | TF-IDF (zero deps) → sentence-transformers (upgrade) |

All v1.0 features (Chitragupta pattern, Sanchitta, Agrasandhanī, regional profiles) are unchanged and fully backward-compatible.

---

## Quick Terminology Reference

| Sanskrit | English | Component |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer |
| Agrasandhanī | Ledger | Audit trail sheet |
| Chitrapat | Memory file | `chitrapat.ods` |
| Karma-Lekha | WriteRequest | Write to LedgerAgent |
| Sanchitta | WriteQueue | `sanchitta.json` |
| Smarana | Session Load | Load context at start |
| Anishtha | Open Loops | Unresolved threads |
| Mudra | Signature | SHA-256 seal |
| Vivada | Conflict | Escalated to user |
| Dharma-Adesh | User Override | User always wins |
| VidyaKosha | Sidecar Index | Semantic search engine |
| Pratibimba | Snapshot | Per-agent frozen index |

---

## 1. File Format

OpenYantra uses **OpenDocument Spreadsheet (`.ods`)** — ISO/IEC 26300.

| Platform | Free Application |
|---|---|
| Linux | LibreOffice Calc |
| macOS | LibreOffice Calc |
| Windows | LibreOffice Calc |
| Android | Collabora Office |
| iOS | Collabora Office |

---

## 2. Schema — 12 Sheets

| Sheet | Sanskrit | English | Mutability |
|---|---|---|---|
| `🗂 INDEX` | Soochi | Index | Read-only |
| `👤 Identity` | Svarupa | Identity | Chitragupta-write, user-override |
| `🎯 Goals` | Sankalpa | Goals | Chitragupta-write, user-override |
| `🚀 Projects` | Karma | Projects | Chitragupta-write, user-override |
| `👥 People` | Sambandha | People | Chitragupta-write, user-override |
| `💡 Preferences` | Ruchi | Preferences | Chitragupta-write, user-override |
| `🧠 Beliefs` | Vishwas | Beliefs | Chitragupta-write, user-override |
| `✅ Tasks` | Kartavya | Tasks | Chitragupta-write, user-override |
| `🔓 Open Loops` | Anishtha | Open Loops | Chitragupta-write, user-override |
| `📅 Session Log` | Dinacharya | Session Log | Chitragupta-write only |
| `⚙️ Agent Config` | Niyama | Agent Config | User-write, agent-read |
| `📒 Agrasandhanī` | Agrasandhanī | Ledger | Chitragupta-append only |

### Universal Columns (every sheet)

| Column | Sanskrit | Values |
|---|---|---|
| `Confidence` | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| `Source` | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| `Last Updated` | Samay | ISO 8601 timestamp |

---

## 3. The Chitragupta Pattern

Only Chitragupta (LedgerAgent) writes. All other agents read. Every write sealed with Mudra (SHA-256) and recorded in Agrasandhanī.

```
chitrapat.ods — READ by any agent (Smarana)
        ↑
Chitragupta (LedgerAgent)
  validates · seals · commits · syncs VidyaKosha · records
        ↑
Karma-Lekha (WriteRequest) from any agent
        ↑
User — Dharma-Adesh overrides all
```

---

## 4. VidyaKosha — Semantic Search (v2.0)

### What it is

VidyaKosha (विद्याकोश — Knowledge Repository) is a sidecar index that sits alongside the Chitrapat and enables agents to query memory by meaning, not just exact keywords.

```
chitrapat.ods  ←  source of truth (Chitragupta writes)
      │
      │ auto-sync on every commit
      ▼
VidyaKosha (vidyakosha.py)
├── vidyakosha.faiss          ← FAISS vector index
├── vidyakosha_bm25.pkl       ← BM25 keyword index
├── vidyakosha_registry.json  ← row metadata
└── pratibimba/               ← per-agent frozen snapshots
```

### Hybrid Retrieval

Every query runs both BM25 (keyword) and vector (semantic) search, then combines scores:

```
hybrid_score = alpha × vector_score + (1 - alpha) × bm25_score
```

Default `alpha = 0.7` (70% semantic, 30% keyword). Configurable per query.

### Embedder Backends

| Backend | Quality | Dependencies | Auto-selected when |
|---|---|---|---|
| TF-IDF + SVD | Good | scikit-learn (built-in) | sentence-transformers not installed |
| sentence-transformers/all-MiniLM-L6-v2 | Best | `pip install sentence-transformers` | Installed |

VidyaKosha auto-detects the best available backend. No configuration needed.

### Pratibimba — Per-Agent Snapshots

In multi-agent environments, each agent can take a frozen snapshot of the index at session start. Writes by other agents during the session don't affect in-progress queries.

```python
# Session start
oy.take_pratibimba()          # freeze index for this agent

# During session — queries read from frozen snapshot
results = oy.search("query", snapshot_mode="per-session")

# Session end
oy.release_pratibimba()       # release snapshot
```

Configure per-agent in `⚙️ Agent Config`:
- Instruction contains "per-session" → `snapshot_mode = "per-session"`
- Instruction contains "live" → `snapshot_mode = "live"` (default)

### Search API

```python
oy.search(query, top_k=5, sheets=None, snapshot_mode=None, hybrid_alpha=0.7)
oy.search_open_loops(query, top_k=5)
oy.search_projects(query, top_k=5)
oy.search_people(query, top_k=5)
```

Result dict per item:
```python
{
    "sheet":         "🚀 Projects",
    "primary_value": "Feature Screenplay",
    "text":          "[🚀 Projects] Project: Feature Screenplay ...",
    "score":         0.954,   # hybrid
    "vector_score":  0.932,
    "bm25_score":    1.000,
    "row":           {...}    # full row dict
}
```

---

## 5. Sanchitta — Crash-Safe WriteQueue

All Karma-Lekha written to `sanchitta.json` before commit. Auto-replayed on next init.

```
Agent submits Karma-Lekha
        ↓
Sanchitta.enqueue()     ← disk write immediately
        ↓
Chitragupta commits
        ↓
Sanchitta entry cleared ← only after successful commit
```

---

## 6. Smarana — Session Load Sequence

```
1. LOAD  👤 Svarupa (Identity)       → system prompt
2. LOAD  ⚙️ Niyama (Agent Config)    → filter Agent = this OR "ALL"
3. LOAD  🚀 Karma (Projects)         → filter Status = "Active"
4. LOAD  🔓 Anishtha (Open Loops)    → filter Resolved? = "No" ← critical
5. LOAD  🎯 Sankalpa (Goals)         → filter Status = "Active"
6. LOAD  ✅ Kartavya (Tasks)         → filter Status != "Done"
```

Load Sambandha, Ruchi, Vishwas on-demand only (triggered by conversation).

**v2.0 addition:** If VidyaKosha is available, call `take_pratibimba()` at session start when `snapshot_mode = "per-session"`.

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

## 7. Session End Sequence

```
1. FLUSH  Anishtha (open loops)    → Karma-Lekha to Chitragupta
2. WRITE  Dinacharya (session log) → Karma-Lekha to Chitragupta
3. UPDATE changed facts            → Karma-Lekha to relevant sheets
4. RESOLVE closed Anishtha        → Resolved? = "Yes"
5. RELEASE Pratibimba             → oy.release_pratibimba() (v2.0)
```

---

## 8. Write Rules

1. All writes via `request_write()` — no direct file access
2. Dharma-Adesh inviolable — User-stated data overrides all agents
3. Append, never delete — Sambandha, Kartavya, Anishtha only grow
4. Mark Source as Chitra (User-stated/Agent-observed) or Gupta (Agent-inferred)
5. Controlled vocabulary — Chitragupta rejects invalid values

---

## 9. Vivada — Conflict Resolution

```
1. DO NOT overwrite — Dharma-Adesh is inviolable
2. Return status: "conflict" with both values
3. Record in Agrasandhanī
4. Raise with user next session
5. Write confirmed Dharma-Adesh via new Karma-Lekha
```

Priority: User-stated > High confidence > Newer timestamp > Escalate

---

## 10. Controlled Vocabulary

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

## 11. Archival

| Sheet | Active retention | Archive |
|---|---|---|
| Dinacharya (Session Log) | 90 days | `chitrapat_YYYY_sessions.ods` |
| Kartavya Done | 30 days | `chitrapat_YYYY_tasks.ods` |
| Anishtha Resolved | 14 days | `chitrapat_YYYY_loops.ods` |

---

## 12. Regional Profiles

| Profile | Law | Key additions |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | DPDP Act 2023 | `Consent_Flag`, `Localisation_Tag` |
| **OpenYantra-EU** 🇪🇺 | GDPR, EU AI Act | `Data_Classification`, `Retention_Policy` |
| **OpenYantra-US** 🇺🇸 | CCPA, HIPAA | `Sensitivity_Tag`, `PHI_Flag` |
| **OpenYantra-CN** 🇨🇳 | PIPL, DSL | `Owner_Role`, `Domain_Tag`, 3-tier hierarchy |

See PRIVACY.md for full specifications.

---

## 13. Agent Implementation Checklist v2.0

- [ ] Uses `.ods` format
- [ ] All writes via `request_write()` — no direct file access
- [ ] Smarana at session start (§6)
- [ ] Chitragupta Context Block in system prompt
- [ ] Anishtha flush before compaction (§7)
- [ ] Dinacharya at session end (§7)
- [ ] Pratibimba taken/released if snapshot_mode=per-session (§4, v2.0)
- [ ] VidyaKosha `search()` used for semantic retrieval (§4, v2.0)
- [ ] Vivada resolution — Dharma-Adesh inviolable (§9)
- [ ] Regional profile applied (§12)

---

## 14. License

Protocol: **CC0 1.0 Universal** (Public Domain)
*The record exists to serve the remembered, not the recorder.*
