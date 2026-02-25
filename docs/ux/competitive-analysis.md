# Deep Research UI — Competitive Analysis

> Extracted design patterns from 4 leading AI Deep Research interfaces.
> Date: 2026-02-24

---

## Table of Contents

- [1. Perplexity Deep Research](#1-perplexity-deep-research)
- [2. ChatGPT Deep Research](#2-chatgpt-deep-research)
- [3. Claude Research](#3-claude-research)
- [4. Grok DeepSearch](#4-grok-deepsearch)
- [5. Cross-Platform Pattern Comparison](#5-cross-platform-pattern-comparison)

---

## 1. Perplexity Deep Research

### Research Progress UI

**Three-Phase Progress Sidebar:**

| Phase | Duration | What's Shown |
|-------|----------|-------------|
| Query Interpretation | 10-20s | Sub-topics breakdown, clarifying questions if ambiguous |
| Research Execution | 1-2 min | Live search stats, source URLs being read, key findings streaming in |
| Synthesis | 30-60s | Drafting previews as report compiles |

- Key findings appear **during** research (partial results stream before completion)
- Users can add follow-up questions **while research is still running**
- Progress sidebar shows real-time source count and search activity
- On completion: report streams into a **file view** (editable); progress sidebar transitions to table of contents

### Typography

| Typeface | Role |
|----------|------|
| **FK Grotesk** | Headlines, UI body text — clean Scandinavian aesthetic |
| **FK Grotesk Neue** | Secondary body — optimized for reading |
| **Berkeley Mono** | Code/technical content (Regular + Bold) |
| **Newsreader** | Serif editorial accent |

| Style | Size | Line Height |
|-------|------|-------------|
| Super | 200px | 170px |
| Extra Large | 60px | 65px |
| Large | 40px | 42px |
| Medium | 14px | 19px |

- Content max-width: `42rem`
- Reports use H2/H3 hierarchy, short paragraphs, bold key facts, bullet points

### Color System

| Token | Hex | Usage |
|-------|-----|-------|
| True Turquoise | `#1FB8CD` | Primary brand accent |
| Background (dark) | `#1a1a1a` | Primary dark mode |
| Surface | `#242424` | Cards, elevated surfaces |
| Borders | `#3a3a3a` | Dividers |
| Primary Text | `#f5f5f5` | Body text (dark mode) |
| Muted Text | `#808080` | Secondary text |
| Cyan Accent | `#20b8cd` | Interactive elements, links |
| Paper White | `#F3F3EE` | Light mode background |
| Offblack | `#13343B` | Dark text (light mode) |

Dark mode uses layered surfaces (`#1a1a1a` -> `#242424` -> `#3a3a3a`) for depth. Bloomberg terminal inspired aesthetic.

### Animations

- Source favicons animate in as discovered
- Real-time thought streaming
- Results stream progressively (not all at once)
- Focus ring: `focus-within:border-[#20b8cd]` with `ring-[#20b8cd]/30`
- Hover scale: `105%` on interactive components
- Backdrop blur on overlays

### Citations

- Inline numbered footnotes `[n]` as superscript
- Expandable source snippets on click
- Source pills with favicons for quick scanning
- Hover previews on citations

### Results

- Table of contents at top
- H2/H3 section hierarchy
- Inline citations with numbered references
- Source confidence ratings (high/medium/uncertain)
- 5-15 pages, bolded key facts
- Export: PDF, Markdown, Perplexity Page, `.bib` citations

---

## 2. ChatGPT Deep Research

### Research Progress UI

**Activity Sidebar (Right Panel):**

| Element | Description |
|---------|-------------|
| Progress Bar | Loads at top; click to expand detail panel |
| Activity Log | Step-by-step transcript of actions (searches, site visits, reasoning) |
| Sources Panel | Toggle view showing websites being reviewed in real-time |
| Live Counters | Searches performed, sources consulted, elapsed time |
| Update Button | Mid-research prompt refinement without restart |

**Pre-Research Flow:**
1. Clarifying questions (via GPT-4.1 intermediate model)
2. Research plan shown for user review/edit
3. Research execution with push notifications when complete (5-30 min)

**Completion:** Push notification + email. Report opens in **fullscreen document viewer** (Feb 2026 update).

**Thinking/Reasoning:**
- Dynamic text labels flash during processing ("Thinking...", "Searching...", "Analyzing...")
- **Collapse-by-default**: reasoning auto-collapses when done
- Manual expansion reveals full chain of thought

### Typography

| Typeface | Role |
|----------|------|
| **Sohne (Soehne)** | Primary UI and body (Book, Demibold, Bold weights) |
| **Sohne Mono** | Code blocks (Regular, Demibold) |
| **OpenAI Sans** | Brand identity only (not chat UI) |

```css
font-family: 'Sohne', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
font-family: 'Sohne Mono', 'PragmataPro', Consolas, monospace; /* code */
```

9 variants total. Chosen for character width variation that makes AI text look more "human-written."

### Color System

| Token | Hex | Usage |
|-------|-----|-------|
| ChatGPT Green | `#10A37F` | Primary accent, CTA buttons |
| Pro Purple | `#AB68FF` | Premium tier indicator |
| Dark Background | `#343540` | Main surface (dark mode) |
| Sidebar | `#000000` | Sidebar background |
| User Message | `#3E3F4A` | User bubble (dark mode) |
| Body Text (dark) | `#F8F8F2` | Near-white text |
| White | `#FFFFFF` | Light mode background |

### Animations

- **SSE streaming**: word-by-word with fade-in opacity transition
- Blinking cursor at insertion point (`0.5s` keyframe)
- Sidebar slides in from right when research begins
- Activity log entries appear in real-time
- Smooth transition to fullscreen document viewer on completion

### Citations

- Numbered superscript `[n]` inline references
- Hover previews on citation numbers
- Dedicated Sources panel in document viewer right column
- Source metadata: publication dates, URLs

### Results (Fullscreen Document Viewer — Feb 2026)

**Three-Column Layout:**

| Left | Center | Right |
|------|--------|-------|
| Table of Contents | Report Content | Citations/Sources Panel |

- Reports span thousands of words (25-50 pages)
- Export: Markdown, Word (.docx), PDF, shareable URL
- Supports tables, images, embedded graphs
- Code execution via Python tool for visualizations

---

## 3. Claude Research

### Research Progress UI

| Element | Description |
|---------|-------------|
| Research Plan | Shows decomposition of question into sub-tasks (visible in real-time) |
| Thinking Indicator | "Thinking" label with running elapsed timer |
| Progress Bar | Fills toward 100% as research proceeds |
| Source Counter | Shows sources being downloaded (e.g., "450 sources") |
| Right Sidebar | Progress Tracker (completed/queued steps) + Context Manager |

- Research runs in **background** (tab can be closed)
- Standard: 5-15 min; Advanced: up to 45 min
- On completion: "Research complete" message, progress disappears
- **Expandable chain-of-thought** section above final response

### Typography

| Typeface | Role |
|----------|------|
| **Galaxie Copernicus** (Book) | Headlines, chat titles — transitional serif |
| **Styrene B** (Regular, Medium, Bold) | User input, UI elements — rounded sans-serif |
| **Tiempos Text** (400, 500) | Claude's response body — transitional serif |

- User messages: **sans-serif** (Styrene B)
- Claude responses: **serif** (Tiempos) — creates a "refined reading experience"
- Fallback: `ui-serif, Georgia, Cambria, "Times New Roman", serif`
- Content max-width: `max-w-3xl` (~768px)

### Color System

| Token | Hex | Usage |
|-------|-----|-------|
| Terra Cotta | `#C15F3C` / `#ae5630` | Primary accent (consistent light/dark) |
| Background (light) | `#F5F5F0` | Warm beige |
| Background (dark) | `#2b2a27` | Warm charcoal |
| Text (light) | `#1a1a18` | Near black |
| Text (dark) | `#eeeeee` | Off-white |
| Muted Text | `#6b6a68` | Secondary |
| User Bubble (light) | `#DDD9CE` | Light beige |
| User Bubble (dark) | `#393937` | Dark gray |
| Active Toggle | Blue | Research toggle enabled |

Design philosophy: "evening conversation rather than cold terminal." Warm tones intentionally anti-clinical.

### Animations

- **Shimmer effect** on thinking indicator (distinctive vs spinner/dots)
- Timer counter ticks during extended thinking
- Token-by-token streaming (typing/writing feel)
- Button feedback: `active:scale-[0.98]`
- Easing: `cubic-bezier(0.165, 0.85, 0.45, 1)` — organic feel
- Multi-layer shadows on composer

### Citations

- Numbered bracket citations `[1]`, `[2]` inline
- Passage-level attribution (Citations API)
- Expandable chain-of-thought reveals full search strategy
- Sources cross-referenced across documents

### Results

- Structured document with clear section headings
- Multi-paragraph content (15+ paragraphs)
- Inline `[n]` citations throughout
- Expandable reasoning trace above response
- Export: Markdown, PDF (with page numbers + ToC)
- Rounded containers: `rounded-2xl`

---

## 4. Grok DeepSearch

### Research Progress UI

**Distinctive Dual-Panel Layout:**

| Left Panel | Right Panel |
|------------|-------------|
| Progress bar + flow diagram showing chain-of-thought | Live thought process + real-time citations |

- Flow diagram animates through: searching -> analyzing -> refining
- 30-40 sources (standard) / 50+ sources (DeeperSearch)
- Up to 86-90 web pages per session
- Standard: 1-2 min; DeeperSearch: ~5 min
- On completion: **"Thoughts" toggle** remains for reviewing reasoning post-research
- X/Twitter integration as unique data source

### Typography

- 91+ typography styles across the design system
- Clean modern sans-serif for body/UI
- Standard monospace for code blocks
- Reports use rich Markdown: H2/H3 headings, tables, lists

### Color System

| Token | Hex | Usage |
|-------|-----|-------|
| Primary Background | `#1e1e1e` | Dark mode workspace |
| Secondary Surface | `#252526` | Tabs, panels |
| Elevated Surface | `#3c3c3c` | Active elements |
| Primary Text | `#d4d4d4` | Body text |
| Bright Text | `#ffffff` | Headings |
| Accent Blue | `#0079cb` | Interactive elements, links |

Monochromatic brand identity (black/white). 8 theme variants: Dark, Cyberpunk, Light, Blood Red, Midnight, Deep Ocean, Celestial, Divine.

### Animations

- Thinking spinner with visible deliberation time
- Token-by-token SSE streaming
- Flow diagram animates through research stages
- Dual-panel simultaneous updates (reasoning left, citations right)

### Citations

- Short 1-2 word hyperlinks inline: `[source](url)`
- **Key Citations** section at bottom (bulleted with ~10-word descriptive titles)
- X/Twitter posts cited with full attribution
- Invalid URLs silently excluded

### Results

**Two-Part Structure:**

1. **Direct Answer**: Short key points with inline URLs
2. **--- (divider)**
3. **Survey/Detailed Section**: Professional article expanding on the answer

- Sections: Executive Summary, Key Findings, Methodology, Critical Analysis, Implications
- Follow-up expandability via prompts
- Unique X/Twitter data integration alongside web sources

---

## 5. Cross-Platform Pattern Comparison

### Research Progress Timeline Pattern

| Feature | Perplexity | ChatGPT | Claude | Grok |
|---------|-----------|---------|--------|------|
| **Progress Location** | Right sidebar | Right sidebar | Inline + right sidebar | Dual-panel (left+right) |
| **Step Visibility** | 3 phases shown | Activity log | Plan + progress bar | Flow diagram |
| **Live Source Count** | Yes | Yes (searches + sources) | Yes | Yes |
| **Mid-Research Input** | Follow-up questions | Update button | No | No |
| **Background Execution** | No | Yes (notification) | Yes (tab closeable) | No |
| **Completion Behavior** | Streams into file view | Fullscreen document viewer | "Research complete" + report | Thoughts toggle + report |
| **Collapsible Progress** | Transitions to ToC | Auto-collapses thinking | Expandable chain-of-thought | "Thoughts" toggle |

### Typography Approach

| Platform | Primary Font | Response Style | Philosophy |
|----------|-------------|---------------|-----------|
| Perplexity | FK Grotesk | Sans-serif | Scandinavian/Bloomberg clean |
| ChatGPT | Sohne | Sans-serif | Human-like character variation |
| Claude | Tiempos/Styrene | Serif responses | Warm, editorial reading |
| Grok | System sans-serif | Sans-serif | Clean, minimal |

### Color Identity

| Platform | Primary Accent | Dark BG | Light BG | Mood |
|----------|---------------|---------|----------|------|
| Perplexity | `#1FB8CD` (turquoise) | `#1a1a1a` | `#F3F3EE` | Bloomberg terminal |
| ChatGPT | `#10A37F` (green) | `#343540` | `#FFFFFF` | Professional neutral |
| Claude | `#ae5630` (terracotta) | `#2b2a27` | `#F5F5F0` | Warm, conversational |
| Grok | `#0079cb` (blue) | `#1e1e1e` | varies | Monochromatic tech |

### Citation Patterns

| Platform | Inline Format | End-of-Report | Hover Preview |
|----------|--------------|---------------|--------------|
| Perplexity | `[n]` superscript | Source pills + favicons | Yes |
| ChatGPT | `[n]` superscript | Sources panel (3-col) | Yes |
| Claude | `[n]` brackets | Expandable chain-of-thought | No (click-through) |
| Grok | Hyperlinked words | Key Citations bulleted list | No |

### The Universal "Research Timeline -> Collapsible -> Results" Pattern

**All 4 platforms implement a variation of this pattern:**

1. **Active Research Phase**: Show a timeline/progress UI with real-time steps
2. **Transition**: Progress UI collapses, fades, or transforms
3. **Results Phase**: Full report replaces or sits below the collapsed progress

| Platform | Active State | Collapse Mechanism | Results Display |
|----------|-------------|-------------------|----------------|
| Perplexity | 3-phase sidebar | Sidebar -> ToC transition | File view (editable) |
| ChatGPT | Activity sidebar + progress bar | Auto-collapse thinking, fullscreen viewer | 3-column document |
| Claude | Plan + progress bar + timer | "Research complete" + expandable thinking | Inline structured report |
| Grok | Dual-panel flow diagram | "Thoughts" toggle (manual) | Two-part report |
