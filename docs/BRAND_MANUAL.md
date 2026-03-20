# OpenYantra Brand Manual v2.12

> Design system for OpenYantra -- The Sacred Memory Machine
> DNA: Teenage Engineering + Sarvam AI

---

## Core Identity

**Mission:** A personal AI memory system where the human is always in control.
**Voice:** Technical, direct, human, transparent.
**DNA Source 1 (Teenage Engineering):** Utilitarian grid. Exposed structure. Bold flat single-function colors. Monospaced type. Every element serves a purpose.
**DNA Source 2 (Sarvam AI):** Blue-to-orange spectrum as continuous gradient. Mandala-derived geometry. Grounded in Indian design heritage.

---

## Logo System

All logo files are in `assets/`. Available formats: SVG (primary) and PNG (fallback).

| File | Use |
|---|---|
| `logo_horizontal.svg` | Primary lockup -- mark + wordmark |
| `icon_512.svg` | App icon, large |
| `icon_192.svg` | App icon, small |
| `og_card.svg` | Social / OG card (1200x630) |
| `banner_github.svg` | GitHub README banner (1280x400) |

### Mark Anatomy

The mark is a mandala-derived geometric symbol. Every element encodes architecture:

- **Outer ring** -- boundary of memory
- **Mid ring** -- Chitragupta write boundary
- **4 cardinal nodes** -- N/E/S/W, each one gradient stop color
- **8 petal arcs** -- domain sheets radiating from center
- **Center core** -- `chitrapat.ods`, where all arcs converge

### Logo Variants

| Variant | Background | Use |
|---|---|---|
| A -- Gradient Dark | Dark (#0b0b0c) | Primary -- always use this first |
| B -- Flat Blue | Dark | Single-color contexts |
| C -- Amber | Dark | Warm accent contexts |
| D -- Mark only | Any dark | Favicon, icon, avatar |
| E -- Gradient Light | Light (#efece5) | Light backgrounds |
| F -- Mono White | Photo / complex | Overlaid on imagery |

### Scale Rules

- 128px+ : full detail, all rings, all arcs
- 64px : reduce inner ring opacity, keep arcs
- 32px : outer ring + nodes only, larger core
- 16px (favicon) : outer ring + 4 nodes + core, no arcs

### Clearspace

Minimum clearspace = diameter of one cardinal node dot on all sides.

### Never

- Rotate the mark (cardinal nodes have directional meaning)
- Recolor individual elements (gradient must stay intact)
- Add shadows or glows to the wordmark
- Place gradient variant on a similarly colored background
- Use below 16px without the simplified favicon version

---

## Color System

### Accent Colors (5 tokens)

| Name | Hex | Role |
|---|---|---|
| Yantra Blue | `#1C6FFF` | Primary interactive, nav active |
| Chitragupta Indigo | `#5535E0` | Write operations, hash values |
| Ledger Coral | `#E84520` | CLI prompt `$`, error states |
| Sanchitta Amber | `#F5A000` | CLI command token, queue states |
| Vidya Green | `#1AA167` | Status OK, success, health |

### Gradient (Primary)

```
linear-gradient(135deg, #1C6FFF 0%, #5535E0 32%, #E84520 66%, #f5a000 100%)
```

Used on: logo mark, primary CTAs, chapter top bars, oracle-card accent. Always 4-stop, always these exact colors.

### Surface Colors (Dark Mode)

| Name | Hex | Use |
|---|---|---|
| Ink | `#0B0B0C` | Page background |
| Surface | `#111113` | Cards, panels |
| Surface 2 | `#161618` | Hover states |
| Dim | `#242228` | Borders, rules |
| Muted | `#524F58` | Labels, metadata |
| Parchment | `#E8E5DE` | Body text |

### Usage Map

| Context | Blue | Indigo | Coral | Amber | Green |
|---|---|---|---|---|---|
| Logo mark | yes | yes | yes | yes | no |
| CLI prompt `$` | no | no | yes | no | no |
| CLI command token | no | no | no | yes | no |
| CLI arg / path | yes | no | no | no | no |
| CLI hash / ID | no | yes | no | no | no |
| CLI success | no | no | no | no | yes |
| CLI error | no | no | yes | no | no |
| Primary CTA | yes | yes | yes | yes | no |
| Health / OK | no | no | no | no | yes |
| WriteQueue | no | no | no | yes | no |
| Open Loops | yes | no | no | no | no |

---

## Typography

Two fonts only. No exceptions.

**IBM Plex Mono** -- headings, UI, labels, code, interactive elements, all terminal output.
**IBM Plex Sans 300** -- body copy and longer descriptive text only.

Import:
```
https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;0,600&family=IBM+Plex+Sans:wght@300;400
```

### Type Scale

| Role | Size | Weight | Tracking | Family |
|---|---|---|---|---|
| Display | clamp(38px, 4.5vw, 62px) | 300 | -0.025em | Mono |
| Heading 1 | clamp(28px, 3vw, 44px) | 300 | -0.02em | Mono |
| Heading 2 | 22px | 500 | 0.02em | Mono |
| UI / Panel | 13-14px | 500 | 0.04em | Mono |
| Body | 14-15px | 300 | normal | Sans |
| Label (caps) | 9-10px | 400 | 0.2-0.28em | Mono, uppercase |
| Micro | 8-9px | 400 | 0.18em | Mono, uppercase |
| CLI output | 11-13px | 400 | 0.02em | Mono |

### Rules

- Never use Inter, Roboto, or system fonts
- Never use Plex Mono above weight 600
- Never use Plex Sans for headings or interactive elements
- Never use justified alignment -- left only
- Heading + label pairing: Mono 300 + Mono caps 400

---

## CLI Color Theme

Each syntax role maps to exactly one color token:

| Role | Color | Token |
|---|---|---|
| Prompt `$` | Ledger Coral | `#E84520` |
| Command `yantra` | Sanchitta Amber | `#F5A000` |
| Argument / path | Yantra Blue | `#1C6FFF` |
| String `"value"` | Vidya Green | `#1AA167` |
| Hash `#A3F9D2` | Chitragupta Indigo | `#5535E0` |
| Flag `--since` | Subtle | `#7A7682` |
| Success / OK | Vidya Green | `#1AA167` |
| Error | Ledger Coral | `#E84520` |
| Output (dim) | Parchment 42% | `rgba(232,229,222,0.42)` |

---

## Iconography

All icons use the **mandala construction principle**: circle-based forms, 45-degree increments, no arbitrary curves.

Domain icons use the circle-with-interior pattern:

- Identity: circle + person outline
- SessionLog: circle + clock hands
- Inbox: circle + plus sign
- Tasks: circle + checkmark
- Goals: circle + radial target
- Beliefs: circle + text lines
- People: circle + two-person silhouette
- OpenLoops: circle + unresolved clock

---

## Brand Assets Summary

All assets are at `assets/`. SVG is primary; PNG kept for compatibility.

```
assets/
-- logo_horizontal.svg    Mark + wordmark, dark bg  (320x60)
-- icon_512.svg           App icon, full detail     (512x512)
-- icon_192.svg           App icon, compact         (192x192)
-- og_card.svg            Social / OG card          (1200x630)
-- banner_github.svg      GitHub README banner      (1280x400)
```

---

*Protocol: CC0 1.0 Universal -- Library: MIT*
*github.com/revanthlevaka/OpenYantra*
