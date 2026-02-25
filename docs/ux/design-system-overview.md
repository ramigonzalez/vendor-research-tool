# Vendor Research Tool — Unified Design System

> A design system combining the best Deep Research UI patterns from Perplexity, ChatGPT, Claude, and Grok.
> Date: 2026-02-24

---

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Atomic Design Structure](#atomic-design-structure)
- [Typography](#typography)
- [Color System](#color-system)
- [Spacing & Layout](#spacing--layout)
- [Animations & Transitions](#animations--transitions)
- [UI Feedback States](#ui-feedback-states)
- [Key Components](#key-components)
- [Accessibility](#accessibility)
- [Token Reference](#token-reference)

---

## Design Philosophy

This design system is built on insights from 4 best-in-class AI Deep Research interfaces. The core principles:

1. **Progressive Disclosure**: Show research activity in real-time, then collapse into results
2. **Transparency Through Timeline**: Users must see what the system is doing at each step
3. **Content-First Chrome**: Minimal UI framing; the research content is the hero
4. **Warm Professionalism**: Not cold/clinical, not playful — trustworthy and approachable
5. **WCAG AA Minimum**: Accessibility is built-in from the token level

### What We Took From Each Platform

| Platform | Key Inspiration |
|----------|----------------|
| **Perplexity** | Three-phase progress model, source confidence ratings, turquoise accent system |
| **ChatGPT** | Fullscreen document viewer, activity log sidebar, three-column report layout |
| **Claude** | Warm typography (serif for responses), collapsible chain-of-thought, terracotta warmth |
| **Grok** | Dual-panel research view, two-part report structure (direct answer + survey) |

---

## Atomic Design Structure

```
Atoms          Molecules              Organisms              Templates
-----------    -------------------    --------------------    -------------------
Icon           SourcePill             ResearchTimeline        ResearchPageLayout
Badge          StepIndicator          ResultsReport           DocumentViewer
ProgressBar    CitationRef            ActivitySidebar
Spinner        SearchQueryChip        SourcesPanel
Tag            ThinkingBlock          CollapsibleProgress
Divider        CounterBadge           CitationsFooter
Link           TimeElapsed
Button
```

---

## Typography

### Font Stack

We adopt a **dual-family approach** inspired by Claude's warmth + Perplexity's clarity:

| Role | Font | Fallback | Rationale |
|------|------|----------|-----------|
| **Headings** | Inter | system-ui, sans-serif | Clean, professional, widely available |
| **Body (AI responses)** | Source Serif 4 | Georgia, ui-serif, serif | Warm readability for long reports (inspired by Claude's Tiempos) |
| **Body (UI/user input)** | Inter | system-ui, sans-serif | Clear distinction between user and AI content |
| **Monospace** | JetBrains Mono | Consolas, monospace | Code blocks, technical content |

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `text-xs` | 12px | 400 | 16px | Captions, timestamps, counters |
| `text-sm` | 14px | 400 | 20px | Secondary text, source metadata |
| `text-base` | 16px | 400 | 24px | Body text, paragraphs |
| `text-lg` | 18px | 500 | 28px | Section headings (H3) |
| `text-xl` | 20px | 600 | 28px | Sub-headings (H2) |
| `text-2xl` | 24px | 700 | 32px | Page headings (H1) |
| `text-3xl` | 30px | 700 | 36px | Hero/report title |

### Report Formatting Rules

- **H1**: Report title only (one per report)
- **H2**: Major sections (Executive Summary, Findings, Analysis, Sources)
- **H3**: Subsections within major sections
- **Paragraphs**: Short (3-5 sentences max), with bold key phrases
- **Lists**: Bulleted for unordered, numbered for sequential/ranked
- **Tables**: For structured data comparison (always with header row)
- **Max content width**: `42rem` (672px) — optimal reading line length

---

## Color System

### Design Tokens

A warm-professional palette combining Claude's warmth with Perplexity's technical clarity.

#### Semantic Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--color-bg-primary` | `#F5F4EF` | `#1a1a1a` | Page background |
| `--color-bg-secondary` | `#FFFFFF` | `#242424` | Cards, surfaces |
| `--color-bg-elevated` | `#FFFFFF` | `#2e2e2e` | Modals, popovers |
| `--color-bg-user-msg` | `#E8E6DF` | `#3a3a3a` | User message bubbles |
| `--color-bg-ai-msg` | transparent | transparent | AI responses (no bubble) |
| `--color-text-primary` | `#1a1a18` | `#f0f0f0` | Body text |
| `--color-text-secondary` | `#6b6a68` | `#a0a0a0` | Muted/secondary text |
| `--color-text-tertiary` | `#9a9893` | `#707070` | Captions, timestamps |
| `--color-border-default` | `#e0ddd5` | `#3a3a3a` | Default borders |
| `--color-border-subtle` | `#ebe8e0` | `#2e2e2e` | Subtle dividers |

#### Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-accent-primary` | `#1a8a7d` | Primary actions, active states, links |
| `--color-accent-primary-hover` | `#157a6e` | Hover state |
| `--color-accent-secondary` | `#c05a35` | Warm accent for emphasis, highlights |
| `--color-accent-tertiary` | `#0079cb` | Informational, metadata links |

#### Status Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-status-searching` | `#1a8a7d` | "Searching" phase indicator |
| `--color-status-reading` | `#2196F3` | "Reading sources" phase |
| `--color-status-analyzing` | `#9C27B0` | "Analyzing" phase |
| `--color-status-writing` | `#c05a35` | "Writing report" phase |
| `--color-status-complete` | `#4CAF50` | Research complete |
| `--color-status-error` | `#E53935` | Error state |
| `--color-status-warning` | `#FF9800` | Warning/caution |

#### Source Confidence

| Token | Value | Usage |
|-------|-------|-------|
| `--color-confidence-high` | `#4CAF50` | High confidence source |
| `--color-confidence-medium` | `#FF9800` | Medium confidence |
| `--color-confidence-low` | `#E53935` | Low confidence/uncertain |

---

## Spacing & Layout

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight internal padding |
| `--space-2` | 8px | Compact spacing |
| `--space-3` | 12px | Default inner padding |
| `--space-4` | 16px | Standard gap |
| `--space-5` | 20px | Section padding |
| `--space-6` | 24px | Card padding |
| `--space-8` | 32px | Section margins |
| `--space-10` | 40px | Large section gaps |
| `--space-12` | 48px | Page-level spacing |
| `--space-16` | 64px | Hero spacing |

### Layout System

```
+------------------------------------------------------------------+
|  Sidebar (collapsible)  |        Main Content         | Activity |
|    240px fixed           |    flex-1 (max 42rem)       |  320px   |
|                          |    centered                  | (toggle) |
+------------------------------------------------------------------+
```

| Token | Value | Usage |
|-------|-------|-------|
| `--layout-sidebar-width` | 240px | Navigation sidebar |
| `--layout-content-max` | 42rem (672px) | Report content max-width |
| `--layout-activity-width` | 320px | Activity/sources panel |
| `--layout-border-radius` | 12px | Cards, containers |
| `--layout-border-radius-sm` | 8px | Buttons, pills |
| `--layout-border-radius-xs` | 4px | Tags, badges |

---

## Animations & Transitions

### Duration Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-instant` | 100ms | Hover states, toggles |
| `--duration-fast` | 200ms | Button feedback, badges |
| `--duration-normal` | 300ms | Panel slides, collapses |
| `--duration-slow` | 500ms | Page transitions, major state changes |
| `--duration-streaming` | 50ms | Token-by-token text streaming delay |

### Easing

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-default` | `cubic-bezier(0.165, 0.85, 0.45, 1)` | General transitions (Claude-inspired organic feel) |
| `--ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful micro-interactions |
| `--ease-smooth` | `cubic-bezier(0.4, 0, 0.2, 1)` | Material-style smooth |

### Key Animations

#### 1. Text Streaming
```css
@keyframes token-fade-in {
  from { opacity: 0.3; }
  to { opacity: 1; }
}
/* Apply to each streamed token span */
.token-new {
  animation: token-fade-in var(--duration-instant) var(--ease-default);
}
```

#### 2. Thinking Shimmer (Claude-inspired)
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.thinking-shimmer {
  background: linear-gradient(
    90deg,
    var(--color-bg-secondary) 25%,
    var(--color-border-default) 50%,
    var(--color-bg-secondary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

#### 3. Progress Step Pulse
```css
@keyframes step-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.step-active {
  animation: step-pulse 1.5s ease-in-out infinite;
}
```

#### 4. Collapse/Expand
```css
.collapsible {
  transition: max-height var(--duration-normal) var(--ease-default),
              opacity var(--duration-fast) var(--ease-default);
  overflow: hidden;
}
.collapsible[data-collapsed="true"] {
  max-height: 48px; /* Shows summary line only */
  opacity: 0.8;
}
.collapsible[data-collapsed="false"] {
  max-height: 2000px;
  opacity: 1;
}
```

#### 5. Source Pill Entrance
```css
@keyframes pill-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
.source-pill-enter {
  animation: pill-enter var(--duration-fast) var(--ease-default);
}
```

---

## UI Feedback States

### Research Phase States

The system must communicate 6 distinct phases. Each has a unique icon, color, and label:

| Phase | Icon | Color Token | Label | Description |
|-------|------|-------------|-------|-------------|
| Planning | `brain` | `--color-text-secondary` | "Planning research..." | Decomposing query into sub-tasks |
| Searching | `search` | `--color-status-searching` | "Searching N sources..." | Active web searches |
| Reading | `book-open` | `--color-status-reading` | "Reading N pages..." | Consuming source content |
| Analyzing | `sparkles` | `--color-status-analyzing` | "Analyzing findings..." | Cross-referencing, reasoning |
| Writing | `pen-line` | `--color-status-writing` | "Writing report..." | Synthesizing final output |
| Complete | `check-circle` | `--color-status-complete` | "Research complete" | Final state |

### Button States

| State | Visual |
|-------|--------|
| Default | Base colors, no shadow |
| Hover | Slight color shift, cursor pointer |
| Active | `scale(0.98)` — tactile press feedback |
| Disabled | 50% opacity, no interaction |
| Loading | Spinner replaces icon/text |

---

## Key Components

See individual component specs in `./components/`:

| Component | Type | File |
|-----------|------|------|
| **ResearchTimeline** | Organism | [research-timeline.md](./components/research-timeline.md) |
| **CitationRef** | Atom | [citation-ref.md](./components/citation-ref.md) |
| **SourcePill** | Molecule | [source-pill.md](./components/source-pill.md) |
| **CollapsibleProgress** | Organism | [collapsible-progress.md](./components/collapsible-progress.md) |
| **ResultsReport** | Organism | [results-report.md](./components/results-report.md) |

---

## Accessibility

### Requirements (WCAG AA)

| Criterion | Requirement | Implementation |
|-----------|-------------|----------------|
| 1.4.3 Contrast | 4.5:1 text, 3:1 large text | All token pairs verified |
| 1.4.11 Non-text Contrast | 3:1 for UI components | Status colors meet threshold |
| 2.1.1 Keyboard | All interactive elements focusable | Focus ring on all controls |
| 2.4.7 Focus Visible | Visible focus indicator | `2px solid var(--color-accent-primary)` with `2px` offset |
| 4.1.2 Name, Role, Value | Proper ARIA labels | All dynamic content announced |

### Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  .thinking-shimmer { animation: none; }
  .token-new { animation: none; opacity: 1; }
}
```

### Screen Reader Considerations

- Research phase transitions announced via `aria-live="polite"`
- Source count updates use `aria-atomic="true"`
- Collapsible sections use `aria-expanded` state
- Citations use `role="doc-noteref"` with linked `role="doc-endnote"`

---

## Token Reference

All design tokens are defined in [`tokens.yaml`](./tokens.yaml).

Import hierarchy:
```
tokens.yaml (source of truth)
  ├── CSS custom properties (runtime)
  ├── Tailwind theme extension (build)
  └── JS/TS constants (typed)
```
