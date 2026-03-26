# Dashboard UI Design Rules
> Based on: [10 Rules for Better Dashboard Design](https://uxplanet.org/10-rules-for-better-dashboard-design-ef68189d734c) by Taras Bakusevych (UX Planet)

Use this document to guide agent-generated dashboard and data UI layouts. A usable dashboard must be **clear**, **meaningful**, **consistent**, and **simple**.

---

## Before You Build: Know Your Audience

- Identify who will use the dashboard and what decisions they need to make with it.
- Understand the user's data literacy level — segment views into basic and advanced if your audience varies.
- Select only the KPIs (Key Performance Indicators) that are relevant to the audience's goals. Avoid showing data just because it's available.

---

## The 10 Rules

### 1. Hierarchy
Present information according to importance — not all data is equal.

- Place the most critical stats in the **top-left** of the layout; less important content moves toward the bottom-right.
- Use **size and position** of widgets to signal priority.
- If there are many categories, consider splitting them across separate views or tabs rather than flattening everything onto one screen.

> ❌ Don't scatter key stats randomly across the layout.  
> ✅ Do put summary metrics (totals, alerts, KPIs) where the eye lands first.

---

### 2. Simplicity
The dashboard's job is to reduce complexity, not add to it.

- Show only what the user needs at a glance — avoid information overload.
- Use **fewer columns** to keep the layout scannable.
- Remove redundant, decorative, or low-value content that competes with meaningful data.

> ❌ Don't cram every available metric onto one screen.  
> ✅ Do trim the dashboard to its essential content.

---

### 3. Consistency
A consistent layout reduces cognitive effort and builds user trust.

- Use the **same chart types** for the same categories of data across the dashboard.
- Keep layout patterns uniform — if one section uses a card grid, use it throughout.
- Group related information visually and place it in predictable locations.

> ❌ Don't mix unrelated chart styles for comparable data sets.  
> ✅ Do use uniform visualization patterns to make comparison easy.

---

### 4. Proximity
Spatial grouping communicates relationships without labels.

- Place related data widgets **near each other**.
- Do not scatter related information across the layout.
- Use visual grouping (cards, borders, background zones) to cluster related content.

> ❌ Don't spread related metrics across opposite ends of the screen.  
> ✅ Do group related content into logical visual clusters.

---

### 5. Alignment
Aligned layouts feel intentional, polished, and easier to scan.

- Align all dashboard widgets to a **grid system**.
- Misaligned elements feel unfinished and undermine user confidence.
- Consistent alignment creates visual rhythm that guides the eye.

> ❌ Don't place widgets at arbitrary positions.  
> ✅ Do snap all elements to a shared grid.

---

### 6. Whitespace
Empty space is not wasted space — it improves readability.

- Give widgets and content areas room to breathe.
- Reducing whitespace causes a cluttered, overwhelming view that users abandon quickly.
- Use whitespace deliberately to reinforce proximity grouping.

> ❌ Don't fill every pixel with content.  
> ✅ Do use padding, margins, and spacing to separate and organize sections.

---

### 7. Color
Color should communicate meaning, not just decorate.

- Choose colors that maintain **high contrast** between text/data and background.
- Avoid inefficient gradients and low-contrast combinations.
- Use color intentionally: highlight alerts with red/amber, use neutral tones for standard data, and reserve accent colors for calls to action.
- Keep the color palette minimal to avoid visual noise.

> ❌ Don't use gradients or low-contrast palettes that obscure data.  
> ✅ Do use a controlled palette with clear contrast ratios.

---

### 8. Fonts
Typography directly affects how quickly users can process information.

- Use **standard, readable fonts** (e.g., system fonts or common sans-serifs like Inter, Roboto, or SF Pro).
- Avoid decorative or stylized fonts — they slow comprehension.
- Do not use all-caps text for body content; it is harder to read.
- Use font size and weight (not just color) to establish hierarchy.

> ❌ Don't use novelty fonts or all-caps labels for data content.  
> ✅ Do use clean, consistent typography scaled to hierarchy.

---

### 9. Number Formats
Over-precise numbers are harder to read and compare than rounded ones.

- **Round numbers** to the appropriate level of precision for the context (e.g., "1.2M" not "1,247,382").
- Truncate trailing zeros and unnecessary decimal places.
- Format large numbers with suffixes (K, M, B) to support quick scanning and comparison.

> ❌ Don't display raw unformatted numbers like `1247382.00`.  
> ✅ Do display compact, readable values like `1.2M`.

---

### 10. Labels
Labels must communicate clearly and stay out of the way.

- Avoid **rotated labels** — they are difficult to read and break scanning flow.
- Use standard abbreviations where widely understood.
- Keep axis labels, legends, and tooltips concise and unambiguous.

> ❌ Don't rotate axis labels 90°.  
> ✅ Do use horizontal labels, abbreviate where clear, and truncate with tooltips if needed.

---

## Summary Checklist for Agents

When generating a dashboard UI, verify:

- [ ] Most important data is in the top-left; least important toward bottom-right
- [ ] Only relevant KPIs are shown — no data padding
- [ ] Chart types are consistent for comparable data
- [ ] Related widgets are grouped spatially
- [ ] All elements are grid-aligned
- [ ] Sufficient whitespace separates sections
- [ ] Color palette has strong contrast; gradients avoided
- [ ] Standard readable fonts are used; no all-caps in data labels
- [ ] Numbers are rounded and formatted with K/M/B suffixes
- [ ] All labels are horizontal and concise