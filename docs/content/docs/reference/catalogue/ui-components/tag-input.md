---
title: TagInputRef
---

Multi-tag entry field. Tab-owned: the browser holds the canonical list of committed tags. The half-typed buffer stays in the browser and is never on the wire.

## kind

input

## defaults (class-level)

| field              | type           | default | notes                                                            |
| ------------------ | -------------- | ------- | ---------------------------------------------------------------- |
| `label`            | `str`          | `""`    | rendered above the field; the label node is hidden when empty.   |
| `placeholder`      | `str`          | `""`    | shown in the buffer input when the committed list is empty.      |
| `value`            | `list[str]`    | `[]`    | initial committed tags; seeds the slice on mount.                |
| `max_tags`         | `int \| None`  | `None`  | when set, further commits past the limit are dropped silently.   |
| `allow_duplicates` | `bool`         | `False` | when false, a commit equal to an existing tag is dropped.        |

Class attributes on `TagInputRef`. Shipped in `mount_props()` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s replace the committed list wholesale; `label`, `placeholder`, `max_tags`, and `allow_duplicates` are mount-time only.

## interactions

| op       | dir            | payload                              | nu method     | notes                                                                  |
| -------- | -------------- | ------------------------------------ | ------------- | ---------------------------------------------------------------------- |
| `write`  | server -> tab  | `list[str]`                          | `store`       | canonical replace of the committed list. Nil -> `[]`. Buffer untouched.|
| `read`   | server -> tab  | request `null`, response `list[str]` | (via `aeval`) | request/response, correlated by `id`. returns the committed list.      |
| `notify` | tab -> server  | `null`                               | `changed`     | fires whenever the committed list changes (commit, x-click, backspace).|

`TagInputRef.aeval` ships a `read` via `session.aread`. `TagInputRef.set(value)` compiles to `write`. `TagInputRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry
{"path": "FormPage.tags", "type": "TagInputRef",
 "props": {"label": "Tags", "placeholder": "add a tag...",
           "value": [], "max_tags": null, "allow_duplicates": false}}

// server replaces the list
{"op": "write",  "ref": "FormPage.tags", "payload": ["python", "rust"]}

// server fetches
{"op": "read",   "ref": "FormPage.tags", "payload": null,                "id": "ab12"}
{"op": "read",   "ref": "FormPage.tags", "payload": ["python", "rust"],  "id": "ab12"}

// browser tells server the committed list changed
{"op": "notify", "ref": "FormPage.tags", "payload": null}
```

`write` and `read`-response payloads are msgpack arrays of strings. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/tag-input.tsx`. A `<label>` block wrapping the optional label span and a bordered flex row. Existing tags render as small pills with an inline `x` remove button; a borderless `<input>` fills the remaining row for the buffer. Enter and `,` commit; Backspace on an empty buffer drops the last tag.

## slice shape

```
{
  type: "TagInputRef",
  value: string[],           // committed list -- get() returns this
  buffer: string,            // half-typed tag, browser-only
  label: string,
  placeholder: string,
  maxTags: number | null,
  allowDuplicates: boolean,
  write: (v) => void,        // replaces value with the incoming list; nil -> []
  get: () => string[],       // returns the committed list (not the buffer)
}
```

Seeded from `field.props` on mount. `write` coerces nil to `[]`; non-array payloads are ignored defensively. `get` reads the live slice to avoid stale closures. The buffer lives on the slice so devtools see it.

## commit rules

- `Enter` -> commit, prevent default.
- `,` -> commit, prevent default (the comma is not inserted).
- `Backspace` with empty buffer and `tags.length > 0` -> drop the last tag, notify.
- blur -> commit.

`commitBuffer()`:

1. Trim. If empty, clear buffer and return.
2. If `max_tags` set and `tags.length >= max_tags`, clear buffer and return (silent drop).
3. If `!allow_duplicates` and the trimmed tag exists, clear buffer and return (silent drop).
4. Append the trimmed tag, clear buffer, send `notify`.

## edge cases

- `write` with msgpack nil: committed list becomes `[]`. Buffer is untouched.
- `write` with a non-list payload: ignored.
- slot never written: slice is seeded from `props.value` (default `[]`).
- `max_tags` reached: further commits drop silently. Removing a tag re-opens capacity.
- duplicate when `allow_duplicates=false`: silent drop. Comparison is exact equality after trim.
- whitespace-only buffer: trimmed to empty, dropped, no notify.
- backspace-remove fires `notify` exactly like an x-click remove.
- pasting `"a, b, c"`: not split in v0.1.0; user must press Enter or `,` to commit each.

## non-goals

- no paste-splitting.
- no drag-reorder, no edit-in-place.
- no per-tag validation regex, colors, or types.
- no `append` / `remove` server-side ops -- the server replaces with `write`.
- no autocomplete or suggestion list.
- no `max_length` per tag.
