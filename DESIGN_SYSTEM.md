# FixFlow Monochrome Design System Specification (v3.0)

> **Aesthetic Foundation:** Pure Pitch Black × Crisp White Minimalist (Swiss Monochrome / Teenage Engineering / Leica Pro)  
> **Color Rule:** Absolutely ZERO blue, cyan, purple, or decorative color washes. 100% black, charcoal, silver, and pure white.  
> **Guiding Principle:** Utilitarian elegance. High contrast. Razor-sharp typography. Tactile physical controls.

---

## 1. Color Palette: Pure Monochrome

| Token Name | Hex Value | Purpose |
|---|---|---|
| `--bg-canvas` | `#000000` | Absolute pitch black root background |
| `--surface-base` | `#080808` | Primary container surfaces |
| `--surface-panel` | `#111111` | Diagnostic cards, input containers, device chassis |
| `--surface-raised` | `#181818` | Interactive rows, hover backgrounds, secondary buttons |
| `--surface-active` | `#222222` | Active toggles, focused inputs |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Hairline dividers and container outlines |
| `--border-strong` | `rgba(255, 255, 255, 0.20)` | Active focus rings, selected card borders |
| `--text-primary` | `#FFFFFF` | Primary headings, button labels, key values |
| `--text-secondary` | `#A3A3A3` | Step instructions, descriptions, body text |
| `--text-muted` | `#666666` | Metadata, tags, timestamps, secondary status |

### Accent Philosophy:
- **Primary CTA:** Solid White (`#FFFFFF`) with pure Black text (`#000000`). On hover: `#E5E5E5`.
- **Secondary CTA:** Dark Charcoal (`#181818`) with crisp White text and subtle white border.
- **Status / Verification:** Monochrome geometric icons (solid white circle, white checkmark, silver outlines).
- **Celebration Confetti:** Monochrome palette: pure white, silver, slate gray, and platinum.

---

## 2. Typography & Density Discipline

- **Font Family:** `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- **Headings:** Sentence casing, negative letter spacing (`-0.025em`), bold (`font-semibold`).
- **Data / Tags / Steps:** Monospaced tabular numbers (`font-mono tracking-wider uppercase text-xs`).
- **Zero AI-slop gradients:** No multi-colored mesh, no radial glare, no blurred blobs.

---

## 3. Component Hierarchy

```
App
├── TopBar (Pure black bar, white badge "FF", white status dot, reset control)
├── Main Grid (Desktop 2-column, Mobile 1-column)
│   ├── Resolution Center (Left)
│   │   ├── DiagnosticIntake (Pitch black card, high-contrast search, white CTA)
│   │   ├── ActionCardStream (Hairline cards, white progress bar, white "Simulate on Galaxy S24" button)
│   │   └── RefinementBox (Monochrome "Yes, fixed!", silver follow-up chips)
│   └── DeviceTwin (Right)
│       ├── Precision Black S24 Ultra Chassis
│       ├── AMOLED One UI 6.1 (Black theme with white text / White theme with black text)
│       ├── Interactive Controls (Brightness slider, Optimize Now, Clear Cache, Quick Panel)
│       └── Quick Jump Bar with sliding white pill indicator
└── Footer (Monochrome links, official phone & email, copyright 2026)
```
