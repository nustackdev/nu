# Container

Styled box that wraps one or more child slots. A `Container` is a Shape
(Section), not a Ref. Display-only, server-owned.

## kind

section (layout primitive)

## defaults (class-level)

| field | type | default | notes |
| --- | --- | --- | --- |
| `title` | `str` | `""` | optional header text above children. empty hides the header entirely. |
| `padding` | `Literal["none", "sm", "md", "lg"]` | `"md"` | inner spacing around children. |
| `border` | `Literal["none", "hairline", "card"]` | `"hairline"` | `hairline` is 1px muted; `card` adds a heavier panel feel. |
| `background` | `Literal["none", "muted", "accent"]` | `"none"` | fill behind children. |
| `shadow` | `Literal["none", "sm", "md"]` | `"none"` | drop shadow. `border == "card"` bumps the effective minimum to `sm`. |
| `gap` | `Literal["none", "sm", "md", "lg"]` | `"md"` | vertical gap between stacked children. |

Children are declared as ordinary slots on the Section body. They become
nested wire-path segments under the container's path.

## interactions

| op | dir | payload | notes |
| --- | --- | --- | --- |
| `write` | server -> tab | `{"title"?: str, "padding"?: str, "border"?: str, "background"?: str, "shadow"?: str, "gap"?: str}` | partial chrome update from the server (not exposed in v0.1.0). |

Children are mount-time only; no runtime reparenting.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.panel",
  "type": "Container",
  "props": {
    "title": "Status",
    "padding": "md",
    "border": "card",
    "background": "muted",
    "shadow": "sm",
    "gap": "md"
  },
  "fields": [
    {"path": "HomePage.panel.status_text", "type": "TextRef",     "props": {...}},
    {"path": "HomePage.panel.progress",    "type": "ProgressRef", "props": {...}}
  ]
}

// title-only update
{"op": "write", "ref": "HomePage.panel", "payload": {"title": "Latest"}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value".

Example:

```python
class Panel(nudle.Container):
    title = "Status"
    padding = "md"
    border = "card"
    background = "muted"
    shadow = "sm"

    status_text = nudle.TextRef.slot()
    progress    = nudle.ProgressRef.slot()


class HomePage(nudle.Page):
    panel = Panel.slot()


# server-side handles
Panel.status_text.store("ok")   # writes HomePage.panel.status_text
Panel.progress.store(0.5)
```

## renderer

`web/src/refs/container.tsx`. A `<section>` with tailwind classes per
slice value, an optional `<h3>` header when `title` is non-empty, and a
vertical flex column of child renderers. Each child path is resolved
against the global slice table and dispatched to its renderer via the
shared `renderers` map. Each child is wrapped in `ErrorBoundary`.

The mount walker registers a slice for the Container entry AND recurses
into its `fields`, so every leaf has a slice.

## slice shape

```
{
  type: "Container",
  value: null,
  title: string,
  padding: string,
  border: string,
  background: string,
  shadow: string,
  gap: string,
  children: string[],
  write: (v: {...partial}) => void,
}
```

Server-owned. Seeded from `field.props` and the nested `fields` list on
mount. `children` is set once and never mutated.

## edge cases

- empty section body: container renders chrome only (title + empty body).
- child slice not present in the global slice table: a small inline error
  label is shown for that slot; siblings keep rendering.
- empty `title`: header is hidden entirely.
- `border == "card"` with `shadow == "none"`: renderer applies `shadow-sm`.

## non-goals

- no runtime reparenting (children are mount-time only).
- no responsive breakpoints.
- no header actions slot. For toolbars, nest a Row inside.
- no collapsible / expandable state.
- no per-instance class overrides. The six enum slots are the only styling levers.
- no instance multiplexing: one Section subclass = one mount point.
