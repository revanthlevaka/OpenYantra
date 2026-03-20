# OpenYantra Changelog

All versions use the `v2.x` scheme.

---

## v2.12 -- Oracle, Export, Doc Debt (2026-03-21)

### New Features
- `oracle()` / `oracle_text()` -- read-only cross-reference engine. Surfaces
  non-obvious connections: Inbox items matching open loops, tasks blocked by
  same-project loops, belief contradictions, stale projects, missing People
  records, loops aging past 50% TTL, orphan tasks linked to closed projects.
- `export()` -- full memory export to Markdown or JSON with sheet filter,
  date filter (`--since`), and file output (`--output`).
- `yantra oracle` and `yantra export` CLI commands.
- `/api/oracle` and `/api/export` endpoints in `yantra_ui.py`.
- Oracle-card wired into Today tab of Briefing Room dashboard.
- Oracle auto-runs as last section of `morning_brief()` terminal output.

### Version Consistency Fixes
- All files unified to version string `2.12`:
  `openyantra.py`, `yantra_ui.py`, `yantra_security.py`, `yantra_digest.py`,
  `yantra_migrate.py`, `ios_shortcut.py`, `telegram_bot.py`, `install.sh`,
  `install.ps1`.
- `SKILL.md` completely rewritten from stale v2.5 content to v2.12.
- `CHANGELOG.md` unified from dual `v0.2.0` / `v2.11` scheme to single `v2.x`.

### Schema / Migration
- `yantra_migrate.py` now detects v2.9+ schema and adds v2.12 migration step.

### Architecture Note -- v3.0 Storage
- `.ods` remains the canonical human-readable file. Non-negotiable.
- v3.0 will add SQLite as the operational write path, syncing bidirectionally
  with `.ods`. Both files will always exist alongside each other.
- `yantra sync` and `yantra sync --watch` commands planned for v3.0.

---

## v2.11 -- v3 Briefing Room, SVG Assets (2026-03-17)

- `UI/v3/dashboard.html` -- new Briefing Room with 7 tabs:
  Today, Inbox, Loops, Projects, Timeline, Review, System.
- `yantra_ui.py` now serves `dashboard.html` via `FileResponse`.
- Oracle-card DOM hook added to Today tab (placeholder, wired in v2.12).
- All brand assets migrated to SVG (replaced PNG files).
- `yantra_mail.py` permanently removed -- email/SMTP capture discontinued.
- `CHANGELOG.md` introduced.

---

## v2.10 -- Morning Brief, Copy Context, Streak Counter (2026-03-10)

- `morning_brief()` / `morning_brief_auto()` -- daily summary with streak counter.
- `build_context_markdown()` / `copy_context()` -- one-click context for any AI chat.
- `yantra morning` and `yantra context` CLI commands.
- Stats tab added to Briefing Room.
- `/api/morning`, `/api/context/markdown`, `/api/context/copy` endpoints.
- `yantra integrity` -- Agrasandhanī signature verification.
- `yantra archive` -- rotate old session logs.

---

## v2.9 -- Integrity Check, Stats Analytics (2026-03-03)

- `yantra integrity` -- verify all SHA-256 Mudra signatures in Agrasandhanī.
- `stats()` method -- memory growth analytics: row counts, writes by agent,
  writes by sheet, loop resolution rate, high-importance items.
- `yantra stats` CLI command.
- `_fast_read_sheet()` -- selective column reads for large sheets.

---

## v2.8 -- VidyaKosha Importance Weighting (2026-02-20)

- VidyaKosha retrieval: `score = relevance × importance × recency`.
- Incremental index sync: O(1) per write, replaces full rebuild.
- `yantra stats` analytics preview.
- Admission rules refined: Importance < 2 filtered.

---

## v2.7 -- VidyaKosha Incremental Sync (2026-02-10)

- O(1) incremental VidyaKosha update per Chitragupta commit.
- `importance_weight` parameter on `search()`.
- Recency decay in retrieval scoring.

---

## v2.6 -- Bootstrap Interview + Onboarding Tour (2026-01-28)

- 12-question bootstrap interview (progress bar, sheet preview after).
- First-launch onboarding tour in dashboard.
- Anti-goals, belief evolution, decision principles added to interview.

---

## v2.5 -- Dashboard Completeness (2026-01-15)

- Today tab, Timeline tab, Conflict Resolver tab.
- Floating quick-capture button (keyboard shortcut `i`).
- Mobile-responsive CSS.
- `VISUAL_GUIDE.html` added.

---

## v2.4 -- Raksha Security Engine (2026-01-05)

- `yantra_security.py` -- injection scanner, trust tiers (0-5), Mudra verification.
- Quarantine sheet (🔒 Nirodh) for blocked writes.
- Security Log sheet (🛡️ Security Log).
- `yantra security` CLI command.
- VidyaKosha poisoning detection via embedding norm outlier analysis.

---

## v2.3 -- Self-Contained Installer + Telegram Bot (2025-12-18)

- `install.sh` / `install.ps1` -- fully self-contained: auto-installs Python,
  LibreOffice, all deps, creates virtual environment, CLI, desktop shortcut.
- `telegram_bot.py` -- Telegram bot: any message to Inbox, `/loop`, `/task`,
  `/goal`, `/health`, `/loops`, `/digest` commands.
- `yantra_digest.py` -- daily proactive digest.
- `yantra doctor` -- system health check.

---

## v2.2 -- Complete Repository (2025-12-05)

- All docs restored: `openclaw/`, `examples/`, `references/`, `docs/DEPLOYMENT.md`.
- `PROTOCOL.md`, `MYTHOLOGY.md`, `WHITEPAPER.md`.

---

## v2.1 -- Inbox, Importance, Browser Dashboard (2025-11-20)

- 📥 Inbox sheet (Avagraha) -- quick capture without forced categorisation.
- Importance 1-10 column on all sheets.
- TTL_Days on Open Loops.
- Admission rules -- filter noise writes before commit.
- Belief diffing -- contradiction detection.
- ✏️ Corrections sheet -- agent-proposed edits for user approval.
- Browser dashboard (`yantra_ui.py`) -- Today, Inbox, Loops, Conflicts, Health.
- `install.sh` first version.

---

## v2.0 -- VidyaKosha Semantic Search (2025-11-01)

- `vidyakosha.py` -- BM25 + TF-IDF hybrid semantic index sidecar.
- FAISS vector index, per-agent Pratibimba snapshots.
- `oy.search()`, `oy.search_open_loops()`, `oy.search_projects()`.

---

## v1.0 -- Core Protocol (2025-10-15)

- Chitragupta/LedgerAgent -- single trusted writer pattern.
- `chitrapat.ods` -- 12-sheet ODS memory file.
- WriteRequest, WriteQueue (Sanchitta), SHA-256 Mudra sealing.
- Agrasandhanī -- immutable append-only audit trail.
- Anishtha (Open Loops) -- Zeigarnik Effect as data structure.
- Conflict resolution (Vivada) -- Dharma-Adesh user override.
- `MYTHOLOGY.md` -- Chitragupta origin and Sanskrit naming system.

---

*Protocol: CC0 1.0 Universal · Library: MIT*
*github.com/revanthlevaka/OpenYantra*
