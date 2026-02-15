# everylens — UX Model

## Starting Point

A root Shape and a root View are passed to everylens. That's the entry point. The UI renders from there — no homepage, no dashboard, no chrome around it.
You're immediately inside the tree.

## Navigation

Single page. No routes, no tabs. You drill into the tree and the view shifts. Breadcrumb trail shows your path. Back is up.

Navigation is recursive and infinite — a Shape contains Shapes which contain Shapes. The UI handles this uniformly: same component at every depth, same interactions, same layout.

## Shapes Are the Schema

The Shape tree is defined in code. Users cannot create or delete Shapes — they are structural, not content. What users CAN do:

- Edit primitive values (str, int, float, bool)
- Append/remove items in lists
- Add/remove entries in dicts (within a Shape's defined structure)
- Navigate into nested Shapes

The Shape is always the source of truth for what exists and what's editable.

## What Maps to What

| everybase | UI |
| --- | --- |
| Shape | Page / section — navigable, contains fields |
| Slot | Field — labeled, typed, editable |
| Primitive | Inline editor — type-specific (text input, number, toggle, ...) |
| DictView | Key-value list — expandable, each entry navigable or inline |
| ListView | Ordered list — reorderable, appendable |
| SetView | Unordered collection — addable, removable |
| Ref | Link — clickable, navigates to target |
| Container | Expandable — click to drill in |

## Vocabulary

Use everybase terms only. No "node", "item", "record", "row", "cell".

- **Shape** — a typed structure
- **Slot** — a named field within a Shape
- **View** — how a container is presented (dict, list, set)
- **Ref** — a reference to another location in the tree (if needed... not sure)
- **Primitive** — a leaf value (str, int, float, bool)
- **Container** — a non-leaf that holds children

These terms appear in the UI — labels, tooltips, empty states.

## Scale

The tree can be huge. The UI must never load everything.

- Containers render a default page of children (e.g. 50), then paginate
- Deep trees lazy-load — children fetch on expand, not on parent render
- Search/filter within large containers rather than scrolling
- No upfront tree walk — every level is independent

## Live Updates

The UI reflects the current state of the tree at all times. When an agent or machine writes a value, the UI updates in place without user action. No refresh button. No stale data.

Edits in flight (focused field) are not overwritten by incoming updates.
