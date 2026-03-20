# OpenYantra Visual Guide v2.12

Architecture diagrams and system maps.

---

## Storage Architecture

```
chitrapat.ods  (ISO/IEC 26300 -- human-readable, always exists)
      ^
      | bidirectional sync
      v
chitrapat.db   (SQLite -- operational write path, v3.0)
```

**Rule:** Both files always exist alongside each other. Neither is optional.
The `.ods` file is the source of truth the human edits. SQLite is rebuilt from `.ods` on user edits via `yantra sync`. Agents write to SQLite; Chitragupta syncs to `.ods`.

---

## Chitragupta Write Flow

```
Any Agent
    |
    | WriteRequest (Karma-Lekha)
    v
Sanchitta (WriteQueue -- sanchitta.json)
    |
    | crash-safe enqueue
    v
Raksha Security Scan
    |-- CONFIRMED threat --> 🔒 Quarantine sheet + log
    |-- SUSPICIOUS -------> 🛡️ Security Log + allow with flag
    |-- CLEAN ------------> continue
    v
Chitragupta (LedgerAgent)
    |-- validate controlled vocabulary
    |-- check admission rules (filter noise)
    |-- detect Vivada (conflict)
    |       └-- conflict --> escalate to user (Dharma-Adesh)
    |-- seal with SHA-256 Mudra
    |-- commit to chitrapat.ods (+ SQLite in v3.0)
    |-- append to Agrasandhanī (immutable ledger)
    v
VidyaKosha incremental sync
    |-- update BM25 index
    |-- update TF-IDF / vector index
    v
Done -- receipt returned to agent
```

---

## The 14-Sheet Schema

```
chitrapat.ods
|
+-- 👤 Identity (Svarupa)          -- who you are
+-- 🎯 Goals (Sankalpa)            -- what you want
+-- 🚀 Projects (Karma)            -- active work + next step
+-- 👥 People (Sambandha)          -- relationships
+-- 💡 Preferences (Ruchi)         -- tools, habits, anti-goals
+-- 🧠 Beliefs (Vishwas)           -- values, worldview, evolution
+-- ✅ Tasks (Kartavya)            -- action items
+-- 🔓 Open Loops (Anishtha)       -- unresolved threads [CRITICAL]
+-- 📅 Session Log (Dinacharya)    -- per-session summaries
+-- ⚙️ Agent Config (Niyama)       -- per-agent instructions
+-- 📒 Agrasandhanī                -- immutable SHA-256 audit trail
+-- 📥 Inbox (Avagraha)            -- quick capture before routing
+-- ✏️ Corrections (Sanshodhan)    -- agent-proposed edits pending
+-- 🔒 Quarantine (Nirodh)         -- blocked injection attempts
```

Universal columns on every sheet: `Confidence`, `Source`, `Last Updated`, `Importance (1-10)`

---

## Anishtha (Open Loops) -- The Compaction Safety Net

```
Session active
    |
    | Agent working...
    |
Context approaching limit
    |
    v
PRE-COMPACTION (critical)
    |
    | oy.flush_open_loop(topic, context)  <-- all unresolved threads
    | oy.flush_open_loop(topic, context)
    | oy.flush_open_loop(topic, context)
    |
    v
Context compaction (LLM compresses old messages)
    |
    v
POST-COMPACTION
    |
    | oy.build_system_prompt_block()  <-- re-injects all loops from file
    |
    v
Session continues with no lost context
```

Implements the Zeigarnik Effect as a persistent data structure: incomplete tasks are externalised to the file before they can be compressed away.

---

## VidyaKosha Retrieval Scoring

```
final_score =
    (alpha * vector_score + (1-alpha) * bm25_score)
    * (1 + importance_weight * normalised_importance)
    * (1 + 0.1 * recency_factor)

where:
    alpha = 0.7 (default)
    normalised_importance = Importance / 10.0
    recency_factor = max(0.1, 1.0 - (age_days / 365))
```

Effect: at equal relevance, Importance=9 surfaces before Importance=3; recent records surface before older ones.

---

## Raksha Trust Tiers

```
Tier 5 -- User          -- Dharma-Adesh -- never blocked, always wins
Tier 4 -- Chitragupta   -- System agent -- full trust
Tier 3 -- Known Agent   -- Claude, OpenClaw, LangChain, AutoGen
Tier 2 -- Unknown Agent -- unregistered -- stricter scan
Tier 1 -- External      -- Telegram, iOS Shortcut -- suspicious = confirmed block
Tier 0 -- Untrusted     -- explicitly flagged -- any flag = block
```

---

## Oracle Cross-Reference Map (v2.12)

```
Inbox items  --+-- keyword overlap? --> open loops  [inbox_loop_match]
               |
Tasks ---------+-- same project as High loop? -----  [task_loop_block]
               |
Beliefs -------+-- same topic, diff positions? -----  [belief_conflict]
               |
Projects ------+-- Active, no session mention 14d? -  [stale_project]
               |
Inbox items ---+-- capitalised name, no People row? - [person_missing]
               |
Open Loops ----+-- past 50% TTL, not in sessions? --  [loop_aging]
               |
Tasks ---------+-- linked to Completed/Cancelled? --  [orphan_task]
```

Oracle is read-only. It never writes. It surfaces; the human decides.

---

## Session Start Sequence (Smarana)

```
1. Read Identity sheet --> name, occupation, location, timezone
2. Read Agent Config   --> filter Agent = this OR "ALL", Active = "Yes"
3. Read Projects       --> Status = "Active"
4. Read Open Loops     --> Resolved? = "No"
                          sort by: -(Importance * recency_factor)
                          take: top 15
5. Read Goals          --> Status in ("Active", "In Progress")
6. Read Tasks          --> Status not in ("Done", None)
7. Count Inbox         --> Routed? = "No"
8. Count Corrections   --> Status = "Pending"
9. take_pratibimba()   --> if Agent Config says per-session mode
```

---

## System Prompt Block Structure

```
[OPENYANTRA CONTEXT -- v2.12 | Chitragupta-secured]
User: {Preferred Name} | {Occupation} | {Location}
Active Projects (Karma): {Project} -> {Next Step} ({Priority})
Open Loops (Anishtha, top 15): [{Priority}] {Topic} -- {Context}
Goals (Sankalpa): {Goal}
Tasks (Kartavya): {Task}
Alerts: 📥 {N} unrouted · ✏️ {N} corrections pending
Agent Instructions (Niyama): {Instruction}
[/OPENYANTRA CONTEXT]
```

---

## Version History Summary

| Version | Key change |
|---|---|
| v1.0 | Core protocol, Chitragupta, 12-sheet schema |
| v2.0 | VidyaKosha search, FAISS, Pratibimba |
| v2.1 | Inbox, Importance, TTL, belief diffing, browser UI |
| v2.4 | Raksha security engine, Quarantine sheet |
| v2.8 | Importance-weighted retrieval |
| v2.10 | Morning brief, context copy, streak |
| v2.11 | v3 Briefing Room, SVG assets |
| v2.12 | Oracle, Export, doc unification |
| v3.0 | SQLite write path + .ods bidirectional sync (planned) |

---

*Protocol: CC0 1.0 Universal -- Library: MIT*
*github.com/revanthlevaka/OpenYantra*
