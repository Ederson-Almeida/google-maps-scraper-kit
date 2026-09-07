# Mahan's carousel design system

Read off two artifacts he built on 2026-08-24: **Carousel Covers** (a Claude Design
canvas with four finished 1080×1350 artboards) and **Carousel Design Review** (36
designs, five cover templates, eight inside slides, plus the three competitor
carousels everything was read from).

This is his established look. Do not invent an alternative. If something here
conflicts with a generic "good design" instinct, his version wins — it was
derived from his own best-performing post, not from taste.

## Palette

His own canvas annotation says it plainly: **"Palette is sampled from your 429K
post, not chosen."** That provenance is the reason to keep it.

| Token | Hex | Use |
|---|---|---|
| Ground | `#FAF7F2` | warm paper. Every slide background. |
| Ink | `#2A2A24` | all primary type; heavy 3px rules; dark inverted panels |
| Coral | `#EA9678` | **fill only** — strike bars, big numerals, blobs, dots |
| Coral text | `#C9694A` | coral at small sizes, and links |
| Coral deep | `#A9543A` | link hover |
| Coral pale | `#EAB4A2` | alternate accent option |
| Mono label | `#8A8278` | the uppercase mono labels in header and footer |
| Prose | `#6E6659` | secondary sentences under a big number |
| Struck | `#A79E90` | the price/name being cancelled |
| Struck alt | `#B8B0A4` | the large struck numeral |
| Hairline | `rgba(42,42,36,0.14)` – `0.2` | dividers, footer top border |
| Card | `#FFFFFF` | the raised white card on Cancellation/Loadout |

**The contrast rule he found the hard way, in his own words:** *"Coral is a FILL
colour. Small type uses `#C9694A` — coral doesn't clear contrast at small sizes
on this ground."* Follow it. Coral body text on warm paper fails.

Accent is a swappable DC prop with these options: `#EA9678`, `#C9694A`,
`#2A2A24`, `#EAB4A2`.

## Type

Loaded from Google Fonts in each artboard's `<helmet>`:

```
Archivo 400;500;600;700 · Archivo Black · JetBrains Mono 400;700
```

- **Archivo Black** — display numerals and uppercase headlines. `letter-spacing`
  `-0.02` to `-0.045em`, `line-height` `0.84`–`1.0`. Sizes seen: 62, 84, 92, 96,
  118, 156, 300px. The tight tracking at huge sizes is what makes it read as
  designed rather than merely large.
- **Archivo 700** — sentence headlines (40–58px) and the wordmark.
- **Archivo 500** — the explanatory line under a number, 27–30px, in `#6E6659`.
- **JetBrains Mono 700** — every label. Always `text-transform: uppercase`, always
  wide `letter-spacing` (`0.14`–`0.3em`), 12–22px, usually `#8A8278`. This is the
  single most recognisable element of the system; a slide without a mono label
  reads as someone else's.

## Frame

Canvas **1080 × 1350**. Padding **56–62px**. `box-sizing: border-box`, column flex.

**Header row** (every slide) — baseline-aligned, space-between:
- left: wordmark `mahan ai` in Archivo 27px/700, `letter-spacing -0.02em`, with the
  full stop in `{{accent}}`
- right: a mono uppercase label naming the artefact — `Receipt 001`, `No. 01`,
  `Monthly software`, `Loadout`

**Footer row** (every slide) — same treatment, `#8A8278`, sometimes with
`border-top: 1.5px solid rgba(42,42,36,0.2); padding-top: 22px`:
- left: `@mahanaicoach` (or `Replaced with [tool]`)
- right: in `#C9694A` — the proof or the nudge: `35,062 ★ · AGPL-3.0`,
  `14 platforms · self-hosted`, `Swipe for all four`, `Swipe for every link`

The header/footer pair is the chrome. It repeats unchanged; only the middle
changes. That repetition is what makes ten slides feel like one object.

## Signature devices

- **The strike.** A cancelled price is not `text-decoration: line-through`. It is
  an absolutely-positioned coral bar, `height: 7–10px`, `border-radius: 2–3px`,
  bleeding ~6–14px past the text on both sides, rotated `-6deg` for a single hero
  price or `±0.35–0.5deg` per row in a list so the rows look hand-struck.
- **The white card.** `border-radius: 22px`, `padding: 56px 52px 48px`, double
  shadow `0 2px 4px rgba(42,42,36,0.05), 0 24px 60px rgba(42,42,36,0.13)`. Used
  when one fact is the whole slide.
- **The coral blob.** A single large SVG `path` ellipse behind centred content,
  with the headline numeral knocked out in ground colour `#FAF7F2` on top.
- **The ledger.** 3px ink rules top and bottom, 1.5px hairlines between rows,
  name left in Archivo 700/40px, amount right in JetBrains Mono 700/36px, total
  row in Archivo Black.
- **The tile.** `border: 3px solid #2A2A24; border-radius: 16px; background: #FFF`,
  a 66px tinted rounded-square icon well, name 25px/700, mono role label 12px, and
  a cost pill in inverted ink (`background:#2A2A24; color:#FFF; border-radius:6px`).
- **The inverted bar.** Ink panel, `border-radius: 16px`, mono label at `opacity
  .68` left, Archivo Black figure in `{{accent}}` right. Used for totals.

## The five cover templates

His own framing: *"Five templates. Each one is generated from a content record —
name, what it replaces, its price, star count, licence, screenshot. Same template,
different subject, and the cover builds itself. That is the repeatable part."*

| ID | Name | What it does |
|---|---|---|
| T1 | **Swap** | the replaced tool against the free one, price struck |
| T2 | **Proof** | the repo screenshot is the hero, star badge pinned |
| T3 | **Kill** | the price is the whole image. Dark, one job |
| T4 | **Field** | everything it covers, as a field of chips |
| T5 | **Counter** | the star count carries the frame |

So the first question for a new carousel is not "what should this look like" but
**"what does the content record contain?"** If you have a star count, T5 is
available; if you have a screenshot, T2 is; if you have a price, T1 and T3 are.
Pick the template the facts can actually fill.

The four finished artboards on the canvas are named **Cancellation** (white card,
struck $99, "You just saved $1,188"), **Coral Field** (blob, `$0` knocked out at
300px), **Ledger** (four struck line items totalling `$0.00`), and **Loadout**
(3×3 tile grid with an inverted total bar).

## The eight inside slides

Body slides, lighter card style — explicitly *"for the middle of the deck, not the
cover."*

`IN-1 Agent Rows` · `IN-2 Split Compare` (before/after, hard numbers) ·
`IN-3 Pull Quote` (one claim, big, attributed) · `IN-4 Bar Metrics` (ranked bars) ·
`IN-5 Timeline` (four steps on a rail) · `IN-6 Shot + Callouts` (real screenshot,
numbered legend) · `IN-7 Do / Don't` (ticks against crosses) · `IN-8 Tile Grid`.

A step-by-step carousel is IN-5. A stack carousel is IN-8. A comparison is IN-2.

## The crew

Fourteen pixel silhouettes: **flat fill, slot eyes, no mouth** — rebuilt to match
`ibra`'s reference. Agent-mode covers only (`AG-A` … `AG-F`); of those, **AG-D
Agent Swap — the freelancer against the agent — is marked his strongest hook.**
Don't put the characters on a tool carousel; they belong to the agent-team story.

## The three references everything was read off

- **REF-1 · jens.heitmann — "8 Jobs for Fable 5"** — cream ground, real
  screenshots, a starter prompt on every slide.
- **REF-2 · ibra — "Free vs Paid, 15 Swaps"** — *"the swap engine. Your thesis as
  a layout."* This is the structural parent of the whole system.
- **REF-3 · ibra — "I Built an AI Content Team"** — where the pixel characters
  come from.

## How it's built and shipped

A **Claude Design canvas**: one `.dc.html` file per artboard, laid out by
`canvas.json` at 1080×1350 with ~100px gutters (`x: 0 / 1180`, `y: 0 / 1450`).
Each artboard is a single absolutely-sized `div`, fonts loaded in `<helmet>`, and
a trailing `data-dc-script` block exposing props:

```html
<script data-dc-script data-props='{"accent":{"editor":"color","default":"#EA9678","options":["#EA9678","#C9694A","#2A2A24","#EAB4A2"]}}'>
class Component extends DCLogic {
  renderVals() { return { accent: this.props.accent ?? '#EA9678' }; }
}
</script>
```

Repeating content uses `<sc-for list="{{tools}}" as="t" hint-placeholder-count="6">`
so one tile markup block renders the whole grid. He edits and exports from the
published canvas.

## Verification discipline — keep this

`canvas.json` carries `annotations` that split facts by confidence, pinned beside
the artboards. His actual note:

> Verified: Postiz 35,062 stars, AGPL-3.0.
> NOT verified: $99 Buffer, $149 Hootsuite, $80 Later, $69 Zapier. Check these
> against real pricing pages before posting.

The Design Review page carries the same split in its header tags: `Prices are
placeholder` next to `Postiz data verified`. Reproduce this on every canvas —
an annotation listing what is verified and what still needs checking before it
goes out. A struck price is the most quotable thing on the slide and the easiest
to get wrong.
