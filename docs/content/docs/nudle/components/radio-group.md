---
title: RadioGroupRef
---

Single-choice picker rendered as a group of radio inputs over a fixed list of options. Tab-owned: the browser holds the canonical selected value.

## kind

input

## defaults (class-level)

| field         | type                                | default      | notes                                                                                                       |
| ------------- | ----------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| `options`     | `list[dict[str, str]]`              | `[]`         | each entry is `{"value": str, "label": str}`. bare-string entries are accepted and normalized to dict form. |
| `selected`    | `str`                               | `""`         | initial selected value. should match an option `value`; empty means nothing selected.                       |
| `orientation` | `str`                               | `"vertical"` | layout direction for the radio items. one of `"vertical"`, `"horizontal"`.                                  |

Class attributes on the python `RadioGroupRef`. Shipped on `mount` under the field entry's `props` key after `mount_props` normalizes `options` into the dict form. Later server -> tab `write`s override slice values.

## interactions

| op       | dir           | payload                                                           | nu method                | notes                                                                          |
| -------- | ------------- | ----------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------ |
| `write`  | server -> tab | `str` (selected value) **or** `{"options": list[{value, label}]}` | `store`, `store_options` | string payload replaces the selected value; map with `options` swaps the list. |
| `read`   | server -> tab | request `null`; resp `str`                                        | (via `aeval`)            | request/response, correlated by `id`. resolves the live selected value.        |
| `notify` | tab -> server | `null`                                                            | `changed`                | emitted on every user pick.                                                    |

Nu methods:

- `RadioGroupRef.aeval` ships a `read` via `session.aread`, returns the selected value as `str`.
- `RadioGroupRef.store(value)` compiles to `write` with a bare string payload.
- `RadioGroupRef.store_options(opts)` compiles to `write` with `{"options": [...]}`. Accepts strings or dicts; normalized server-side.
- `RadioGroupRef.changed()` returns a `Changed` subscription driven by inbound `notify` frames.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.size", "type": "RadioGroupRef", "props": {
  "options":     [{"value": "s", "label": "Small"}, {"value": "m", "label": "Medium"}, {"value": "l", "label": "Large"}],
  "selected":    "m",
  "orientation": "vertical"
}}

// server pushes a selected value
{"op": "write",  "ref": "HomePage.size", "payload": "l"}

// server swaps the option list
{"op": "write",  "ref": "HomePage.size", "payload": {"options": [{"value": "xs", "label": "XS"}, {"value": "xl", "label": "XL"}]}}

// server fetches
{"op": "read",   "ref": "HomePage.size", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.size", "payload": "l",  "id": "ab12"}

// browser tells server the user picked something
{"op": "notify", "ref": "HomePage.size", "payload": null}
```

`write` payload is a msgpack string (selected push) or a msgpack map with an `options` key (list swap). `read`-response is a msgpack string; `notify` and `read`-request are msgpack nil.

## renderer

`web/src/refs/radio-group.tsx`. Native `<input type="radio">` per option, all sharing a `name` derived from the wire path. Items wrap in a flex container -- `flex-col gap-2` when `orientation === "vertical"`, `flex-row gap-4` when `"horizontal"`. Tailwind utility classes match `select.tsx`; no shadcn dep. Each item is a `<label>` wrapping the radio and its label text.

## slice shape

```
{
  type: "RadioGroupRef",
  value: null,
  selected: string,
  options: Array<{ value: string; label: string }>,
  orientation: "vertical" | "horizontal",
  write: (v: unknown) => void,
  get: () => string,
}
```

Seeded from `field.props` on mount. `write` dispatches on payload shape: a map with `options` overwrites the option list; anything else is coerced via `String(v)` and assigned to `selected` (nil becomes `""`). `get` reads from the live store to avoid stale closures.

## edge cases

- `write` payload is msgpack nil: slice `selected` becomes `""`; no radio is checked.
- `write` payload is a string not present in `options`: still stored on the slice; no radio renders as checked until the next pick.
- `write` payload is `{"options": [...]}` and the current `selected` is not in the new list: `selected` is left untouched; no radio renders as checked.
- `write` payload is a non-string, non-map (e.g. number): coerced via `String(v)`.
- `options` entry missing `value` or `label`: coerced via `String(...)`; nil becomes `""`.
- slot never written and no `props` on mount: slice defaults to `selected=""`, `options=[]`, `orientation="vertical"`.
- `orientation` prop unrecognized: slice falls back to `"vertical"`.
- empty `options`: nothing is rendered inside the container.
- no debounce: every user pick ships one `notify`.

## non-goals

- no multi-select. that is a separate `CheckboxGroupRef`.
- no per-option disabled state.
- no grouped / nested options.
- no inline description / helper text per option (label only).
- no keyboard roving-tabindex custom behavior; rely on native radio semantics.
- no form integration beyond the standard slice contract.
