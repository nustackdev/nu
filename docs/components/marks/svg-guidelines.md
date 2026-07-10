# Inline SVG guidelines

Source of truth for any inline SVG mark or diagram on the nustack site.
Keep it flat, hairline, mono. Dev-tool aesthetic — not marketing.

## The priority: comprehension over minimalism

Users see the SVG for 2 seconds. If they can't say "oh — that's what this section is about", the SVG has failed. Prefer:

- **Labeled shapes over abstract nodes.** Name what the thing is (`ref: counter/value`, `interaction: store(1)`, `fabric: browser`).
- **Concrete API strings and values** — same voice as the code we ship.
- **Before/after or process framings** over static diagrams — a value transitioning from 0 to 1 tells the story.
- **Substrate icons** (browser chrome, disk block, memory block) over generic squares.

Reference the Nu-page `TransitionViz` / `MemViz` / `VirtualsViz` / `NudleViz` in `docs/app/(home)/nu/page.tsx` for the concrete/labeled style that works here.

## Aspect + sizing

- viewBox `0 0 400 300` (4:3) is the default; wider (`0 0 480 300`) or larger (`0 0 600 380`) is fine when the concept demands.
- Render fluid: `width="100%"`, `height="auto"`, `preserveAspectRatio="xMidYMid meet"`.
- Never hardcode pixel dimensions on the `<svg>` root.
- The visual slot has NO vertical seam next to it (`.sectionVisual` has no `border-left`) — the SVG must feel finished at its own edges.

## Palette + roles (strict)

Every color comes from a token in `_tokens.module.css`. No hex.

- `var(--nu-accent)` (purple) — **primary role only**: the key node, brand identity, primary edges, `nu` callouts. Reserve; do not spend it on decoration.
- `var(--nu-accent-wash)` — light purple fill (~6-13%). Max one wash per SVG.
- `var(--nu-accent-line)` — light purple stroke for the wash surface.
- `var(--nu-accent-2)` (blue) — **secondary role only**: status pills, live dots, "after" state accents. Never a primary edge.
- `var(--nu-ink)` / `--nu-ink-2` / `--nu-ink-3` / `--nu-ink-4` — text tiers, dark → soft.
- `var(--nu-rule)` / `--nu-rule-2` — hairline connectors, grid backdrops.

Never mix roles. Never introduce a third accent.

## Stroke rules

- Default hairline: `strokeWidth={1}`.
- Emphasis (primary edges, the key node): `strokeWidth={1.25}` (rarely `1.5`).
- Always set `vectorEffect="non-scaling-stroke"` so hairlines survive scaling.
- Fills: prefer `fill="none"`. Accent-wash on one shape max.
- Dashed strokes for containers/substrate: `strokeDasharray="3 3"`.

## Text rules

- Font: `var(--font-mono)` only. No serif ever.
- Size range: 9-12px. Substrate/brand labels may go to ~15px.
- `letterSpacing: '0.16em'` (min) — `'0.24em'` (index/caption). Wide.
- Case: lowercase (`ref`, `interaction`, `fabric`, `nu`, `app · 01`). No title case.
- Apply via `style={{ fill, fontFamily, fontSize, letterSpacing }}` — CSS vars work inside `style`, not always inside SVG attrs.
- Anchor deliberately: `textAnchor="start" | "middle" | "end"` per placement.

## Motion

- Optional. If any, subtle only: opacity pulse or blink. No rotation, no scale bounce, no translate.
- CSS-based via `marks.module.css`. Available classes: `.pulse` (3.2s ease-in-out) and `.blink` (2.6s ease-in-out).
- The module includes `@media (prefers-reduced-motion: reduce) { animation: none; }` — always honor.

## Micro-chrome (encouraged)

Signal "considered instrument," not decoration.

- **Corner ticks** at the four canvas corners: 8px L-shaped `path` in `var(--nu-rule)`. Use sparingly, not on every SVG.
- **Bottom-right caption** in `var(--nu-ink-4)`: short mono label ~9px.
- **No `m · NN` index tag** — user rejected this.
- **Inner container ticks** (small L-marks) at corners of a fabric/substrate.
- **Snap notches** — short ticks flanking a node — hint at "assembleable" pieces.
- **Faint grid lines** inside a container in `var(--nu-rule-2)` at ~0.6 opacity.

## Signature vocabulary

The alphabet is small and shared across every mark.

- **Ref** — small circle. `r=4-5` (min 3.5 in compact contexts). Hairline stroke `var(--nu-ink-2)`, no fill.
- **Interaction** — small square. Side `10-14`. Hairline stroke. Purple accent + wash when it is the primary node; ink-2 stroke when it is inline vocabulary.
- **Fabric / substrate** — dashed hairline rectangle. Ink-rule stroke for a neutral fabric; accent-line stroke + accent-wash fill for the Nu substrate.
- **Connectors** — straight lines or right-angle bends. No bezier curves unless the concept demands one (loops).
- **Glyphs** — `>>`, `→` may appear as small mono text inside an Interaction node.

## Component contract

```tsx
type Props = { className?: string };

export function XyzSvg({ className }: Props) {
  return (
    <svg
      viewBox="0 0 400 300"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="…what the mark shows…"
      className={className}
    >
      {/* corner ticks · index tag · content · caption */}
    </svg>
  );
}
```

- No props beyond `className`. No sizing knobs — this is a fixed mark, not an icon.
- Prefer `role="img"` with an `aria-label` sentence over `aria-hidden` if the mark carries meaning; use `aria-hidden` for pure decoration.
- Use CSS custom properties for every color, so dark mode flips cleanly.
