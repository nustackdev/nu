---
title: NumberInputRef
---

Single-line numeric input with min/max/step and stepper buttons. Tab-owned: the browser holds the canonical value.

## kind

input

## defaults (class-level)

| field         | type            | default | notes                                                                              |
| ------------- | --------------- | ------- | ---------------------------------------------------------------------------------- |
| `label`       | `str`           | `""`    | label rendered above the input. empty means no label node.                         |
| `placeholder` | `str`           | `""`    | passed to `<input placeholder=...>`.                                               |
| `min`         | `float \| None` | `None`  | lower bound. clamped on commit if set. omitted from `<input min>` when None.       |
| `max`         | `float \| None` | `None`  | upper bound. clamped on commit if set. omitted from `<input max>` when None.       |
| `step`        | `float`         | `1.0`   | passed to `<input step>` and drives stepper button delta.                          |
| `default`     | `float`         | `0.0`   | initial value seeded into the slice on mount. mirrored to slice key `value`.       |

Class attributes on the python `NumberInputRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override slice fields.

## interactions

| op       | dir            | payload                       | nu method      | notes                                                                  |
| -------- | -------------- | ----------------------------- | -------------- | ---------------------------------------------------------------------- |
| `write`  | server -> tab  | `float` (scalar) or partial map | `store`, `store_value`, `store_min`, `store_max`, `store_step`, `store_label` | scalar replaces `value`; map merges any subset of `{value, min, max, step, label}`. |
| `read`   | server -> tab  | request `null`; resp `float`  | (via `aeval`)  | request/response correlated by `id`.                                   |
| `notify` | tab -> server  | `null`                        | `changed`      | emitted on commit (blur, Enter, stepper click).                        |

`NumberInputRef.aeval` ships a `read` via `session.aread` and returns the number. `NumberInputRef.store(value)` compiles to `write` (scalar form when only `value` is passed, map form when other kwargs are present). `NumberInputRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.qty", "type": "NumberInputRef",
 "props": {"label": "quantity", "placeholder": "0",
           "min": 0.0, "max": 100.0, "step": 1.0, "default": 0.0}}

// server pushes just a value (scalar shortcut)
{"op": "write",  "ref": "HomePage.qty", "payload": 42.0}

// server adjusts bounds + value together (map form)
{"op": "write",  "ref": "HomePage.qty",
 "payload": {"value": 5.0, "min": 0.0, "max": 10.0, "step": 0.5}}

// server sets just the label
{"op": "write",  "ref": "HomePage.qty", "payload": {"label": "count"}}

// server fetches
{"op": "read",   "ref": "HomePage.qty", "payload": null,  "id": "ab12"}
{"op": "read",   "ref": "HomePage.qty", "payload": 42.0,  "id": "ab12"}

// browser tells server the user committed
{"op": "notify", "ref": "HomePage.qty", "payload": null}
```

`write` scalar payload is a msgpack float (or nil -> coerced to the slice's effective floor: `min` if set else `0`). `write` map payload is a msgpack map with any subset of `{value, min, max, step, label}`. `read`-response is a msgpack float. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/number-input.tsx`. A `<label>` block wrapping the optional label span above a flex row: a `[-]` button, a native `<input type="number">`, a `[+]` button. Tailwind utility classes; no shadcn dep. Stepper buttons mutate the local slice by `+/- step` (clamped) then commit. `<input>` commit fires `notify` on blur and on Enter (Enter also blurs the input). Browser clamps the value to `[min, max]` on commit if either bound is set.

## slice shape

```
{
  type: "NumberInputRef",
  value: number,
  min: number | null,
  max: number | null,
  step: number,
  label: string,
  placeholder: string,
  write: (v: unknown) => void,
  get: () => number,
}
```

Seeded from `field.props` on mount: `value = props.default`, plus `min`, `max`, `step`, `label`, `placeholder`. `write` accepts scalar (number/nil) or partial map. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` scalar nil: coerced to `min` if set, else `0`.
- `write` scalar non-finite (NaN, Infinity): coerced to `min` if set, else `0`.
- `write` map `min: null` or `max: null`: clears that bound.
- `min` and `max` both None: no clamping; raw input value is committed.
- value below `min` on commit: clamped up to `min`.
- value above `max` on commit: clamped down to `max`.
- slot never written and no `props` on mount: slice defaults to `value=0`, `min=null`, `max=null`, `step=1`, `label=""`, `placeholder=""`.
- empty `label`: label span omitted.
- stepper buttons at bounds: still emit a commit; clamp keeps value within range. no disabled state in v0.1.0.
- user types a non-numeric string: native `<input type="number">` rejects; slice keeps last valid number.

## non-goals

- no integer-only variant (use `step=1` and accept floats on the wire).
- no per-keystroke notify; only commit (blur, Enter, stepper) notifies.
- no validation messages or invalid state styling.
- no readonly / disabled flags.
- no unit suffix / prefix decoration.
- no scientific notation toggle.
