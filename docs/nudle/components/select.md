# SelectRef

Single-select dropdown over a fixed list of options. Tab-owned: the browser holds the canonical selected value.

## kind

input

## defaults (class-level)

| field         | type                                  | default | notes                                                                                              |
| ------------- | ------------------------------------- | ------- | -------------------------------------------------------------------------------------------------- |
| `options`     | `list[str] \| list[dict[str, str]]`   | `[]`    | accepted as a list of strings (value == label) or a list of `{"value": str, "label": str}` dicts.  |
| `selected`    | `str`                                 | `""`    | initial selected value. should match an option `value`; empty means nothing selected.              |
| `placeholder` | `str`                                 | `""`    | text shown as a disabled leading option when nothing is selected.                                  |

Class attributes on the python `SelectRef`. Shipped on `mount` under the field entry's `props` key after `mount_props` normalizes `options` into the dict form. Later server -> tab `write`s override slice values.

## interactions

| op       | dir            | payload                                                                | nu method                | notes                                                                          |
| -------- | -------------- | ---------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------ |
| `write`  | server -> tab  | `str` (selected value) **or** `{"options": list[{value, label}]}`      | `store`, `store_options` | string payload replaces the selected value; map with `options` swaps the list. |
| `read`   | server -> tab  | request `null`; resp `str`                                             | (via `aeval`)            | request/response, correlated by `id`. resolves the live selected value.        |
| `notify` | tab -> server  | `null`                                                                 | `changed`                | emitted on every user pick.                                                    |

Nu methods:

- `SelectRef.aeval` ships a `read` via `session.aread`, returns the selected value as `str`.
- `SelectRef.store(value)` compiles to `write` with a bare string payload.
- `SelectRef.store_options(opts)` compiles to `write` with `{"options": [...]}`. Accepts strings or dicts; normalized server-side.
- `SelectRef.changed()` returns a `Changed` subscription driven by inbound `notify` frames.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.flavor", "type": "SelectRef", "props": {
  "options":  [{"value": "v", "label": "Vanilla"}, {"value": "c", "label": "Chocolate"}],
  "selected": "v",
  "placeholder": "pick one"
}}

// server pushes a selected value
{"op": "write",  "ref": "HomePage.flavor", "payload": "c"}

// server swaps the option list
{"op": "write",  "ref": "HomePage.flavor", "payload": {"options": [{"value": "s", "label": "Strawberry"}]}}

// server fetches
{"op": "read",   "ref": "HomePage.flavor", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.flavor", "payload": "s",  "id": "ab12"}

// browser tells server the user picked something
{"op": "notify", "ref": "HomePage.flavor", "payload": null}
```

`write` payload is a msgpack string (selected push) or a msgpack map with an `options` key (list swap). `read`-response is a msgpack string; `notify` and `read`-request are msgpack nil.

## renderer

`web/src/refs/select.tsx`. Native `<select>` with the option list rendered as `<option>` children. Placeholder is a disabled leading option that only shows while `selected === ""`. Tailwind utility classes match `input.tsx`; no shadcn dep.

## slice shape

```
{
  type: "SelectRef",
  value: null,
  selected: string,
  options: Array<{ value: string; label: string }>,
  placeholder: string,
  write: (v: unknown) => void,
  get: () => string,
}
```

Seeded from `field.props` on mount. `write` dispatches on payload shape: a map with `options` overwrites the option list; anything else is coerced via `String(v)` and assigned to `selected` (nil becomes `""`). `get` reads from the live store to avoid stale closures.

## edge cases

- `write` payload is msgpack nil: slice `selected` becomes `""`.
- `write` payload is a string not present in `options`: still stored on the slice; the native `<select>` will render no option as selected until the next pick.
- `write` payload is `{"options": [...]}` and the current `selected` is not in the new list: `selected` is left untouched; the renderer shows nothing selected.
- `write` payload is a non-string, non-map (e.g. number): coerced via `String(v)`.
- `options` entry missing `value` or `label`: coerced via `String(...)`; nil becomes `""`.
- slot never written and no `props` on mount: slice defaults to `selected=""`, `options=[]`, `placeholder=""`.
- empty `placeholder` and empty `selected`: no leading placeholder option is rendered.
- no debounce: every user pick ships one `notify`.
