# Component: SourcePill

> **Type:** Molecule
> **Atomic Level:** Molecule (Icon atom + Badge atom + Link atom)
> **Status:** Spec Ready

---

## Overview

A compact badge showing a discovered source during the research process. Displays favicon + domain name. Appears with an entrance animation as sources are found in real-time. Inspired by Perplexity's source pills that animate in during research.

---

## Visual

### Default
```
┌──────────────────┐
│ 🌐 gartner.com   │
└──────────────────┘
```

### With Confidence
```
┌───────────────────────┐
│ 🌐 gartner.com  [Hi]  │
└───────────────────────┘
```

### Hover
```
┌───────────────────────────────────────┐
│ 🌐 Gartner 2026 Magic Quadrant — ga… │
└───────────────────────────────────────┘
```

---

## Props / API

```typescript
interface SourcePillProps {
  /** Source URL */
  url: string;

  /** Display domain */
  domain: string;

  /** Favicon URL (falls back to generic globe icon) */
  favicon?: string;

  /** Full source title (shown on hover) */
  title?: string;

  /** Confidence rating */
  confidence?: 'high' | 'medium' | 'low';

  /** Whether this pill is animating in (just discovered) */
  isNew?: boolean;

  /** Click handler */
  onClick?: () => void;
}
```

---

## Styling

```css
.source-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--color-border-default);
  border-radius: var(--layout-border-radius-full);
  background: var(--color-bg-secondary);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all var(--duration-instant) var(--ease-default);
}

.source-pill:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
  max-width: 300px;
}

.source-pill .favicon {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  flex-shrink: 0;
}

/* Entrance animation for newly discovered sources */
.source-pill[data-new="true"] {
  animation: pill-enter var(--duration-fast) var(--ease-default);
}

@keyframes pill-enter {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Confidence badge */
.source-pill .confidence-badge {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: var(--layout-border-radius-xs);
  font-weight: var(--font-weight-medium);
}

.confidence-badge[data-level="high"] {
  background: color-mix(in srgb, var(--color-confidence-high) 15%, transparent);
  color: var(--color-confidence-high);
}

.confidence-badge[data-level="medium"] {
  background: color-mix(in srgb, var(--color-confidence-medium) 15%, transparent);
  color: var(--color-confidence-medium);
}

.confidence-badge[data-level="low"] {
  background: color-mix(in srgb, var(--color-confidence-low) 15%, transparent);
  color: var(--color-confidence-low);
}
```

---

## Accessibility

- `role="link"` with `aria-label` including full source title and domain
- Keyboard focusable with visible focus ring
- Confidence badge has `aria-label` (e.g., "High confidence")
- Favicon uses `alt=""` (decorative) since domain text is present
