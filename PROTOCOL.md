# OpenYantra Protocol Specification — v1.0

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*  
> — Brahma to Chitragupta

> **OpenYantra** — The Sacred Memory Machine  
> Inspired by Chitragupta (चित्रगुप्त), the Hindu God of Data  
> Protocol License: CC0 1.0 Universal (Public Domain)

---

## Overview

OpenYantra is an open protocol defining how AI agents read, write, and maintain a structured mind map of a user — called the **Chitrapat** (life scroll) — across sessions, platforms, and model resets.

The protocol has one foundational rule: **only Chitragupta (LedgerAgent) writes**. All other agents read. Every write is sealed with a Mudra (SHA-256 signature) and permanently recorded in the Agrasandhanī (audit ledger). User edits — the Dharma-Adesh (righteous command) — always override agent writes.

See [MYTHOLOGY.md](MYTHOLOGY.md) for the complete origin story.

---

## Quick Terminology Reference

Every OpenYantra term has both a Sanskrit name (for cultural depth) and an English name (for universal understanding). Both are always valid.

| Sanskrit | English | Meaning |
|---|---|---|
| Chitragupta | LedgerAgent | Sole writer — the trusted recorder |
| Agrasandhanī | Ledger sheet | Immutable audit trail |
| Chitrapat | Memory file | `chitrapat.ods` — the life scroll |
| Karma-Lekha | WriteRequest | A write submitted to LedgerAgent |
| Sanchitta | WriteQueue | Crash-safe write queue (`sanchitta.json`) |
| Smarana | Session Load | Calling forth the record at session start |
| Anishtha | Open Loops | Unresolved threads — compaction safety net |
| Mudra | Signature | SHA-256 seal on every write |
| Vivada | Conflict | Dispute escalated to user |
| Dharma-Adesh | User Override | User edits always win |
| Lekhani | The Library | `openyantra.py` — the writing instrument |
| Yamapuri | Memory Directory | `~/openyantra/` |

---

## 1. File Format

OpenYantra uses **OpenDocument Spreadsheet (`.ods`)** — ISO/IEC 26300 open standard. Not Excel. Not any proprietary format.

| Platform | Free Application |
|---|---|
| Linux | LibreOffice Calc (native) |
| macOS | LibreOffice Calc |
| Windows | LibreOffice Calc |
| Android | Collabora Office |
| iOS | Collabora Office |

**Rationale:** A memory standard claiming to give users ownership of their data cannot be tied to a paid proprietary format. `.ods` is ISO-certified, royalty-free, and readable by every major spreadsheet application on every platform.

### Directory structure (Yamapuri)

```
~/openyantra/             ← Yamapuri (domain of records)
├── chitrapat.ods         ← The Chitrapat (active life scroll)
├── sanchitta.json        ← Sanchitta (accumulated pending karma / write queue)
├── chitrapat.YYYY-MM-DD.ods  ← Daily snapshot backup
└── archive/
    ├── chitrapat_YYYY_sessions.ods
    ├── chitrapat_YYYY_tasks.ods
    └── chitrapat_YYYY_loops.ods
```

---

## 2. Schema — The 12 Sheets

Sheet names are standardised. Agents MUST use exact canonical names.

| Sheet | Sanskrit | English | Domain | Mutability |
|---|---|---|---|---|
| `🗂 INDEX` | Soochi | Index | Schema overview | Read-only |
| `👤 Identity` | Svarupa | Identity | Who the user is | LedgerAgent-write, user-override |
| `🎯 Goals` | Sankalpa | Goals | Long/short-term aims | LedgerAgent-write, user-override |
| `🚀 Projects` | Karma | Projects | Active work | LedgerAgent-write, user-override |
| `👥 People` | Sambandha | People | Relationships | LedgerAgent-write, user-override |
| `💡 Preferences` | Ruchi | Preferences | Taste, style, habits | LedgerAgent-write, user-override |
| `🧠 Beliefs` | Vishwas | Beliefs | Values and worldview | LedgerAgent-write, user-override |
| `✅ Tasks` | Kartavya | Tasks | Action items | LedgerAgent-write, user-override |
| `🔓 Open Loops` | Anishtha | Open Loops | Unresolved threads | LedgerAgent-write, user-override |
| `📅 Session Log` | Dinacharya | Session Log | Per-session summaries | LedgerAgent-write only |
| `⚙️ Agent Config` | Niyama | Agent Config | Per-agent instructions | User-write, agent-read |
| `📒 Agrasandhanī` | Agrasandhanī | Ledger | Immutable audit trail | LedgerAgent-append only |

### Universal Columns — every sheet

| Column | Sanskrit | English | Values |
|---|---|---|---|
| `Confidence` | Nishchaya | Confidence | `High` / `Medium` / `Low` / `Inferred` |
| `Source` | Strot | Source (Chitra or Gupta) | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| `Last Updated` | Samay | Last Updated | ISO 8601 `YYYY-MM-DDTHH:MM:SS` |

**The Chitra/Gupta Source distinction:**  
`User-stated` and `Agent-observed` are Chitra sources (explicit, visible, higher trust).  
`Agent-inferred` is a Gupta source (hidden, inferred, lower trust).  
In Vivada (conflict), Chitra always beats Gupta.

---

## 3. The Chitragupta Pattern — Single Trusted Writer

### The Single Writer Principle

Only **Chitragupta (LedgerAgent)** may write to the Chitrapat. All other agents are read-only. They submit **Karma-Lekha (WriteRequest)** objects.

```
             chitrapat.ods (Chitrapat)
          ┌──────────────────────────┐
          │  Smarana — READ any agent │
          └──────────┬───────────────┘
                     │ WRITE (exclusive)
          ┌──────────▼───────────────┐
          │     Chitragupta          │
          │     (LedgerAgent)        │  ← sole writer
          │                          │  ← validates Karma-Lekha
          │                          │  ← seals with Mudra (SHA-256)
          │                          │  ← records in Agrasandhanī
          └──────────▲───────────────┘
                     │ Karma-Lekha (WriteRequest)
       ┌─────────────┼─────────────┐
       │             │             │
    Claude        AutoGen      OpenClaw
   (read-only)  (read-only) (read-only)
                     │
                   User
           (Dharma-Adesh — overrides all)
```

### Karma-Lekha (WriteRequest) structure

```python
WriteRequest(
    requesting_agent = "Claude",         # who is requesting
    sheet            = "🚀 Projects",    # canonical sheet name
    operation        = "add",            # add / update / resolve / archive
    fields           = {
        "Project":   "My Film",
        "Status":    "Active",
        "Next Step": "Write screenplay",
    },
    row_identifier   = None,             # for update/resolve: primary key
    confidence       = "High",           # Nishchaya
    source           = "User-stated",    # Chitra or Gupta
    session_id       = "2025-03-15",
)
```

### Chitragupta receipt — the Mudra

```python
# Written — sealed with Mudra
{"status": "written", "signature": "sha256:613fcea53c09...", "timestamp": "..."}

# Vivada — conflict escalated to user
{"status": "conflict", "existing_value": "X", "requested_value": "Y",
 "resolution": "pending_user"}

# Rejected — invalid Karma-Lekha
{"status": "rejected", "reason": "Invalid Status 'In Review'"}
```

---

## 4. The Agrasandhanī — Immutable Audit Trail

The `📒 Agrasandhanī` records every write committed to the Chitrapat. No agent may write to it via WriteRequest — only Chitragupta appends to it internally.

| Column | Sanskrit | English | Description |
|---|---|---|---|
| `Timestamp` | Samay | Timestamp | UTC ISO 8601 |
| `Request ID` | Karma-ID | Request ID | SHA-256 derived unique ID |
| `Agent` | Doot | Agent | Requesting agent name |
| `Sheet` | Patra | Sheet | Target sheet |
| `Operation` | Kriya | Operation | add / update / resolve / archive |
| `Row Identifier` | Sutra | Row ID | Primary key of affected row |
| `Status` | Sthiti | Status | written / rejected / conflict |
| `Confidence` | Nishchaya | Confidence | Confidence level |
| `Source` | Strot | Source | Chitra or Gupta provenance |
| `Signature` | Mudra | Signature | `sha256:<32-char>` — the divine seal |
| `Reason / Notes` | Karan | Notes | Rejection reason or conflict detail |

---

## 5. Sanchitta — Crash-Safe WriteQueue

The **Sanchitta** (write queue) is stored as `sanchitta.json` alongside the Chitrapat. It ensures no Karma-Lekha is lost if the process crashes mid-commit.

```
Agent submits Karma-Lekha
        ↓
Sanchitta.enqueue()     ← persisted to disk immediately
        ↓
Chitragupta commits     ← validates + signs + writes
        ↓
Sanchitta entry cleared ← only after successful commit
```

On next `OpenYantra()` init, `replay_sanchitta()` runs automatically. Any pending Karma-Lekha from the previous crashed session are replayed before the new session begins.

---

## 6. Smarana — Session Load Sequence

Every agent MUST execute Smarana (remembrance) at session start:

```
1. LOAD  👤 Svarupa (Identity)        → system prompt user context
2. LOAD  ⚙️ Niyama (Agent Config)     → filter Agent = this OR "ALL"
3. LOAD  🚀 Karma (Projects)          → filter Status = "Active"
4. LOAD  🔓 Anishtha (Open Loops)     → filter Resolved? = "No" ← most critical
5. LOAD  🎯 Sankalpa (Goals)          → filter Status = "Active"
6. LOAD  ✅ Kartavya (Tasks)          → filter Status != "Done"
```

Load Sambandha (People), Ruchi (Preferences), Vishwas (Beliefs) **on-demand only**.

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

### On-demand loading triggers

| Trigger | Load |
|---|---|
| User mentions a person | Sambandha (People) |
| Agent about to recommend | Ruchi (Preferences) |
| Agent about to advise | Vishwas (Beliefs) |
| User references past goals | Sankalpa (Goals) — all rows |

---

## 7. Session End Sequence

```
1. FLUSH  Anishtha (open loops)    → Karma-Lekha to Chitragupta
2. WRITE  Dinacharya (session log) → Karma-Lekha to Chitragupta
3. UPDATE changed facts            → relevant sheets via Karma-Lekha
4. RESOLVE closed Anishtha        → Resolved? = "Yes"
```

### What to flush as Anishtha (Open Loops)

Before compaction or session end, scan the conversation for:
- Unresolved decisions (user weighing options, no conclusion)
- Mid-task threads (work started, not finished)
- Promises made ("I'll help you with X next session")
- New user facts not yet written to any sheet

The Anishtha sheet is the formal implementation of the **Zeigarnik Effect** (1927) — unfinished tasks occupy working memory more persistently than completed ones. Externalising them to Anishtha prevents context compaction from destroying them.

---

## 8. Write Rules

1. **All Karma-Lekha via `request_write()`** — never open the Chitrapat directly
2. **Dharma-Adesh is inviolable** — user-edited cells with higher Nishchaya cannot be overwritten
3. **Append, never delete** — Sambandha, Kartavya, Anishtha only gain rows
4. **Mark Source as Chitra or Gupta** — provenance determines trust
5. **Use controlled vocabulary** — Chitragupta rejects invalid values

---

## 9. Vivada — Conflict Resolution

When Chitragupta detects a Vivada (conflict):

```
1. DO NOT overwrite — Dharma-Adesh is inviolable
2. Return status: "conflict" with both values
3. Record in Agrasandhanī
4. Raise with user at next session:
   "I want to update [field] to [X], but you have [Y]. Which is correct?"
5. Write user's confirmed Dharma-Adesh via new Karma-Lekha
```

**Priority order (Vivada arbitration):**
1. `User-stated` (Chitra) beats all `Agent-*` (Gupta) — Dharma-Adesh
2. Higher `Confidence` (Nishchaya) beats lower
3. Newer `Last Updated` (Samay) beats older
4. If all equal → escalate to user (Vivada)

---

## 10. Archival — Sanchitta Rotation

| Sheet | Retention | Archive |
|---|---|---|
| Dinacharya (Session Log) | 90 days | `chitrapat_YYYY_sessions.ods` |
| Kartavya Done (Tasks) | 30 days | `chitrapat_YYYY_tasks.ods` |
| Anishtha Resolved (Open Loops) | 14 days | `chitrapat_YYYY_loops.ods` |

---

## 11. Controlled Vocabulary

| Field (English) | Field (Sanskrit) | Allowed Values |
|---|---|---|
| Project Status | Karma-Sthiti | `Active` / `Paused` / `Completed` / `Cancelled` |
| Task Status | Kartavya-Sthiti | `Pending` / `In Progress` / `Done` / `Blocked` |
| Goal Status | Sankalpa-Sthiti | `Active` / `In Progress` / `Achieved` / `Abandoned` |
| Resolved? | Nishpanna | `Yes` / `No` |
| Priority | Pradhanta | `Critical` / `High` / `Medium` / `Low` |
| Confidence | Nishchaya | `High` / `Medium` / `Low` / `Inferred` |
| Source | Strot | `User-stated` / `Agent-observed` / `Agent-inferred` / `System` |
| Strength | Bal | `Strong` / `Mild` / `Uncertain` |
| Sentiment | Bhavana | `Positive` / `Neutral` / `Negative` / `Complex` |

---

## 12. Regional Profiles

| Profile | Region | Primary Law | Key columns added |
|---|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India | DPDP Act 2023, IT Act 2000 | `Consent_Flag`, `Localisation_Tag` |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act | `Data_Classification`, `Retention_Policy`, `Legal_Basis` |
| **OpenYantra-US** 🇺🇸 | United States | CCPA/CPRA, HIPAA, COPPA | `Sensitivity_Tag`, `PHI_Flag`, `State_Jurisdiction` |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL | `Owner_Role`, `Domain_Tag`, `Cross_Border` |

See [PRIVACY.md](PRIVACY.md) for full specification per region.

---

## 13. Agent Implementation Checklist

- [ ] Uses `.ods` format — not `.xlsx`, not any proprietary format
- [ ] All writes via `request_write()` — no direct file access
- [ ] Executes Smarana (Session Load §6) at session start
- [ ] Injects Chitragupta Context Block into system prompt
- [ ] Flushes Anishtha before compaction (§7)
- [ ] Writes Dinacharya at session end (§7)
- [ ] Respects Vivada — Dharma-Adesh is inviolable (§9)
- [ ] Uses Chitra/Gupta Source distinction
- [ ] Handles bootstrap / Chitragupta Puja
- [ ] Respects archival rotation (§10)
- [ ] Regional profile applied if applicable (§12)

---

## 14. Versioning

**OpenYantra Protocol v1.0** — initial public release.

---

## 15. License

Protocol Specification: **CC0 1.0 Universal** (Public Domain)  
*The record exists to serve the remembered, not the recorder.*
