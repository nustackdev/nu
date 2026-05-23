# AccordionRef

Stack of collapsible sections, each wrapping a child Ref. An
`AccordionRef` is a Shape (Section), not a Ref. Tab owns the open state,
server owns the section list.

## kind

section (layout primitive, layout-with-children)

## defaults (class-level)

| field | type | default | notes |
| --- | --- | --- | --- |
| `sections` | `list[dict[str, str]]` | `[]` | each entry `{"id": str, "label": str}`. order = render order; aligns to children by slot order. |
| `open` | `list[str]` | `[]` | ids of currently-open sections. seeds tab state on mount. |
| `multi` | `bool` | `True` | if `False`, opening one section closes the others. |

Children are declared as ordinary slots on the Section body. The slot
order determines which body pairs with which section: `slots[i]` is the
body for `sections[i]`. Length mismatch is allowed -- extra slots render
under no header, extra sections render with empty bodies.

## interactions

| op | dir | payload | nu method | notes |
| --- | --- | --- | --- | --- |
| `write` | server -> tab | `{"sections"?: list[{id, label}], "open"?: list[str], "multi"?: bool}` | `store_sections(items)`, `store_open(ids)` | partial chrome update. each nu method compiles to a `write` frame whose payload contains just the one key. |
| `notify` | tab -> server | `list[str]` (post-toggle open ids) | `changed()` | fired on user toggle after local state is updated. payload is the post-toggle open list. |

`changed()` returns a `Subscription`. Server reads of the open list rely
on this; there is no `read` op.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.faq",
  "type": "AccordionRef",
  "props": {
    "sections": [
      {"id": "a", "label": "what is nu"},
      {"id": "b", "label": "how do i install"}
    ],
    "open":  ["a"],
    "multi": true
  },
  "fields": [
    {"path": "HomePage.faq.a", "type": "TextRef", "props": {...}},
    {"path": "HomePage.faq.b", "type": "TextRef", "props": {...}}
  ]
}

// store_sections([...])
{"op": "write", "ref": "HomePage.faq",
 "payload": {"sections": [{"id": "a", "label": "what is nu"}, {"id": "b", "label": "install"}]}}

// store_open(["b"])
{"op": "write", "ref": "HomePage.faq", "payload": {"open": ["b"]}}

// tab -> server: user toggled, "b" is now open in addition to "a"
{"op": "notify", "ref": "HomePage.faq", "payload": ["a", "b"]}
```

Wire-path note: child slot paths follow the standard Section rule
(slot attribute name appended to the parent path). The `id` on each
section is a logical label only; it never appears in the child wire
path. The renderer pairs `sections[i]` with the i-th child slice by
slot order.

Example:

```python
class FAQ(nudle.AccordionRef):
    sections = [{"id": "a", "label": "what is nu"}, {"id": "b", "label": "install"}]
    open = ["a"]
    multi = True

    a = nudle.TextRef.slot()
    b = nudle.TextRef.slot()


class HomePage(nudle.Page):
    faq = FAQ.slot()


# server-side handles
FAQ.store_open(["b"])              # collapse a, expand b
FAQ.store_sections([{"id": "a", "label": "..."}, {"id": "c", "label": "..."}])
async for ids in FAQ.changed():    # post-toggle open list
    ...
```

## renderer

`web/src/refs/accordion.tsx`. Plain tailwind (no shadcn dependency).
A bordered, rounded container with `divide-y` between rows. Each row is
a `<button>` header (label on the left, `+` / `-` marker on the right)
followed by a content `<div>` rendered only when the section id is in
`open`. On click, the renderer computes the next open list locally
(filter out the id if it was open; add it if not; in `multi=false`
mode, replace with `[id]` or clear). It then writes the new list into
the slice and ships an `OP_NOTIFY` with the list as payload. Children
iterate the same way as `column.tsx` / `fieldset.tsx`: lookup
`refs[childPath]`, find renderer in `renderers[type]`, wrap in
`ErrorBoundary`.

## slice shape

```
{
  type: "AccordionRef",
  value: null,
  sections: {id: string, label: string}[],
  open: string[],
  multi: boolean,
  children: string[],
  write: (v: {sections?, open?, multi?}) => void,
  notifyChanged: (v: string[]) => void,
}
```

Tab is the source of truth for `open` between server writes.
`store_open` from the server overwrites local. User toggles mutate
local then send `notify`.

## edge cases

- empty `sections`: renders an empty container; no headers.
- empty `open`: all sections collapsed.
- `multi = False` with `open` containing multiple ids on mount or via
  `store_open`: renderer keeps the first id and drops the rest. Server
  is not corrected (no echo).
- duplicate ids in `sections`: behavior undefined. The renderer keys by
  index so React keys do not collide, but toggle by id will affect the
  first match.
- id in `open` that is not in `sections`: ignored by the renderer (no
  header opens for it).
- `sections` length > children length: trailing sections render with
  empty bodies.
- children length > `sections` length: trailing children are
  unreachable (no header opens them).
- payload is msgpack nil: each individual key is ignored (slice keeps
  current value).
- `multi` payload absent on mount: defaults to `True`.

## non-goals

- no per-section disabled flag.
- no icons or custom header content beyond `label`.
- no animations.
- no nested accordion-specific sugar (a child may itself be a Section,
  with no special-casing).
- no `read`: server does not pull the open list, it relies on `changed`.
- no reordering of sections from the tab side.
- no instance multiplexing: one `AccordionRef` subclass = one mount
  point.
