---
title: LinkRef
---

Anchor with an href, label, target, and an optional external indicator. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field      | type                                | default     | notes                                                                                                                                                  |
| ---------- | ----------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `href`     | `str`                               | `""`        | url the anchor points to. empty string renders an inert anchor (no `href` attr).                                                                       |
| `label`    | `str`                               | `""`        | visible link text. falls back to `href` when empty.                                                                                                    |
| `target`   | `Literal["_self", "_blank"]`        | `"_self"`   | `"_blank"` also emits `rel="noopener noreferrer"`. unknown values fall back to `"_self"`.                                                              |
| `external` | `bool \| None`                      | `None`      | tri-state: `True` forces the indicator, `False` suppresses it, `None` auto-detects (true when `target` is `_blank` or the host differs from the tab's host). |

Declared as plain class attributes on the python `LinkRef`. Shipped on `mount` under the field entry's `props` key and used to seed the browser slice (no explicit `write` needed). Subsequent server -> tab writes override slice values.

## interactions

| op      | dir           | payload                                                                            | nu method                                                              | notes                                                                                |
| ------- | ------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `write` | server -> tab | `{"href"?: str, "label"?: str, "target"?: str, "external"?: bool \| null}`         | `store_href`, `store_label`, `store_target`, `store_external`, `store` | partial update; any subset of keys may be present. unknown `target` clamps to `_self`. |

Five nu methods compile to the same wire op with different payload subsets:

- `store_href(url)` -> `write {"href": url}`
- `store_label(text)` -> `write {"label": text}`
- `store_target(name)` -> `write {"target": name}`
- `store_external(flag)` -> `write {"external": flag}` (flag may be `True`, `False`, or `None`)
- `store(href=..., label=..., target=..., external=...)` -> `write` with only the kwargs explicitly passed. Implemented via a private `_UNSET` sentinel so callers can pass `external=None` to reset to auto without it being confused with "do not touch".

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.docs", "type": "LinkRef", "props": {"href": "", "label": "", "target": "_self", "external": null}}

// href-only update
{"op": "write", "ref": "HomePage.docs", "payload": {"href": "https://nu.dev"}}

// label-only update
{"op": "write", "ref": "HomePage.docs", "payload": {"label": "docs"}}

// target switch + suppress external indicator
{"op": "write", "ref": "HomePage.docs", "payload": {"target": "_blank", "external": false}}

// combined update
{"op": "write", "ref": "HomePage.docs", "payload": {"href": "https://nu.dev", "label": "Nu docs", "target": "_blank", "external": null}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels decode as msgpack nil; on the browser nil maps to `""` for `href` / `label`, `"_self"` for `target`, and `null` (auto) for `external`.

## renderer

`web/src/refs/link.tsx`. A plain tailwind `<a>` with optional `rel="noopener noreferrer"` when `target="_blank"`. The external indicator is a `↗` glyph in an `aria-hidden` span. `isCrossHost` uses `new URL(href, window.location.href)` to compare hosts; relative urls resolve to same host and the indicator stays off.

## slice shape

```
{
  type: "LinkRef",
  value: null,
  href: string,
  label: string,
  target: "_self" | "_blank",
  external: boolean | null,
  write: (v: {href?, label?, target?, external?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `href` is msgpack nil: stored as `""`; renderer omits the `href` attr.
- `label` is msgpack nil or empty: renderer falls back to displaying `href` as the text.
- `target` is msgpack nil or unknown: stored / clamped to `"_self"`.
- `external` is msgpack nil: stored as `null` (auto).
- both `href` and `label` empty: renders an empty `<a>` with no `href` attr. No error frame.
- non-absolute `href` (e.g. `/docs`): auto-detection sees same host and suppresses the indicator unless `external` is explicitly `True`.
- slot never written and no `props` on mount: selector defaults kick in.

## non-goals

- no `append`, no `read`, no `notify`. Single record, server-owned. Click telemetry is out of scope.
- no icon slot beyond the fixed external indicator.
- no per-instance colour or weight overrides.
- no `download`, `ping`, `referrerpolicy`, `hreflang`.
- no router-aware navigation. NavRef handles app-internal routing; LinkRef is a plain anchor.
- no `caps` flags on mount; deferred catalog-wide.
