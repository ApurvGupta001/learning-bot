# Design — Visual language

The current UI is an intentionally lean dark theme defined in
`frontend/app/globals.css`. This document is the source of truth for visual
decisions; update it and `globals.css` together.

## 1. Theme
Dark, calm, focused — a "study at night" feel. Minimal chrome so the lesson text
is the star. Light-on-dark for reduced eye strain during long sessions.

## 2. Color palette (CSS variables)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0b1020` | App background (deep navy) |
| `--panel` | `#141a2e` | Cards / chat container |
| `--text` | `#e6e9f2` | Primary text (near-white) |
| `--muted` | `#9aa3b8` | Secondary/hint text |
| `--accent` | `#6ea8fe` | Buttons, links, highlights (blue) |
| `--border` | `#232a42` | Card & input borders |

**Message bubbles**
- User: background `#1c2540`.
- Assistant: background `#182136` with `--border`.

**Accent usage:** the blue `--accent` signals interactivity (send button, links).
Button text uses a very dark navy (`#06122b`) for contrast on the blue.

### Accessibility
- Maintain WCAG AA contrast (≥ 4.5:1 for body text) — the near-white on deep navy
  passes comfortably.
- Don't rely on color alone for meaning (e.g., mastery states should also use
  labels/icons in the future dashboard).

## 3. Typography
- **Font family:** system UI stack —
  `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
  Fast, no web-font download, native feel per OS.
- **Base size:** browser default (16px). Hints/small print ~14px.
- **Headings:** default weight/scale for now; keep hierarchy clear (`h1` page
  title, `h2` section).
- **Body:** relaxed line length; chat bubbles wrap with `white-space: pre-wrap`
  so code/newlines from lessons render faithfully.
- **Future:** when lessons include code, add a monospace block style
  (`ui-monospace, SFMono-Regular, Menlo, monospace`).

## 4. Layout & spacing
- Centered container, `max-width: 820px` — comfortable reading measure.
- Page padding: 32px vertical / 20px horizontal.
- **Radii:** cards 12px, bubbles/inputs/buttons 10px — soft, modern.
- **Rhythm:** 8–16px gaps between elements; bubbles have 8px vertical margin.

## 5. Components
- **Card** (`.card`): panel bg, 1px border, 12px radius, 20px padding.
- **Chat bubble** (`.msg.user` / `.msg.assistant`): distinct fills; wraps text.
- **Input** (`.input`): dark field, bordered, flex-grows to fill the row.
- **Button** (`.btn`): accent fill, bold, dark text; disabled state at 50%
  opacity with `not-allowed` cursor.

## 6. Interaction & motion
- Streaming text appears token by token (feels alive) — no extra animation needed.
- Disabled send button + "…" label while a response streams, to prevent double
  sends.
- Keep motion minimal and purposeful; avoid distracting animation.

## 7. Future direction
- Citation "chips" under grounded answers (small bordered pills linking to the
  source doc).
- Progress dashboard: concept-graph visualization with mastery color-coding
  (paired with labels for accessibility).
- Optional light theme via `color-scheme` + a variable swap.
