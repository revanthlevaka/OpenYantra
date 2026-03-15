# OpenYantra Protocol Specification — v2.3

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*
> — Brahma to Chitragupta

> **OpenYantra** — The Sacred Memory Machine
> Protocol License: CC0 1.0 Universal (Public Domain)

---

## Changelog

| Version | Key additions |
|---|---|
| v1.0 | Core protocol — Chitragupta pattern, Agrasandhanī, Anishtha, Sanchitta |
| v2.0 | VidyaKosha sidecar semantic index, Pratibimba snapshots |
| v2.1 | Inbox sheet, Importance column, TTL, Admission rules, Belief diffing, Corrections sheet |
| v2.3 | Packaging — complete repo, PROTOCOL.md, SKILL.md, DEPLOYMENT.md restored |

---

## Quick Terminology Reference

| Sanskrit | English | Component |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer |
| Agrasandhanī | Ledger | Immutable audit trail sheet |
| Chitrapat | Memory file | `chitrapat.ods` |
| Karma-Lekha | WriteRequest | Write to Chitragupta |
| Sanchitta | WriteQueue | `sanchitta.json` crash queue |
| Smarana | Session Load | Load context at session start |
| Anishtha | Open Loops | Unresolved threads |
| Mudra | Signature | SHA-256 seal |
| Vivada | Conflict | Escalated to user |
| Dharma-Adesh | User Override | User always wins |
| VidyaKosha | Sidecar Index | Semantic search |
| Pratibimba | Snapshot | Per-agent frozen index |
| Avagraha | Inbox | Quick capture sheet (v2.1) |
| Sanshodhan | Corrections | Pending edits sheet (v2.1) |

---

## 1. File Format

OpenYantra uses **OpenDocument Spreadsheet (`.ods`)** — ISO/IEC 26300.

Free on: Linux (LibreOffice), macOS (LibreOffice), Windows (LibreOffice), Android (Collabora), iOS (Collabora).

### Directory structure

```
~/openyantra/
├── chitrapat.ods         ← active memory (Chitrapat)
├── sanchitta.json        ← pending write queue (Sanchitta)
├── vidyakosha.faiss      ← vector index (VidyaKosha)
├── vidyakosha_bm25.pkl   ← keyword index
├── vidyakosha_registry.json
└── pratibimba/           ← per-agent snapshots
```

---

## 2. Schema — 14 Sheets (v2.3)

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
| `📥 Inbox` | Avagraha | Inbox | Chitragupta-write, user-override |
| `✏️ Corrections` | Sanshodhan | Corrections | Chitragupta-write, user-override |

### Universal columns — every sheet

| Column | Sanskrit | Values |
|---|---|---|
| `Confidence` | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| `Source` | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| `Last Updated` | Samay | ISO 8601 timestamp |
| `Importance` | Pradhanta-Ank | 1–10 integer (v2.1) |

---

## 3. The Chitragupta Pattern

Only Chitragupta (LedgerAgent) writes. All other agents read.

```
chitrapat.ods — READ (any agent, Smarana)
        ↑
Chitragupta (LedgerAgent) — sole writer
  admission gate → validate → seal Mudra → commit → audit → sync VidyaKosha
        ↑
Karma-Lekha (WriteRequest) from any agent
        ↑
User — Dharma-Adesh overrides all
```

### Admission Rules (v2.1)

Before committing, Chitragupta filters:
- Noise patterns ("user said thanks", "acknowledged", etc.)
- Importance < 2
- Insufficient content (< 3 characters of meaningful data)
- System-always-admitted sheets: Session Log, Ledger, Inbox

---

## 4. VidyaKosha — Semantic Search

Sidecar index auto-synced on every Chitragupta commit.

**Hybrid retrieval:**
```
score = α × vector_score + (1-α) × bm25_score
```
Default α = 0.7.

**Embedder stack (progressive):**
- TF-IDF + SVD (zero deps, auto-sized) — default
- sentence-transformers/all-MiniLM-L6-v2 — when installed

**API:**
```python
oy.search(query, top_k=5)
oy.search_open_loops(query)
oy.search_projects(query)
oy.search_people(query)
oy.take_pratibimba()      # freeze snapshot at session start
oy.release_pratibimba()   # release at session end
```

---

## 5. Inbox — Quick Capture (v2.1)

The `📥 Inbox` sheet accepts any content without forced categorisation.

```python
oy.inbox("Priya mentioned budget needs revision by Friday")
oy.inbox("I want to learn Rust this year")
```

Chitragupta routes items via keyword heuristics. Low-confidence routing marked for user review in browser dashboard.

CLI: `yantra inbox "text"`

---

## 6. Smarana — Session Load Sequence

```
1. LOAD  👤 Svarupa (Identity)
2. LOAD  ⚙️ Niyama (Agent Config)     → filter Agent = this OR "ALL"
3. LOAD  🚀 Karma (Projects)          → Status = "Active"
4. LOAD  🔓 Anishtha (Open Loops)     → Resolved? = "No", sorted by Importance × recency, max 15
5. LOAD  🎯 Sankalpa (Goals)          → Status = "Active"
6. LOAD  ✅ Kartavya (Tasks)          → Status != "Done"
7. CHECK 📥 Inbox                     → count unrouted
8. CHECK ✏️ Corrections               → count pending
9. (v2.1) take_pratibimba()           → if snapshot_mode = per-session
```

### System Prompt Block (v2.3)

```
[OPENYANTRA CONTEXT — v2.3 | Chitragupta-secured]
User: {Name} | {Occupation} | {Location}
Active Projects (Karma): {Project} → {NextStep}
Open Loops (Anishtha, top 15): [{Priority}] {Topic} — {Context}
Goals (Sankalpa): {Goal}
Tasks (Kartavya): {Task}
Alerts: 📥 {N} unrouted · ✏️ {N} corrections pending
Agent Instructions (Niyama): {Instruction}
[/OPENYANTRA CONTEXT]
```

---

## 7. Session End Sequence

```
1. FLUSH  Anishtha (open loops)    → Karma-Lekha
2. WRITE  Dinacharya (session log) → Karma-Lekha
3. UPDATE changed facts            → Karma-Lekha
4. RESOLVE closed Anishtha        → Resolved? = "Yes"
5. RELEASE Pratibimba             → oy.release_pratibimba()
```

---

## 8. Belief Diffing (v2.1)

Monthly contradiction detection:

```python
contradictions = oy.diff_beliefs()
# Returns: [{type, topic, positions, dates, message}]
```

Flags same-topic beliefs with different positions. Surfaced at session start or via `yantra diff`.

---

## 9. Open Loop TTL (v2.1)

Each loop carries `TTL_Days` (default 90). Expired loops surfaced via:

```python
expired = oy.check_anishtha_ttl(default_ttl_days=90)
# Returns: [{topic, age_days, ttl_days, message}]
```

CLI: `yantra ttl`

---

## 10. Corrections Flow (v2.1)

```
Agent calls propose_correction()
        ↓
Written to ✏️ Corrections sheet (Status: Pending)
        ↓
User reviews in browser dashboard (yantra ui)
        ↓
User approves → apply_corrections() commits to target sheet
User rejects  → Status = "Rejected"
```

---

## 11. Vivada — Conflict Resolution

Priority order:
1. `User-stated` (Chitra) beats `Agent-*` (Gupta) — Dharma-Adesh
2. Higher Importance beats lower
3. Newer Last Updated beats older
4. If all equal → escalate to user

---

## 12. Controlled Vocabulary

| English | Sanskrit | Values |
|---|---|---|
| Project Status | Karma-Sthiti | `Active` / `Paused` / `Completed` / `Cancelled` |
| Task Status | Kartavya-Sthiti | `Pending` / `In Progress` / `Done` / `Blocked` |
| Goal Status | Sankalpa-Sthiti | `Active` / `In Progress` / `Achieved` / `Abandoned` |
| Resolved? | Nishpanna | `Yes` / `No` |
| Priority | Pradhanta | `Critical` / `High` / `Medium` / `Low` |
| Confidence | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| Source | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| Importance | Pradhanta-Ank | 1–10 |

---

## 13. Archival

| Sheet | Retention | Archive |
|---|---|---|
| Session Log | 90 days active | `chitrapat_YYYY_sessions.ods` |
| Tasks Done | 30 days | `chitrapat_YYYY_tasks.ods` |
| Anishtha Resolved | 14 days | `chitrapat_YYYY_loops.ods` |

---

## 14. Regional Profiles

| Profile | Law | Key additions |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | DPDP Act 2023 | `Consent_Flag`, `Localisation_Tag` |
| **OpenYantra-EU** 🇪🇺 | GDPR, EU AI Act | `Data_Classification`, `Retention_Policy` |
| **OpenYantra-US** 🇺🇸 | CCPA, HIPAA | `Sensitivity_Tag`, `PHI_Flag` |
| **OpenYantra-CN** 🇨🇳 | PIPL, DSL | `Owner_Role`, `Domain_Tag` |

---

## 15. Agent Implementation Checklist v2.3

- [ ] All writes via `request_write()` — no direct file access
- [ ] Smarana at session start
- [ ] Chitragupta Context Block in system prompt
- [ ] Anishtha flush before compaction
- [ ] Dinacharya at session end
- [ ] Pratibimba taken/released if per-session mode
- [ ] VidyaKosha `search()` for semantic retrieval
- [ ] `inbox()` for quick captures
- [ ] Check corrections pending at session start
- [ ] Belief diff run monthly

---

## 16. License

Protocol: **CC0 1.0 Universal** (Public Domain)  
*The record exists to serve the remembered, not the recorder.*
