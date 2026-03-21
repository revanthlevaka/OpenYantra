# OpenYantra Changelog

All notable changes documented here. Follows semantic versioning.

---

## [3.0.0] -- 2026-03-21

### Breaking changes
- SQLite WAL is now the operational source of truth. ODS file is the human-readable export.
- `chitrapat.ods` is no longer written on every Chitragupta commit. It is exported atomically after each write (async, off hot path).
- Direct ODS editing via LibreOffice now requires `yantra sync` to import changes back into SQLite.
- **Sort Catastrophe warning:** Sorting a single column in LibreOffice scrambles all row data. Never sort -- use `yantra open` + `yantra sync` for manual edits only.

### Added
- `yantra_sqlite.py` -- SyncEngine: SQLite WAL backend with atomic ODS export
  - 2ms writes at any row count (vs 2012ms at 5000 rows in v2.x)
  - Write idempotency via `request_id` dedup check
  - Atomic ODS export: write to `.tmp`, fsync, verify row counts against SQLite, `os.replace()`
  - `PRAGMA wal_checkpoint(TRUNCATE)` after each ODS export
  - portalocker integration: prevents concurrent file corruption
  - `import_ods()`: ingest user edits from LibreOffice back into SQLite (Dharma-Adesh flow)
- `yantra_morning.py` -- Morning Briefing
  - Surfaces open loops (importance >= 7, sorted by TTL urgency)
  - Stale project detection (no update in 7+ days)
  - Proactive suggestion: cross-references inbox items with open loops
  - Streak counter: consecutive days with at least one write
  - Past memory: random goal or belief for reflection
  - Auto-runs on first `yantra` command of the day
- `yantra_context.py` -- Copy Context
  - Formats full memory as clean Markdown block
  - Copies to clipboard automatically (pbcopy / xclip / clip)
  - Works with any web AI: Claude.ai, ChatGPT, Gemini, etc.
  - Selective section export via `--sections` flag
- `yantra sync` CLI command -- import ODS edits back to SQLite
- `yantra corrections` CLI command -- list and apply pending agent corrections
- `yantra morning` CLI command -- run morning brief on demand
- `yantra context` CLI command -- copy context to clipboard

### Changed
- `openyantra.py` VERSION: `2.8` -> `3.0.0`
- All version strings updated throughout codebase
- `build_context_markdown()` method added to `OpenYantra` class
- `morning_brief()` method added to `OpenYantra` class

### Fixed
- All em dashes removed from documentation (v2.13.0 regression cleanup)
- `--ink` token corrected to `#0a0a0b` in all screenshot HTML files
- `--dim` token corrected to `#242228` in all screenshot HTML files
- `docs/docs/visual-guide.html` broken path fixed to `visual-guide.html` in README
- Version badge corrected to current version in README, index.html, SKILL.md
- Domain count corrected to 14 in all public-facing documents
- Removed phantom commands `yantra oracle`, `yantra export` from README
- Duplicate version history entries in README removed
- `index.html` nav Docs link now points to `visual-guide.html`
- `index.html` nav now links to `openyantra-brand-manual.html`

### Architecture (Round 5 stress test, 7 models)
- 7/7 consensus: SQLite WAL as operational backend (ODS as export)
- 7/7 consensus: formal SyncEngine with Vivada conflict rules
- 7/7 consensus: write idempotency via request_id
- 6/7: atomic ODS export pattern
- 5/7: portalocker as core dependency
- 1/1 (GLM5): Sort Catastrophe warning -- critical safety note
- 1/1 (Grok): dashboard reads must come from SQLite, not ODS
- 1/1 (DeepSeek + Grok): VidyaKosha incremental_update reads from SQLite

---

## [2.13.0] -- 2026-03-21

### Added
- `visual-guide.html` -- interactive architecture diagram (dark/light mode)
- `openyantra-brand-manual.html` -- full brand identity and design system
- `assets/brand/` -- SVG logo mark, horizontal logo, minimal mark, favicon
- `assets/screenshots/` -- screenshot HTML files for web UI, CLI, banner

### Fixed
- Token alignment: `--ink #0b0b0c` -> `#0a0a0b`, `--dim #252328` -> `#242228` in index.html
- Em dashes removed from index.html (18), brand-manual.html (41), visual-guide.html (21)
- Version badge in index.html updated to v2.13.0

---

## [2.12.0] -- 2026-03-20

### Added
- `yantra_morning.py` -- Morning Briefing (stub)
- Daily Insight card at top of browser dashboard Today tab
- Streak counter
- iOS Shortcut server (`yantra shortcut`, port 7332)
- Email-to-Inbox SMTP server (`yantra mail`, port 2525)
- `yantra migrate` -- schema migration tool
- `yantra schedule` -- schedule daily digest via cron/launchd
- `yantra context` -- copy context to clipboard (stub)

---

## [2.9.0] -- 2026-03-15

### Added
- Agrasandhanī integrity check (`yantra integrity`)
- Session log archival (`yantra archive`)
- Stats tab in browser dashboard
- 7 UI screenshots

---

## [2.8.0] -- 2026-03-10

### Added
- Incremental VidyaKosha sync (O(1) per write)
- Importance-weighted retrieval (relevance x importance x recency)
- `yantra stats` command
- Admission rule refinement

---

## [2.7.0] -- 2026-03-05

### Added
- Importance-weighted retrieval in VidyaKosha
- `yantra stats` memory growth analytics

---

## [2.6.0] -- 2026-03-01

### Added
- 12-question Bootstrap interview (`yantra bootstrap`)
- First-launch onboarding tour in browser dashboard
- Brand assets rebuilt

---

## [2.5.0] -- 2026-02-20

### Added
- Today tab with one-click actions
- Timeline tab (chronological activity feed)
- Conflict Resolver tab (visual diff)
- Floating capture button (keyboard shortcut `i`)
- Mobile-responsive CSS

---

## [2.4.0] -- 2026-02-10

### Added
- Raksha security engine (`yantra_security.py`)
- Prompt injection scanner (confirmed patterns blocked)
- Agent trust tiers 0-5
- Mudra signature verification
- Quarantine sheet for blocked writes
- VidyaKosha poisoning detection
- `yantra security` command

---

## [2.3.0] -- 2026-02-01

### Added
- Self-contained installer (`install.sh` / `install.ps1`)
  - Auto-installs Python, LibreOffice, all deps
  - Creates venv, CLI, desktop shortcut
- Telegram bot (`telegram_bot.py`)
- Daily digest (`yantra_digest.py`)
- `yantra doctor` system health check

---

## [2.2.0] -- 2026-01-25

### Added
- Complete repo restored: all docs, openclaw/, examples/, references/
- `docs/DEPLOYMENT.md` -- framework integration guide
- LangChain adapter (`examples/langchain_adapter.py`)

---

## [2.1.0] -- 2026-01-15

### Added
- `📥 Inbox` sheet (Avagraha) -- quick capture without categorisation
- `✏️ Corrections` sheet (Sanshodhan) -- agent-proposed edits
- Importance column (1-10) on all sheets
- TTL_Days column on Open Loops
- Admission rules (filter noise writes)
- Belief diffing (contradiction detection)
- `memory_correction()` -- agent proposes, user approves
- Dead man's switch -- alert if Chitragupta silent > N minutes
- `route_inbox()` -- keyword-based routing
- Browser dashboard (`yantra ui`)
- Bootstrap interview (6 questions)

---

## [2.0.0] -- 2026-01-01

### Added
- VidyaKosha sidecar semantic index
- BM25 keyword index
- TF-IDF + SVD embedder (zero extra deps)
- FAISS vector index
- Hybrid retrieval: alpha x vector + (1-alpha) x BM25
- Pratibimba per-agent frozen snapshots
- `oy.search()`, `oy.search_open_loops()`, `oy.search_projects()`, `oy.search_people()`
- `oy.take_pratibimba()`, `oy.release_pratibimba()`

---

## [1.0.0] -- 2025-12-01

### Added
- Core Chitragupta pattern: single-writer LedgerAgent
- Agrasandhanī audit trail (SHA-256 signed, append-only)
- 12-sheet schema: Identity, Goals, Projects, People, Preferences, Beliefs, Tasks, Open Loops, Session Log, Agent Config, Ledger, INDEX
- WriteRequest (Karma-Lekha)
- WriteQueue / Sanchitta (crash-safe JSON queue)
- Vivada conflict detection and escalation
- Dharma-Adesh: user edits always win
- Controlled vocabulary enforcement
- `build_system_prompt_block()` -- Smarana session load
- `flush_open_loop()` -- Zeigarnik Effect implementation
- MYTHOLOGY.md, WHITEPAPER.md, PROTOCOL.md, SKILL.md
- MIT + CC0 dual license
