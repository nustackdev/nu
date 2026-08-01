---
title: Form
---

Semantic `<form>` Section. Stacks child slots vertically and blocks the
browser's native page reload when Enter is pressed in a child input.
Display-only, server-owned.

A `Form` is a Shape (Section), not a leaf Ref. Subclass `nudle.Form`, pin
chrome on the subclass, declare children as ordinary slots (typically
InputRef / SelectRef / SliderRef / CheckboxRef plus a ButtonRef), then
mount at a Page.

## kind

section (layout primitive, with children)

## defaults (class-level)

| field     | type                                                | default     | notes                                                                 |
| --------- | --------------------------------------------------- | ----------- | --------------------------------------------------------------------- |
| `title`   | `str`                                               | `""`        | optional header text rendered above children. empty hides the header. |
| `gap`     | `int` (tailwind unit)                               | `4`         | vertical gap between children; maps to `gap-<n>`.                     |
| `padding` | `int` (tailwind unit)                               | `0`         | inner padding; maps to `p-<n>`.                                       |
| `align`   | `Literal["start", "center", "end", "stretch"]`      | `"stretch"` | cross-axis (horizontal) alignment of children.                        |

The form does not own a submit button. Wire a `ButtonRef` as a child slot
and react to its `clicked()` on the server.

## children

Declared as ordinary slots on the Section body, in submit order. The form
does NOT batch or collect child values; each child remains an
independently addressable Ref.

```python
class SignupForm(nudle.Form):
    title = "sign up"
    gap = 3
    padding = 4

    name   = nudle.InputRef.slot()
    email  = nudle.InputRef.slot()
    submit = nudle.ButtonRef.slot()


class HomePage(nudle.Page):
    form = SignupForm.slot()


@SignupForm.submit.clicked
def on_submit():
    name = SignupForm.name.read()
    email = SignupForm.email.read()
    ...
```

Wire paths: `HomePage.form.name`, `HomePage.form.email`,
`HomePage.form.submit`.

## interactions

| op      | dir           | payload                                                          | nu method              | notes                                                  |
| ------- | ------------- | ---------------------------------------------------------------- | ---------------------- | ------------------------------------------------------ |
| `write` | server -> tab | `{"title"?: str, "gap"?: int, "padding"?: int, "align"?: str}`   | `set(...)` (partial) | partial chrome update. missing keys leave slice as is. |

No `notify`, no `read`. The form itself owns no value.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.form",
  "type": "Form",
  "props": {"title": "sign up", "gap": 3, "padding": 4, "align": "stretch"},
  "fields": [
    {"path": "HomePage.form.name",   "type": "InputRef",  "props": {...}},
    {"path": "HomePage.form.email",  "type": "InputRef",  "props": {...}},
    {"path": "HomePage.form.submit", "type": "ButtonRef", "props": {...}}
  ]
}

// title-only runtime update
{"op": "write", "ref": "HomePage.form", "payload": {"title": "sign in"}}

// gap update
{"op": "write", "ref": "HomePage.form", "payload": {"gap": 6}}
```

`title` is a string (msgpack str); `gap` and `padding` are integers;
`align` is a string. Nu sentinels for `title` serialize as msgpack nil and
decode to `""` in the slice.

## renderer

`web/src/refs/form.tsx`. A `<form onSubmit={(e) => e.preventDefault()}>`
with tailwind `flex flex-col gap-<n> p-<n> items-<align>`. Optional `<h3>`
header when `title` is non-empty. Children are read from `slice.children`
(array of wire paths) and dispatched through the global `renderers` map,
each wrapped in `ErrorBoundary`.

The mount walker registers a slice for the Form entry AND recurses into
its `fields`, so every leaf has a slice.

## slice shape

```
{
  type: "Form",
  value: null,
  title: string,
  gap: number,
  padding: number,
  align: string,
  children: string[],
  write: (v: {title?, gap?, padding?, align?}) => void,
}
```

`children` is set once on mount and never mutated.

## edge cases

- empty `title`: header is hidden entirely; no empty `<h3>` rendered.
- `title` payload is msgpack nil: slice stores `""`, header hidden.
- empty section body: renders a `<form>` with chrome only (header if
  `title` set, otherwise visually empty unless `padding > 0`).
- child slice missing from the global slice table: a small inline error
  label is shown for that slot; siblings keep rendering.
- child slice present but no renderer registered for its `type`: same
  inline error pattern.
- `gap` / `padding` non-integer on the wire: coerced via `Number(...)`;
  NaN falls back to defaults (4 / 0).
- unknown `align`: stored raw; renderer falls back to `stretch`.
- Enter pressed in any child input: native submit is blocked by
  `preventDefault`; child ButtonRef must be explicitly clicked to submit.
- nested sections: a Form may declare another Section slot as a child if
  desired. Not the common case.

## non-goals

- no value batching. The form does not collect, validate, or ship child
  values as a single payload. Each child Ref stays addressable; the
  server reads siblings on demand via per-Ref `read`.
- no built-in submit button. Compose a `ButtonRef` child and react to its
  `clicked()`.
- no Enter-to-submit auto-wiring. The form only prevents reload; it does
  not synthesize a `clicked` on any child button.
- no field-level validation, no error display slot, no `aria-invalid`
  plumbing. Children handle their own validity.
- no `disabled` / `readonly` cascade to children.
- no horizontal / inline form layout. Children stack vertically only; for
  inline groups, nest a `Row` inside.
- no per-instance class overrides.
- no instance multiplexing: one Form subclass = one mount point.
- no `read`, no `notify` on the Form itself.
- no runtime reparenting (children are mount-time only).
