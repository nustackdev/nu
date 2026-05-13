# Design — Style Guide

## Tone

Devtool, not app. Closer to VS Code and Chrome DevTools than to Notion or Linear. Dense, professional, vibrant. The kind of tool where you instantly know what you're looking at before you even read the labels — through color, shape, and position.

## Craft

Data density is the priority — but density doesn't mean ugly. Transitions should be smooth, hover states should feel alive, focus rings should be crisp.
The UI should feel polished and intentional at every pixel.
Nice UI is the standard, not a stretch goal.

## Type Coloring

Every Nu category gets a distinct color. This is the primary visual language — you should be able to glance at a tree and know what's a Value, what's a Ref, what's a Flow, what's a Span, what's an Op without reading text.

Exact palette TBD — but the principle is non-negotiable: type = color, always, everywhere.

## Badges

Small colored pills for metadata that matters at a glance: `PURE`, `VALUE`, `CONTAINER`, view type. Muted, not shouting. Sit next to the type name, never alone.

## Color

- Dark mode primary — dark background, light text. This is a devtool.
- Light mode supported but dark is the default.
- Neutral grays for structure. Type colors for data.

[todo — exact palette]

## Typography

- Roboto for UI labels, headers, navigation
- Monospace for values, keys, paths, type names — anything that is data
- Size scale: small, default, large. No more.

[todo — exact sizes]

## Spacing

- Tight but breathable. 4px base unit.
- Flat hierarchy — use indentation guides (tree lines) and subtle borders, not cards-within-cards.
- Whitespace separates meaningful groups, not just fills space.

[todo]

## Components

- Use shadcn/ui primitives as the base. Don't fight them.
- No custom components when a shadcn primitive exists.

[todo]

## Icons

- Lucide (ships with shadcn). One icon set, no mixing.
- Small, subtle, contextual — next to type names, in tree indicators, in the toolbar. Not decorative.
