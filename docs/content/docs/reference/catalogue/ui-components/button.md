---
title: ButtonRef
---

Click trigger. Tab-owned: the browser emits a `notify` on every click; the server pushes labels, variants, and disabled state via `write`.

## kind

input

## defaults (class-level)

| field      | type                                                  | default     | notes                                                       |
| ---------- | ----------------------------------------------------- | ----------- | ----------------------------------------------------------- |
| `label`    | `str`                                                 | `""`        | text inside the button. empty falls back to the path.       |
| `variant`  | `Literal["primary", "secondary", "ghost", "danger"]`  | `"primary"` | drives the tailwind colour map.                             |
| `disabled` | `bool`                                                | `False`     | when True, the renderer skips the click handler.            |
| `icon`     | `str \| None`                                         | `None`      | optional leading icon name; renderer treats unknown as none. |

Class attributes on the python `ButtonRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override slice values.

## interactions

| op       | dir            | payload                                                                       | nu method                                                  | notes                                                            |
| -------- | -------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------- |
| `write`  | server -> tab  | `{"label"?: str, "variant"?: str, "disabled"?: bool, "icon"?: str \| nil}`    | `store_label`, `store_variant`, `store_disabled`, `store`  | partial update; absent keys leave the slice untouched.           |
| `notify` | tab -> server  | `null`                                                                        | `clicked`                                                  | emitted on every click; suppressed while `disabled` is true.     |

Mutators compile to the same `write` op with different payload subsets:

- `store_label(text)` -> `write {"label": text}`
- `store_variant(name)` -> `write {"variant": name}`
- `store_disabled(flag)` -> `write {"disabled": flag}`
- `set(label, variant=..., disabled=..., icon=...)` -> `write {...}` with only the keys passed
- `clicked()` -> `Changed` subscription on `notify`

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.drop", "type": "ButtonRef", "props": {"label": "drop", "variant": "primary", "disabled": false, "icon": null}}

// label-only update
{"op": "write", "ref": "HomePage.drop", "payload": {"label": "saving..."}}

// variant-only update
{"op": "write", "ref": "HomePage.drop", "payload": {"variant": "danger"}}

// disabled toggle
{"op": "write", "ref": "HomePage.drop", "payload": {"disabled": true}}

// combined
{"op": "write", "ref": "HomePage.drop", "payload": {"label": "retry", "variant": "danger", "disabled": false}}

// browser click
{"op": "notify", "ref": "HomePage.drop", "payload": null}
```

`write` payload is a msgpack map. Missing keys mean "keep current slice value". `notify` payload is msgpack nil. Nu sentinels (EMPTY / INVALID) on any field encode as msgpack nil; on the browser, nil decodes to the field default (`""` for label, `"primary"` for variant, `false` for disabled, `null` for icon).

## renderer

`web/src/refs/button.tsx`. A `<button type="button">` with tailwind utility classes per variant. The variant -> class map is a local const (`VARIANT_CLASSES`). Unknown variant strings fall back to the `primary` class set. When the slice `label` is `""`, the renderer shows the path so a freshly mounted button is still locatable. When `disabled` is true, the button is rendered with the native `disabled` attribute and the click handler returns early. `icon`, when set, is rendered as a leading text token; a full icon library is out of scope.

## slice shape

```
{
  type: "ButtonRef",
  value: null,
  label: string,
  variant: string,
  disabled: boolean,
  icon: string | null,
  write: (v: {label?, variant?, disabled?, icon?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice. Non-string label / variant / icon coerce via `String(v)` (nil -> default); non-bool `disabled` coerces via `Boolean(v)`.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `label` is msgpack nil: stored as `""`.
- `variant` is msgpack nil: stored as `"primary"`.
- `disabled` is msgpack nil: stored as `false`.
- `icon` is msgpack nil: stored as `null`.
- variant string outside the four known names: stored raw; renderer falls back to the primary class map. No error frame.
- clicked while `disabled` is true: no `notify` emitted.
- slot never written and no `props` on mount: selector defaults kick in (`""` / `"primary"` / `false` / `null`); the path is shown as the button text.
- no debounce: each user click emits one `notify`.

## non-goals

- no `read`; the server does not query button state.
- no `append`.
- no per-instance colour overrides beyond the four variants.
- no tooltip, no loading spinner. A future `LoadingButtonRef` can wrap.
- no key bindings.
