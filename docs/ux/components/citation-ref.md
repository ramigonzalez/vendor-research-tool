# Component: CitationRef

> **Type:** Atom
> **Atomic Level:** Atom
> **Status:** Spec Ready

---

## Overview

An inline citation reference rendered as a superscript number `[n]` within report text. On hover, shows a preview tooltip with source metadata. On click, scrolls to the source in the Sources footer.

All 4 platforms use numbered inline citations — this is the universal pattern.

---

## Visual

### Default
```
...according to market analysis [3] the vendor...
                                 ↑
                            superscript, teal
```

### Hover
```
...according to market analysis [3] the vendor...
                                 ↑
                    ┌──────────────────────────────┐
                    │ 🌐 Gartner 2026 Magic Quad.  │
                    │ gartner.com · High confidence │
                    │ "The vendor landscape has     │
                    │  shifted significantly..."    │
                    └──────────────────────────────┘
```

---

## Props / API

```typescript
interface CitationRefProps {
  /** Citation number */
  number: number;

  /** Source data for tooltip */
  source: {
    title: string;
    url: string;
    domain: string;
    favicon?: string;
    confidence: 'high' | 'medium' | 'low';
    snippet?: string;
  };

  /** Scroll to source in footer */
  onNavigate: (sourceId: number) => void;
}
```

---

## Styling

```css
.citation-ref {
  display: inline;
  font-size: 0.75em;
  font-weight: var(--font-weight-medium);
  color: var(--color-accent-primary);
  cursor: pointer;
  vertical-align: super;
  line-height: 0;
  padding: 1px 3px;
  border-radius: var(--layout-border-radius-xs);
  transition: background var(--duration-instant) var(--ease-default);
}

.citation-ref:hover {
  background: color-mix(in srgb, var(--color-accent-primary) 12%, transparent);
  text-decoration: underline;
}

.citation-ref:focus-visible {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 1px;
}
```

---

## Accessibility

- Uses `role="doc-noteref"` with `aria-describedby` pointing to the source entry
- Keyboard accessible: focusable, activatable with Enter
- Tooltip content available to screen readers via `aria-label`
- Link semantics: `<a href="#source-{n}">` for in-page navigation
