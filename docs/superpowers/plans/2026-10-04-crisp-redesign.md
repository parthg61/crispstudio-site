# Crisp Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the look of all pages on the Crisp Design System, keeping copy and page structure.

**Architecture:** Static HTML/CSS/JS served by GitHub Pages. Shared header, footer and `<head>` live once in `src/partials/`; `tools/build.py` stamps them into each page body in `src/pages/` and writes the final `index.html` files. Styles are `css/tokens.css` (generated from the design system's `tokens.json`) plus `css/site.css` (components and page layouts). `tools/check.py` is the automated test: it fails on any value outside the design system.

**Tech Stack:** HTML, CSS (custom properties, container-free grid), vanilla JS, Python 3 build/check scripts, Schibsted Grotesk (Google Fonts), Lenis dropped.

**Spec:** `docs/superpowers/specs/2026-10-04-crisp-redesign-design.md`. Design system tokens: `scratchpad/artifact-files/d02da3dd-07f0-4eed-82f8-c56ba7ebac07/project/tokens.json` (copy to `tools/tokens.json` in Task 1).

## Global Constraints

- Font: Schibsted Grotesk 400 and 600 only; no other family.
- Colours only from tokens: `#021F53 #FF8A00 #FF6A00 #CC4806 #FECA98 #FD9F0F #FFFFFF #F4F4F2 #ECECE9 #DEDEDA #E6E6E2 #4A5675`.
- No navy, cream or orange card/section backgrounds. Orange never as text on white; text on orange is navy.
- Radius only 8, 12, 16, 24, 32 px or 50%. Buttons 12px, 48px tall (small 40px), never pills.
- Spacing values only from 4, 8, 12, 16, 24, 32, 48, 64, 96, 128 px (or the clamp tokens in `tokens.json`).
- Shadows only the seven tokens; no offset/hard shadows, no borders thicker than 1.5px.
- Body 18px desktop / 16px mobile, text measure at most 65ch; tracking never tighter than -1%.
- No highlight, marker or squiggle behind headline words. No scroll-reveal animation. `prefers-reduced-motion` respected.
- Copy is unchanged from the current pages (design only). Site email stays `team@crispstudio.in`.
- Logo files used as supplied, straight on white or grey, never in a dark box. Cats only in 404, contact success and empty states.
- Light theme only; keep URLs (`/`, `/services/`, `/work/`, `/about/`, `/blog/`, `/contact/`, `/404.html`).

## Review Focus

- Very long client or post names must wrap inside cards without overflow (375px).
- Blog with 1 or 2 posts shows them without the empty state; zero shows only the empty state.
- Contact form: submitting with nothing checked keeps focus on the first invalid field and shows its error; endpoint failure keeps entered values.
- Keyboard-only use: every interactive element shows an orange focus ring and the mobile menu closes on Escape.
- Reduced-motion users get no autoplaying video: the hero shows the still logo.

---

### Task 1: Tokens, build pipeline and the check script

**Files:**
- Create: `tools/tokens.json` (copy), `tools/tokens_to_css.py`, `css/tokens.css`, `tools/build.py`, `tools/check.py`, `src/partials/head.html`, `src/partials/header.html`, `src/partials/footer.html`
- Modify: `.gitignore` (none expected)

**Interfaces:**
- Produces: CSS custom properties named exactly as `tokens.json` (`--navy`, `--orange`, `--surface`, `--space-1`…`--space-10`, `--radius-sm`…`--radius-2xl`, `--pad-section`, `--layout-margin`, `--gap-*`, `--shadow-*`, type styles as `--fs-display-xl` etc.); `python3 tools/build.py` writes every `src/pages/<slug>.html` to `<slug>/index.html` (`home` to `index.html`, `404` to `404.html`); `python3 tools/check.py` exits 0 only when every rule in Global Constraints holds for `css/*.css` and all built HTML.

- [ ] **Step 1: Write `tools/check.py` first.** Functions `check_css(path) -> list[str]`, `check_html(path) -> list[str]`; print each violation and exit 1 if any. Rules: hex colours not in the allowed list; `font-family` not Schibsted; `border-radius` not in the allowed set; `box-shadow` containing a positive x/y offset with 0 blur; `border` width above 1.5px; `border-radius:999px`; `reveal` or `squiggle` classes in HTML; `<img>` without `alt`.
- [ ] **Step 2: Run it against the current site.** Run: `python3 tools/check.py`. Expected: FAIL with many violations (Inter, outlines, pills), proving the check bites.
- [ ] **Step 3: Implement `tools/tokens_to_css.py`** reading `tools/tokens.json` and writing `css/tokens.css` (`:root` variables; desktop type scale as `--fs-*`/`--lh-*`, mobile overrides under `@media (max-width:599px)`; resolve `{alias}` colours).
- [ ] **Step 4: Implement partials and `tools/build.py`.** `head.html` takes `{{title}}`, `{{desc}}`, `{{slug}}`; header marks `aria-current="page"` for the current slug; footer has the five links, `team@crispstudio.in`, Mumbai, three social links (`#` placeholders), `© <year> Crisp. All rights reserved.` Nav: Work · Services · About · Blog · Let's chat (small primary button). Uses the Google Fonts link for Schibsted Grotesk 400;600.
- [ ] **Step 5: Run build and check.** Run: `python3 tools/tokens_to_css.py && python3 tools/build.py`. Expected: pages written; `check.py` still fails only for the old `css/site.css` (replaced in Task 2).
- [ ] **Step 6: Commit.** `git add tools css/tokens.css src && git commit -m "Add design-system tokens, build pipeline and check script"`

### Task 2: Components and Home

**Files:**
- Replace: `css/site.css` (components and layout only; every value via tokens)
- Create: `src/pages/home.html`
- Modify: `js/site.js` (keep nav, logo ticker, blog block; remove reveal, tape, cycle, Lenis, hero-handoff except the crunch clip)

**Interfaces:**
- Produces components used by Tasks 3–5: `.btn`, `.btn--secondary`, `.btn--sm`, `.card`, `.tile`, `.chip`, `.tag`, `.bullets`, `.field`, `.input`, `.table`, `.section`, `.section--lg`, `.wrap`, `.grid-12`, `.stack`, `.label`.

- [ ] **Step 1: Extend `check.py` with a Home test:** `home` HTML contains the exact strings `Design with a crunch!`, `Good work speaks for itself.`, `Brands we've been baking for!`, `Strategy. Brand. Product. Build.`, `Design that has a job to do.`, `Got something worth making?`; fails if missing.
- [ ] **Step 2: Run it.** Expected: FAIL (page not written yet).
- [ ] **Step 3: Write `css/site.css`** with the components above using only tokens; nav 72px with `shadow-nav` after scroll; primary button orange with navy text, hover `--orange-hover`; secondary white with `shadow-outline`, hover `shadow-outline-hover` and orange text; inputs 48px, `--surface-3` border, 2px orange focus ring; global `:focus-visible` ring.
- [ ] **Step 4: Write `src/pages/home.html`** per spec: Display XL headline left and 32px grey block right holding `Crisp_Avatar`-free full-colour croissant logo with `--shadow-logo` (video clip inside only if it passes the grey-ground check below; reduced motion shows the still); work cards row (HDFC securities, The Mind Mojo, NMIMS, NDA card with lock icon); ticker; four "What we do" tiles linking to `/services/#strategy` `#branding` `#product` `#build`; Why Crisp statement; blog block `hidden` until 3 posts; closing block.
- [ ] **Step 5: Run build and check; open in browser at 1440, 1024, 375.** Expected: `check.py` exit 0; no horizontal scroll; headline never orphans a word; screenshot reviewed.
- [ ] **Step 6: Commit and push.** `git commit -m "Rebuild components and Home on the design system" && git push origin site-v1`

### Task 3: Services

**Files:** Create `src/pages/services.html`; modify `css/site.css` (services layout only).

**Interfaces:** Consumes Task 2 components. Produces anchors `#strategy #branding #product #build #process` that Home links to.

- [ ] **Step 1: Add check:** services HTML contains `Get the mix right.`, `Don't design the wrong thing beautifully.`, `Position first. Pixels second.`, `Make complex feel simple.`, `If we designed it, we build it.`, `Built for people. Designed for business.` and all five ids above.
- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Write the page:** sticky left index (hidden below 1024px), four long sections with curl-bullet "Problems we unpack", chips for "What we do", capability table on grey (UX Design … Prototyping), business panel as a grey card, "How we work" as a four-row stage table (the only numbered content), closing CTA.
- [ ] **Step 4: Build, check, view at 375/1024/1440; click each Home tile link and confirm it lands on its section.** Expected: exit 0, anchors resolve.
- [ ] **Step 5: Commit and push.**

### Task 4: Work

**Files:** Create `src/pages/work.html`; modify `css/site.css` and `js/site.js` (filter).

**Interfaces:** Consumes Task 2 components. Produces `.case` tile and `data-services` filter hook `[data-filter]`.

- [ ] **Step 1: Add check:** work HTML contains `Fresh from the Oven.`, the six client names, `Want to see more?`, and each `.case` has a visual, a tag, a one-line description.
- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Write the page:** hero, filter chips (All / Strategy & Research / Branding / Product Design / Build, `aria-pressed`), six large grey case tiles with client logo on `--surface-2` visual, Pandora's Box grey card with lock icon and closing CTA.
- [ ] **Step 4: Verify** filter shows only matching tiles and updates the count; 375px has no overflow with "HDB Financial Services". Expected: pass.
- [ ] **Step 5: Commit and push.**

### Task 5: About, Blog, Contact, 404

**Files:** Create `src/pages/about.html`, `blog.html`, `contact.html`, `404.html`; modify `css/site.css`, `js/site.js` (blog list and form logic carried over).

**Interfaces:** Consumes Task 2 components; form markup keeps ids `contact-form`, `f-needs`, `form-done`, `form-note` and `data-endpoint=""`.

- [ ] **Step 1: Add checks:** copy strings for each page (`No half-baked ideas.`, `Food for thought.`, `Let's make something crispy.`, `Got it. We'll be in touch within two working days.`); contact has the five fields and five checkboxes.
- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Write the pages** per spec; Samosa/Idli (use the avatar asset until cat artwork is supplied, flagged to the user) only in the success state and 404; empty blog state uses a grey card with a primary button.
- [ ] **Step 4: Verify behaviours in the browser:** empty submit lists four errors and focuses the name field; valid submit with a stubbed endpoint shows the success state; blog with a 1-item and a 3-item `posts.json` renders correctly (restore the file after).
- [ ] **Step 5: Commit and push.**

### Task 6: Whole-site verification

**Files:** Modify only what verification finds; update `sitemap.xml` if URLs change; update the memory note `crisp-site-build.md`.

- [ ] **Step 1: Run `python3 tools/build.py && python3 tools/check.py`.** Expected: exit 0.
- [ ] **Step 2: For each of 7 pages at 375, 768, 1024, 1440:** no horizontal scroll, no console errors, tab through the page and see the focus ring, contrast spot-check on muted text and button text.
- [ ] **Step 3: Reduced motion:** emulate it; hero shows the still logo, nothing autoplays.
- [ ] **Step 4: Fix anything found, re-run Steps 1–3, commit, push.** Report results with screenshots.
