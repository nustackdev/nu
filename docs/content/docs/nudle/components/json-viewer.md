---
title: JsonViewerRef
---

Collapsible json tree viewer. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field          | type                              | default     | notes                                                                            |
| -------------- | --------------------------------- | ----------- | -------------------------------------------------------------------------------- |
| `value`        | `object`                          | `None`      | the json data: arbitrary nested map / list / scalar. msgpack-encoded as is.      |
| `expand_depth` | `int`                             | `1`         | how deep the tree auto-expands. `0` = collapsed root, `1` = root expanded, ...   |
| `theme`        | `Literal["light", "dark"]`        | `"light"`   | colour scheme on the browser side. unknown values render the light styles.      |
| `copyable`     | `bool`                            | `False`     | when true, a small copy button copies the json as a string to the clipboard.    |
| `sortable`     | `bool`                            | `False`     | when true, object keys render sorted alphabetically. lists keep order.          |
| `max_height`   | `int \| None`                     | `None`      | pixel cap on the viewer container. `None` = no cap. when set, the container scrolls. |

Declared as plain class attributes on the python `JsonViewerRef`. They are shipped once on `mount` under the field entry's `props` key and seed the browser slice (no explicit `write` needed). Later server -> tab writes override slice values via partial-merge.

## interactions

| op      | dir           | payload                                                                                                       | nu method                                                                                                                                                          | notes                                                                |
| ------- | ------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `write` | server -> tab | `{"value"?: any, "expand_depth"?: int, "theme"?: str, "copyable"?: bool, "sortable"?: bool, "max_height"?: int \| None}` | `store`, `store_value`, `store_expand_depth`, `store_theme`, `store_copyable`, `store_sortable`, `store_max_height` | partial update; keys absent from the payload leave the slice as is.  |

Nu method -> wire payload subset:

- `store_value(v)` -> `write {"value": v}`
- `store_expand_depth(n)` -> `write {"expand_depth": n}`
- `store_theme(name)` -> `write {"theme": name}`
- `store_copyable(b)` -> `write {"copyable": b}`
- `store_sortable(b)` -> `write {"sortable": b}`
- `store_max_height(px)` -> `write {"max_height": px}` (pass `None` to remove the cap)
- `store(value, **opts)` -> `write` with `{"value": value}` plus any opt keys explicitly passed

## wire payloads

```
// mount field entry (defaults shipped under props)
{"path": "HomePage.tree", "type": "JsonViewerRef", "props": {"value": null, "expand_depth": 1, "theme": "light", "copyable": false, "sortable": false, "max_height": null}}

// value-only update
{"op": "write", "ref": "HomePage.tree", "payload": {"value": {"a": 1, "b": [2, 3]}}}

// config-only update
{"op": "write", "ref": "HomePage.tree", "payload": {"expand_depth": 3, "theme": "dark"}}

// combined
{"op": "write", "ref": "HomePage.tree", "payload": {"value": [1, 2, 3], "copyable": true, "max_height": 400}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels encode as msgpack nil; on the browser, nil decodes to the field's default (`null` for `value`, `1` for `expand_depth`, `"light"` for `theme`, `false` for `copyable` / `sortable`, `null` for `max_height`).

## renderer

`web/src/refs/json-viewer.tsx`. Wraps `<JsonView>` from `react-json-view-lite` in a `<div>` carrying `text-xs font-mono`. When `max_height` is set, the container takes an inline `maxHeight` and `overflow: auto`. When `copyable` is on, a small `<button>` above the tree copies `JSON.stringify(value, null, 2)` via `navigator.clipboard.writeText`. When `sortable` is on, the slice value is run through a recursive object-key sort before being passed to `<JsonView>`; lists are left in order. `theme` picks between the lib's `defaultStyles` and `darkStyles`; unknown values fall back to light.

## slice shape

```
{
  type: "JsonViewerRef",
  value: unknown,
  expand_depth: number,
  theme: string,
  copyable: boolean,
  sortable: boolean,
  max_height: number | null,
  write: (v: Partial<...>) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `value` is msgpack nil: stored as `null`; renderer shows an empty object tree.
- `expand_depth` is msgpack nil: stored as `1`.
- `theme` is msgpack nil or unknown string: stored raw in the slice; renderer falls back to light styles.
- `copyable` / `sortable` are msgpack nil: stored as `false`.
- `max_height` is msgpack nil: stored as `null`; container drops the inline style and grows naturally.
- slot never written and no `props` on mount: selector defaults kick in (`null`, `1`, `"light"`, `false`, `false`, `null`).
- huge payloads: no chunking, no virtualization. `max_height` plus scroll is the only mitigation.
- circular references: not possible on the wire (msgpack rejects cycles server-side).

## non-goals

- no `append`. Json is a whole-value unit; partial-merge applies only to the top-level config keys, not to the json `value`.
- no `read`, no `notify`. Server-owned.
- no edit-in-place. The tree is read-only.
- no search / filter, no per-node click callbacks, no diff view.
- no schema validation, no type-inference badges.
- no `caps` flags on mount; deferred catalog-wide.
