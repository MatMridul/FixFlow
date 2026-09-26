# FixFlow Design System Specification

> **Aesthetic Foundation:** Samsung Galaxy Flagship Care × Linear Precision Luxury Minimalist  
> **Target Audience:** Galaxy device owners seeking effortless, reliable resolution for hardware & software issues.  
> **Guiding Principle:** Consumer clarity over developer telemetry. Absolute functional precision. Zero visual slop.

---

## 1. System Philosophy & Aesthetic Directives

FixFlow blends the calm, humane clarity of **Samsung Galaxy Flagship Support** with the razor-sharp density, obsidian depth, and typographic discipline of **Linear**.

### Core Tenets:
1. **Consumer-First Dignity:** No backend engine jargon (`FastAPI`, `N1 Cache Tier`, `9.2ms`, `$0.0000 USD`, `SIIS Catalog`, or raw machine URIs). Every word speaks directly to the user about their device, symptoms, and fixes.
2. **Surface Ladder over Dropshadows:** Visual depth is achieved through an obsidian surface hierarchy with microscopic hairline borders (`1px solid rgba(255,255,255,0.06)`), not puffy Gaussian blur shadows or decorative glowing blobs.
3. **Restrained Chromatic Focal Points:** Accent color (Samsung Cobalt `#1E56FF` / Electric `#2F68FD`) is used strictly for active interactive states, primary action triggers, and verified fix indicators. 90% of the surface remains calm, dark titanium monochrome.
4. **Authentic Device Grounding:** The device simulator is not a decorative image. It is an active, responsive twin of Samsung One UI 6.1 that mirrors real Galaxy settings (Display, Battery, Storage, Quick Panel, and Home Screen) with live animated responses.

---

## 2. Token Specification

### 2.1 Surface Ladder (Dark Mode Obsidian)
| Token Name | Hex Value | Purpose |
|---|---|---|
| `--surface-canvas` | `#08090B` | Deepest root background canvas |
| `--surface-subtle` | `#0E1013` | Secondary ambient surfaces, container backgrounds |
| `--surface-panel` | `#13151A` | Main application panels, device chassis bezel |
| `--surface-raised` | `#191C23` | Interactive list items, inputs, table rows |
| `--surface-hover` | `#20242D` | Hover and active selection states |
| `--surface-border` | `rgba(255, 255, 255, 0.07)` | Hairline division lines between panels |
| `--surface-border-strong` | `rgba(255, 255, 255, 0.14)` | Focused inputs, active step boundaries |

### 2.2 Brand & Semantic Accents
| Token Name | Hex Value | Purpose |
|---|---|---|
| `--accent-samsung-blue` | `#1E56FF` | Flagship primary CTA, active toggles, brand mark |
| `--accent-electric-sky` | `#2F68FD` | Hover states on primary buttons, active link highlight |
| `--accent-success` | `#10B981` | Fix applied, battery optimized, cache cleared (0MB) |
| `--accent-warning` | `#F59E0B` | Battery drain alert, critical device warning |
| `--accent-danger` | `#EF4444` | Hardware defect warning, reset confirmation |

### 2.3 Typography Scale (Inter / Samsung Sans-inspired)
- **Font Family:** `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Headings:** Sentence casing, tight negative letter spacing (`tracking-tight` / `-0.02em`), semi-bold (`font-semibold`).
- **Body:** Neutral grey (`#9496A1` on `#08090B`), high legibility, normal tracking (`tracking-normal`).
- **Data / Status / Counters:** Monospace / tabular numbers (`font-mono tracking-wider text-xs uppercase`).

---

## 3. Strict Anti-Patterns (BANNED)

| Anti-Pattern | Why It Is Banned | FixFlow Standard |
|---|---|---|
| **Purple/Violet AI Gradients** | Generic AI slop that looks like a prototype template. | Solid obsidian surfaces with hairline borders and single Samsung Blue accent. |
| **Giant Hero Typography** | Wastes screen real estate and feels like a marketing pitch rather than support. | Compact, purposeful diagnostic header (24px max) with immediate search intake. |
| **Puffy Rounded Cards** | Over-rounded borders (`rounded-3xl`) look childish and waste space. | Subtle, disciplined squircle radii (`rounded-xl` / `12px` max). |
| **Cards-inside-Cards-inside-Cards** | Cluttered visual noise that reduces reading flow. | Single-depth panel with clean tabular rows or hairline-divided steps. |
| **Excessive Glassmorphism** | Heavy backdrop blur makes text muddy and strains readability. | Opaque or 95% opacity dark panels with crisp 1px hairline borders. |
| **Decorative Blobs & Floating Orbs** | Distracting decorative gimmicks with zero functional purpose. | Pure flat surface ladder with high-contrast content. |
| **Emoji as UI Icons** | Inconsistent across platforms, looks unprofessional. | Lucid, uniform SVG vector icons (20px / 16px). |
| **Developer Telemetry on Consumer UI** | "N1 Cache Tier", "FastAPI:8000", "9.2ms", "$0.0000 USD" confuse real users. | Humane, actionable language: "Galaxy S24 Ultra connected", "3-step guided fix". |
| **Non-functional Phone Simulator** | A static mockup makes the app feel broken and useless. | Fully responsive One UI 6.1 simulator that reacts to step simulation and direct interaction. |

---

## 4. Component Vocabulary

Before any code implementation, the interface is decomposed into these single-responsibility components:

```
App
├── TopNav (Brand, Connected Device Badge, Model Selector)
├── Main Workspace (2-Column Desktop Grid / 1-Column Mobile Stack)
│   ├── Left Column: Resolution Center
│   │   ├── DiagnosticIntake (Search Bar + Benchmark Pills)
│   │   ├── ResolutionStream (Step-by-Step Flow, Progress, One-Click Device Automation)
│   │   └── FeedbackBar (Resolution Confirmation, Safe Mode, Expert Escalation)
│   └── Right Column: DeviceTwin (Interactive One UI 6.1 Simulator)
│       ├── DeviceHardwareChassis (Titanium Bezel, Dynamic AMOLED Screen, Power/Volume)
│       ├── OneUiStatusBar (Signal, Battery %, Wi-Fi, Clock)
│       ├── OneUiScreenSwitch (Home | Display | Battery & Care | App Storage)
│       └── OneUiInteractiveCanvas (Live toggles, Brightness slider, Cache cleaner)
└── SupportFooter (Official 24/7 Helpline, Email Support, Dynamic Copyright 2026)
```

### Component Contracts:

#### 1. `TopNav`
- **Inputs:** `deviceModel: string`, `systemStatus: 'connected' | 'offline'`, `onReset: () => void`
- **Output:** Clean 56px header with FixFlow Galaxy brand, device connection pill, and reset action.

#### 2. `DiagnosticIntake`
- **Inputs:** `query: string`, `onQueryChange: (q: string) => void`, `onSelectScenario: (scenario: Scenario) => void`, `loading: boolean`
- **Output:** High-density search bar with keyboard shortcut (`Enter`), 4 pre-warmed benchmark pills for instant testing.

#### 3. `ResolutionStream`
- **Inputs:** `plan: TroubleshootingPlan`, `currentStepIndex: number`, `completedSteps: number[]`, `onExecuteStep: (step: Step) => void`, `onToggleStep: (index: number) => void`
- **Output:** Structured step-by-step checklist. Each row has step number, clear human instruction, subsystem tag, and "Simulate on Galaxy" button.

#### 4. `DeviceTwin` (Phone Simulator)
- **Inputs:** `activeSubsystem: Subsystem`, `deviceState: DeviceState`, `onStateChange: (newState: DeviceState) => void`
- **Output:** Authentic One UI 6.1 screen. Supports:
  - Display settings: Dark/Light mode switch, live brightness slider.
  - Device Care: Score meter, "Optimize Now" animated button.
  - App Storage: Storage breakdown, working "Clear Cache" button (184MB -> 0MB).
  - Home screen: Real Samsung Galaxy widgets and clickable apps.
  - Quick Panel: Interactive toggle buttons.

#### 5. `FeedbackBar`
- **Inputs:** `isResolved: boolean`, `onConfirmResolution: () => void`, `onRequestEscalation: () => void`
- **Output:** "Did this resolve your issue?", "Yes, fixed!" (triggers celebration), and "Connect to Galaxy Expert".

#### 6. `SupportFooter`
- **Inputs:** none
- **Output:** 24/7 Samsung Helpline (`tel:1-800-726-7864`), Email Support (`mailto:support@samsung.com`), current dynamic year (`2026`).

---

## 5. Layout & Responsive Specifications

- **Desktop (>= 1024px):** 60% Resolution Center on left, 40% DeviceTwin sticky on right. Max width 1380px centered.
- **Mobile (< 1024px):** Full-width Resolution Center with floating bottom toggle "Show Galaxy S24 Screen" that opens a slide-over drawer containing the DeviceTwin.
- **Accessibility:** WCAG AA contrast ratio (> 4.5:1 for body text, > 7:1 for headings), ARIA attributes on all interactive controls.
