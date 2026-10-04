# Crisp redesign, round 2: livelier look, one logo, Idli and Samosa

Date: 2026-10-04 · Branch: `site-v1` · Extends `2026-10-04-crisp-redesign-design.md` (all of its design-system rules still apply; this spec only adds to it and overrides where stated).

## Why
The user found the first build "too boring" and said the Crisp logo appears in too many places. Direction chosen with the user: bolder *inside* the design system; logo appears **once**, big in the Home hero, and travels into the navbar on scroll; Idli and Samosa are sprinkled in; inspiration from the Sumi board v2 (`.sumi/refs/board.md`: Direct Design Agency, Rebelliously Optimistic, Huy Phan, Gil Huybrecht).

## Logo (overrides the old spec)
- Exactly one logo visual per page: the navbar logo. Remove every other use: Home hero block, closing-block avatar, footer logo, blog/contact/404 avatars, and any `Crisp_Avatar_*` / `Crisp_Logo_*` img outside the header.
- Home only: a large full-colour logo in the hero (with `--shadow-logo` drop-shadow). On scroll it travels and scales into the navbar logo slot and stays there (shared-element move, driven by scroll position with JS; interpolate the hero logo's rect to the nav slot's rect over the first ~320px of scroll). The navbar logo slot is empty (visibility hidden) while the hero logo is large and the move is incomplete; the hero logo is the same element, `position: fixed`, so it is never duplicated.
- Fallbacks: no JS → plain navbar logo only and no hero logo. `prefers-reduced-motion` → no travel; navbar logo only, hero shows the work cards. Other pages: navbar logo only. Mobile (<600px): same travel with a smaller hero logo; the nav bar logo stays tappable (links to `/`).

## Cats: Idli and Samosa (official artwork, never recoloured, no new expressions)
Files are in `assets/cats/`: `Crisp_Cat_Samosa.svg`, `Crisp_Cat_Idli.svg`, `Crisp_Cat_Idli_Cream.svg` (full body, viewBox -4 0 108 96) and `Crisp_Avatar_Samosa.svg`, `Crisp_Avatar_Idli.svg` (round, 100x100). Design-system rules: small friendly moments only; **never in the hero or next to client work**; avatars are circles at 96px (feature) or 48px; hover tilt, quick squash on tap; looping motion (blink every few seconds, gentle tail sway) stops with `prefers-reduced-motion`. Placements:
- Contact: full-body Samosa (burnt) and Idli (`Crisp_Cat_Idli_Cream`) peeking over the top edge of the form card; success state shows the two round avatars.
- 404: full-body Samosa and Idli.
- Blog empty state: Idli avatar 96px. About: Samosa avatar 48px next to the closing block text, tilt on hover.
- Home: the pair peeking over the top edge of the closing block (not in the hero, not by the work cards).
- Footer: Idli peeking over the footer's top edge, small. Services closing block: Samosa avatar 48px.
Not on: Work page, hero sections, work cards.

## Icons (official, from the design system)
`assets/icons/`: `Crisp_Icon_UIUX.svg` (Product Design), `Crisp_Icon_Branding.svg` (Branding), `Crisp_Icon_DesignToCode.svg` (Build), `Crisp_Bullet_Curl.svg`, `Crisp_Spinner_Curl.svg`. Strategy & Research has no official icon: draw one `Crisp_Icon_Strategy.svg` with the same recipe (56px grid, rounded ends, at most navy/orange/cream, no outlines on filled shapes, no gradients/shadows; a magnifier with an orange lens dot). Icons are decorative (`aria-hidden`), tilt -10° and grow 6% on hover (off for reduced motion). Use the official curl bullet and spinner files instead of CSS-mask look-alikes.

## Livelier layout and interaction (all inside the design system)
- **Home hero:** left: Display XL headline with a bold line and a lighter-weight lede (one family, two weights), button; right: the three client cards (HDFC, Mind Mojo, NMIMS) stacked and tilted on a grey block; on load they fan out once in perspective (the single Home load animation), then lift on hover. The big logo sits above the fan and travels to the navbar on scroll.
- **What we do:** bento grid (one tall tile, one wide, two small) with the official icons (icon on a `--surface-2` tile; orange only in the icon itself) and the service tags inside tiles.
- **Services marquee:** a slow strip of the four service names at Display size with orange curl marks between, with a visible pause/play button (also stops with reduced motion). The client-logo ticker gets the same pause button.
- **Work cards (Home and Work page):** visual zooms slightly on hover and an orange arrow circle appears (navy arrow on orange); Work page uses numbered frame strips: client name left, frames 01–0N right, tags and one line under (Gil Huybrecht reference). No cats here.
- **Why Crisp:** one very large statement ("Everything we make has a job") with the job words swapping in place (no highlight behind words; stops with reduced motion).
- **Rhythm:** alternate a narrow left heading column with full-width bands; bigger scale contrast; more white space between sections.
- Motion budget: one load moment on Home (card fan), the logo scroll-travel, hover/tap feedback, marquee and ticker (both pausable), cat loops. Nothing else animates on scroll.

## Unchanged
Copy, palette tokens, Schibsted Grotesk, 12px buttons, no navy sections, no outlines/offset shadows/pills, light only, 4.5:1 contrast, no lone last-line words in headings, `tools/check.py` rules (extended below).

## Verification additions
`tools/check.py` must also fail when: any `<img>` outside `<header>` references a path containing `Crisp_Logo` or `Crisp_Avatar_Orange`/`Crisp_Avatar_Navy`; a cat asset appears on `work/index.html` or inside a `.hero`; a `Crisp_Cat_*`/`Crisp_Avatar_Samosa|Idli` file is missing or modified (compare against the design system sha256 values recorded in `tools/assets.sha256`). Manual: scroll-travel works at 375/768/1024/1440, reduced motion removes all loops and the travel, keyboard can pause both marquees.
