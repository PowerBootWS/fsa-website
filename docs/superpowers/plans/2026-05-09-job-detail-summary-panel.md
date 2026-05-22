# Job Detail Summary Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Style the AI-generated job summary as a visually distinct inset panel above the raw job description in the job detail view.

**Architecture:** Add a `.job-summary-panel` CSS class (inset card with left orange accent, matching the site's dark plate aesthetic) and update the JS `renderDetail()` function in `jobs.html` to conditionally render the summary inside this panel and the description as a plain section below it — only when both fields are present.

**Tech Stack:** Vanilla JS, CSS custom properties (existing design system), static HTML

---

### Task 1: Add `.job-summary-panel` CSS

**Files:**
- Modify: `styles-v2.css` (after line 2759 — end of `.job-detail-cta`)

- [ ] **Step 1: Open `styles-v2.css` and locate the end of the `.job-detail-cta` block (around line 2756–2759)**

The block looks like:
```css
.job-detail-cta {
  align-self: flex-start;
  margin-top: 0.5rem;
}
```

- [ ] **Step 2: Insert the following CSS immediately after `.job-detail-cta`**

```css
/* AI summary inset panel on job detail */
.job-summary-panel {
  background: var(--iron);
  border: 1px solid var(--plate-edge);
  border-left: 3px solid var(--orange);
  border-radius: 4px;
  padding: 1.2rem 1.4rem;
}

.job-summary-panel .job-summary-label {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--amber);
  margin-bottom: 0.6rem;
}

.job-summary-panel p {
  font-size: 0.92rem;
  color: var(--gray-light);
  line-height: 1.7;
  margin-bottom: 0.8rem;
}

.job-summary-panel p:last-child {
  margin-bottom: 0;
}
```

- [ ] **Step 3: Verify the file saved correctly by grepping for the new class**

Run: `grep -n "job-summary-panel" styles-v2.css`
Expected: 2–3 lines showing the new rules.

---

### Task 2: Update `renderDetail()` in `jobs.html`

**Files:**
- Modify: `jobs.html` (the `renderDetail()` function, around lines 364–413)

The current JS builds the detail view by setting `innerHTML` for `#detail-summary` and `#detail-description` as siblings inside `.job-detail-body`, each wrapped in a `.job-detail-section` div with an `<h3>` heading.

The HTML structure for the body currently is (static in the HTML file, lines 180–191):
```html
<div class="job-detail-body">
  <div class="job-detail-section">
    <h3>Summary</h3>
    <div id="detail-summary"></div>
  </div>
  <div class="job-detail-section">
    <h3>Description</h3>
    <div id="detail-description"></div>
  </div>
  <a id="detail-apply" ...>Apply on Company Website →</a>
</div>
```

The JS sets content via:
```js
document.getElementById('detail-summary').innerHTML = formatText(job.ai_summary || '');
document.getElementById('detail-description').innerHTML = formatText(job.description || '');
```

- [ ] **Step 1: Replace the static summary section in `jobs.html` (lines 181–184) with a container div that JS will populate**

Find this block in `jobs.html`:
```html
          <div class="job-detail-section">
            <h3>Summary</h3>
            <div id="detail-summary"></div>
          </div>
```

Replace with:
```html
          <div id="detail-summary-section"></div>
```

- [ ] **Step 2: In `renderDetail()` (around line 389), replace the line that sets `detail-summary` innerHTML**

Find:
```js
            document.getElementById('detail-summary').innerHTML = formatText(job.ai_summary || '');
```

Replace with:
```js
            var summarySection = document.getElementById('detail-summary-section');
            if (job.ai_summary && job.description) {
              summarySection.innerHTML =
                '<div class="job-summary-panel">' +
                  '<div class="job-summary-label">AI Summary</div>' +
                  formatText(job.ai_summary) +
                '</div>';
            } else if (job.ai_summary) {
              summarySection.innerHTML =
                '<div class="job-detail-section">' +
                  '<h3>Summary</h3>' +
                  '<div>' + formatText(job.ai_summary) + '</div>' +
                '</div>';
            } else {
              summarySection.innerHTML = '';
            }
```

- [ ] **Step 3: Update the description section label to remove the "Description" heading when summary panel is shown (optional but clean)**

Find:
```js
            document.getElementById('detail-description').innerHTML = formatText(job.description || '');
```

Replace with:
```js
            var descEl = document.getElementById('detail-description');
            if (descEl) descEl.innerHTML = formatText(job.description || '');
```

(No change needed here — the description `<h3>Description</h3>` heading in the static HTML is fine to keep as-is.)

- [ ] **Step 4: Verify the page renders correctly**

Open `jobs.html?id=<any-valid-id>` in a browser (or via local dev server). Confirm:
- When `ai_summary` and `description` are both present: summary appears as an orange-left-accented inset panel; description appears below as a plain section.
- When only `ai_summary` is present (no description): summary renders in the old flat section style.
- When neither is present: no panel is shown.

---

### Task 3: Deploy

- [ ] **Step 1: Commit changes**

```bash
git add styles-v2.css jobs.html
git commit -m "feat: style AI summary as inset panel on job detail view"
```

- [ ] **Step 2: Deploy using the `fsa-website-deploy` skill**

Invoke skill: `fsa-website-deploy`

