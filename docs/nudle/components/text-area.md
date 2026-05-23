# TextAreaRef

Multi-line text input. Tab-owned: the browser holds the canonical value.

## kind

input

## defaults (class-level)

| field         | type          | default | notes                                                              |
| ------------- | ------------- | ------- | ------------------------------------------------------------------ |
| `value`       | `str`         | `""`    | initial text seeded on mount.                                      |
| `placeholder` | `str`         | `""`    | placeholder shown when the value is empty.                         |
| `rows`        | `int`         | `4`     | initial visible rows; minimum height when `auto_resize` is on.     |
| `max_length`  | `int \| None` | `None`  | optional hard cap on character count. `None` disables the cap.     |
| `auto_resize` | `bool`        | `False` | when true, the textarea grows with content past `rows`.            |

Class attributes on the python `TextAreaRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override the slice `value` only; the other props are structural and stay fixed for the slot's life.

## interactions

| op       | dir            | payload                    | nu method     | notes                                                                    |
| -------- | -------------- | -------------------------- | ------------- | ------------------------------------------------------------------------ |
| `write`  | server -> tab  | `str`                      | `store`       | canonical push or reset; replaces the local value.                       |
| `read`   | server -> tab  | request `null`; resp `str` | (via `aeval`) | request/response, correlated by `id`. resolves the live value.           |
| `notify` | tab -> server  | `null`                     | `changed`     | emitted on commit only: blur or cmd-enter / ctrl-enter.                  |

`TextAreaRef.aeval` ships a `read` via `session.aread` and returns the string. `TextAreaRef.store(value)` compiles to `write`. `TextAreaRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry
{"path": "HomePage.body", "type": "TextAreaRef", "props": {"value": "", "placeholder": "type here", "rows": 6, "max_length": null, "auto_resize": true}}

// server pushes a value
{"op": "write",  "ref": "HomePage.body", "payload": "line one\nline two"}

// server clears via Nu sentinel
{"op": "write",  "ref": "HomePage.body", "payload": null}

// server fetches
{"op": "read",   "ref": "HomePage.body", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.body", "payload": "line one\nline two", "id": "ab12"}

// browser commits
{"op": "notify", "ref": "HomePage.body", "payload": null}
```

`write` and `read`-response payloads are msgpack strings. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/text-area.tsx`. Native controlled `<textarea>` with tailwind utility classes (matches `InputRef` weight). When `auto_resize` is on, a layout effect resets `height = "auto"` then `height = scrollHeight` on every value change so the box tracks content. Plain Enter inserts a newline; cmd/ctrl-Enter commits and blurs.

## edge cases

- `write` payload is msgpack nil (Nu sentinel): slice `value` becomes `""`.
- `write` payload is non-string: coerced via `String(v)`; no error frame.
- slot never written and no `props`: slice defaults to the class-level values.
- `max_length` enforced by the browser via the `maxLength` attribute; `None` disables.
- only blur and cmd/ctrl-Enter emit `notify`; per-keystroke edits stay local until commit.
- when `auto_resize` is off the textarea keeps its native resize handle behavior; with `auto_resize` on the inline height overrides it.
