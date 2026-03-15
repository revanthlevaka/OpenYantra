<p align="center">
  <img src="assets/logo_horizontal.png" alt="OpenYantra" width="620"/>
</p>

<h1 align="center">OpenYantra</h1>
<h3 align="center">The Sacred Memory Machine</h3>
<h4 align="center"><em>यन्त्र — Inspired by Chitragupta, the Hindu God of Data</em></h4>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0-saffron?style=flat-square&color=FF9933" />
  <img src="https://img.shields.io/badge/Protocol-CC0%201.0-gold?style=flat-square&color=D4AF37" />
  <img src="https://img.shields.io/badge/Library-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Format-.ods%20ISO%2FIEC%2026300-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Works%20on-All%20Platforms-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" />
</p>

<p align="center">
  <strong>A vendor-neutral, human-readable persistent memory standard for agentic AI systems.</strong><br/>
  Any agent. Any framework. Any model. Any platform.
</p>

---

<p align="center">
  <img src="assets/banner_github.png" alt="OpenYantra Banner" width="100%"/>
</p>

---

## What is OpenYantra?

**Yantra** (यन्त्र) means two things in Sanskrit:

1. A **sacred geometric diagram** used in Hindu ritual — precise, structured, and imbued with purpose
2. A **machine or instrument** — a tool that works on your behalf

OpenYantra is both. It is a structured memory instrument for AI agents, designed with the precision and purpose of a yantra, inspired by the world's oldest data architect — **Chitragupta**.

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*  
> — Brahma to Chitragupta

---

## The Problem

Every AI agent session starts blank. You repeat yourself. The agent forgets your projects, your preferences, your unfinished conversations. Context compaction silently destroys active work. Memory systems are model-specific, opaque, and need infrastructure you have to manage. In multi-agent environments, agents overwrite each other's data with no coordination and no audit trail.

**OpenYantra solves this permanently — with a single open-standard file and a single trusted writer.**

---

## The Architecture

Instead of storing *what happened*, OpenYantra stores *who you are* — a structured mind map living in a `.ods` file (OpenDocument Spreadsheet — ISO/IEC 26300, free on all platforms).

```
chitrapat.ods  (The Life Scroll — open in LibreOffice on any platform)
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
```

**Open it in LibreOffice. Edit any cell. The AI reads your changes next session.**  
Works free on Linux, macOS, Windows, Android, and iOS.

---

## The Chitragupta Pattern — Single Trusted Writer

The biggest failure mode in multi-agent memory is write conflict. OpenYantra solves it with a single architectural decision: **only Chitragupta (LedgerAgent) writes to the file**.

```
              chitrapat.ods
           ┌──────────────────┐
           │  READ — any agent│
           └────────┬─────────┘
                    │ WRITE (exclusive)
           ┌────────▼─────────┐
           │   Chitragupta    │  ← LedgerAgent — sole writer
           │  (LedgerAgent)   │  ← validates every write
           │                  │  ← seals with SHA-256 (Mudra)
           │                  │  ← records in Agrasandhanī
           └────────▲─────────┘
                    │ WriteRequest (Karma-Lekha)
       ┌────────────┼────────────┐
       │            │            │
    Claude       AutoGen     OpenClaw
   (read-only)  (read-only) (read-only)
                    │
                  User
            (Dharma-Adesh — user edits always win)
```

Every write is sealed with a **Mudra** (SHA-256 signature) and permanently recorded in the **Agrasandhanī** (audit ledger). Nothing is lost. Nothing is silently overwritten. Every agent's action is traceable.

---

## Quickstart

```bash
pip install odfpy pandas
git clone https://github.com/yourusername/openyantra
cd openyantra
```

```python
from openyantra import OpenYantra, WriteRequest

# The Chitragupta Puja — consecrating the memory file
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Inject into any agent's system prompt — read-only
print(oy.build_system_prompt_block())

# All writes route through Chitragupta (LedgerAgent) automatically
oy.add_project("My Feature Film", domain="Creative", status="Active",
               priority="High", next_step="Finish screenplay act 2")

# Flush open threads before context compaction (Anishtha)
oy.flush_open_loop(
    topic="3-act vs 5-act structure",
    context="Deciding screenplay structure — undecided",
    priority="High",
    related_project="My Feature Film"
)

# Session end — write summary (Dinacharya)
oy.log_session(
    topics=["screenplay structure", "OpenYantra setup"],
    decisions=["Use 3-act structure"],
    open_loops_created=1
)
```

**System prompt output:**
```
[OPENYANTRA CONTEXT — v1.0 | Chitragupta-secured]
User: Revanth | Filmmaker | Hyderabad, IN
Active Projects (Karma): My Feature Film → Finish screenplay act 2
Open Loops (Anishtha): 3-act vs 5-act — Deciding screenplay structure
Goals (Sankalpa): None
Tasks (Kartavya): None
[/OPENYANTRA CONTEXT]
```

---

## The Four Problems OpenYantra Solves

**The Compaction Problem** — When conversations get too long, agents compress older messages. Unresolved context disappears. OpenYantra's Anishtha (Open Loops) sheet is flushed before every compaction and re-injected after. Nothing is lost.

**The Restart Problem** — Docker restarts, crashes, updates — runtime state is gone. OpenYantra lives in a file outside the agent. The Sanchitta (WriteQueue) persists pending writes to disk — they replay automatically on next startup.

**The Repetition Problem** — You shouldn't re-explain your projects every session. OpenYantra's Smarana (Session Load) injects your full context into the system prompt automatically at session start.

**The Conflict Problem** — Multiple agents, concurrent writes, no coordination — memory corrupts. Chitragupta serialises all writes, detects conflicts, and escalates to you rather than silently overwriting.

---

## OpenClaw Integration

```toml
# openclaw/config.toml
[hooks]
pre_compact  = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact = "openyantra.openclaw.hooks:post_compact_hook"
session_end  = "openyantra.openclaw.hooks:session_end_hook"

[env]
OPENYANTRA_FILE = "~/openyantra/chitrapat.ods"
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for the complete OpenClaw setup guide with examples.

---

## LangChain Integration

```python
from openyantra.examples.langchain_adapter import OpenYantraChatMemory
from langchain.agents import initialize_agent

memory = OpenYantraChatMemory(
    path="~/openyantra/chitrapat.ods",
    agent_name="MyAgent"
)
agent = initialize_agent(tools, llm, memory=memory)
```

---

## Framework Support

| Framework | Status | File |
|---|---|---|
| OpenClaw | ✅ Ready | `openclaw/plugin.py`, `openclaw/hooks.py` |
| LangChain | ✅ Ready | `examples/langchain_adapter.py` |
| AutoGen | 🚧 Planned | — |
| CrewAI | 🚧 Planned | — |
| Raw Anthropic API | ✅ Ready | `openyantra.py` |

---

## Global Stress-Test — 8 AI Models, 3 Continents

Before v1.0 launch, the architecture was independently reviewed by 8 AI models across 3 continents. No coordination between models. The convergence is the signal.

| Model | Country | Key finding |
|---|---|---|
| ChatGPT | 🇺🇸 USA | "Optimises for human trust over machine efficiency" |
| Gemini | 🇺🇸 USA | Sidecar index + cold/hot cache split |
| Grok | 🇺🇸 USA | Single-writer pattern (LedgerAgent) solves fatal flaw |
| GLM (Tsinghua) | 🇨🇳 China | Open Loops = formalised Zeigarnik Effect — BDI mapping |
| Mistral | 🇫🇷 Europe | GDPR-native architecture — user is sole data controller |
| Qwen (Alibaba) | 🇨🇳 China | "Position as schema spec, not storage implementation" |
| Kimi (Moonshot) | 🇨🇳 China | Adversarial injection + posthumous memory scenarios |
| DeepSeek | 🇨🇳 China | Open Loops = write-ahead log — BM25 + vector retrieval |

---

## How OpenYantra Compares

| | Flat Text | Vector / RAG | MemGPT | Mem0 | Zep | OpenAI Memory | **OpenYantra** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Human-readable** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **User can edit directly** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Structured / relational** | ❌ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ✅ |
| **Compaction-safe** | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **Multi-agent safe** | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Immutable audit trail** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| **Open format (ISO)** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Zero infrastructure** | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ |
| **GDPR-native** | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Open protocol / standard** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Regional Compliance

| Profile | Region | Law |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India (home) | DPDP Act 2023, IT Act 2000 |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act, Data Act 2023 |
| **OpenYantra-US** 🇺🇸 | United States | CCPA/CPRA, HIPAA, COPPA |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL, Cybersecurity Law |

See [PRIVACY.md](PRIVACY.md) for full guidance per region.

---

## Inspired by Chitragupta — The Hindu God of Data

In Hindu mythology, **Chitragupta** (चित्रगुप्त) is the divine scribe who maintains the complete, incorruptible record of every soul's deeds in the **Agrasandhanī**. He is the sole writer of the cosmic ledger. All other beings are read-only subjects of it.

The OpenYantra architecture maps directly onto this 3,000-year-old system:

| Mythology | OpenYantra |
|---|---|
| Chitragupta — sole trusted recorder | LedgerAgent — only writer to memory |
| Agrasandhanī — the cosmic register | `📒 Agrasandhanī` sheet — audit trail |
| Chitrapat — the life scroll | `chitrapat.ods` — memory file |
| Karma-Lekha — a deed for recording | `WriteRequest` — write to LedgerAgent |
| Dharma-Adesh — righteous command | User edits always override agents |

See [MYTHOLOGY.md](MYTHOLOGY.md) for the complete origin and Sanskrit naming system.

---

## File Structure

```
openyantra/
├── assets/
│   ├── icon_512.png
│   ├── icon_192.png
│   ├── logo_horizontal.png
│   ├── banner_github.png
│   └── og_card.png
├── docs/
│   └── DEPLOYMENT.md         ← Implementation guide for agentic AI systems
├── openclaw/
│   ├── plugin.py             ← OpenClaw session plugin
│   └── hooks.py              ← Pre/post compaction hooks
├── examples/
│   ├── bootstrap.py          ← Quickstart — the Chitragupta Puja
│   └── langchain_adapter.py  ← LangChain memory backend
├── references/
│   └── controlled-vocab.md
├── openyantra.py             ← Core library — Chitragupta + Sanchitta
├── PROTOCOL.md               ← Open protocol spec (CC0)
├── SKILL.md                  ← AI skill definition
├── PRIVACY.md                ← Regional compliance (IN · EU · US · CN)
├── MYTHOLOGY.md              ← Chitragupta origin + Sanskrit naming
├── LICENSE                   ← MIT (library) + CC0 (protocol)
└── chitrapat_template.ods    ← Blank memory file — open in LibreOffice
```

---

## Design Principles

**Human-readable first** — open the file, understand everything.  
**Open format forever** — ISO/IEC 26300, free on every platform.  
**Single trusted writer (Chitragupta)** — sole writer, all others read.  
**Crash-safe (Sanchitta)** — write queue persists, replays on recovery.  
**Externally persistent** — lives outside the context window, survives everything.  
**Transparent (Agrasandhanī)** — every write signed and auditable.  
**Dharma-Adesh** — user edits always win.

---

## Contributing

- **Framework adapters** — AutoGen, CrewAI, Semantic Kernel, Spring AI
- **Sidecar index** — Faiss / sqlite-vss semantic retrieval layer (v1.1)
- **Benchmarks** — LOCOMO / DMR evaluation suite
- **Language ports** — TypeScript, Rust, Go, Java

Open an issue before a PR for anything that changes the protocol spec.

---

## License

OpenYantra Protocol Specification: **CC0 1.0 Universal** (Public Domain)  
OpenYantra Library (`openyantra.py`): **MIT License**

---

## Origin

Built in Hyderabad, India. Conceived by Revanth — filmmaker and open-source builder.  
Stress-tested by 8 AI models across 3 continents before v1.0 launch.  
Named in honour of Chitragupta — the Hindu God of Data.

*The record exists to serve the remembered, not the recorder.*
