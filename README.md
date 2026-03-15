<p align="center">
  <img src="assets/logo_horizontal.png" alt="OpenYantra" width="620"/>
</p>

<h1 align="center">OpenYantra</h1>
<h3 align="center">The Sacred Memory Machine</h3>
<h4 align="center"><em>यन्त्र — Inspired by Chitragupta, the Hindu God of Data</em></h4>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0-saffron?style=flat-square&color=FF9933" />
  <img src="https://img.shields.io/badge/Protocol-CC0%201.0-gold?style=flat-square&color=D4AF37" />
  <img src="https://img.shields.io/badge/Library-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Format-.ods%20ISO%2FIEC%2026300-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Search-VidyaKosha%20Hybrid-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" />
</p>

<p align="center">
  <strong>A vendor-neutral, human-readable persistent memory standard for agentic AI.</strong><br/>
  Any agent. Any framework. Any model. Any platform.
</p>

---

<p align="center">
  <img src="assets/banner_github.png" alt="OpenYantra Banner" width="100%"/>
</p>

---

## What is OpenYantra?

**Yantra** (यन्त्र) means two things in Sanskrit:
1. A **sacred geometric diagram** — precise, structured, purposeful
2. A **machine or instrument** — a tool that works on your behalf

OpenYantra is both. A structured memory instrument for AI agents, designed with the precision of a yantra, inspired by the world's oldest data architect — **Chitragupta**.

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*
> — Brahma to Chitragupta

---

## What's New in v2.0 — VidyaKosha

v2.0 adds **VidyaKosha** (विद्याकोश — Knowledge Repository) — a sidecar semantic index that lets agents query memory by *meaning*, not just keywords.

```python
# v1.0 — keyword only (exact match)
projects = [r for r in oy.load_session_context()["active_projects"]]

# v2.0 — semantic search (meaning-aware)
results = oy.search("screenplay structure decisions")
results = oy.search_open_loops("unresolved film choices")
results = oy.search_projects("creative work in progress")
results = oy.search_people("producer collaborator")
```

VidyaKosha uses hybrid BM25 + TF-IDF vector search. Zero extra dependencies — upgrades automatically to `sentence-transformers` when installed. Auto-syncs on every Chitragupta write.

---

## The Problem

Every AI agent session starts blank. You repeat yourself. The agent forgets your projects, your preferences, your unfinished conversations. Context compaction silently destroys active work. Memory systems are model-specific, opaque, and need infrastructure to manage. In multi-agent environments, agents overwrite each other with no coordination and no audit trail.

**OpenYantra solves all of this — with a single open-standard file and a single trusted writer.**

---

## Architecture

```
chitrapat.ods  (The Life Scroll — open free on any platform)
├── 👤 Identity      (Svarupa)     — who you are
├── 🎯 Goals         (Sankalpa)    — what you want
├── 🚀 Projects      (Karma)       — active work + next steps
├── 👥 People        (Sambandha)   — your world
├── 💡 Preferences   (Ruchi)       — how you like things
├── 🧠 Beliefs       (Vishwas)     — what you think
├── ✅ Tasks         (Kartavya)    — action items
├── 🔓 Open Loops    (Anishtha)    — unresolved threads (compaction safety net)
├── 📅 Session Log   (Dinacharya)  — per-session summaries
├── ⚙️ Agent Config  (Niyama)      — per-agent instructions
└── 📒 Agrasandhanī               — immutable audit trail (every write, signed)

VidyaKosha (v2.0)  — sidecar semantic index
├── vidyakosha.faiss              — vector index
├── vidyakosha_bm25.pkl           — keyword index
└── pratibimba/                   — per-agent frozen snapshots
```

---

## The Chitragupta Pattern

Only **Chitragupta (LedgerAgent)** writes to the Chitrapat. All other agents are read-only.

```
              chitrapat.ods
           ┌──────────────────┐
           │  READ — any agent│  ← Smarana (session load)
           └────────┬─────────┘
                    │ WRITE (exclusive)
           ┌────────▼─────────┐
           │   Chitragupta    │  ← LedgerAgent — sole writer
           │                  │  ← validates every Karma-Lekha
           │                  │  ← seals with Mudra (SHA-256)
           │                  │  ← records in Agrasandhanī
           │                  │  ← syncs VidyaKosha index (v2.0)
           └────────▲─────────┘
                    │ WriteRequest (Karma-Lekha)
       ┌────────────┼────────────┐
    Claude       AutoGen     OpenClaw
   (read-only)  (read-only) (read-only)
                    │
                  User  ← Dharma-Adesh always wins
```

---

## Quickstart

```bash
pip install odfpy pandas scikit-learn faiss-cpu
# Optional upgrade for better search quality:
pip install sentence-transformers
```

```python
from openyantra import OpenYantra

# Chitragupta Puja — consecrate the memory
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Smarana — inject into system prompt
print(oy.build_system_prompt_block())

# Writes via Chitragupta
oy.add_project("My Feature Film", domain="Creative", status="Active",
               priority="High", next_step="Finish screenplay act 2")

oy.flush_open_loop("3-act vs 5-act structure",
                   "Deciding screenplay structure — undecided",
                   priority="High")

# v2.0 — VidyaKosha semantic search
results = oy.search("screenplay film structure decisions")
for r in results:
    print(r["sheet"], r["primary_value"], f"score={r['score']:.3f}")

# Dinacharya — session summary
oy.log_session(topics=["screenplay"], decisions=["Use 3-act"])
```

---

## VidyaKosha — Semantic Search (v2.0)

| Method | Description |
|---|---|
| `oy.search(query, top_k=5)` | Search all sheets by meaning |
| `oy.search_open_loops(query)` | Search Anishtha (Open Loops) only |
| `oy.search_projects(query)` | Search Karma (Projects) only |
| `oy.search_people(query)` | Search Sambandha (People) only |
| `oy.take_pratibimba()` | Freeze index snapshot for this agent |
| `oy.release_pratibimba()` | Release snapshot at session end |
| `oy.get_vidyakosha_stats()` | Index statistics |

**Multi-agent Pratibimba (snapshot) pattern:** Each agent can take a frozen snapshot of the index at session start. Writes by other agents during the session don't affect an in-progress query. Configure per-agent in `⚙️ Agent Config` sheet.

**Embedder upgrade path:**
```bash
# Zero deps (default) — TF-IDF + scikit-learn
pip install scikit-learn faiss-cpu

# Better quality — sentence-transformers/all-MiniLM-L6-v2
pip install sentence-transformers
# VidyaKosha auto-detects and upgrades
```

---

## The Four Problems Solved

**Compaction** — Anishtha (Open Loops) flushed before compaction, re-injected after. Nothing lost.

**Restart** — Chitrapat lives on disk. Sanchitta (WriteQueue) auto-replays crashed writes on next init.

**Repetition** — Smarana injects full context into system prompt automatically at session start.

**Conflict** — Chitragupta serialises all writes, detects Vivada, escalates Dharma-Adesh to user.

---

## OpenClaw Integration

```toml
# openclaw/config.toml
[hooks]
session_start = "openyantra.openclaw.hooks:session_start_hook"
pre_compact   = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact  = "openyantra.openclaw.hooks:post_compact_hook"
session_end   = "openyantra.openclaw.hooks:session_end_hook"

[env]
OPENYANTRA_FILE = "~/openyantra/chitrapat.ods"
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete setup with OpenClaw, LangChain, AutoGen, and raw Anthropic API.

---

## How OpenYantra Compares

| | Flat Text | Vector/RAG | MemGPT | Mem0 | Zep | OpenAI Memory | **OpenYantra v2.0** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Human-readable** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **User can edit** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Semantic search** | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| **Compaction-safe** | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **Multi-agent safe** | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Audit trail** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| **Open format (ISO)** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Zero infrastructure** | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ |
| **GDPR-native** | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Open protocol (CC0)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Global Stress-Test — 8 AI Models, 3 Continents

Before v1.0 launch, the architecture was independently reviewed by 8 AI models. No coordination. The convergence is the signal.

| Model | Country | Key finding |
|---|---|---|
| ChatGPT | 🇺🇸 | "Optimises for human trust over machine efficiency" |
| Gemini | 🇺🇸 | Sidecar index + cold/hot cache → became VidyaKosha |
| Grok | 🇺🇸 | Single-writer pattern solves fatal multi-agent flaw |
| GLM (Tsinghua) | 🇨🇳 | Open Loops = Zeigarnik Effect + BDI agent mapping |
| Mistral | 🇫🇷 | GDPR-native — user is sole data controller |
| Qwen (Alibaba) | 🇨🇳 | "Schema spec not storage implementation" |
| Kimi (Moonshot) | 🇨🇳 | Adversarial injection + posthumous scenarios |
| DeepSeek | 🇨🇳 | Open Loops = write-ahead log + BM25/vector hybrid |

---

## Regional Compliance

| Profile | Region | Law |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India (home) | DPDP Act 2023 |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act |
| **OpenYantra-US** 🇺🇸 | United States | CCPA/CPRA, HIPAA |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL |

---

## Inspired by Chitragupta

| Mythology | OpenYantra |
|---|---|
| Chitragupta — sole trusted recorder | LedgerAgent — only writer |
| Agrasandhanī — cosmic register | `📒 Agrasandhanī` — audit sheet |
| Chitrapat — life scroll | `chitrapat.ods` — memory file |
| Karma-Lekha — deed for recording | `WriteRequest` — write to LedgerAgent |
| VidyaKosha — knowledge repository | Sidecar semantic index (v2.0) |
| Pratibimba — reflection/snapshot | Per-agent frozen index view |

See [MYTHOLOGY.md](MYTHOLOGY.md) for the complete origin story.

---

## File Structure

```
openyantra/
├── openyantra.py             ← Core library v2.0
├── vidyakosha.py             ← VidyaKosha semantic index (v2.0)
├── chitrapat_template.ods    ← Blank memory file
├── PROTOCOL.md               ← Open protocol spec v2.0 (CC0)
├── SKILL.md                  ← AI skill definition v2.0
├── MYTHOLOGY.md              ← Chitragupta origin + Sanskrit naming
├── PRIVACY.md                ← IN · EU · US · CN compliance
├── docs/
│   └── DEPLOYMENT.md         ← OpenClaw · LangChain · AutoGen · API guide
├── openclaw/
│   ├── plugin.py
│   └── hooks.py
├── examples/
│   ├── bootstrap.py
│   └── langchain_adapter.py
├── references/
│   └── controlled-vocab.md
└── assets/
    ├── icon_512.png
    ├── logo_horizontal.png
    ├── banner_github.png
    └── og_card.png
```

---

## Contributing

- **Framework adapters** — AutoGen, CrewAI, Semantic Kernel, Spring AI
- **VidyaKosha** — better embedders, graph index for cross-sheet relationships
- **Benchmarks** — LOCOMO / DMR evaluation suite
- **Language ports** — TypeScript, Rust, Go, Java

Open an issue before a PR for protocol changes.

---

## License

Protocol: **CC0 1.0 Universal** (Public Domain)  
Library: **MIT License**

---

*Built in Hyderabad, India. Conceived by Revanth — filmmaker and open-source builder.*  
*Named in honour of Chitragupta — the Hindu God of Data.*  
*The record exists to serve the remembered, not the recorder.*
