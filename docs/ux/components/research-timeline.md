# Component: ResearchTimeline

> **Type:** Organism
> **Atomic Level:** Organism (composed of StepIndicator molecules and atom elements)
> **Status:** Spec Ready

---

## Overview

The ResearchTimeline is the **centerpiece component** of the Deep Research experience. It shows the user what the system is doing in real-time via a vertical timeline of steps, then **collapses into a summary** when research completes, revealing the full results report below.

This pattern was observed across all 4 platforms (Perplexity, ChatGPT, Claude, Grok) and represents the **universal Deep Research UX pattern**.

---

## Behavior Flow

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Active Research (expanded)                        │
│                                                              │
│  ┌─ Research Timeline ────────────────────────────────────┐ │
│  │                                                         │ │
│  │  [*] Planning research...              0:05             │ │
│  │   |  "Breaking down: vendor comparison analysis"        │ │
│  │   |                                                     │ │
│  │  [*] Searching 12 sources...           0:23             │ │
│  │   |  query: "enterprise vendor comparison 2026"         │ │
│  │   |  query: "Gartner magic quadrant..."                 │ │
│  │   |  ┌──────┐ ┌──────┐ ┌──────┐                       │ │
│  │   |  │ 🌐 G │ │ 🌐 F │ │ 🌐 T │  <- source pills     │ │
│  │   |  └──────┘ └──────┘ └──────┘                       │ │
│  │   |                                                     │ │
│  │  [◉] Reading 8 pages...   <- ACTIVE (pulsing)  1:04    │ │
│  │   |  "Found pricing data in Gartner report..."          │ │
│  │   |                                                     │ │
│  │  [ ] Analyzing findings...                              │ │
│  │  [ ] Writing report...                                  │ │
│  │                                                         │ │
│  │  ──────────────────── 1:04 elapsed ─────────────────── │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  [No results visible yet — timeline fills the view]          │
└─────────────────────────────────────────────────────────────┘

          ↓ Research completes → auto-collapse transition ↓

┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Complete (collapsed)                               │
│                                                              │
│  ┌─ Research Summary (collapsed) ──────────────── [▸ Expand]│
│  │  ✓ Research complete · 24 sources · 2:47 elapsed         │
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Results Report ─────────────────────────────────────────┐│
│  │  # Vendor Comparison Analysis                            ││
│  │                                                          ││
│  │  ## Executive Summary                                    ││
│  │  Based on analysis of 24 sources including...            ││
│  │  ...                                                     ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## States

### 1. Planning
```
[◉] Planning research...                    0:05
 |  "Breaking down query into 4 sub-tasks"
```
- Icon: `brain` (pulsing animation)
- Color: `--color-text-secondary`
- Shows: Sub-task decomposition text

### 2. Searching
```
[✓] Planning research...                    0:05
[◉] Searching 12 sources...                 0:34
 |  ┌──────┐ ┌──────┐ ┌──────┐
 |  │ 🌐 G │ │ 🌐 F │ │ 🌐 T │
 |  └──────┘ └──────┘ └──────┘
```
- Icon: `search` (pulsing)
- Color: `--color-status-searching`
- Shows: Source pills appearing with favicon + domain (animated entrance)
- Counter: "Searching N sources..." increments in real-time

### 3. Reading
```
[✓] Planning research...                    0:05
[✓] Searched 18 sources                     0:34
[◉] Reading 8 pages...                      1:12
 |  "Found pricing comparison in Forbes article"
 |  "Cross-referencing with Gartner data..."
```
- Icon: `book-open` (pulsing)
- Color: `--color-status-reading`
- Shows: Key findings streaming as they're discovered (Perplexity pattern)

### 4. Analyzing
```
[✓] Planning research...                    0:05
[✓] Searched 18 sources                     0:34
[✓] Read 14 pages                           1:12
[◉] Analyzing findings...                   1:58
 |  "Comparing vendor pricing models..."
```
- Icon: `sparkles` (pulsing)
- Color: `--color-status-analyzing`
- Shows: Brief reasoning snippets

### 5. Writing
```
[✓] Planning research...                    0:05
[✓] Searched 18 sources                     0:34
[✓] Read 14 pages                           1:12
[✓] Analyzed findings                       1:58
[◉] Writing report...                       2:30
```
- Icon: `pen-line` (pulsing)
- Color: `--color-status-writing`
- Shows: Report begins streaming below the timeline

### 6. Complete (Auto-Collapse)
```
┌──────────────────────────────────────────── [▸ Expand] ┐
│  ✓ Research complete · 24 sources · 2:47                │
└─────────────────────────────────────────────────────────┘
```
- Icon: `check-circle` (static, green)
- Color: `--color-status-complete`
- Timeline collapses to **single summary line**
- Click "Expand" to review full timeline steps

---

## Props / API

```typescript
interface ResearchTimelineProps {
  /** Current research phase */
  phase: 'planning' | 'searching' | 'reading' | 'analyzing' | 'writing' | 'complete';

  /** Steps with their status and metadata */
  steps: ResearchStep[];

  /** Total elapsed time in seconds */
  elapsedSeconds: number;

  /** Total sources found so far */
  sourceCount: number;

  /** Whether the timeline is collapsed (auto-collapses on complete) */
  collapsed: boolean;

  /** Toggle collapse state */
  onToggleCollapse: () => void;

  /** Key findings discovered during research */
  keyFindings?: string[];
}

interface ResearchStep {
  id: string;
  phase: 'planning' | 'searching' | 'reading' | 'analyzing' | 'writing';
  status: 'pending' | 'active' | 'complete';
  label: string;
  description?: string;
  timestamp: number; // seconds when step started
  sources?: SourcePill[];  // for searching phase
  findings?: string[];     // for reading/analyzing phase
}

interface SourcePill {
  url: string;
  domain: string;
  favicon?: string;
  title?: string;
}
```

---

## Collapse/Expand Animation

```css
.research-timeline {
  transition: max-height var(--duration-normal) var(--ease-default),
              padding var(--duration-normal) var(--ease-default);
  overflow: hidden;
}

/* Expanded: full height */
.research-timeline[data-state="expanded"] {
  max-height: 600px;
  padding: var(--space-6);
}

/* Collapsed: single summary line */
.research-timeline[data-state="collapsed"] {
  max-height: 52px;
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--layout-border-radius-sm);
  background: var(--color-bg-secondary);
}

.research-timeline[data-state="collapsed"]:hover {
  border-color: var(--color-border-default);
  background: var(--color-bg-elevated);
}
```

---

## Accessibility

- Timeline uses `role="log"` with `aria-live="polite"` for phase updates
- Each step uses `role="listitem"` within a `role="list"` container
- Phase transitions announced: "Now searching 12 sources"
- Collapsed state uses `aria-expanded="false"` on the summary button
- Elapsed time counter uses `aria-label="Elapsed research time: 2 minutes 47 seconds"`
- Source pills are focusable with descriptive `aria-label`

---

## Responsive Behavior

| Breakpoint | Behavior |
|-----------|----------|
| `>= lg` (1024px) | Full timeline with source pills and findings inline |
| `md` (768-1023px) | Timeline condensed; source pills wrap to 2 rows |
| `< md` (< 768px) | Simplified: phase icon + label + time only; source pills hidden; findings in expandable accordion |

---

## Related Components

- **StepIndicator** (Molecule): Individual step row with icon, label, status
- **SourcePill** (Molecule): Favicon + domain badge for discovered sources
- **TimeElapsed** (Atom): Formatted elapsed time counter
- **CollapsibleProgress** (Organism): Generic collapsible wrapper (reusable)
- **ResultsReport** (Organism): The report that appears below on completion
