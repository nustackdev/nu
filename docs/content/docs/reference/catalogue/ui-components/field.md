---
title: FieldRef
---

Label + child input + help / error text. A `FieldRef` is a Shape (Section), not a Ref, that wraps exactly one input Ref in a labelled form-field box. Display-only, server-owned.

## kind

section (layout primitive, layout-with-children, exactly one child)

## defaults (class-level)

| field      | type   | default | notes                                                                 |
| ---------- | ------ | ------- | --------------------------------------------------------------------- |
| `label`    | `str`  | `""`    | label text rendered above the child input. empty hides the label row. |
| `help`     | `str`  | `""`    | helper text rendered below the child. empty hides the help row.       |
| `error`    | `str`  | `""`    | error text. non-empty replaces `help` and tints the field red.        |
| `required` | `bool` | `False` | when true, renders a red `*` after the label text.                    |

All four are seeded into the mount entry's `props` and overridden at runtime via the ops below.

The single child is declared as one ordinary Ref slot on the Section body. Declaring zero or more than one slot raises at subclass-creation time.

## interactions

| op | dir | payload | nu method | notes |
| --- | --- | --- | --- | --- |
| `write` | server -> tab | `{"label"?: str, "help"?: str, "error"?: str, "required"?: bool}` | `store_label(str)`, `store_help(str)`, `store_error(str)`, `store_required(bool)` | partial chrome update. each nu method compiles to a `write` frame whose payload contains just that one key. |

No tab -> server ops. The FieldRef carries no value of its own; the child Ref owns user input and notifies on its own path.

## wire payloads

```
// mount field entry, recursive (one nested field, exactly)
{
  "path": "SignupPage.name_field",
  "type": "FieldRef",
  "props": {"label": "Name", "help": "your full name", "error": "", "required": true},
  "fields": [
    {"path": "SignupPage.name_field.input", "type": "InputRef", "props": {...}}
  ]
}

// store_label("Full name")
{"op": "write", "ref": "SignupPage.name_field", "payload": {"label": "Full name"}}

// store_help("we never share this")
{"op": "write", "ref": "SignupPage.name_field", "payload": {"help": "we never share this"}}

// store_error("name is required")  (switches to error visual)
{"op": "write", "ref": "SignupPage.name_field", "payload": {"error": "name is required"}}

// store_error("")  (clears error, restores help)
{"op": "write", "ref": "SignupPage.name_field", "payload": {"error": ""}}

// store_required(True)
{"op": "write", "ref": "SignupPage.name_field", "payload": {"required": true}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels (`EMPTY`, `INVALID`) serialize as msgpack nil; the renderer coerces nil to `""` for the three string keys and to `false` for `required`.

Example:

```python
class NameField(nudle.FieldRef):
    label = "Name"
    help = "your full name"
    required = True

    input = nudle.InputRef.slot()


class SignupPage(nudle.Page):
    name_field = NameField.slot()


# server-side handles
NameField.store_label("Full name")
NameField.store_error("name is required")
NameField.store_error("")              # clears, restores prior help
```

## renderer

`web/src/refs/field.tsx`. A `<label>` wrapping three rows: label row, child slot, help-or-error row. When `label` is non-empty, a `<span>` carries the text plus an optional red `*`. The single child is resolved through `refs[childPath]` and dispatched via `renderers[childSlice.type]`, wrapped in `ErrorBoundary`. The bottom row is rendered only when `error` or `help` is non-empty: when `error` is non-empty it shows red, otherwise the help text shows in muted color. No shadcn primitive; plain `<label>` plus tailwind.

## slice shape

```
{
  type: "FieldRef",
  value: null,
  label: string,
  help: string,
  error: string,
  required: boolean,
  children: string[],         // length 1
  write: (v: {label?: string, help?: string, error?: string, required?: boolean}) => void,
}
```

Server-owned. Seeded from `field.props` and the single-entry `fields` list on mount. `children` is set once and never mutated. `write` is partial: keys absent leave the slice value untouched. `null` for a string key lands as `""`; `null` for `required` lands as `false`.

## edge cases

- msgpack nil for a string key -> stored as `""`. For `required` -> stored as `false`.
- `error == ""` and `help == ""`: bottom row is omitted entirely (no empty space).
- `error` non-empty: the help text is suppressed visually, but kept in the slice (clearing `error` restores the prior help).
- `label == ""` with `required == True`: the `*` is not rendered (no label row at all).
- child slice missing from the global slice table: inline error label is shown in the input slot; the field chrome (label, help / error) still renders.
- exactly-one-child invariant: enforced at subclass-creation time. The renderer also treats `children.length != 1` as a child-missing error.
- no client-side validation: `error` is purely a display channel; the server decides when to set / clear it.

## non-goals

- no multiple children. Group with a `Column` inside if multi-input layout is needed.
- no inline icons / adornments in the label row.
- no tooltip variant of help text.
- no label position option (always above the child for v0.1.0).
- no `notify`, no `read`. FieldRef carries no user-owned value.
- no styling props (padding, gap, border): the wrapper is fixed chrome. Use a `Container` outside for box styling.
