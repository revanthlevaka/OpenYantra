# OpenYantra: A Human-Readable Persistent Memory Standard for Personal Agentic AI

**Version:** 2.10
**Author:** Revanth Levaka, Hyderabad, India
**License:** CC0 1.0 Universal (Public Domain)
**Repository:** https://github.com/revanthlevaka/OpenYantra

---

## Abstract

Current AI agent memory systems optimise for machine efficiency at the expense of human transparency. They store memory in opaque vector databases, proprietary cloud services, or unstructured flat files -- all of which the user cannot inspect, understand, or correct. We propose **OpenYantra**, a vendor-neutral persistent memory protocol for personal agentic AI systems, using an open-standard spreadsheet (ISO/IEC 26300 `.ods`) as the storage primitive. The protocol introduces a single trusted writer pattern (Chitragupta/LedgerAgent), a hybrid semantic search index (VidyaKosha), a compaction-safe unresolved thread mechanism (Anishtha/Open Loops), prompt injection protection (Raksha), and a browser-based local dashboard for human review. The design is grounded in cognitive science (Zeigarnik Effect, BDI agent theory), validated through independent review by eight AI models across three continents in four rounds, and inspired by Chitragupta -- the Hindu God of Data.

---

## 1. Introduction

### 1.1 The Personal AI Memory Problem

AI agents suffer from a fundamental memory problem. Each session begins blank. Users repeat themselves. Active work context disappears when conversations grow too long and are automatically compressed. Memory systems that do exist are model-specific, cloud-dependent, or technically inaccessible to the user.

This creates four distinct failure modes:

**The Compaction Problem.** When a conversation exceeds the model's context window, older messages are compressed into a summary. Unresolved threads disappear from the agent's awareness.

**The Restart Problem.** Process restarts, software updates, and system crashes wipe runtime state.

**The Repetition Problem.** Users re-explain their projects, preferences, and context at the start of every session because nothing persists.

**The Conflict Problem.** In multi-agent environments, multiple agents writing to the same memory store without coordination creates race conditions, silent overwrites, and data corruption.

### 1.2 The Transparency Gap

Existing memory systems compound these problems by being opaque:

- **Vector databases** (Pinecone, Weaviate) store memory as embedding vectors -- mathematically inaccessible to humans
- **Cloud memory stores** (OpenAI Memory, AWS AgentCore) give users no visibility into what was recorded
- **LLM context injection** loses memory the moment context is compressed

The user cannot answer: *What does my AI agent actually know about me? Is it accurate? Can I fix it?*

### 1.3 Our Approach

OpenYantra treats personal AI memory as a **human-owned file** rather than an agent-owned database. The memory lives in a structured spreadsheet the user can open, read, and edit. Every write is performed by a single trusted agent (Chitragupta/LedgerAgent), signed with SHA-256, and permanently recorded in an audit trail (Agrasandhanī). A sidecar semantic index (VidyaKosha) enables meaning-aware retrieval. The Raksha security engine protects against prompt injection before any write reaches the file.

---

## 2. Mythological Foundation

### 2.1 Chitragupta -- The Hindu God of Data

OpenYantra is inspired by **Chitragupta** (Sanskrit: चित्रगुप्त) -- the divine scribe of Hindu mythology, servant of Yama (the god of justice), and keeper of the Agrasandhanī -- a cosmic register containing the complete record of every human being's actions across their lifetime.

The name derives from *Chitra* (picture, document, the visible record) and *Gupta* (hidden, the unseen persistence). Together: *the hidden picture* -- a complete record that persists invisibly, always accurate, always available.

Brahma instructed Chitragupta: *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*

This is precisely the function of a persistent AI memory system. The architectural parallel between the Chitragupta mythology and the OpenYantra design was independently derived -- not retrofitted.

### 2.2 The Architecture as Mythology, Implemented

| Sanskrit | English | OpenYantra Component |
|---|---|---|
| Chitragupta | The hidden recorder | LedgerAgent -- sole writer |
| Agrasandhanī | The cosmic register | `📒` audit trail sheet |
| Chitrapat | The life scroll | `chitrapat.ods` |
| Karma-Lekha | A deed for recording | WriteRequest |
| Sanchitta | Accumulated karma | WriteQueue -- crash-safe queue |
| Smarana | Remembrance | Session Load Sequence |
| Anishtha | Unfinished intent | Open Loops -- compaction safety |
| Mudra | The divine seal | SHA-256 signature |
| Vivada | Dispute | Conflict escalated to user |
| Dharma-Adesh | Righteous command | User edits always override agents |
| VidyaKosha | Knowledge repository | Sidecar semantic index |
| Pratibimba | Reflection / snapshot | Per-agent frozen index view |
| Raksha | Protection | Prompt injection security engine |
| Nirodh | Containment | Quarantine sheet for blocked writes |

---

## 3. System Architecture

### 3.1 Overview

```
┌─────────────────────────────────────────────────────────┐
│                    chitrapat.ods                         │
│         The Life Scroll (14 sheets, ISO/IEC 26300)       │
│        Open in LibreOffice -- free on all platforms       │
└──────────────────────┬──────────────────────────────────┘
                       │ READ (any agent, Smarana)
                       │ WRITE (Chitragupta only)
              ┌────────▼─────────┐
              │    Raksha        │  Prompt injection scan
              │  Security Engine │  Agent trust tiers 0-5
              └────────┬─────────┘
              ┌────────▼─────────┐
              │   Chitragupta    │  Single trusted writer
              │  (LedgerAgent)   │  SHA-256 Mudra seal
              │                  │  Agrasandhanī audit
              └────────▲─────────┘
                       │ WriteRequest (Karma-Lekha)
       ┌───────────────┼──────────────────┐
       │               │                  │
    Claude          AutoGen           OpenClaw
   (read-only)    (read-only)        (read-only)
                       │
                     User ← Dharma-Adesh (always wins)
                       │
              ┌────────▼─────────┐
              │   VidyaKosha     │  BM25 + TF-IDF hybrid
              │  Semantic Index  │  Importance × recency weighted
              └──────────────────┘
```

### 3.2 The 14-Sheet Schema

| Sheet | Sanskrit | Purpose | Version |
|---|---|---|---|
| Identity | Svarupa | Who the user is | v1.0 |
| Goals | Sankalpa | Long/short-term aims | v1.0 |
| Projects | Karma | Active work | v1.0 |
| People | Sambandha | Relationships | v1.0 |
| Preferences | Ruchi | Taste, habits, anti-goals | v1.0 |
| Beliefs | Vishwas | Values, worldview, evolution | v1.0 |
| Tasks | Kartavya | Action items | v1.0 |
| Open Loops | Anishtha | Unresolved threads | v1.0 |
| Session Log | Dinacharya | Per-session history | v1.0 |
| Agent Config | Niyama | Per-agent instructions | v1.0 |
| Agrasandhanī | -- | Immutable audit trail | v1.0 |
| Inbox | Avagraha | Quick capture, route later | v2.1 |
| Corrections | Sanshodhan | Pending agent edits | v2.1 |
| Quarantine | Nirodh | Blocked injection attempts | v2.4 |

Every sheet carries: Confidence, Source, Last Updated, Importance (1–10).

### 3.3 The Chitragupta Pattern (Single Trusted Writer)

The most important architectural decision in OpenYantra -- validated unanimously by all 8 models across all 4 stress-test rounds. The only unanimous verdict in the entire series.

Every write pipeline:
1. Raksha security scan
2. Admission rules -- noise filtering
3. Vocabulary validation
4. Conflict detection (Vivada)
5. SHA-256 Mudra seal
6. Commit to `.ods`
7. VidyaKosha incremental sync
8. Agrasandhanī audit record

### 3.4 The Anishtha Mechanism (Compaction Safety)

The Anishtha (Open Loops) mechanism -- named unanimously by all 8 models across all 4 rounds as the strongest and most novel feature.

Before context compaction: agents flush unresolved threads to Open Loops. After compaction: re-inject top-N loops (ranked by importance × recency). Each loop carries TTL_Days. Expired loops surface for review.

Implements the **Zeigarnik Effect** (Zeigarnik, 1927) as a persistent data structure.

### 3.5 VidyaKosha (Sidecar Semantic Index)

Hybrid retrieval formula (v2.7):

```
score = relevance × (1 + importance_weight × normalised_importance) × recency
```

BM25 handles proper nouns (project names, people). TF-IDF is the default embedder, upgrades automatically to sentence-transformers when installed.

### 3.6 Raksha -- Security Engine (v2.4)

Permissive mode: only confirmed threats blocked.

- 20+ confirmed injection patterns -- ignored instructions, jailbreak keywords (DAN, STAN), agent impersonation
- 12+ suspicious patterns -- warned, flagged, allowed
- Agent trust tiers 0–5: User > Chitragupta > Known > Unknown > External > Untrusted
- Mudra verification on read -- detects post-hoc tampering
- User writes (Dharma-Adesh) always bypass Raksha

### 3.7 Capture Channels (v2.3–v2.8)

All routes converge on the Inbox sheet through Chitragupta:

| Channel | Command |
|---|---|
| CLI | `yantra inbox "text"` |
| Browser dashboard | Floating `+` button, keyboard `i` |
| Telegram bot | `yantra telegram` |
| iOS Shortcut | `yantra shortcut` |
| Email (SMTP) | `yantra mail` |

### 3.8 Morning Briefing (v2.10)

The daily hook. Runs automatically on first `yantra` command of each day.

Surfaces: urgent Open Loops with TTL countdown, overdue tasks, stale projects, unrouted Inbox items, cross-reference suggestions, one past memory, streak counter. Available in terminal, Telegram, and Markdown. Also rendered as Daily Insight card in dashboard.

### 3.9 Copy Context (v2.9.1)

Formats the top memories as a clean Markdown block, copies to clipboard in one command (`yantra context`). Paste into Claude.ai, ChatGPT, or any web-based AI tool. Bridges OpenYantra local memory to tools people use daily.

---

## 4. Validation -- Four Rounds, 8 Models, 3 Continents

### 4.1 Round 1 -- Architecture Review (pre-v1.0)

| Model | Country | Key finding |
|---|---|---|
| ChatGPT | 🇺🇸 USA | "Optimises for human trust over machine efficiency" |
| Gemini | 🇺🇸 USA | Proposed sidecar index architecture |
| Grok | 🇺🇸 USA | Identified full-file I/O as primary failure mode |
| GLM (Tsinghua) | 🇨🇳 China | Open Loops = formalised Zeigarnik Effect; BDI mapping |
| Mistral | 🇫🇷 France | GDPR-native; user as sole data controller |
| Qwen (Alibaba) | 🇨🇳 China | Schema specification, not storage implementation |
| Kimi (Moonshot) | 🇨🇳 China | Adversarial injection scenarios |
| DeepSeek | 🇨🇳 China | BM25 + vector hybrid retrieval |

### 4.2 Round 2 -- Live Code Review (post-v2.0)

All gaps identified were addressed in subsequent versions. Unanimous: Anishtha is the strongest feature. Interface layer is the adoption barrier.

### 4.3 Round 3 -- Live Product Review (post-v2.2)

6 of 8 models independently named Telegram as the mobile capture solution. 6 of 8 named daily digest as the adoption lever. Results shaped v2.3 through v2.9.

### 4.4 Round 4 -- Maturity Review (post-v2.9)

The question shifted to longevity: "Will this last 10 years?"

**8 of 8 unanimous:** Chitragupta pattern must never change.

**7 of 8:** The `.ods` file must remain the canonical user-facing reality. SQLite is the right v3.0 engine, but human readability and editability must survive the migration.

**7 of 8:** The abandonment gap is lack of proactive daily value. The system captures but does not surface. Addressed in v2.9.1 (Copy Context) and v2.10 (Morning Briefing).

Key quotes from Round 4:
- Grok: *"The AI literally cannot lie or overwrite without leaving fingerprints."*
- Kimi: *"Sync or Die -- bidirectional `.ods` ↔ SQLite sync is the 10-year decision."*
- DeepSeek: *"Protect the kernel; make everything else a plugin."*
- ChatGPT: *"Is OpenYantra a database or a cognitive system? Databases store information. Cognitive systems prioritise attention."*

### 4.5 Cognitive Science Alignment

| Framework | Sheet mapping |
|---|---|
| Tulving (1972) -- Episodic memory | Session Log, Open Loops |
| Tulving (1972) -- Semantic memory | Identity, Beliefs, Preferences |
| Tulving (1972) -- Prospective memory | Tasks, Open Loops |
| Baddeley (2000) -- Episodic buffer | Open Loops -- integrating across time |
| BDI agents (Rao & Georgeff, 1991) | Beliefs → Goals → Tasks + Loops |
| Zeigarnik Effect (1927) | Anishtha -- loops persist until resolved |

---

## 5. Comparison with Related Systems

| Feature | Flat Text | Vector/RAG | MemGPT | Mem0 | Zep | OpenAI Memory | **OpenYantra** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Human-readable | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| User can edit | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Semantic search | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Compaction-safe | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Multi-agent safe | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| Immutable audit trail | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| Injection protection | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Open format (ISO) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Zero infrastructure | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ |
| Browser dashboard | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| Mobile capture | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Daily briefing | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Copy context for web AI | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| GDPR-native | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Open protocol (CC0) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 6. Design Principles

**Human-readable first.** The user can open the memory file at any time and understand it completely. No technical knowledge required.

**The record serves the remembered.** Memory exists to help the user, not to feed the agent. User edits (Dharma-Adesh) always override agent writes.

**Open format forever.** ISO/IEC 26300 `.ods` -- free on every platform, forever.

**Single trusted writer.** Chitragupta is the sole writer. All agents read. Writes are signed, validated, and audited.

**Externally persistent.** Memory lives in a file outside the context window.

**Proactive, not passive.** The system must surface value without being asked.

**Dharma-Adesh.** User edits always win. The user is sovereign.

---

## 7. Version History

| Version | Key additions |
|---|---|
| v1.0 | Core protocol -- Chitragupta, Agrasandhanī, Anishtha, Sanchitta, 12-sheet schema |
| v2.0 | VidyaKosha semantic index, BM25 + TF-IDF hybrid, Pratibimba snapshots |
| v2.1 | Inbox, Importance column, TTL loops, admission rules, belief diffing, browser dashboard, installer |
| v2.2 | Complete repo -- all docs, openclaw/, examples/, references/ |
| v2.3 | Self-contained installer (auto Python + LibreOffice + all deps), Telegram bot, daily digest |
| v2.4 | Raksha security -- injection scanner, agent trust tiers 0–5, Mudra verification, quarantine |
| v2.5 | Today tab, Timeline, Conflict Resolver, floating capture, mobile CSS, docs/docs/visual-guide.html |
| v2.6 | 12-question Bootstrap interview, first-launch onboarding tour, brand assets |
| v2.7 | Importance-weighted retrieval (relevance × importance × recency), `yantra stats` |
| v2.8 | iOS Shortcut server, email-to-inbox SMTP, `yantra migrate`, `yantra schedule` |
| v2.9 | Integrity check, session log archival, partial ODS reads, Stats tab, 7 UI screenshots |
| v2.9.1 | Copy Context -- `yantra context`, paste memory into Claude.ai / ChatGPT / any AI chat |
| v2.10 | Morning Briefing -- `yantra morning`, Daily Insight card, streak counter |
| v3.0 *(planned)* | SQLite backend, `.ods` as canonical export, bidirectional sync, kernel/plugin architecture |

---

## 8. Limitations and Future Work

**Write latency.** Full `.ods` rewrite on every commit. Addressed in v3.0.

**Bidirectional sync.** Users can edit `.ods` directly, but changes are not auto-detected. v3.0 will implement watched-file sync.

**Entity resolution.** VidyaKosha cannot resolve aliases for the same person. Planned for v3.0.

**Temporal graph queries.** Not yet supported. Planned for v3.0.

**Formal benchmarks.** LOCOMO / DMR evaluation not yet complete.

**v3.0 architecture (locked by Round 4 consensus):**
- SQLite as live storage engine
- `.ods` remains the canonical human-facing reality -- not an export, the contract
- Bidirectional sync: human edit → Chitragupta re-sign → update SQLite
- Kernel/plugin separation: Chitragupta + Agrasandhanī + schema = kernel; everything else = plugin

---

## 9. Regional Compliance

- **OpenYantra-IN** 🇮🇳 -- DPDP Act 2023, IT Act 2000
- **OpenYantra-EU** 🇪🇺 -- GDPR, EU AI Act, Data Act 2023
- **OpenYantra-US** 🇺🇸 -- CCPA/CPRA, HIPAA, COPPA
- **OpenYantra-CN** 🇨🇳 -- PIPL, DSL, Cybersecurity Law

---

## 10. Conclusion

OpenYantra proposes a different answer to the personal AI memory problem: instead of giving agents more sophisticated ways to remember, give users transparent control over what is remembered.

The `.ods` file is not the optimal storage engine for high-frequency writes. It is the optimal format for human trust. When users can open their memory file, read it in plain language, and correct any entry -- they trust the system. When they trust the system, they use it daily. When they use it daily, the memory becomes genuinely useful.

Grok, reviewing v2.9: *"The AI literally cannot lie or overwrite without leaving fingerprints."*

That is the property worth preserving at any cost.

*The record exists to serve the remembered, not the recorder.*

---

## References

Baddeley, A. (2000). The episodic buffer: a new component of working memory? *Trends in Cognitive Sciences*, 4(11), 417-423.

Rao, A. S., & Georgeff, M. P. (1991). Modeling rational agents within a BDI-architecture. *Proceedings of the Second International Conference on Principles of Knowledge Representation and Reasoning*, 473-484.

Tulving, E. (1972). Episodic and semantic memory. In E. Tulving & W. Donaldson (Eds.), *Organization of Memory*, 381-402. Academic Press.

Zeigarnik, B. (1927). Über das Behalten von erledigten und unerledigten Handlungen. *Psychologische Forschung*, 9, 1-85.

---

## Acknowledgements

OpenYantra was conceived by Revanth Levaka, filmmaker and open-source builder, in Hyderabad, India.

Four rounds of global stress-testing -- 8 AI models across 3 continents -- provided the independent validation that shaped every version from v1.0 to v2.10.

Named in honour of Chitragupta -- the Hindu God of Data -- whose 3,000-year-old mythological architecture arrived at the same conclusions as modern systems design.

*Conceived in Hyderabad. Built for everyone.*
