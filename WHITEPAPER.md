# OpenYantra: A Human-Readable Persistent Memory Standard for Personal Agentic AI

**Version:** 2.1  
**Author:** Revanth Levaka, Hyderabad, India  
**License:** CC0 1.0 Universal (Public Domain)  
**Repository:** https://github.com/revanthlevaka/OpenYantra

---

## Abstract

Current AI agent memory systems optimise for machine efficiency at the expense of human transparency. They store memory in opaque vector databases, proprietary cloud services, or unstructured flat files — all of which the user cannot inspect, understand, or correct. We propose **OpenYantra**, a vendor-neutral persistent memory protocol for personal agentic AI systems, using an open-standard spreadsheet (ISO/IEC 26300 `.ods`) as the storage primitive. The protocol introduces a single trusted writer pattern (Chitragupta/LedgerAgent), a hybrid semantic search index (VidyaKosha), a compaction-safe unresolved thread mechanism (Anishtha/Open Loops), and a browser-based local dashboard for human review. The design is grounded in cognitive science (Zeigarnik Effect, BDI agent theory), validated through independent review by eight AI models across three continents, and inspired by Chitragupta — the Hindu God of Data.

---

## 1. Introduction

### 1.1 The Personal AI Memory Problem

AI agents — systems that take sequences of actions on behalf of a user, often across multiple sessions — suffer from a fundamental memory problem. Each session begins blank. Users repeat themselves. Active work context disappears when conversations grow too long and are automatically compressed. Memory systems that do exist are model-specific, cloud-dependent, or technically inaccessible to the user.

This creates four distinct failure modes:

**The Compaction Problem.** When a conversation exceeds the model's context window, older messages are compressed into a summary. Unresolved threads — mid-task decisions, pending questions, active work — disappear from the agent's awareness.

**The Restart Problem.** Process restarts, software updates, and system crashes wipe runtime state. Even within a session, agent memory is volatile.

**The Repetition Problem.** Users re-explain their projects, preferences, and context at the start of every session because nothing persists.

**The Conflict Problem.** In multi-agent environments, multiple agents writing to the same memory store without coordination creates race conditions, silent overwrites, and data corruption.

### 1.2 The Transparency Gap

Existing memory systems compound these problems by being opaque:

- **Vector databases** (Pinecone, Weaviate) store memory as embedding vectors — mathematically inaccessible to humans
- **Cloud memory stores** (OpenAI Memory, AWS AgentCore) give users no visibility into what was recorded
- **LLM context injection** loses memory the moment context is compressed

The user cannot answer: *What does my AI agent actually know about me? Is it accurate? Can I fix it?*

### 1.3 Our Approach

OpenYantra treats personal AI memory as a **human-owned file** rather than an agent-owned database. The memory lives in a structured spreadsheet the user can open, read, and edit. Every write is performed by a single trusted agent (Chitragupta/LedgerAgent), signed with SHA-256, and permanently recorded in an audit trail (Agrasandhanī). A sidecar semantic index (VidyaKosha) enables meaning-aware retrieval without moving data out of the user's control.

---

## 2. Mythological Foundation

### 2.1 Chitragupta — The Hindu God of Data

OpenYantra is inspired by **Chitragupta** (Sanskrit: चित्रगुप्त) — the divine scribe of Hindu mythology, servant of Yama (the god of justice), and keeper of the Agrasandhanī — a cosmic register containing the complete record of every human being's actions across their lifetime.

The name derives from *Chitra* (picture, document, the visible record) and *Gupta* (hidden, the unseen persistence). Together: *the hidden picture* — a complete record that persists invisibly, always accurate, always available.

Brahma instructed Chitragupta: *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*

This is, precisely, the function of a persistent AI memory system. The architectural parallel between the Chitragupta mythology and the OpenYantra design was independently derived — not retrofitted. The single trusted writer pattern, the immutable audit trail, and the principle that the record serves the remembered rather than the recorder are all present in both the mythology and the software.

### 2.2 The Architecture as Mythology, Implemented

| Sanskrit / Mythology | English | OpenYantra Component |
|---|---|---|
| Chitragupta | The hidden recorder | LedgerAgent — sole writer |
| Agrasandhanī | The cosmic register | `📒 Agrasandhanī` — audit trail sheet |
| Chitrapat | The life scroll | `chitrapat.ods` — memory file |
| Karma-Lekha | A deed for recording | WriteRequest — write submitted to LedgerAgent |
| Sanchitta | Accumulated karma awaiting reckoning | WriteQueue — crash-safe write queue |
| Smarana | Remembrance | Session Load Sequence |
| Anishtha | Unfinished intent | Open Loops — flushed before compaction |
| Mudra | The divine seal | SHA-256 signature |
| Vivada | Dispute | Conflict escalated to user |
| Dharma-Adesh | Righteous command | User edits always override agents |
| VidyaKosha | Knowledge repository | Sidecar semantic index |
| Pratibimba | Reflection / snapshot | Per-agent frozen index view |

### 2.3 The Yantra

**Yantra** (यन्त्र) means both a sacred geometric diagram used in Hindu ritual and a machine or instrument. OpenYantra is both simultaneously — a precisely structured schema imbued with purpose, functioning as an instrument that works on the user's behalf.

---

## 3. System Architecture

### 3.1 Overview

```
┌─────────────────────────────────────────────────────┐
│                    chitrapat.ods                     │
│            The Life Scroll (14 sheets)               │
│         Open in LibreOffice — free everywhere        │
└──────────────────────┬──────────────────────────────┘
                       │ READ (any agent, Smarana)
                       │ WRITE (Chitragupta only)
              ┌────────▼─────────┐
              │   Chitragupta    │  Single trusted writer
              │  (LedgerAgent)   │  SHA-256 seal (Mudra)
              │                  │  Agrasandhanī audit
              └────────▲─────────┘
                       │ WriteRequest (Karma-Lekha)
       ┌───────────────┼───────────────┐
       │               │               │
    Claude          AutoGen        OpenClaw
   (read-only)    (read-only)    (read-only)
                       │
                     User ← Dharma-Adesh (always wins)
                       │
              ┌────────▼─────────┐
              │   VidyaKosha     │  Sidecar semantic index
              │  BM25 + vectors  │  O(1) incremental update
              └──────────────────┘
```

### 3.2 The 14-Sheet Schema

OpenYantra v2.1 organises user memory into 14 domain-separated sheets:

| Sheet | Sanskrit | Purpose | v2.1 addition |
|---|---|---|---|
| Identity | Svarupa | Who the user is | Importance column |
| Goals | Sankalpa | Long/short-term aims | Importance, TTL |
| Projects | Karma | Active work | Importance column |
| People | Sambandha | Relationships | Importance column |
| Preferences | Ruchi | Taste and habits | Importance column |
| Beliefs | Vishwas | Values and worldview | Contradiction_Flag |
| Tasks | Kartavya | Action items | Importance column |
| Open Loops | Anishtha | Unresolved threads | TTL_Days column |
| Session Log | Dinacharya | Per-session history | — |
| Agent Config | Niyama | Per-agent settings | VidyaKosha mode |
| Agrasandhanī | Agrasandhanī | Immutable audit trail | Importance logged |
| Inbox | Avagraha | Quick capture (v2.1) | New in v2.1 |
| Corrections | Sanshodhan | Pending edits (v2.1) | New in v2.1 |
| INDEX | Soochi | Schema overview | — |

This separation maps closely onto established cognitive science models. The Identity, Beliefs, and Preferences sheets correspond to semantic memory (Tulving, 1972). The Session Log and Open Loops sheets correspond to episodic memory and the episodic buffer (Baddeley, 2000). Goals, Tasks, and Open Loops implement prospective memory — remembering to perform future actions. The structure also maps onto the Belief-Desire-Intention (BDI) agent model (Rao & Georgeff, 1991): Beliefs sheets contain agent beliefs, Goals contains desires, and Tasks + Open Loops contain intentions.

### 3.3 Universal Columns

Every sheet in v2.1 carries three universal columns:

- **Confidence** (`High` / `Medium` / `Low` / `Inferred`) — certainty of the recorded data
- **Source** (`User-stated` / `Agent-observed` / `Agent-inferred` / `System`) — provenance
- **Importance** (1–10) — salience for retrieval weighting

The Source column implements the *Chitra/Gupta distinction* from Hindu tradition: Chitra sources (User-stated, Agent-observed) are explicit and carry higher trust; Gupta sources (Agent-inferred) are hidden inference and carry lower trust. In conflict resolution, Chitra always beats Gupta.

### 3.4 The Chitragupta Pattern (Single Trusted Writer)

The most important architectural decision in OpenYantra is the single trusted writer principle: only Chitragupta (LedgerAgent) writes to the Chitrapat. All other agents are read-only.

Every agent submits a Karma-Lekha (WriteRequest) containing the target sheet, operation, fields, confidence, source, and importance. LedgerAgent:

1. Applies admission rules — filters noise writes (importance < threshold, no actionable content)
2. Validates controlled vocabulary
3. Detects Vivada (conflicts) — when agent data conflicts with user-edited data
4. Seals with SHA-256 Mudra
5. Commits to the `.ods` file
6. Records permanently in the Agrasandhanī

This pattern is equivalent to the Single Writer Multiple Reader (SWMR) pattern in systems programming, the write-ahead log in database systems, and double-entry bookkeeping in accounting — all independently arrived at the same solution to the write coordination problem.

### 3.5 The Anishtha Mechanism (Compaction Safety)

The Anishtha (Open Loops) mechanism is OpenYantra's primary solution to the context compaction problem and its most broadly validated innovation. Before any context compaction, agents flush unresolved threads to the Open Loops sheet. After compaction, they re-inject the top-N loops (ranked by importance × recency) into the new context.

This implements the **Zeigarnik Effect** (Zeigarnik, 1927) as a persistent data structure. Zeigarnik demonstrated that humans remember incomplete tasks more vividly than completed ones. OpenYantra externalises this cognitive mechanism — unresolved threads are captured before they can be compacted away, and re-surfaced automatically.

In v2.1, each Open Loop carries a TTL_Days field specifying expiry. Loops older than TTL are surfaced for user review: *"This loop has been open for 90 days. Resolve, delegate, or archive?"*

### 3.6 VidyaKosha (Sidecar Semantic Index)

VidyaKosha is a sidecar index that enables semantic retrieval across the Chitrapat without modifying the storage format. It maintains:

- A FAISS vector index (one embedding per row)
- A BM25 keyword index
- A row manifest for change detection
- Per-agent Pratibimba (snapshot) directories

The hybrid retrieval formula:

```
score = α × vector_score + (1-α) × bm25_score
```

Default α = 0.7. The BM25 component is critical for personal data containing proper nouns — names, project codes, place names — which vector search tends to generalise into semantic concepts. For "Project Manikonda," BM25 guarantees exact recall while vectors provide semantic context.

The embedder is pluggable: TF-IDF (zero extra dependencies, built-in) upgrades automatically to `sentence-transformers/all-MiniLM-L6-v2` when installed.

In v2.1, VidyaKosha supports incremental updates — O(1) index maintenance per write, eliminating the full-rebuild latency identified in testing.

### 3.7 The Inbox Sheet (v2.1)

A critical gap identified in the global review: forcing categorisation at write time creates hallucinated sheet assignments and write-time bottlenecks. The Inbox sheet accepts any content without categorisation. Chitragupta routes items to correct sheets using keyword heuristics, with low confidence marking for user review.

This mirrors the GTD (Getting Things Done) inbox primitive, email inboxes, and Apple Notes — the most successful personal capture tools all have an uncategorised catch-all as the primary input mechanism.

---

## 4. Validation

### 4.1 Global Stress-Test — Round 1 (Architecture Review)

Before v1.0 launch, the proposed architecture was submitted to 8 AI models across 3 continents for independent evaluation. No model was aware of another's response.

| Model | Country | Key finding |
|---|---|---|
| ChatGPT | 🇺🇸 USA | "Optimises for human trust over machine efficiency" |
| Gemini | 🇺🇸 USA | Proposed sidecar index + cold/hot cache architecture |
| Grok | 🇺🇸 USA | Identified full-file I/O as primary failure mode |
| GLM (Tsinghua) | 🇨🇳 China | Open Loops = formalised Zeigarnik Effect; BDI agent mapping |
| Mistral | 🇫🇷 France | GDPR-native architecture; user as sole data controller |
| Qwen (Alibaba) | 🇨🇳 China | "Position as schema specification, not storage implementation" |
| Kimi (Moonshot) | 🇨🇳 China | Adversarial injection scenarios; posthumous memory ethics |
| DeepSeek | 🇨🇳 China | Open Loops = write-ahead log; BM25 + vector hybrid retrieval |

All 8 models independently validated the Anishtha mechanism. All 8 identified the need for a sidecar retrieval layer. The Chitragupta single-writer pattern was validated by 7 of 8 (one questioned implementation speed, not the concept).

### 4.2 Global Stress-Test — Round 2 (Live Project Review)

After v2.0 launch, the same 8 models reviewed the live GitHub repository (https://github.com/revanthlevaka/OpenYantra). Key findings:

**Unanimous agreements across all 8:**
- Anishtha (Open Loops) is the strongest and most novel feature — keep it always
- The interface layer (not the architecture) is the adoption barrier
- VidyaKosha semantic search is well-implemented and sufficient for personal scale
- The Chitragupta single-writer pattern is architecturally correct

**Specific gaps identified:**
- Full-file rewrite on every VidyaKosha sync (fixed in v2.1 via incremental updates)
- No catch-all Inbox for quick capture (added in v2.1)
- No importance scoring for retrieval ranking (added in v2.1)
- Memory admission rules needed to filter noise writes (added in v2.1)
- Belief diffing / contradiction detection missing (added in v2.1)
- Browser-based UI needed for human review (added in v2.1 as `yantra ui`)
- Bootstrap interview needed for cold start (added in v2.1)
- Mobile capture missing (roadmap for v2.2)

### 4.3 Cognitive Science Alignment

The OpenYantra schema maps onto three established cognitive science frameworks:

**Tulving's memory systems (1972):**
- Episodic memory → Session Log (Dinacharya), Open Loops (Anishtha)
- Semantic memory → Identity (Svarupa), Beliefs (Vishwas), Preferences (Ruchi)
- Prospective memory → Tasks (Kartavya), Open Loops (Anishtha)

**Baddeley's working memory model (2000):**
- Central executive → Agent Config (Niyama), admission rules
- Episodic buffer → Open Loops (Anishtha) — integrating across time

**Belief-Desire-Intention (BDI) agents (Rao & Georgeff, 1991):**
- Beliefs → Identity, Beliefs, People sheets
- Desires → Goals (Sankalpa)
- Intentions → Tasks (Kartavya), Open Loops (Anishtha)

---

## 5. Comparison with Related Systems

| Feature | Flat Text | Vector/RAG | MemGPT | Mem0 | Zep | OpenAI Memory | **OpenYantra** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Human-readable | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| User can edit | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Semantic search | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Compaction-safe | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Multi-agent safe | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| Immutable audit | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| Open format (ISO) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Zero infrastructure | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ |
| GDPR-native | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Open protocol (CC0) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Known gaps:** OpenYantra does not match Zep's bi-temporal graph reasoning or Mem0's relationship graph density. These are deliberate tradeoffs for the personal-use target.

---

## 6. Design Principles

**Human-readable first.** The user can open the memory file at any time and understand it completely. No technical knowledge required.

**The record serves the remembered.** Memory exists to help the user, not to feed the agent. User edits (Dharma-Adesh) always override agent writes.

**Open format forever.** ISO/IEC 26300 `.ods` — free on every platform, forever. No proprietary format, no paid subscription, no vendor lock-in.

**Single trusted writer.** Chitragupta is the sole writer. All agents read. Writes are signed, validated, and audited.

**Externally persistent.** Memory lives in a file outside the context window. It survives compaction, restarts, and process crashes.

**Transparent.** Every write is logged in the Agrasandhanī with agent name, timestamp, SHA-256 signature, and status.

**Dharma-Adesh.** User edits always win. The user is sovereign over their own memory.

---

## 7. Limitations and Future Work

### 7.1 Current limitations

**Write latency.** Full `.ods` file rewrite on every Chitragupta commit adds 100–500ms at current scale. Incremental updates (v2.1) mitigate this at the index layer; full incremental `.ods` writes require format-level changes (SQLite backend planned for v3.0).

**Temporal reasoning.** VidyaKosha supports recency weighting but not full temporal graph queries ("what did I believe about X before event Y?"). A TimeAgent with date-range query support is planned for v2.2.

**Mobile capture.** No native mobile input in v2.1. Telegram bot and iOS Shortcut integration planned for v2.2.

**Entity resolution.** VidyaKosha cannot resolve "my brother," "Rahul," and "that guy from the wedding" as the same person. Coreference resolution planned for v3.0.

**Formal benchmarks.** OpenYantra has not yet been evaluated on established benchmarks (LoCoMo, DMR). Benchmark suite planned for v2.2.

### 7.2 Roadmap

| Version | Key additions |
|---|---|
| v2.1 (current) | Inbox, Importance, TTL, Belief diffing, Browser UI, CLI installer |
| v2.2 | Mobile capture (Telegram/iOS), TimeAgent, benchmark suite |
| v3.0 | SQLite backend + `.ods` as export view, entity resolution, graph layer |

---

## 8. Regional Compliance

OpenYantra ships four regional compliance profiles:

- **OpenYantra-IN** 🇮🇳 — DPDP Act 2023, IT Act 2000 (home profile)
- **OpenYantra-EU** 🇪🇺 — GDPR, EU AI Act, Data Act 2023
- **OpenYantra-US** 🇺🇸 — CCPA/CPRA, HIPAA, COPPA
- **OpenYantra-CN** 🇨🇳 — PIPL, DSL, three-tier team hierarchy

Under GDPR, the user is the sole data controller (Article 4). No data processing agreements are required. The Agrasandhanī satisfies EU AI Act Article 13 transparency requirements.

---

## 9. Conclusion

OpenYantra proposes a different answer to the personal AI memory problem: instead of giving agents more sophisticated ways to remember, give users transparent control over what is remembered.

The `.ods` file is not the optimal storage engine for high-frequency writes. It is the optimal format for human trust. When users can open their memory file, read it in plain language, and correct any entry — they trust the system. When they trust the system, they use it daily. When they use it daily, the memory becomes genuinely useful.

ChatGPT 5.3, reviewing the project, offered the most apt comparison: *"Not flashy. But foundational. A bit like SQLite quietly running inside half the software on Earth."*

That is the aspiration. A memory standard that agents and users can both rely on — transparent, durable, owned by the human it serves.

*The record exists to serve the remembered, not the recorder.*

---

## References

Baddeley, A. (2000). The episodic buffer: a new component of working memory? *Trends in Cognitive Sciences*, 4(11), 417-423.

Rao, A. S., & Georgeff, M. P. (1991). Modeling rational agents within a BDI-architecture. *Proceedings of the Second International Conference on Principles of Knowledge Representation and Reasoning*, 473-484.

Tulving, E. (1972). Episodic and semantic memory. In E. Tulving & W. Donaldson (Eds.), *Organization of Memory*, 381-402. Academic Press.

Zeigarnik, B. (1927). Über das Behalten von erledigten und unerledigten Handlungen [On the retention of completed and uncompleted actions]. *Psychologische Forschung*, 9, 1-85.

---

## Acknowledgements

OpenYantra was conceived by Revanth Levaka, filmmaker and open-source builder, in Hyderabad, India.

The global stress-test review — 8 AI models across 3 continents — provided the independent validation that shaped v2.0 and v2.1. The convergence of independent evaluations from different architectures, training data, and geopolitical contexts gave confidence that the core design decisions were correct.

Named in honour of Chitragupta — the Hindu God of Data — whose 3,000-year-old mythological architecture arrived at the same conclusions as modern systems design.

*Conceived in Hyderabad. Built for everyone.*
