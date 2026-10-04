# Crisp site redesign: design spec

Date: 2026-10-04 · Branch: `site-v1`

## Goal
Rebuild the visual layer of all six pages (Home, Services, Work, About, Blog, Contact, plus 404) so the site follows the Crisp Design System (artifact `d02da3dd-07f0-4eed-82f8-c56ba7ebac07`, README dated 4 Oct 2026) exactly. Copy and page structure stay as written; only design changes.

## Source of truth
Design system tokens and README, saved locally at the session scratchpad and mirrored into `css/tokens.css`. Rules that override earlier decisions (the Sumi board, the old brand skill):
- Light only. White page, grey surfaces (`#F4F4F2`, `#ECECE9`, `#DEDEDA`), hairline `#E6E6E2`.
- Orange `#FF8A00` for buttons/icons/small highlights only; text on orange is navy `#021F53`; hover `#FF6A00`; coloured text uses burnt `#CC4806`; orange is never text on white.
- No navy, cream or orange card backgrounds; no navy sections.
- Schibsted Grotesk 400/600 only; scale 88/64/44/32/24/20/18/14/12 (mobile 48/40/32/26/22/18/16); tracking never tighter than -1%; body 65ch max; no highlight or marker behind headline words.
- Buttons: 12px radius, 48px (small 40px), never pills. Secondary: white, hairline border, text and outline orange on hover.
- Radius jobs: 8 chips, 12 buttons/inputs, 16 images in cards, 24 cards, 32 large blocks, 50% avatars/dots only.
- Spacing only from the 10-step scale; section padding 48→96, hero/work/closing 64→128; gutter 16→32; margin 16→64; max 1280.
- Shadows: soft navy-tinted tokens only. No offset/hard shadows, no thick outlines.
- Logo files unchanged and straight on white/grey, never in a dark box. Cats (Samosa, Idli) only in small moments (404, contact success, empty states).

## Components
Nav (72px, white, 1px line after scroll), buttons (primary/secondary/small), grey card, chip/tag, curl bullet, input (48px, `surface-3` border, orange focus ring), form card, table on grey, footer.

## Pages
- **Home:** Display XL headline + big grey block (32px) with croissant logo and `shadow-logo`; row of grey work cards directly beneath; logo ticker; four large grey "What we do" tiles linking to Services anchors; "Why Crisp" statement; blog block (hidden until 3 posts); closing block.
- **Services:** sticky left index of the four services beside long reading sections; capability table and four-stage process as plain grey tables (these are real sequences, so numbering is allowed); closing CTA.
- **Work:** vertical list of large grey case tiles (visual, sector/service tags, one-line description, link only if a case study exists); filter by service; the Pandora's Box as a grey card with lock icon.
- **About:** large statement type; three "it's not done" lines as stacked grey rows; difference and audience sections; closing CTA.
- **Blog:** grey post cards from `posts.json`; empty state invites action.
- **Contact:** one grey form card; validation and `data-endpoint` behaviour kept; Samosa/Idli on success.
- **404:** cat moment, link home.

## Motion
One moment per page. Home: the Remotion croissant clip plays in the grey block if it reads correctly on `#F4F4F2`, otherwise a still logo. No scroll-reveal animations. Interaction feedback (hover, focus, form states) only. `prefers-reduced-motion` respected.

## Removed
Squiggle underlines, gold headline words, crumbs, tape bands, recipe card, fan tiles, offset shadows, outlines, pills, every navy section, Inter, the old `.reveal` system.

## Implementation notes
- Replace `css/site.css` wholesale; add `css/tokens.css` generated from `tokens.json`. Keep `js/site.js` behaviours (nav, blog, form, filter, logos), drop the removed effects.
- Keep file layout and URLs. Reuse local logo/client assets; official Crisp-Assets CDN links are the fallback.
- Verify each page at 375, 768, 1024 and 1440px: no horizontal scroll, keyboard focus visible, contrast 4.5:1, no console errors.
- Commit per page group and push `site-v1`; `main` stays untouched until launch.

## Open item (from the design system)
Whether `brand-orange` `#FD9F0F` is used in the UI beyond the logo, avatar and brand moments. Default: logo and brand moments only.
