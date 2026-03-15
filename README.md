<p align="center">
  <img src="assets/logo_horizontal.png" alt="OpenYantra" width="620"/>
</p>

<h1 align="center">OpenYantra</h1>
<h3 align="center">The Sacred Memory Machine</h3>
<h4 align="center"><em>यन्त्र — Inspired by Chitragupta, the Hindu God of Data</em></h4>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.8-saffron?style=flat-square&color=FF9933" />
  <img src="https://img.shields.io/badge/Protocol-CC0%201.0-gold?style=flat-square&color=D4AF37" />
  <img src="https://img.shields.io/badge/Library-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Format-.ods%20ISO%2FIEC%2026300-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/UI-Browser%20Dashboard-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Install-One%20Command-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/Security-Raksha%20Engine-red?style=flat-square&color=DC143C" />
</p>

<p align="center">
  <strong>A vendor-neutral, human-readable persistent memory standard for personal agentic AI.</strong><br/>
  Any agent. Any framework. Any model. Any platform.
</p>

---

<p align="center">
  <img src="assets/banner_github.png" alt="OpenYantra Banner" width="100%"/>
</p>

---

## Install in one command

**Mac / Linux** — fully self-contained, installs Python + LibreOffice + all deps automatically:
```bash
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex
```

Then:
```bash
yantra bootstrap    # 12-question interview — populates memory via conversation
yantra ui           # browser dashboard → http://localhost:7331
yantra inbox "text" # quick capture from terminal
yantra digest       # daily proactive summary
yantra telegram     # start Telegram bot for mobile capture
yantra security     # full security audit
yantra doctor       # system health check
```

---

## What is OpenYantra?

**Yantra** (यन्त्र) means two things in Sanskrit:
1. A **sacred geometric diagram** — precise, structured, purposeful
2. A **machine or instrument** — a tool that works on your behalf

OpenYantra is both. A structured memory instrument for personal AI agents, inspired by **Chitragupta** (चित्रगुप्त) — the Hindu God of Data.

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*
> — Brahma to Chitragupta

---

## The Problem

Every AI agent session starts blank. You repeat yourself. Active work disappears when context gets compressed. Memory systems are opaque and cloud-dependent. In multi-agent environments, agents overwrite each other with no coordination and no audit trail.

**OpenYantra solves all of this — with a single open-standard file and a single trusted writer.**

---

## Architecture

```
chitrapat.ods  (open free in LibreOffice on any platform)
├── 👤 Identity      (Svarupa)     — who you are
├── 🎯 Goals         (Sankalpa)    — what you want
├── 🚀 Projects      (Karma)       — active work + next steps
├── 👥 People        (Sambandha)   — your world
├── 💡 Preferences   (Ruchi)       — how you like things
├── 🧠 Beliefs       (Vishwas)     — values, worldview, belief evolution
├── ✅ Tasks         (Kartavya)    — action items
├── 🔓 Open Loops    (Anishtha)    — unresolved threads (compaction safety net) ★
├── 📅 Session Log   (Dinacharya)  — per-session summaries
├── ⚙️ Agent Config  (Niyama)      — per-agent instructions
├── 📒 Agrasandhanī               — immutable audit trail (SHA-256 signed)
├── 📥 Inbox         (Avagraha)    — quick capture, route later
├── ✏️ Corrections   (Sanshodhan) — pending agent edits for approval
└── 🔒 Quarantine    (Nirodh)      — blocked injection attempts
```

**★ Anishtha (Open Loops)** — unanimously named by all 8 models across 3 stress-test rounds as the strongest and most novel feature. Flushes unresolved threads before context compaction, re-injects after. Implements the Zeigarnik Effect as a persistent data structure.

---

## The Chitragupta Pattern

Only **Chitragupta (LedgerAgent)** writes to the Chitrapat. All other agents are read-only. Every write is sealed with SHA-256 (Mudra) and permanently recorded in the Agrasandhanī.

```
              chitrapat.ods
           ┌──────────────────┐
           │  READ — any agent│  ← Smarana (session load)
           └────────┬─────────┘
                    │ WRITE (exclusive)
           ┌────────▼─────────┐
           │   Chitragupta    │  ← sole writer
           │  (LedgerAgent)   │  ← Raksha security scan
           │                  │  ← validates + admission rules
           │                  │  ← SHA-256 Mudra seal
           │                  │  ← Agrasandhanī audit
           │                  │  ← VidyaKosha index sync
           └────────▲─────────┘
                    │ WriteRequest (Karma-Lekha)
       ┌────────────┼────────────┐
    Claude       AutoGen     OpenClaw
   (read-only)  (read-only) (read-only)
                    │
                  User ← Dharma-Adesh always wins
```

---

## Quickstart (Python)

```bash
pip install odfpy pandas scikit-learn faiss-cpu fastapi uvicorn
```

```python
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

# Smarana — inject context into system prompt at session start
print(oy.build_system_prompt_block())

# Writes via Chitragupta
oy.add_project("My Film", domain="Creative", status="Active",
               priority="High", next_step="Write act 2", importance=9)
oy.flush_open_loop("3-act vs 5-act", "Undecided on structure",
                   priority="High", ttl_days=30)

# Quick capture to Inbox
oy.inbox("Priya mentioned budget revision needed by Friday")

# VidyaKosha — semantic search (v2.8: importance-weighted results)
results = oy.search("screenplay structure decisions")
for r in results:
    print(r["sheet"], r["primary_value"], f"score={r['score']:.3f}")

# Session end
oy.log_session(topics=["screenplay"], decisions=["Research 5-act structure"])
```

---

## Browser Dashboard — `yantra ui`

```bash
yantra ui  # → http://localhost:7331
```

| Tab | What it shows |
|---|---|
| 🌅 **Today** | Unified daily view — urgent loops, stale projects, pending tasks. One-click actions. |
| 📥 **Inbox** | Unrouted captures. Route all with one click. Keyboard shortcut `i` anywhere. |
| 🚀 **Projects** | Active Karma with status, priority, next step. |
| 🔓 **Open Loops** | All Anishtha sorted by importance × recency. TTL countdown. |
| ✅ **Tasks** | Pending Kartavya. Complete from Today view. |
| 📅 **Timeline** | Chronological activity feed — every write, by whom, when. |
| ⚡ **Conflicts** | Visual diff — agent value vs your value. Accept/Reject with one click. |
| ✏️ **Corrections** | Agent-proposed edits pending approval. |
| 🔒 **Security** | Quarantine review, security threat log, full scan. |
| 📒 **Ledger** | Full Agrasandhanī — SHA-256 signed, immutable. |
| 💚 **Health** | System status, row counts, VidyaKosha, stale projects. |

First launch shows an interactive 7-step onboarding tour.

---

## CLI — All Commands

```bash
yantra bootstrap    # 12-question interview covering all sheets
yantra ui [port]    # browser dashboard — auto-opens browser
yantra doctor       # system check: Python, packages, port, ODS integrity
yantra health       # memory stats: loops, inbox, corrections, file size
yantra stats        # memory growth analytics (v2.8)
yantra inbox "text" # quick capture without categorisation
yantra route        # auto-route all unprocessed Inbox items
yantra digest       # daily summary: loops + projects + insights + past memory
yantra telegram     # Telegram bot → Inbox + /loop /task /goal /digest
yantra security     # full Chitrapat security audit
yantra loops        # list all unresolved Open Loops
yantra diff         # belief contradiction check
yantra ttl          # check expired Open Loops past TTL
yantra shortcut     # iOS Shortcut server → Inbox (port 7332)
yantra mail         # Email-to-Inbox SMTP server (port 2525)
yantra migrate      # upgrade older Chitrapat to current schema
yantra schedule     # schedule daily digest via cron/launchd
yantra open         # open Chitrapat in LibreOffice
yantra version      # show version
```

---

## Raksha — Security Engine (v2.4)

Every write scanned before commit. Permissive mode — only confirmed threats blocked.

**Protects against:** Prompt injection · Jailbreak attempts · Agent impersonation · Unicode/RTL attacks · Schema corruption

**Agent trust tiers:**

| Tier | Agents | Treatment |
|---|---|---|
| 5 — User | Human | Never blocked — Dharma-Adesh |
| 4 — Chitragupta | System, LedgerAgent | Full trust |
| 3 — Known | Claude, OpenClaw, LangChain, AutoGen | Standard scan |
| 2 — Unknown | Unregistered agents | Stricter scan |
| 1 — External | Telegram bot, email | Suspicious → confirmed block |
| 0 — Untrusted | Flagged agents | Any non-clean → block |

---

## Mobile Capture — Telegram Bot (v2.3)

```bash
export TELEGRAM_BOT_TOKEN="your_token_from_BotFather"
yantra telegram
```

Any text → Inbox. `/loop`, `/task`, `/goal`, `/health`, `/digest`, `/loops` commands.

---

## Daily Digest (v2.3)

```bash
yantra digest
yantra digest --schedule --time 08:00  # run daily at 8am
```

Surfaces: urgent loops with TTL · stale projects · unrouted inbox · memory insight · "on this day" past memory.

---

## Bootstrap Interview (v2.6)

12-question conversation — covers Identity, Goals, Projects, People, Preferences, Beliefs, Open Loops, Anti-goals, Belief evolution, Reminder preference. Ends with a live preview of populated sheets (the aha moment).

---

## VidyaKosha — Semantic Search (v2.0+, improved v2.8)

```python
oy.search("query", top_k=5)          # all sheets, importance-weighted
oy.search_open_loops("query")        # Anishtha only
oy.search_projects("query")          # Karma only
oy.search_people("query")            # Sambandha only
oy.take_pratibimba()                 # freeze snapshot (multi-agent safety)
oy.release_pratibimba()              # release at session end
```

v2.8: retrieval now weights by `relevance × importance × recency`. High-importance memories surface first.

---

## OpenClaw Integration

```toml
[hooks]
session_start = "openyantra.openclaw.hooks:session_start_hook"
pre_compact   = "openyantra.openclaw.hooks:pre_compact_hook"
post_compact  = "openyantra.openclaw.hooks:post_compact_hook"
session_end   = "openyantra.openclaw.hooks:session_end_hook"

[env]
OPENYANTRA_FILE = "~/openyantra/chitrapat.ods"
```

Full guides for OpenClaw · LangChain · AutoGen · Raw API → [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## How It Compares

| | Flat Text | Vector/RAG | MemGPT | Mem0 | Zep | OpenAI Memory | **OpenYantra** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Human-readable** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **User can edit** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Semantic search** | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| **Compaction-safe** | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **Multi-agent safe** | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Immutable audit trail** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| **Security / injection guard** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Open format (ISO)** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Zero infrastructure** | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ |
| **Browser UI** | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **CLI installer** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Mobile capture** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Daily digest** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Open protocol (CC0)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Version History

| Version | Key additions |
|---|---|
| **v1.0** | Core protocol — Chitragupta pattern, Agrasandhanī, Anishtha, Sanchitta, 12-sheet schema |
| **v2.0** | VidyaKosha semantic index, BM25 + TF-IDF hybrid, Pratibimba snapshots |
| **v2.1** | Inbox sheet, Importance column, TTL loops, admission rules, belief diffing, corrections, browser dashboard, installer |
| **v2.2** | Complete repo — all docs, openclaw/, examples/, references/, DEPLOYMENT.md |
| **v2.3** | Self-contained installer (auto-installs everything), Telegram bot, daily digest, `yantra doctor` |
| **v2.4** | Raksha security — injection scanner, trust tiers, Mudra verification, quarantine |
| **v2.5** | Today tab, Timeline, Conflict Resolver, floating capture, mobile CSS, VISUAL_GUIDE.html |
| **v2.6** | 12-question bootstrap interview, first-launch onboarding tour, brand assets rebuilt |
| **v2.8** | Incremental VidyaKosha sync, importance-weighted retrieval, `yantra stats`, admission refinement |
| **v3.0** *(planned)* | SQLite backend, `.ods` as export view, sub-10ms retrieval, temporal graph queries |

---

## Global Stress-Test — 8 AI Models, 3 Continents, 3 Rounds

Architecture reviewed three times — before v1.0, after v2.0, and after v2.2. All 8 models independently validated Anishtha as the strongest feature. Telegram bot named by 6 of 8 as the mobile capture solution. Daily Digest named by 6 of 8 as the adoption lever.

See [WHITEPAPER.md](WHITEPAPER.md) for the full synthesis.

---

## Inspired by Chitragupta

| Sanskrit | Mythology | OpenYantra |
|---|---|---|
| Chitragupta | Sole trusted recorder | LedgerAgent — only writer |
| Agrasandhanī | Cosmic register | `📒` audit trail |
| Chitrapat | Life scroll | `chitrapat.ods` |
| Anishtha | Unfinished intent (Zeigarnik) | Open Loops — compaction safety |
| VidyaKosha | Knowledge repository | Semantic search engine |
| Raksha | Divine protection | Security engine |
| Mudra | Divine seal | SHA-256 signature |
| Dharma-Adesh | Righteous command | User edits always win |

See [MYTHOLOGY.md](MYTHOLOGY.md) · [WHITEPAPER.md](WHITEPAPER.md) · [VISUAL_GUIDE.html](VISUAL_GUIDE.html)

---

## Regional Compliance

| Profile | Region | Law |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India (home) | DPDP Act 2023, IT Act 2000 |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act, Data Act 2023 |
| **OpenYantra-US** 🇺🇸 | United States | CCPA/CPRA, HIPAA, COPPA |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL, Cybersecurity Law |

---

## File Structure

```
openyantra/
├── openyantra.py             ← Core library v2.8
├── vidyakosha.py             ← Semantic search (VidyaKosha)
├── yantra_ui.py              ← Browser dashboard
├── yantra_security.py        ← Raksha security engine
├── yantra_digest.py          ← Daily proactive digest
├── telegram_bot.py           ← Telegram → Inbox
├── ios_shortcut.py           ← iOS Shortcut → Inbox (HTTP)
├── yantra_mail.py            ← Email-to-Inbox (SMTP)
├── yantra_migrate.py         ← Schema migration tool
├── install.sh                ← Mac/Linux self-contained installer
├── install.ps1               ← Windows self-contained installer
├── chitrapat_template.ods    ← Blank memory file
├── VISUAL_GUIDE.html         ← Interactive architecture diagram
├── WHITEPAPER.md             ← Research document
├── PROTOCOL.md               ← Open spec (CC0)
├── SKILL.md                  ← AI skill definition
├── MYTHOLOGY.md              ← Chitragupta origin
├── PRIVACY.md                ← Regional profiles
├── docs/DEPLOYMENT.md        ← Framework integration guide
├── openclaw/                 ← OpenClaw hooks + plugin
├── examples/                 ← Bootstrap + LangChain adapter
├── references/               ← Controlled vocabulary
└── assets/                   ← Brand assets
```

---

## Contributing

Framework adapters · Mobile capture · Benchmarks · Language ports · v3.0 SQLite backend

Open an issue before a PR for protocol-level changes.

---

## License

Protocol: **CC0 1.0 Universal** (Public Domain)
Library: **MIT License**

---

*Built in Hyderabad, India. Conceived by Revanth — filmmaker and open-source builder.*
*Stress-tested by 8 AI models across 3 continents across 3 rounds.*
*Named in honour of Chitragupta — the Hindu God of Data.*

*The record exists to serve the remembered, not the recorder.*
