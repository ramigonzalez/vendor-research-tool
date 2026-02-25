# Component: CollapsibleProgress

> **Type:** Organism
> **Atomic Level:** Organism
> **Status:** Spec Ready

---

## Overview

A generic container that displays rich progress content during an operation, then **auto-collapses to a single summary line** when the operation completes. The primary use case is wrapping the ResearchTimeline, but it can be reused for any long-running operation.

This is the **core UX pattern** identified across all 4 Deep Research platforms.

---

## Visual States

### Expanded (Active)

```
┌──────────────────────────────────────────────────────────┐
│  [icon] Title                               elapsed time │
│  ──────────────────────────────────────────────────────── │
│                                                          │
│  [children — any content: timeline, activity log, etc.]  │
│                                                          │
│  ──────────────────────────────────────── source count ── │
└──────────────────────────────────────────────────────────┘
```

### Collapsed (Complete)

```
┌──────────────────────────────────────────────── [▸] ─────┐
│  ✓ Summary text · metric1 · metric2 · elapsed            │
└──────────────────────────────────────────────────────────┘
```

### Re-Expanded (User clicks to review)

```
┌──────────────────────────────────────────────── [▾] ─────┐
│  ✓ Summary text · metric1 · metric2 · elapsed            │
│  ──────────────────────────────────────────────────────── │
│                                                          │
│  [full children content visible again, dimmed slightly]   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Props / API

```typescript
interface CollapsibleProgressProps {
  /** Current state of the operation */
  state: 'active' | 'complete' | 'error';

  /** Title shown in expanded header */
  title: string;

  /** Summary shown in collapsed state */
  summary: string;

  /** Metrics displayed in summary line (e.g., "24 sources", "2:47") */
  metrics: { label: string; value: string }[];

  /** Icon for the header */
  icon: string;

  /** Auto-collapse when state becomes 'complete' */
  autoCollapse?: boolean; // default: true

  /** Delay before auto-collapse (ms) — gives user time to see completion */
  collapseDelay?: number; // default: 1500

  /** Whether currently collapsed */
  collapsed: boolean;

  /** Callback when collapse state changes */
  onToggle: (collapsed: boolean) => void;

  /** Children: the progress content (timeline, activity log, etc.) */
  children: React.ReactNode;
}
```

---

## Auto-Collapse Behavior

When `state` transitions from `'active'` to `'complete'`:

1. **Complete icon appears** (check-circle, green) — `0ms`
2. **Brief pause** to let user register completion — `1500ms` (configurable via `collapseDelay`)
3. **Smooth collapse animation** — `300ms` using `--ease-default`
4. **Summary line visible** with metrics
5. **Results content below becomes visible** (was hidden/below fold during active state)

```
Timeline:
  0ms        → "✓ Research complete" appears
  1500ms     → Collapse animation starts
  1800ms     → Collapsed to summary line
  1800ms+    → Results report scrolls into view
```

---

## Styling

```css
.collapsible-progress {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--layout-border-radius-md);
  background: var(--color-bg-timeline);
  overflow: hidden;
  transition: all var(--duration-normal) var(--ease-default);
}

/* Expanded */
.collapsible-progress[data-state="active"] {
  padding: var(--space-5);
  border-color: var(--color-border-default);
}

/* Collapsed */
.collapsible-progress[data-collapsed="true"] {
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
}

.collapsible-progress[data-collapsed="true"]:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-accent-primary);
}

/* Error state */
.collapsible-progress[data-state="error"] {
  border-color: var(--color-status-error);
  border-left: 3px solid var(--color-status-error);
}

/* Summary line */
.collapsible-summary {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.collapsible-summary .metric {
  color: var(--color-text-tertiary);
}

.collapsible-summary .metric::before {
  content: "·";
  margin: 0 var(--space-2);
}

/* Toggle chevron */
.collapse-toggle {
  transition: transform var(--duration-fast) var(--ease-default);
}

.collapse-toggle[data-collapsed="false"] {
  transform: rotate(90deg);
}
```

---

## Accessibility

- Container uses `role="region"` with `aria-label` describing the operation
- Toggle button uses `aria-expanded` attribute
- State transitions announced via `aria-live="polite"` region
- Collapse/expand is keyboard accessible (Enter/Space on summary)
- Focus is managed: on auto-collapse, focus moves to the results report heading

---

## Usage Example

```tsx
<CollapsibleProgress
  state={researchState}
  title="Researching vendor comparison"
  summary="Research complete"
  metrics={[
    { label: "sources", value: "24" },
    { label: "elapsed", value: "2:47" }
  ]}
  icon="search"
  collapsed={isCollapsed}
  onToggle={setIsCollapsed}
>
  <ResearchTimeline
    phase={currentPhase}
    steps={steps}
    elapsedSeconds={elapsed}
    sourceCount={sourceCount}
    collapsed={false}
    onToggleCollapse={() => {}}
  />
</CollapsibleProgress>

{/* Results appear below — visible when collapsed */}
{researchState === 'complete' && (
  <ResultsReport data={reportData} />
)}
```
