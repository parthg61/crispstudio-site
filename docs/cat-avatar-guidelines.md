# Cat avatar

Samosa and Idli, Radhika's cats, drawn from the real pair as flat, friendly characters for small moments. Both are tuxedo cats with green eyes: a dark coat, white chest, white paws, and a white muzzle and blaze.

## The two cats

- **Idli:** almost Persian. Fluffier than Samosa, with a short flat face, round cheeks, a big white chest ruff and small rounded ears (neither is clipped). She is mostly lying down, loafing and purring, so she is drawn calm, soft and sleepy: eyes half-closed or shut, never wide.
- **Samosa:** the leaner, fit one, with a longer body and taller, sharper ears. His left ear has a flat-cut clipped tip. A cat's left is the viewer's right, so in every pose the clipped ear is the one on the right of the picture. He is always trying to snatch food, so his props are croissants, and his eyes are wide and always up to something.

## Colours

Only system tokens, plus one new one for the eyes. Never recolour the cats.

| Part | Token | Value |
| --- | --- | --- |
| Fur | `navy` | #021F53 |
| Chest, paws, muzzle, blaze | `bg` (white) | #FFFFFF |
| Inner ears | `cream` | #FECA98 |
| Eyes | `eye-green` (new) | #4DAF6B |
| Nose | `burnt` | #CC4806 |
| Croissant | `brand-orange` with `burnt` shading | #FD9F0F / #CC4806 |
| Samosa avatar disc | `cream` | #FECA98 |
| Idli avatar disc | `brand-orange` | #FD9F0F |

`eye-green` is for the cats' eyes only, never text, buttons or UI. It sits on navy fur (5.8:1).

## Drawing rules

- Flat shapes only: no gradients, no soft shadows. Filled shapes have no outline, with one exception: white paws and chest carry a thin navy hairline so they hold on a white page.
- Looping motion (blink, tail sway, purr breathing) is added in code and never baked into the SVG. Each file keeps `head`, `tail`, `paw`, `eye`, `ear` and `body` as separate groups, and `purr`, `zzz` and `croissant` where a pose has them. Positioning sits on an inner group, so a CSS `transform` on these classes never moves the art. Suggested pivots: head `50% 100%`, eyes `50% 50%` (blink by `scaleY`), tail at its root (see the table).
- Every file reads at 48px and at 216px wide.
- Full-body files share the same width, `-4 … 108` units, with the ground (or the edge being peeked over) on the bottom edge, so every pose keeps the same scale. Upright poses use the classic `-4 0 108 96` box. Low or wide poses trim the empty top; the viewBox is in the table.

## Round avatars

- **Samosa:** open green eyes on a `cream` disc. **Idli:** half-closed green eyes on a `brand-orange` disc.
- **Sizes:** 96px for a feature moment, 48px for small placements such as a chat bubble or team row. The shape is always a circle (`radius-full`).
- **Motion:** a small tilt on hover and a quick squash on tap. Nothing loops, and reduced motion turns it off.

## Poses

| File | Pose | viewBox | Tail pivot |
| --- | --- | --- | --- |
| `Crisp_Cat_Samosa.svg` | Samosa sitting alert, tail flicking | `-4 0 108 96` | `0% 100%` |
| `Crisp_Cat_Samosa_Reach.svg` | Reaching up to swipe a croissant | `-4 0 108 96` | `100% 100%` |
| `Crisp_Cat_Samosa_Run.svg` | Running off with a stolen croissant | `-4 8 108 88` | `100% 100%` |
| `Crisp_Cat_Samosa_Peek.svg` | Peeking over an edge, one paw out, tail flicking | `-4 24 108 72` | `100% 100%` |
| `Crisp_Cat_Idli.svg` | Stretched out and purring, eyes half-closed | `-4 36 108 60` | `100% 100%` |
| `Crisp_Cat_Idli_Loaf.svg` | Loafing, purring | `-4 26 108 70` | `0% 100%` |
| `Crisp_Cat_Idli_Curl.svg` | Curled up asleep, with Zs | `-4 34 108 62` | none (tail wraps the body) |
| `Crisp_Cat_Idli_Peek.svg` | Peeking over an edge: head and white paws | `-4 30 108 66` | none |
| `Crisp_Cat_Idli_Cream.svg` | Sitting content, eyes closed (the pair partner for Samosa) | `-4 0 108 96` | `0% 0%` |

The peek files end exactly on their bottom edge: put that edge on the top edge of the card, and the card hides the rest.

## Which pose for which moment

| Moment | Pose |
| --- | --- |
| Contact form | Samosa and Idli peeking over the top edge of the form card (`Samosa_Peek`, `Idli_Peek`) |
| Contact success message | Samosa and Idli sitting side by side (`Samosa`, `Idli_Cream`) |
| 404 | Both full body (`Samosa`, `Idli_Loaf`) |
| Home | The pair peeking over the closing card, never in the hero |
| Footer | Idli lying along the top edge, small (`Idli`) |
| Blog empty state | Idli sleeping (`Idli_Curl`) |
| About and Services closings | Samosa avatar, 48px |
| Loader, hover moments | `Samosa_Reach` or `Samosa_Run`; no fixed placement yet |

## Use

- Use them for small moments only. Never in a hero or next to client work, so the work stays the hero.
- Never recolour the cats or give them new expressions or poses without checking with Radhika.

## More poses

A second set of poses, 9 for Samosa and 10 for Idli, is in the Cat poses asset group. Radhika has approved it. It sits alongside the poses above and doesn't replace them. Those files are not split into animatable groups yet, so use the poses in the table above where a looping animation is needed.
