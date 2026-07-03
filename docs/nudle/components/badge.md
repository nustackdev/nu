# BadgeRef

Small inline label with a variant tag. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field     | type                                                   | default     | notes                                 |
| --------- | ------------------------------------------------------ | ----------- | ------------------------------------- |
| `label`   | `str`                                                  | `""`        | text shown in the badge body          |
| `variant` | `Literal["info", "warn", "ok", "danger", "neutral"]`   | `"neutral"` | drives the tailwind colour map        |

Declared as plain class attributes on the python `BadgeRef`. They are shipped once on `mount` under the field entry's `props` key and used to seed the browser slice (no explicit `write` needed). Later server -> tab writes override slice values.

## interactions

| op      | dir           | payload                              | nu method                                | notes                                                                |
| ------- | ------------- | ------------------------------------ | ---------------------------------------- | -------------------------------------------------------------------- |
| `write` | server -> tab | `{"label"?: str, "variant"?: str}`   | `store_label`, `store_variant`, `store`  | partial update; keys absent from the payload leave the slice as is.  |

Three nu methods compile to the same wire op with different payload subsets:

- `store_label(text)` -> `write {"label": text}`
- `store_variant(name)` -> `write {"variant": name}`
- `store(label, variant=...)` -> `write {"label": label, "variant": variant}` (variant omitted if not passed)

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.status", "type": "BadgeRef", "props": {"label": "", "variant": "neutral"}}

// label-only update
{"op": "write", "ref": "HomePage.status", "payload": {"label": "queued"}}

// variant-only update
{"op": "write", "ref": "HomePage.status", "payload": {"variant": "ok"}}

// combined update
{"op": "write", "ref": "HomePage.status", "payload": {"label": "failed", "variant": "danger"}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels on either field encode as msgpack nil; on the browser, nil decodes to `""` for `label` and `"neutral"` for `variant`.

## renderer

`web/src/refs/badge.tsx`. A `<span>` with tailwind utility classes per variant. No external shadcn dep; the variant -> class map is a local const (`VARIANT_CLASSES`). Unknown variant strings fall back to the `neutral` class set.

## slice shape

```
{
  type: "BadgeRef",
  value: null,
  label: string,
  variant: string,
  write: (v: {label?, variant?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `label` is msgpack nil: stored as `""`.
- `variant` is msgpack nil: stored as `"neutral"`.
- variant string outside the five known names: stored raw in the slice; the renderer falls back to the neutral class map. No error frame.
- slot never written and no `props` on mount: selector defaults kick in (`""` / `"neutral"`).
- no max length on `label`; truncation is a css concern.

## non-goals

- no `append`, no `read`, no `notify`. Single label, server-owned.
- no click / hover. A clickable badge belongs to a separate `ChipRef`.
- no icon slot, no per-instance colour overrides, no tooltip.
- no `caps` flags on mount; deferred catalog-wide.
