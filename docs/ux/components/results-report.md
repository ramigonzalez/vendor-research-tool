# Component: ResultsReport

> **Type:** Organism
> **Atomic Level:** Organism
> **Status:** Spec Ready

---

## Overview

The final research output displayed after the ResearchTimeline collapses. Renders a structured, citation-rich document combining the best report patterns from all 4 platforms.

---

## Report Structure

Inspired by **Grok's two-part format** + **ChatGPT's document viewer** + **Perplexity's source confidence**:

```
┌──────────────────────────────────────────────────────────┐
│  # Report Title                                          │
│                                                          │
│  ┌── Key Takeaways ───────────────────────────────────┐  │
│  │  - Finding 1 with inline citation [1]               │  │
│  │  - Finding 2 with inline citation [2]               │  │
│  │  - Finding 3 with inline citation [3]               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                          │
│  ─────────────────────────────────────────────────────── │
│                                                          │
│  ## Section Heading                                      │
│                                                          │
│  Body text with **bold key phrases** and inline          │
│  citations [4] that link to sources. Short paragraphs    │
│  optimized for scanning.                                 │
│                                                          │
│  | Column A | Column B | Column C |                      │
│  |----------|----------|----------|                      │
│  | data     | data     | data     |                      │
│                                                          │
│  ## Another Section                                      │
│  ...                                                     │
│                                                          │
│  ─────────────────────────────────────────────────────── │
│                                                          │
│  ### Sources (24)                                        │
│  [1] Title — domain.com  [High confidence]               │
│  [2] Title — domain.com  [High confidence]               │
│  [3] Title — domain.com  [Medium confidence]             │
│  ...                                                     │
│                                                          │
│  ───────────────────────────── [Export ▾] [Share] [Copy] │
└──────────────────────────────────────────────────────────┘
```

---

## Sections

### 1. Key Takeaways (Always First)

A highlighted box at the top with 3-5 bullet points summarizing the most important findings. Each bullet includes an inline citation. Inspired by Perplexity's "key findings during research" pattern — gives immediate value.

### 2. Detailed Sections (H2 Headings)

The body of the report, organized by topic. Uses:
- H2 for major sections
- H3 for subsections
- Short paragraphs (3-5 sentences)
- **Bold key phrases** for scannability
- Bulleted lists for multiple items
- Tables for structured comparisons
- Inline citations `[n]` after every claim

### 3. Sources Footer

All citations listed with:
- Reference number `[n]`
- Source title
- Domain name
- Confidence level badge (High / Medium / Low)
- Clickable link to original

---

## Props / API

```typescript
interface ResultsReportProps {
  /** Report title */
  title: string;

  /** Key takeaways (3-5 bullet points) */
  keyTakeaways: Takeaway[];

  /** Report sections (rendered as Markdown) */
  sections: ReportSection[];

  /** All cited sources */
  sources: Source[];

  /** Whether the report is still streaming */
  isStreaming: boolean;

  /** Export handlers */
  onExport: (format: 'markdown' | 'pdf' | 'docx') => void;
  onShare: () => void;
  onCopy: () => void;
}

interface Takeaway {
  text: string;
  citationIds: number[];
}

interface ReportSection {
  heading: string;
  level: 2 | 3;
  content: string; // Markdown content with [n] citations
}

interface Source {
  id: number;
  title: string;
  url: string;
  domain: string;
  favicon?: string;
  confidence: 'high' | 'medium' | 'low';
  snippet?: string;
}
```

---

## Streaming Behavior

When the report first appears (while research is in the "writing" phase):

1. **Title renders first** (immediate)
2. **Key Takeaways stream in** bullet by bullet (token-by-token with `token-fade-in` animation)
3. **Sections stream sequentially** — each paragraph streams as tokens arrive
4. **Sources populate** as citations are referenced in the text
5. **Export buttons appear** only after streaming completes

```css
/* Streaming cursor at end of content */
.report-streaming::after {
  content: "";
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: var(--color-accent-primary);
  animation: blink 0.8s step-end infinite;
  margin-left: 2px;
  vertical-align: text-bottom;
}

@keyframes blink {
  50% { opacity: 0; }
}
```

---

## Citation Interactions

### Inline Citation `[n]`

```css
.citation-ref {
  font-size: var(--text-xs);
  color: var(--color-accent-primary);
  cursor: pointer;
  vertical-align: super;
  padding: 0 2px;
  border-radius: var(--layout-border-radius-xs);
  transition: background var(--duration-instant);
}

.citation-ref:hover {
  background: color-mix(in srgb, var(--color-accent-primary) 15%, transparent);
  text-decoration: underline;
}
```

### Hover Preview (Perplexity-inspired)

On hover over `[n]`, a tooltip shows:
```
┌─────────────────────────────────────┐
│ 🌐 Source Title                     │
│ domain.com · [High confidence]      │
│ "Relevant snippet from the          │
│  source document..."                │
└─────────────────────────────────────┘
```

---

## Key Takeaways Box

```css
.key-takeaways {
  background: color-mix(in srgb, var(--color-accent-primary) 8%, var(--color-bg-secondary));
  border: 1px solid color-mix(in srgb, var(--color-accent-primary) 20%, transparent);
  border-radius: var(--layout-border-radius-md);
  padding: var(--space-5);
  margin-bottom: var(--space-8);
}

.key-takeaways h3 {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent-primary);
  margin-bottom: var(--space-3);
}
```

---

## Export Bar

```
┌─────────────────────────────────────────────────────────┐
│                              [📋 Copy] [📤 Share] [⬇ Export ▾] │
│                                              ┌──────────┐│
│                                              │ Markdown  ││
│                                              │ PDF       ││
│                                              │ Word      ││
│                                              └──────────┘│
└─────────────────────────────────────────────────────────┘
```

- Sticky at bottom of report
- Only appears after streaming completes
- Export dropdown with format options

---

## Accessibility

- Report uses semantic HTML: `<article>`, `<h2>`, `<h3>`, `<section>`
- Citations use `role="doc-noteref"` linking to `role="doc-endnote"` in Sources
- Key Takeaways box uses `role="complementary"` with `aria-label="Key takeaways"`
- Streaming state announced: `aria-busy="true"` while streaming
- Source confidence badges have `aria-label` (e.g., "High confidence source")
- Tables use `<caption>` for context

---

## Responsive Behavior

| Breakpoint | Behavior |
|-----------|----------|
| `>= lg` | Full-width report with side margins |
| `md` | Slightly narrower, tables scroll horizontally |
| `< md` | Full-bleed report, tables in horizontal scroll container, export bar becomes full-width fixed bottom |
