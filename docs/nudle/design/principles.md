# Design — Principles

## Shape-Driven, Not Content-Driven

The UI is generated from the Shape schema. Every component, every editor, every navigation option exists because a Shape declared it. No special-case layouts. No content-aware rendering. If the Shape changes, the UI changes. If the Shape doesn't declare it, it doesn't exist in the UI.

## Single Surface, Infinite Depth

One page. No routes, no tabs, no modals for navigation. You drill into the tree and the view shifts. Breadcrumb shows where you are. Back is up. The same component renders at every depth — a Shape 10 levels deep looks and works identical to the root.

## Type-Specific Editors

Every primitive type has exactly one editor. str → text input. int → number input. float → number input. bool → toggle. No ambiguity, no "smart" detection. The Shape schema specifies the type, the editor follows.

Collections have type-specific interactions: dict → key-value pairs, list → ordered with append/reorder/remove, set → unordered with add/remove.

## Lazy Everything

Nothing loads until the user navigates to it. No upfront tree walk. No preloading of children. Each level is independent — expanding a container fetches its children, not its grandchildren. Large collections show a bounded page, not the full contents.

## Nothing Custom

The UI has zero knowledge of any specific Shape. It cannot tell the difference between a `Market` Shape and a `Config` Shape. Both render through the same generic pipeline. If you find yourself writing a component that checks the Shape name — stop. The abstraction is wrong.

## Density Over Chrome

Show data. Decorate only without harming readability.

Every pixel earns its place by showing information or enabling interaction.

## Respond, Don't Acknowledge

When the user edits a value, the result should be visible immediately. No success toasts, no "saving..." spinners, no confirmation dialogs for reversible actions.
The UI is a live projection — the change is the feedback.
