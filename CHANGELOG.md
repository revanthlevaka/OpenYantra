# Changelog

All notable changes to OpenYantra are documented in this file.

Versioning: [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

---

## [v0.2.0] — 2026-03-17

### Added
- `assets/logo-mark.svg` — canonical full-detail vector logo mark (brand manual §02 compliant)
  - 3 concentric rings (outer r=47, mid r=33, inner r=18)
  - 4 cardinal satellite nodes: N=#1c6fff, E=#5535e0, S=#e84520, W=#f5a000
  - 4 cardinal + 4 diagonal petal arcs (mandala geometry)
  - Full gradient fill center core (#1c6fff → #5535e0 → #e84520 → #f5a000)
- `assets/logo-mark-minimal.svg` — 32px scale-optimised mark (outer + mid ring, 4 nodes, arcs, dot)
- `assets/favicon.svg` — 16px favicon (outer ring + 4 cardinal nodes + center dot only)
- `assets/logo-horizontal.svg` — horizontal wordmark lockup (mark + "OpenYantra" in IBM Plex Mono + tagline)
- `CHANGELOG.md` — this file; establishes unified versioning history

### Changed
- Unified versioning across all files to `v0.2.0`
- Brand manual (`openyantra-brand-manual.html`) sidebar footer version string bumped from `v0.1.0-alpha` → `v0.2.0`
- `README.md` updated to note `visual-guide.html` is superseded by the brand manual

### Deprecated
- `visual-guide.html` — early visual guide, now fully superseded by `openyantra-brand-manual.html`
  Retained for historical reference; do not use for brand decisions

### Notes
- First formal versioned release under unified version scheme
- All future SVG assets must be derived from `assets/logo-mark.svg` as the single source of truth
- PNG raster exports (`icon_192.png`, `icon_512.png`, `logo_horizontal.png`, `og_card.png`, `banner_github.png`)
  should be re-exported from the new SVG sources at next opportunity

---

## [v0.1.0-alpha] — 2025 (initial)

### Added
- `openyantra.py` — core memory system (Chitrapat.ods writer, BM25 search, single-writer rule)
- `vidyakosha.py` — semantic search and knowledge layer
- `yantra_security.py` — SHA-256 integrity signing for memory records
- `yantra_migrate.py` — schema migration tooling
- `yantra_digest.py` — daily digest and report generation
- `yantra_ui.py` — local web UI server (yantra ui, localhost:7432)
- `telegram_bot.py` — Telegram quick-capture integration
- `ios_shortcut.py` — iOS Shortcuts integration for mobile capture
- `install.sh` / `install.ps1` — cross-platform installers (Linux/macOS + Windows)
- `index.html` — project landing page
- `openyantra-brand-manual.html` — full brand identity & design manual (11 chapters)
- `visual-guide.html` — early visual reference (now superseded)
- `chitrapat_template.ods` — blank memory file template
- `PROTOCOL.md` — agent communication and single-writer protocol specification
- `WHITEPAPER.md` — system architecture and philosophy whitepaper
- `MYTHOLOGY.md` — naming mythology and Sanskrit conceptual reference
- `PRIVACY.md` — privacy model and data handling principles
- `SKILL.md` — AI skill/agent integration guide
- `assets/` — raster brand assets (PNG icons, banners, OG card)
- `openclaw/` — OpenClaw memory persistence module
- `docs/` — extended documentation
- `examples/` — usage examples and integration templates
- `references/` — external reference materials

---

*OpenYantra is MIT licensed. Personal Cognition Ledger.*
*Built on one principle: the human is always in control.*
