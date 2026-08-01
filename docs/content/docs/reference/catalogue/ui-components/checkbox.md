---
title: CheckboxRef
---

Boolean toggle. Tab-owned: the browser holds the canonical checked state.

## kind

input

## defaults (class-level)

| field     | type   | default | notes                                                   |
| --------- | ------ | ------- | ------------------------------------------------------- |
| `label`   | `str`  | `""`    | text next to the box; empty means no label, box only.   |
| `checked` | `bool` | `False` | initial checked state seeded on mount.                  |

Class attributes on the python `CheckboxRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override the slice value.

## interactions

| op       | dir            | payload                     | nu method  | notes                                                              |
| -------- | -------------- | --------------------------- | ---------- | ------------------------------------------------------------------ |
| `write`  | server -> tab  | `bool`                      | `store`    | canonical push or reset; replaces the local checked state.         |
| `read`   | server -> tab  | request `null`; resp `bool` | (via `aeval`) | request/response, correlated by `id`. resolves the live value.  |
| `notify` | tab -> server  | `null`                      | `changed`  | emitted on every user toggle of the box or its label.              |

`CheckboxRef.aeval` ships a `read` via `session.aread` and returns the bool. `CheckboxRef.set(value)` compiles to `write`. `CheckboxRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.agree", "type": "CheckboxRef", "props": {"label": "I agree", "checked": false}}

// server pushes a value
{"op": "write",  "ref": "HomePage.agree", "payload": true}

// server fetches
{"op": "read",   "ref": "HomePage.agree", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.agree", "payload": true, "id": "ab12"}

// browser tells server the user toggled
{"op": "notify", "ref": "HomePage.agree", "payload": null}
```

`write` and `read`-response payloads are msgpack bools. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/checkbox.tsx`. Native `<input type="checkbox">` wrapped in a `<label>` so the label text is also a click target. Tailwind utility classes; no shadcn dep.

## slice shape

```
{
  type: "CheckboxRef",
  value: null,
  label: string,
  checked: boolean,
  write: (v: unknown) => void,
  get: () => boolean,
}
```

Seeded from `field.props` on mount. `write` coerces non-bool / nil payloads via `Boolean(v)`. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` payload is msgpack nil (Nu sentinel): coerced to `false`.
- `write` payload is non-bool: `Boolean(v)` coercion; no error frame.
- slot never written and no `props` on mount: slice defaults to `checked=false`, `label=""`.
- empty `label`: the trailing `<span>` is omitted; only the box is clickable.
- no debounce: each user toggle emits one `notify`.
