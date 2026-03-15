<p align="center">
  <img src="assets/logo_horizontal.png" alt="OpenYantra" width="620"/>
</p>

<h1 align="center">OpenYantra</h1>
<h3 align="center">The Sacred Memory Machine</h3>
<h4 align="center"><em>यन्त्र — Inspired by Chitragupta, the Hindu God of Data</em></h4>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.9-saffron?style=flat-square&color=FF9933" />
  <img src="https://img.shields.io/badge/Protocol-CC0%201.0-gold?style=flat-square&color=D4AF37" />
  <img src="https://img.shields.io/badge/Library-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Format-.ods%20ISO%2FIEC%2026300-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/UI-Browser%20Dashboard-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Install-One%20Command-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/Security-Raksha%20Engine-red?style=flat-square&color=DC143C" />
</p>

<p align="center">
  <strong>Your personal AI agents remember nothing between sessions. OpenYantra fixes that.</strong><br/>
  One open-standard file. One trusted writer. Any agent. Any framework. Zero cloud.
</p>

---

<p align="center">
  <img src="assets/banner_github.png" alt="OpenYantra Banner" width="100%"/>
</p>

---

## The Problem — Why Your AI Forgets

Every time you open a new chat with Claude, ChatGPT, or any AI agent — it starts completely blank. It doesn't know your current projects, your decisions from last week, or what you left unfinished yesterday. You repeat yourself every single session.

And when the conversation gets too long, the AI compresses older messages into a summary — your active work context disappears mid-task.

**OpenYantra solves this permanently:**

| Without OpenYantra | With OpenYantra |
|---|---|
| AI starts blank every session | AI knows your projects, goals, preferences |
| Repeat your context every time | Context injected automatically at session start |
| Unfinished work disappears in compaction | Open Loops flushed before compaction, restored after |
| No record of what agents changed | Every write SHA-256 signed, permanent audit trail |
| Agents can overwrite each other | Single trusted writer (Chitragupta) — no conflicts |
| Memory lives in a cloud you don't control | Memory lives in a file on your computer |

---

## What is OpenYantra?

OpenYantra is a **personal AI memory system** — a structured file that your AI agents can read from and write to, so your context persists across sessions, across agents, and across time.

It is:
- **Local-first** — your memory file lives on your machine, never in a cloud
- **Human-readable** — open it in LibreOffice, read it, edit it like a spreadsheet
- **Agent-agnostic** — works with Claude, ChatGPT, OpenClaw, LangChain, AutoGen
- **Auditable** — every write signed with SHA-256, permanent audit trail
- **Protected** — Raksha security engine blocks prompt injection attempts

The project is inspired by **Chitragupta** (चित्रगुप्त) — the Hindu God of Data, divine scribe who keeps the complete record of every soul's deeds across time. The architecture mirrors the mythology precisely: one trusted recorder, one immutable ledger, and a rule that the user's word (Dharma-Adesh) always overrides everything else.

> *"Your purpose is to stay in the minds of all people and record their thoughts and deeds."*
> — Brahma to Chitragupta

---

## Install in One Command

**Mac / Linux** — fully self-contained installer. Installs Python, LibreOffice, all dependencies, creates a virtual environment, sets up the CLI, adds a desktop shortcut, and opens the browser dashboard automatically:

```bash
curl -sSL https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/revanthlevaka/OpenYantra/main/install.ps1 | iex
```

After install:
```bash
yantra bootstrap    # 12-question interview — sets up your memory
yantra ui           # opens http://localhost:7331
```

That's it. No API keys required. No cloud account. No configuration files.

---

## How It Works — In Plain English

When you run `yantra bootstrap`, OpenYantra asks you 12 questions — your name, your projects, your goals, the people you work with, what your AI should never suggest. The answers populate your **Chitrapat** (memory file) — a `.ods` spreadsheet you can open in LibreOffice at any time.

When you start an AI session, OpenYantra injects a context block into the system prompt:

```
[OPENYANTRA CONTEXT — v2.9]
User: Revanth | Filmmaker | Hyderabad, IN
Active Projects: Feature Screenplay → Write act 2 | OpenYantra → ship v2.9
Open Loops: [High] 3-act vs 5-act — undecided | [Medium] Follow up with Priya
Goals: Complete debut feature film
```

Your AI agent now knows who you are, what you're working on, and what's unresolved — without you saying a word.

During the session, your agent writes new memories back through **Chitragupta (LedgerAgent)** — the sole trusted writer. Every write is validated, security-scanned, and signed before it touches the file. Nothing slips through unaudited.

---

## The 14-Sheet Memory File

<p align="center">
  <img src="screenshots/screenshot_today.png" alt="Today Tab" width="100%"/>
  <em>The Today tab — your daily command centre. Resolve open loops, complete tasks, route inbox captures, all with one click.</em>
</p>

Your memory is organised across 14 domain-separated sheets:

| Sheet | Sanskrit | What it stores |
|---|---|---|
| 👤 **Identity** | Svarupa | Name, occupation, location, timezone, communication style |
| 🎯 **Goals** | Sankalpa | Long and short-term aims with priority and deadlines |
| 🚀 **Projects** | Karma | Active work — domain, status, next concrete step |
| 👥 **People** | Sambandha | Relationships, context, sentiment, last mentioned |
| 💡 **Preferences** | Ruchi | Tools, habits, communication style, anti-goals |
| 🧠 **Beliefs** | Vishwas | Values, worldview, belief evolution history |
| ✅ **Tasks** | Kartavya | Action items with project link and priority |
| 🔓 **Open Loops** ★ | Anishtha | Unresolved threads — compaction safety net |
| 📅 **Session Log** | Dinacharya | Per-session summaries with topics and decisions |
| ⚙️ **Agent Config** | Niyama | Per-agent instructions and preferences |
| 📒 **Agrasandhanī** | — | Immutable audit trail — every write SHA-256 signed |
| 📥 **Inbox** | Avagraha | Quick capture — categorise later |
| ✏️ **Corrections** | Sanshodhan | Agent-proposed edits pending your approval |
| 🔒 **Quarantine** | Nirodh | Blocked injection attempts for your review |

**★ Open Loops (Anishtha)** is the strongest feature — validated unanimously by 8 AI models across 3 continents. It captures unresolved threads before your context window compresses them, and re-injects them after. Implements the **Zeigarnik Effect** as a data structure.

---

## The Browser Dashboard

```bash
yantra ui   # → http://localhost:7331
```

<p align="center">
  <img src="screenshots/screenshot_loops.png" alt="Open Loops Tab" width="100%"/>
  <em>Open Loops tab — all unresolved Anishtha threads with priority and TTL countdown.</em>
</p>

<p align="center">
  <img src="screenshots/screenshot_timeline.png" alt="Timeline Tab" width="100%"/>
  <em>Timeline tab — chronological activity feed of every write Chitragupta has made.</em>
</p>

The dashboard has 12 tabs:

| Tab | Purpose |
|---|---|
| 🌅 **Today** | Daily command centre — urgent items with one-click resolve/complete |
| 📥 **Inbox** | Unrouted captures — press `i` anywhere to capture instantly |
| 🚀 **Projects** | Active work with status, priority, next step |
| 🔓 **Open Loops** | All unresolved threads sorted by importance |
| ✅ **Tasks** | Pending action items |
| 📅 **Timeline** | Chronological activity feed |
| ⚡ **Conflicts** | Visual diff — agent proposed vs your value. You decide. |
| ✏️ **Corrections** | Agent-proposed edits pending approval |
| 🔒 **Security** | Quarantine review and threat log |
| 📒 **Ledger** | Full SHA-256 signed audit trail |
| 💚 **Health** | System status and row counts |
| 📊 **Stats** | Memory growth analytics |

First launch shows a 7-step interactive onboarding tour.

---

## Security — Raksha Engine

<p align="center">
  <img src="screenshots/screenshot_security.png" alt="Security Tab" width="100%"/>
  <em>Security tab — quarantine review, threat log, and agent trust tiers.</em>
</p>

Every write to your memory is scanned by **Raksha** (रक्षा — Protection) before Chitragupta commits it:

```
Confirmed threats  → Blocked + Quarantine sheet (you review in dashboard)
Suspicious writes  → Warned + Security Log + allowed (permissive mode)
Clean writes       → Pass through normally
Your edits         → Always bypass — you are sovereign (Dharma-Adesh)
```

**Protects against:** prompt injection · jailbreak attempts (DAN, STAN) · agent impersonation · Unicode/RTL attacks · schema corruption

**Agent trust tiers** — the less trusted the source, the stricter the scan:

| Tier | Who | Treatment |
|---|---|---|
| 5 | You | Never blocked — Dharma-Adesh |
| 4 | Chitragupta / System | Full trust |
| 3 | Claude, OpenClaw, LangChain | Standard scan |
| 2 | Unknown agents | Stricter scan |
| 1 | Telegram bot, email, iOS | Suspicious → confirmed block |
| 0 | Untrusted (flagged) | Any flag → block |

---

## Mobile Capture

**Telegram bot** — the simplest daily capture:
```bash
export TELEGRAM_BOT_TOKEN="your_token_from_BotFather"
yantra telegram
# Any message → Inbox. /loop /task /goal /digest /health commands.
```

**iOS Shortcut** — home screen widget:
```bash
yantra shortcut
# Prints your Mac's IP + exact Shortcut setup instructions
# iPhone Share Sheet or home screen tap → captured to Inbox
```

**Email** — forward anything:
```bash
yantra mail
# Local SMTP on port 2525
# Forward emails → Subject + body → Inbox
```

---

## Bootstrap Interview

<p align="center">
  <img src="screenshots/screenshot_bootstrap.png" alt="Bootstrap Interview" width="100%"/>
  <em>The 12-question bootstrap interview — populates all key sheets via conversation, not empty forms.</em>
</p>

```bash
yantra bootstrap
```

No empty spreadsheets. No database configuration. A 5-minute conversation that asks:

1. What does your AI always forget?
2. Your name, occupation, location
3. Life domains (career, health, creative work...)
4. Active projects + next concrete step
5. Goals + how you'll measure success
6. Important people + open thread with each
7. Preferences, tools, working hours
8. Anti-goals — what AI should never suggest
9. Decision principles + belief evolution
10. Current second-guessing + recurring problems
11. Reminder preference (morning digest / Telegram / dashboard)
12. Live preview of all populated sheets ← the aha moment

---

## Daily Digest

```bash
yantra digest        # run now
yantra schedule      # run automatically every morning at 08:00
```

Every morning, OpenYantra surfaces what matters:

```
🌅 OpenYantra Daily Digest

🔓 Open Loops needing attention:
   • [High] Decide screenplay structure (TTL: 3 days left)
   • [Medium] Follow up with Priya on budget (TTL: 8 days left)

🚀 Stale Projects — no update in 7+ days:
   • Feature Screenplay → Write act 2

📥 Inbox: 2 items awaiting routing

💡 Memory Insight: You've mentioned "screenplay structure" 4 times this week

🕰️ On this day: "Creative freedom over short-term money" (from Beliefs)
```

---

## Memory Analytics — `yantra stats`

<p align="center">
  <img src="screenshots/screenshot_stats.png" alt="Stats Tab" width="100%"/>
  <em>Stats tab — memory growth analytics, writes by sheet and agent, loop resolution rate.</em>
</p>

```bash
yantra stats
```

Shows: total rows · total writes · writes last 7 / 30 days · open loops · loop resolution rate · high-importance items · writes by agent · writes by sheet · file size.

---

## Quick Start (Python)

```python
from openyantra import OpenYantra

# Initialise (loads existing memory, replays any crashed writes)
oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")

# Inject into system prompt — your AI now knows your full context
system_prompt = oy.build_system_prompt_block()

# Write new memories via Chitragupta
oy.add_project("My Film", domain="Creative", status="Active",
               priority="High", next_step="Write act 2", importance=9)

# Flush before context compaction
oy.flush_open_loop("Structure decision", "3-act vs 5-act undecided",
                   priority="High", ttl_days=30)

# Quick capture
oy.inbox("Priya mentioned budget revision needed by Friday")

# Semantic search — importance-weighted results (v2.7)
results = oy.search("screenplay structure")

# Session end
oy.log_session(topics=["screenplay"], decisions=["Research 5-act"])
```

---

## All CLI Commands

```bash
# Setup
yantra bootstrap    # 12-question interview — first-time setup
yantra doctor       # system check: Python, packages, port, ODS integrity

# Daily use
yantra ui [port]    # browser dashboard → auto-opens http://localhost:7331
yantra inbox "text" # quick capture to Inbox
yantra digest       # daily summary: loops + stale projects + insights
yantra stats        # memory growth analytics

# Memory management
yantra health       # stats: loops, inbox, corrections, file size
yantra route        # auto-route all unprocessed Inbox items
yantra loops        # list all unresolved Open Loops
yantra diff         # belief contradiction check
yantra ttl          # check expired Open Loops past TTL

# Mobile + integrations
yantra telegram     # Telegram bot → Inbox
yantra shortcut     # iOS Shortcut server (port 7332)
yantra mail         # Email-to-Inbox SMTP server (port 2525)
yantra schedule     # schedule daily digest (launchd/cron)

# Maintenance
yantra integrity    # verify Agrasandhani SHA-256 signatures
yantra archive      # rotate old session logs to archive file
yantra migrate      # upgrade older Chitrapat to current schema
yantra security     # full Chitrapat security audit
yantra open         # open Chitrapat in LibreOffice
yantra version      # show version
```

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

Full guides for OpenClaw · LangChain · AutoGen · Raw Anthropic API → [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## How It Compares

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
| Browser UI | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| CLI installer | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Mobile capture | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Daily digest | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Schema migration | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Open protocol (CC0) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Version History

| Version | Key additions |
|---|---|
| **v1.0** | Core protocol — Chitragupta pattern, Agrasandhanī, Anishtha, Sanchitta, 12-sheet schema |
| **v2.0** | VidyaKosha semantic index, BM25 + TF-IDF hybrid, Pratibimba snapshots |
| **v2.1** | Inbox sheet, Importance column, TTL loops, admission rules, belief diffing, browser dashboard, installer |
| **v2.2** | Complete repo — all docs, openclaw/, examples/, references/, DEPLOYMENT.md |
| **v2.3** | Self-contained installer (auto Python + LibreOffice), Telegram bot, daily digest, `yantra doctor` |
| **v2.4** | Raksha security — injection scanner, agent trust tiers, Mudra verification, quarantine |
| **v2.5** | Today tab, Timeline, Conflict Resolver, floating capture button, mobile CSS, VISUAL_GUIDE.html |
| **v2.6** | 12-question bootstrap interview, first-launch onboarding tour, brand assets rebuilt |
| **v2.7** | Importance-weighted search (relevance × importance × recency), `yantra stats` |
| **v2.8** | iOS Shortcut server, email-to-inbox SMTP, `yantra migrate` schema upgrade, scheduled digest |
| **v2.9** | Agrasandhanī integrity check, session log archival, partial ODS reads, Stats dashboard tab |
| **v3.0** *(planned)* | SQLite backend, `.ods` as export view, sub-10ms retrieval, temporal graph queries |

---

## Global Stress-Test — 8 AI Models, 3 Continents, 3 Rounds

Architecture reviewed three times — before v1.0, after v2.0, and after v2.2.

**Universal consensus across all 3 rounds:**
- Anishtha (Open Loops) — strongest feature, unique in the space
- Telegram bot — the right mobile capture solution (6 of 8 models named it specifically)
- Daily Digest — the adoption lever (6 of 8 models named it)
- Architecture is sound — risk is now behavioral adoption, not technical

See [WHITEPAPER.md](WHITEPAPER.md) for the full synthesis including model-by-model breakdown.

---

## Inspired by Chitragupta

The architecture is not metaphor — it is mythology implemented as software:

| Sanskrit | Mythology | OpenYantra |
|---|---|---|
| Chitragupta | Sole trusted recorder of all deeds | LedgerAgent — only writer to the memory file |
| Agrasandhanī | Cosmic register — complete and immutable | `📒` audit trail — SHA-256 signed, append-only |
| Chitrapat | The life scroll — a person's complete record | `chitrapat.ods` — your memory file |
| Anishtha | Unfinished intent (Zeigarnik Effect) | Open Loops — compaction safety net |
| Mudra | Divine seal of authenticity | SHA-256 signature on every write |
| Dharma-Adesh | The righteous command that cannot be overruled | Your edits always override agent writes |
| Raksha | Divine protection — armour | Security engine — injection scanner |
| VidyaKosha | Repository of all knowledge | Sidecar semantic index |

See [MYTHOLOGY.md](MYTHOLOGY.md) · [WHITEPAPER.md](WHITEPAPER.md) · [VISUAL_GUIDE.html](VISUAL_GUIDE.html)

---

## Regional Compliance

| Profile | Region | Laws |
|---|---|---|
| **OpenYantra-IN** 🇮🇳 | India (home) | DPDP Act 2023, IT Act 2000 |
| **OpenYantra-EU** 🇪🇺 | Europe | GDPR, EU AI Act, Data Act 2023 |
| **OpenYantra-US** 🇺🇸 | United States | CCPA/CPRA, HIPAA, COPPA |
| **OpenYantra-CN** 🇨🇳 | China | PIPL, DSL, Cybersecurity Law |

---

## File Structure

```
openyantra/
├── openyantra.py             ← Core library v2.9
├── vidyakosha.py             ← Semantic search engine
├── yantra_ui.py              ← Browser dashboard (12 tabs)
├── yantra_security.py        ← Raksha security engine
├── yantra_digest.py          ← Daily proactive digest
├── telegram_bot.py           ← Telegram → Inbox
├── ios_shortcut.py           ← iOS Shortcut → Inbox
├── yantra_mail.py            ← Email → Inbox (SMTP)
├── yantra_migrate.py         ← Schema migration tool
├── install.sh                ← Mac/Linux self-contained installer
├── install.ps1               ← Windows self-contained installer
├── chitrapat_template.ods    ← Blank memory file
├── VISUAL_GUIDE.html         ← Interactive architecture diagram
├── WHITEPAPER.md             ← Research document
├── PROTOCOL.md               ← Open spec (CC0)
├── SKILL.md                  ← AI skill definition
├── MYTHOLOGY.md              ← Chitragupta origin + Sanskrit naming
├── PRIVACY.md                ← Regional profiles (IN · EU · US · CN)
├── screenshots/              ← UI screenshots
├── docs/DEPLOYMENT.md        ← Framework integration guide
├── openclaw/                 ← OpenClaw plugin + hooks
├── examples/                 ← Quickstart + LangChain adapter
├── references/               ← Controlled vocabulary
└── assets/                   ← Brand assets
```

---

## Contributing

- Framework adapters — CrewAI, Semantic Kernel, Spring AI
- Mobile capture improvements — Android widget, email rules
- Benchmarks — LOCOMO / DMR evaluation suite
- Language ports — TypeScript, Rust, Go
- v3.0 SQLite backend — contributions welcome

Open an issue before a PR for protocol-level changes.

---

## License

Protocol Specification: **CC0 1.0 Universal** (Public Domain)
Library: **MIT License**

---

*Built in Hyderabad, India. Conceived by Revanth — filmmaker and open-source builder.*
*Stress-tested by 8 AI models across 3 continents across 3 rounds.*
*Named in honour of Chitragupta — the Hindu God of Data.*

*The record exists to serve the remembered, not the recorder.*
