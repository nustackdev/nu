---
title: InputRef
---

Single-line text input. Tab-owned: the browser holds the canonical value.

## kind

input

## defaults (class-level)

| field         | type                                                | default     | notes                                                              |
| ------------- | --------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| `label`       | `str`                                               | `""`        | visible label rendered above the input. empty means no label node. |
| `placeholder` | `str`                                               | `""`        | passed to `<input placeholder=...>`.                               |
| `value`       | `str`                                               | `""`        | initial value seeded into the slice on mount.                      |
| `type`        | `Literal["text", "password", "email", "number"]`    | `"text"`    | drives the native `<input type>`.                                  |
| `max_length`  | `int | None`                                        | `None`      | passed as `maxLength` on the `<input>` when not None.              |

Class attributes on the python `InputRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override slice `value`; `label`, `placeholder`, `type`, and `max_length` are mount-time only.

## interactions

| op       | dir            | payload                       | nu method     | notes                                                                  |
| -------- | -------------- | ----------------------------- | ------------- | ---------------------------------------------------------------------- |
| `write`  | server -> tab  | `str`                         | `store`       | canonical push or reset; replaces the local value.                     |
| `read`   | server -> tab  | request `null`; resp `str`    | (via `aeval`) | request/response, correlated by `id`. resolves the live value.         |
| `notify` | tab -> server  | `null`                        | `changed`     | emitted when the user commits a change (blur or Enter).                |

`InputRef.aeval` ships a `read` via `session.aread` and returns the string. `InputRef.set(value)` compiles to `write`. `InputRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.name", "type": "InputRef",
 "props": {"label": "your name", "placeholder": "type here",
           "value": "", "type": "text", "max_length": null}}

// server pushes a value
{"op": "write",  "ref": "HomePage.name", "payload": "alice"}

// server fetches
{"op": "read",   "ref": "HomePage.name", "payload": null,    "id": "ab12"}
{"op": "read",   "ref": "HomePage.name", "payload": "alice", "id": "ab12"}

// browser tells server the user committed
{"op": "notify", "ref": "HomePage.name", "payload": null}
```

`write` and `read`-response payloads are msgpack strings. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/input.tsx`. A `<label>` block wrapping a label span above a native `<input>`. Tailwind utility classes; no shadcn dep. Commit emits one `notify` on blur and on Enter (Enter also blurs the input).

## slice shape

```
{
  type: "InputRef",
  value: string,
  label: string,
  placeholder: string,
  inputType: string,
  maxLength: number | null,
  write: (v: unknown) => void,
  get: () => string,
}
```

Seeded from `field.props` on mount. `write` coerces nil to `""` and non-string payloads via `String(v)`. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` payload is msgpack nil (Nu sentinel): coerced to `""`.
- `write` payload is non-string: stored as `String(v)`.
- slot never written and no `props` on mount: slice defaults to `value=""`, `label=""`, `placeholder=""`, `inputType="text"`, `maxLength=null`.
- empty `label`: the label span is omitted; only the input renders.
- `max_length` None: no `maxLength` attribute on the `<input>`.
- `type` outside the four allowed: passed through; the browser falls back to `text`.
- no debounce: one `notify` per commit (blur or Enter).

## non-goals

- no multi-line variant (that belongs to a separate `TextAreaRef`).
- no per-keystroke notify; only commit notifies.
- no validation rules beyond `max_length`.
- no readonly / disabled flags.
