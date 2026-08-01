---
title: AlertRef
---

Variant-tagged banner with a title and a body. Display, optionally dismissible by the user.

## kind

display

## defaults (class-level)

| field         | type                                        | default  | notes                                                          |
| ------------- | ------------------------------------------- | -------- | -------------------------------------------------------------- |
| `variant`     | `Literal["info", "warn", "ok", "danger"]`   | `"info"` | drives the tailwind colour map                                 |
| `title`       | `str`                                       | `""`     | bold heading line; empty means no heading row                  |
| `body`        | `str`                                       | `""`     | longer body text shown under the title                         |
| `dismissible` | `bool`                                      | `False`  | when True, the renderer shows an X and emits `notify` on click |

Declared as plain class attributes on the python `AlertRef`. Shipped once on `mount` under the field entry's `props` key and used to seed the browser slice. Later server -> tab `write`s override slice values.

## interactions

| op       | dir           | payload                                                                | nu method                                                                  | notes                                                                 |
| -------- | ------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `write`  | server -> tab | `{"variant"?: str, "title"?: str, "body"?: str, "dismissible"?: bool}` | `store_variant`, `store_title`, `store_body`, `store_dismissible`, `store` | partial update; absent keys leave the slice untouched                 |
| `notify` | tab -> server | `null`                                                                 | `dismissed`                                                                | emitted once when user clicks the X; only when `dismissible` is True  |

Nu methods compile to the same `write` op with different payload subsets:

- `store_variant(name)` -> `write {"variant": name}`
- `store_title(text)` -> `write {"title": text}`
- `store_body(text)` -> `write {"body": text}`
- `store_dismissible(flag)` -> `write {"dismissible": flag}`
- `set(title, body=..., variant=..., dismissible=...)` -> `write {...}` with only keys passed
- `dismissed()` -> `Changed` subscription on `notify`

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.alert", "type": "AlertRef", "props": {"variant": "info", "title": "", "body": "", "dismissible": false}}

// variant-only update
{"op": "write", "ref": "HomePage.alert", "payload": {"variant": "warn"}}

// title + body
{"op": "write", "ref": "HomePage.alert", "payload": {"title": "queued", "body": "your job is in the queue"}}

// enable dismissible
{"op": "write", "ref": "HomePage.alert", "payload": {"dismissible": true}}

// combined
{"op": "write", "ref": "HomePage.alert", "payload": {"variant": "danger", "title": "failed", "body": "see logs", "dismissible": true}}

// browser dismiss click
{"op": "notify", "ref": "HomePage.alert", "payload": null}
```

`write` payload is a msgpack map. Missing keys mean "keep current slice value". `notify` payload is msgpack nil. Nu sentinels (EMPTY / INVALID) on any field encode as msgpack nil; on the browser, nil decodes to the field default (`"info"` for variant, `""` for title and body, `false` for dismissible).

## renderer

`web/src/refs/alert.tsx`. A `<div role="alert">` styled with tailwind utility classes per variant; the variant -> class map is a local const (`VARIANT_CLASSES`) keyed on `info | warn | ok | danger`. Unknown variant strings fall back to the `info` class set. Inside: an optional bold title row (rendered only when title is non-empty), a body paragraph (rendered only when body is non-empty), and, when `dismissible` is true, a trailing X button. Clicking the X sends `{op: OP_NOTIFY, ref: path, payload: null}`. The renderer does not hide itself on dismiss; the server decides whether to clear or re-`write` the alert.

## slice shape

```
{
  type: "AlertRef",
  value: null,
  variant: string,
  title: string,
  body: string,
  dismissible: boolean,
  write: (v: {variant?, title?, body?, dismissible?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice. Non-string variant / title / body coerce via `String(v)` (nil -> default); non-bool `dismissible` coerces via `Boolean(v)`.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `variant` is msgpack nil: stored as `"info"`.
- `title` is msgpack nil: stored as `""`; renderer omits the title row.
- `body` is msgpack nil: stored as `""`; renderer omits the body paragraph but still draws the frame.
- `dismissible` is msgpack nil: stored as `false`.
- variant string outside the four known names: stored raw; renderer falls back to the info class map. No error frame.
- X clicked while `dismissible` is false: not reachable; the X is not rendered.
- slot never written and no `props` on mount: selector defaults kick in (`"info"` / `""` / `""` / `false`); a bare info-variant frame renders with no title or body.
- both `title` and `body` empty: an empty frame is still drawn (server may use it as a placeholder slot).
- no max length on title / body; long body wraps; truncation is a css concern.

## non-goals

- no auto-dismiss timer.
- no icon slot. The variant colour is the only visual signal beyond text.
- no per-instance colour overrides beyond the four variants.
- no `append`, no `read`.
- no action buttons inside the alert; compose a separate `ButtonRef` next to it.
- no animation on mount or dismiss.
- the renderer does not auto-hide on dismiss; server owns visibility.
