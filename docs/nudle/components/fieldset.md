# Fieldset

Grouped fields with a legend and shared vertical spacing. A `Fieldset` is
a Shape (Section), not a Ref. Display-only, server-owned. Renders a
native HTML `<fieldset>` with an optional `<legend>`; children are
stacked vertically like a `Column`.

## kind

section (layout primitive, layout-with-children)

## defaults (class-level)

| field | type | default | notes |
| --- | --- | --- | --- |
| `legend` | `str` | `""` | text in the `<legend>` element. empty hides the `<legend>` entirely. |
| `gap` | `Literal["sm", "md", "lg"]` | `"md"` | vertical gap between stacked children. `sm` -> `gap-2`, `md` -> `gap-4`, `lg` -> `gap-6`. |
| `disabled` | `bool` | `False` | visual-only dim of the group. does NOT cascade `disabled` to child inputs; each input controls its own enabled state. |

Children are declared as ordinary slots on the Section body. They become
nested wire-path segments under the fieldset's path.

## interactions

| op | dir | payload | nu method | notes |
| --- | --- | --- | --- | --- |
| `write` | server -> tab | `{"legend"?: str, "gap"?: str, "disabled"?: bool}` | `store_legend(str)`, `store_gap(str)`, `store_disabled(bool)` | partial chrome update. each nu method compiles to a `write` frame whose payload contains just that one key. |

Children are mount-time only; no runtime reparenting.

## wire payloads

```
// mount field entry, recursive
{
  "path": "FormPage.contact",
  "type": "Fieldset",
  "props": {"legend": "Contact", "gap": "md", "disabled": false},
  "fields": [
    {"path": "FormPage.contact.name",  "type": "InputRef", "props": {...}},
    {"path": "FormPage.contact.email", "type": "InputRef", "props": {...}}
  ]
}

// store_legend("Contact details")
{"op": "write", "ref": "FormPage.contact", "payload": {"legend": "Contact details"}}

// store_gap("lg")
{"op": "write", "ref": "FormPage.contact", "payload": {"gap": "lg"}}

// store_disabled(true)
{"op": "write", "ref": "FormPage.contact", "payload": {"disabled": true}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value".
`disabled` is encoded as a msgpack bool. `null` values are ignored.

Example:

```python
class Contact(nudle.Fieldset):
    legend = "Contact"
    gap = "md"

    name  = nudle.InputRef.slot()
    email = nudle.InputRef.slot()


class FormPage(nudle.Page):
    contact = Contact.slot()


# server-side handles
Contact.store_legend("Contact details")   # writes FormPage.contact legend
Contact.store_disabled(True)              # dims the group visually
```

## renderer

`web/src/refs/fieldset.tsx`. A native `<fieldset>` with a tailwind class
chain (`border border-border rounded-md p-4`). When `legend` is
non-empty, a `<legend>` element is emitted before the body. The body is
a `<div>` with `flex flex-col gap-<n>` where `<n>` follows the
`sm|md|lg` mapping. When `disabled` is true, `opacity-50` is added to
the `<fieldset>`. The HTML `disabled` attribute is deliberately NOT set,
so child controls stay interactive. Children iterate the same way as
`column.tsx`: lookup `refs[childPath]`, find renderer in
`renderers[type]`, wrap in `ErrorBoundary`. No shadcn primitive; plain
HTML.

## slice shape

```
{
  type: "Fieldset",
  value: null,
  legend: string,
  gap: string,           // "sm" | "md" | "lg"
  disabled: boolean,
  children: string[],
  write: (v: {legend?: string, gap?: string, disabled?: boolean}) => void,
}
```

Server-owned. Seeded from `field.props` and the nested `fields` list on
mount. `children` is set once and never mutated. `write` is partial:
keys absent leave the slice value untouched; `null` values are ignored.

## edge cases

- empty `legend`: the `<legend>` element is omitted entirely.
- `gap` outside `sm|md|lg`: stored raw, renderer falls back to `md`.
- `disabled` payload is msgpack nil: ignored (slice keeps current value).
- empty body (no children declared): renders chrome only -- `<fieldset>`
  with optional `<legend>` and an empty body `<div>`.
- child slice missing from the global slice table: small inline error
  label for that slot; siblings keep rendering (same as Column /
  Container).
- mount entry with no `props` key: slice seeds with class-level defaults
  (`legend=""`, `gap="md"`, `disabled=false`).
- no browser-side validation. server is the source of truth.

## non-goals

- no cascading `disabled` to child inputs.
- no horizontal layout variant (use a `Row` inside).
- no form-submit semantics. `Fieldset` is visual grouping, not `<form>`.
- no per-child styling overrides from the parent.
- no collapsible / expandable state.
- no `read`, no `notify`. Fieldset is server-owned.
- no responsive breakpoints.
- no runtime reparenting; children are mount-time only.
- no instance multiplexing: one `Fieldset` subclass = one mount point.
