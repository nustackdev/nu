# Modal

Dialog overlay. Server controls visibility; tab notifies on user dismissal.
A `Modal` is a Shape (Section), not a leaf Ref. Subclass `nudle.Modal`, pin
chrome on the subclass, declare body Refs as ordinary slots, then mount at
a Page. Children stack vertically inside the dialog.

## kind

section (layout primitive)

## defaults (class-level)

| field         | type   | default | notes                                                                              |
| ------------- | ------ | ------- | ---------------------------------------------------------------------------------- |
| `open`        | `bool` | `False` | initial visibility. Server flips later via `store_open`.                           |
| `title`       | `str`  | `""`    | header text inside the dialog. empty hides the header.                             |
| `dismissible` | `bool` | `True`  | when True, backdrop click and Escape close the dialog and emit `notify`.           |

Children are declared as ordinary slots on the Section body. They become
nested wire-path segments under the modal's path.

## interactions

| op       | dir            | payload                                       | nu method                                  | notes                                                                                  |
| -------- | -------------- | --------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------- |
| `write`  | server -> tab  | `{"open"?: bool, "title"?: str}`              | `store_open`, `store_title`, `store`       | partial update; absent keys leave the slice untouched.                                 |
| `notify` | tab -> server  | `{"open": false}`                             | `changed`                                  | emitted when the user dismisses (backdrop click or Escape) and `dismissible == True`.  |

Mutators compile to the same `write` op with different payload subsets:

- `store_open(flag)` -> `write {"open": flag}`
- `store_title(text)` -> `write {"title": text}`
- `store(open=..., title=...)` -> `write {...}` with only keys passed
- `changed()` -> `Changed` subscription on `notify`

`dismissible` is mount-time only; not editable at runtime in v0.1.0. The
renderer never optimistically flips the slice's `open` flag on dismissal:
it emits the `notify` and waits for the server's `write {open: false}`.
Server stays the single source of truth for visibility.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.modal",
  "type": "Modal",
  "props": {"open": false, "title": "Confirm", "dismissible": true},
  "fields": [
    {"path": "HomePage.modal.body",   "type": "TextRef",   "props": {...}},
    {"path": "HomePage.modal.cancel", "type": "ButtonRef", "props": {...}},
    {"path": "HomePage.modal.ok",     "type": "ButtonRef", "props": {...}}
  ]
}

// open the modal
{"op": "write", "ref": "HomePage.modal", "payload": {"open": true}}

// close it
{"op": "write", "ref": "HomePage.modal", "payload": {"open": false}}

// retitle
{"op": "write", "ref": "HomePage.modal", "payload": {"title": "Are you sure?"}}

// user dismissed (backdrop / Escape)
{"op": "notify", "ref": "HomePage.modal", "payload": {"open": false}}
```

Payload is a msgpack map. `open` is a msgpack bool, `title` a msgpack str.
Missing keys leave the slice untouched.

Example:

```python
class ConfirmModal(nudle.Modal):
    title = "Confirm"
    dismissible = True

    body   = nudle.TextRef.slot()
    cancel = nudle.ButtonRef.slot()
    ok     = nudle.ButtonRef.slot()


class HomePage(nudle.Page):
    modal = ConfirmModal.slot()


# server-side handles
HomePage.modal.store_open(True)
HomePage.modal.store_title("Are you sure?")
sub = HomePage.modal.changed()   # fires when the user dismisses
```

## renderer

`web/src/refs/modal.tsx`. An always-mounted wrapper `<div hidden={!open}>`
keeps child slices alive across open/close cycles. When `open == true`, a
fixed backdrop and a centered panel are rendered above siblings. The panel
shows an optional `<h3>` header when `title` is non-empty and a vertical
flex column of child renderers. Each child path is resolved against the
global slice table and dispatched via the shared `renderers` map, wrapped
in `ErrorBoundary`.

Backdrop click and the Escape key call the dismiss handler. When
`dismissible == false`, dismiss is a no-op: the dialog can only be closed
by a server-side `write {open: false}`.

## slice shape

```
{
  type: "Modal",
  value: null,
  open: boolean,
  title: string,
  dismissible: boolean,
  children: string[],
  write: (v: {open?: bool, title?: str}) => void,
}
```

Server-owned. Seeded from `field.props` and the nested `fields` list on
mount. `children` and `dismissible` are set once on mount and never
mutated. `open` and `title` are mutated by server `write` frames only.

## edge cases

- `open` value is msgpack nil: treated as `false`. Body remains mounted but hidden.
- `title` value is msgpack nil: slice stores `""`, header hidden entirely.
- backdrop click / Escape with `dismissible == false`: renderer absorbs the event, no `notify` is sent, slice stays `open == true`.
- `notify` is fired only on user-initiated dismissal. A server-driven `store_open(False)` does not echo a `notify`.
- child slice missing from the global slice table: small inline error label for that slot; siblings keep rendering.
- empty body: modal renders chrome only (header if `title` set, otherwise an empty content panel).
- rapid open/close toggles: each `write` lands on the slice; the renderer follows the latest value. No debouncing.
- focus management: native; children inside keep their focus state across open/close because they stay mounted.
- nested modals: not modeled in v0.1.0. Structurally allowed (Modal is a Section) but stacking / focus semantics are unspecified.

## non-goals

- no built-in close button. Compose a `ButtonRef` child and react to its `clicked()` to call `store_open(False)`.
- no built-in confirm / cancel buttons. Same pattern.
- no controlled `dismissible` at runtime.
- no size / width prop. Wrap content in a styled child for sizing.
- no animation prop.
- no `read` on the Modal. Server owns `open`.
- no per-instance class overrides.
- no instance multiplexing: one Modal subclass = one mount point.
- no runtime reparenting (children are mount-time only).
- no scroll lock toggle.
