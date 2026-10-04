# Crisp Livelier Redesign Implementation Plan (round 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the site livelier without leaving the design system: one logo that travels from the Home hero into the navbar, Idli and Samosa in small friendly moments, official icons, and more personality in layout and interaction.

**Architecture:** Same static site and pipeline as round 1 (`src/pages` + `src/partials` → `tools/build.py`; `css/tokens.css` + `css/site.css`; `js/site.js`; `tools/check.py` is the lint/test). Only edits to those; the spec decides all values.

**Tech Stack:** HTML, CSS, vanilla JS, Python build/check scripts. Official assets already in `assets/cats/` and `assets/icons/` (hashes in `tools/assets.sha256`).

**Spec:** `docs/superpowers/specs/2026-10-04-crisp-livelier-design.md` (extends `2026-10-04-crisp-redesign-design.md`). Design system book: `/private/tmp/claude-501/-Users-parthgupta-Library-CloudStorage-GoogleDrive-parthg61-gmail-com-My-Drive-Crisp-Studio-Website/85cf1661-ee73-4f7f-a6e3-ca6561b9659e/scratchpad/artifact-files/d02da3dd-07f0-4eed-82f8-c56ba7ebac07/project/README.md` and `components/CatAvatar/README.md`, `components/CardIcon/README.md` in the same folder.

## Global Constraints

- All round-1 constraints still hold: Schibsted Grotesk 400/600 only; token colours/radius/spacing/shadows only; buttons 12px/48px orange with navy text; no navy/cream/orange card backgrounds; no outlines, offset shadows, pills, gradients, highlight behind headline words; light only; contrast >= 4.5:1; no lone last-line words in any h1/h2/h3 at 375/768/1024/1440; copy unchanged.
- Exactly one logo visual per page (the navbar logo); on Home it starts large in the hero and travels into the navbar slot on scroll.
- Cats: official files only, never recoloured, never in a hero or beside client work or on the Work page; avatars are circles (96px or 48px); loops (blink, tail sway) and hover/tap motion are off under `prefers-reduced-motion`.
- Everything that moves on its own (card fan, logo travel, marquee, ticker, cat loops) respects `prefers-reduced-motion`; both marquee/ticker have a visible pause/play button reachable by keyboard.
- `python3 tools/check.py` and `python3 tools/test_check.py` stay green; every task adds its own check first (TDD).

## Review Focus

- Scroll-travel logo: no flash of two logos, no jump at the end of the move, correct position after resize and after load at a scrolled position (e.g. reload mid-page), and tab/keyboard focus stays on the link in the navbar.
- Reduced motion and no-JS users see exactly one logo (the navbar) and no animation.
- Cat loops never run for reduced motion; cats never appear inside `.hero`, on `work/`, or beside `.case`/work cards.
- Marquee/ticker pause button: keyboard operable, state announced (`aria-pressed`/label), pausing really stops the animation.
- Bento grid and hero fan do not overflow at 375px and keep the headline free of lone last-line words.

---

### Task 1: One logo, cats and official icons wired in (sitewide)

**Files:**
- Modify: `src/partials/header.html`, `src/partials/footer.html`, `src/pages/{home,services,work,about,blog,contact,404}.html`, `css/site.css`, `js/site.js`, `tools/check.py`, `tools/test_check.py`; rebuild all pages.

**Interfaces:**
- Produces: `.cat` (inline `<img>` helper: sizes `.cat--96`, `.cat--48`, `.cat--body`), `.cat-peek` (pair peeking over the top edge of a card or footer; blink/sway loops via CSS only), `.icon-chip` (56px official icon on a `--surface-2` square, tilt on hover), header slot `<a class="brandmark" data-logo-slot>` consumed by Task 2.

- [ ] **Step 1: Extend `tools/check.py` first:** (a) no `<img>` outside `<header>` whose `src` contains `Crisp_Logo` or `Crisp_Avatar_Orange`/`Crisp_Avatar_Navy`; (b) a cat asset (`Crisp_Cat_*`, `Crisp_Avatar_Samosa|Idli`) must not appear on `work/index.html` or inside a `.hero` element; (c) every file listed in `tools/assets.sha256` exists and matches its hash; (d) CSS: cat loop animations must be wrapped in `@media (prefers-reduced-motion: no-preference)`. Add tests proving each rule fires and passes.
- [ ] **Step 2: Run `python3 tools/check.py`.** Expected: FAIL (hero block logo, closing avatars, footer logo, stand-in avatars).
- [ ] **Step 3: Remove every non-header logo/avatar usage** (Home hero block and closing block, Services/About/Contact/Blog closing blocks, footer brand image — keep the "Design with a crunch!" text, 404, blog empty, contact success) and place cats per the spec: Contact pair peeking over the form card top edge + success shows the two avatars; 404 full-body pair; Blog empty Idli avatar 96px; About Samosa avatar 48px; Services closing Samosa avatar 48px; Home closing pair peeking over the closing card (do not put cats in `.hero`); footer Idli peeking over the top edge (small). Alt text empty for decorative cats (the heading carries meaning).
- [ ] **Step 4: Replace CSS-mask curl bullets/spinner with the official `assets/icons/Crisp_Bullet_Curl.svg` / `Crisp_Spinner_Curl.svg`**, and draw `assets/icons/Crisp_Icon_Strategy.svg` (56px grid; magnifier, navy ring and handle, orange lens dot, cream fill; same recipe) plus add its hash to `tools/assets.sha256`.
- [ ] **Step 5: Build, run check and tests; verify in the browser at 375/1440:** one logo per page, cats visible and positioned, hover tilt, loops stop under reduced motion (check by reading the media query/evaluating `getAnimations()` with the rule applied), no overflow. Commit: `git commit -m "One logo, Idli and Samosa and official icons across the site"`.

### Task 2: Home hero: travelling logo and fanned work cards

**Files:** Modify `src/pages/home.html`, `src/partials/header.html` (slot), `css/site.css`, `js/site.js`, `tools/check.py`, `tools/test_check.py`; rebuild `index.html`.

**Interfaces:**
- Consumes: Task 1's `[data-logo-slot]`.
- Produces: `function initLogoTravel(): void` in `js/site.js` (reads `.hero [data-hero-logo]` and `[data-logo-slot]`; progress `p = clamp(scrollY / 320, 0, 1)`; sets transform/size by interpolating the two rects; hides the slot until `p === 1`; recomputes on `resize` and on load; does nothing when `matchMedia('(prefers-reduced-motion: reduce)')` matches or on pages without a hero logo, in which case the slot shows the navbar logo normally); `.fan` hero card stack.

- [ ] **Step 1: Add checks first:** Home has exactly one `data-hero-logo` element and it is inside `.hero`; the header slot exists on all pages; `initLogoTravel` is defined and called only when the hero logo exists; `.fan` cards (3) exist in the hero with the client names; the fan animation lives inside `@media (prefers-reduced-motion: no-preference)`. Run: FAIL.
- [ ] **Step 2: Build the hero:** left column Display XL "Design with a crunch!" (bold) + lede at lighter weight (400) with the existing clause in semibold, Let's chat button; right column: big hero logo (full colour, `--shadow-logo`) above three tilted client cards (HDFC, Mind Mojo, NMIMS on `--surface` with `--surface-2` logo areas) on a grey block; on load the cards fan out once (CSS animation, `--ease`, 700ms staggered), then lift on hover (shadow-md). Mobile: smaller logo, cards stack tighter, no overflow.
- [ ] **Step 3: Implement `initLogoTravel`** (fixed-position hero logo; interpolation per the interface; `will-change: transform`; `pointer-events: none` until docked; once docked the navbar link works; after reload at a scrolled position it renders docked immediately; no duplicate logo at any scroll position).
- [ ] **Step 4: Verify in the browser at 375/768/1024/1440:** at scroll 0, 160, 320, 600 and after resize there is exactly one logo visible (assert via DOM: count visible logo imgs by bounding rect), the move ends exactly on the navbar slot rect (within 1px), keyboard Tab reaches the navbar logo link, no horizontal scroll, headline has no lone last-line word, reduced motion (apply `@media` rules / evaluate `getAnimations()`) shows only the navbar logo. Commit.

### Task 3: Home sections: bento, marquee, hover and Why Crisp

**Files:** Modify `src/pages/home.html`, `css/site.css`, `js/site.js`, `tools/check.py`, `tools/test_check.py`; rebuild.

**Interfaces:** Produces `.bento` grid (tall + wide + two small tiles), `.marquee` with `[data-pause]` button (`aria-pressed`, label "Pause"/"Play" toggling), `.card-go` (orange arrow circle that appears on card hover), `.why-statement`; consumes Task 1's `.icon-chip`.

- [ ] **Step 1: Add checks first:** Home "What we do" has four tiles inside `.bento` linking to `#strategy #branding #product #build` with the official icons (Strategy/Branding/Product(UIUX)/Build(DesignToCode)) and their tags; a `.marquee` containing the four service names (copy exactly: Strategy & Research, Branding, Product Design, Build) with a pause button; the client-logo ticker has a pause button; `.why-statement` contains "Everything we make has a job" text from the existing Why Crisp copy (do not reword the paragraph; the swapping job words are clarify, engage, convert, simplify, move someone to act). Run: FAIL.
- [ ] **Step 2: Build the sections per spec:** bento "What we do" (one tall, one wide, two small tiles; icon chip top, name, line, tags); Services marquee at Display size with orange curl separators, slow, pause button; client ticker gets the same pause button (JS `initPausables()`); work cards: visual zoom 1.04 and orange arrow circle on hover/focus-visible; Why Crisp as a very large statement with the job words swapping in place (no highlight; paused under reduced motion); keep copy exact and the blog block behaviour.
- [ ] **Step 3: Verify in the browser at 375/768/1024/1440:** no overflow, heading audit (no lone last-line words), pause buttons work with keyboard (Space/Enter) and `getAnimations()` reports paused, reduced motion shows static strips, hover states visible, contrast >= 4.5:1 for new text. Commit and push.

### Task 4: Work and Services liveliness (round 2 after the user sees Home)

**Files:** Modify `src/pages/work.html`, `src/pages/services.html`, `css/site.css`, `js/site.js`, `tools/check.py`; rebuild.

- [ ] **Step 1: Checks first:** Work cases render as numbered frame strips (client name left; frames `01`…`0N` right; tags and one line under; frame visuals are the client logo on `--surface-2` plus 2 neutral grey placeholder frames labelled by number only); no cat on the page; Services sections use the official icons on `.icon-chip` (Strategy, Branding, Product, Build) and the Services marquee is not duplicated. Run: FAIL.
- [ ] **Step 2: Build** with the same hover/arrow treatment and bigger scale contrast; keep filter behaviour and counts; Services keeps its sticky index and tables. Keep all copy.
- [ ] **Step 3: Verify** at four widths (overflow, filter, headings, contrast); commit and push.

### Task 5: About, Contact, Blog, 404 liveliness and whole-site verification

**Files:** Modify `src/pages/{about,contact,blog,404}.html`, `css/site.css`, `tools/check.py`; rebuild.

- [ ] **Step 1: Checks first:** headings and sections keep copy; one `.cat-peek` pair on Contact only; no logo outside the header on any page; all pages have exactly one visible logo (script-assert in the verification step).
- [ ] **Step 2: Apply the alternating narrow-heading/full-width-band rhythm and larger scale contrast to About; keep Contact, Blog and 404 as built in Task 1 with polish only.**
- [ ] **Step 3: Whole-site verification:** `python3 tools/build.py && python3 tools/check.py && python3 tools/test_check.py`; 7 pages x 4 widths: overflow, console errors, one visible logo, lone-word audit, contrast minimum, reduced motion (no animations running), Tab through each page; report a raw measurement table and 6 screenshots. Commit and push.
