# SliderRef

Numeric slider with min/max/step. Tab-owned: the browser holds the canonical value.

## kind

input

## defaults (class-level)

| field        | type    | default | notes                                                              |
| ------------ | ------- | ------- | ------------------------------------------------------------------ |
| `min`        | `float` | `0.0`   | left bound, inclusive.                                             |
| `max`        | `float` | `100.0` | right bound, inclusive.                                            |
| `step`       | `float` | `1.0`   | quantization step. Must be positive.                               |
| `value`      | `float` | `0.0`   | initial position seeded on mount.                                  |
| `label`      | `str`   | `""`    | text above the track; empty means no label rendered.               |
| `show_value` | `bool`  | `True`  | when true, current value is rendered next to the track.            |

Class attributes on the python `SliderRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override slice fields.

## interactions

| op       | dir            | payload                       | nu method            | notes                                                              |
| -------- | -------------- | ----------------------------- | -------------------- | ------------------------------------------------------------------ |
| `write`  | server -> tab  | `float` or partial map        | `store`, `store_value`, `store_min`, `store_max`, `store_step`, `store_label`, `store_show_value` | scalar replaces `value`; map merges given keys. |
| `read`   | server -> tab  | request `null`; resp `float`  | (via `aeval`)        | request/response correlated by `id`. resolves the live value.      |
| `notify` | tab -> server  | `null`                        | `changed`            | emitted on slider release (pointerup, blur, Enter, arrow keyup).   |

`SliderRef.aeval` ships a `read` via `session.aread` and returns the number. `SliderRef.store(value)` compiles to `write` (scalar form when only `value` is passed, map form otherwise). `SliderRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.volume", "type": "SliderRef", "props": {"min": 0.0, "max": 100.0, "step": 1.0, "value": 0.0, "label": "", "show_value": true}}

// server pushes a scalar value
{"op": "write",  "ref": "HomePage.volume", "payload": 42.0}

// server reconfigures range and value
{"op": "write",  "ref": "HomePage.volume", "payload": {"min": 0.0, "max": 1.0, "step": 0.01, "value": 0.5}}

// server fetches
{"op": "read",   "ref": "HomePage.volume", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.volume", "payload": 42.0,  "id": "ab12"}

// browser reports release
{"op": "notify", "ref": "HomePage.volume", "payload": null}
```

`write` scalars and `read`-responses are msgpack floats. `write` map payloads are msgpack maps with string keys. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/slider.tsx`. Native `<input type="range">` wrapped with an optional label above and an optional value readout to the right. Tailwind utility classes; no shadcn dep. Drag updates the slice (controlled input); `notify` fires only on release.

## slice shape

```
{
  type: "SliderRef",
  value: number,
  min: number,
  max: number,
  step: number,
  label: string,
  show_value: boolean,
  write: (v: unknown) => void,
  get: () => number,
}
```

Seeded from `field.props` on mount. `write` accepts scalar (number/nil) or partial map. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` scalar nil (Nu sentinel): coerced to `min` so the input never goes uncontrolled.
- `write` scalar non-finite (NaN, Infinity): coerced to `min`.
- `write` map missing keys: untouched fields keep prior slice values.
- slot never written and no `props` on mount: slice defaults to `value=0`, `min=0`, `max=100`, `step=1`, `label=""`, `show_value=true`.
- value outside `[min, max]`: stored as sent; the DOM clamps the visual thumb. `notify` reports the user-committed value.
- `notify` debounce: emitted on pointerup, blur, Enter, and arrow keyup. No notify during continuous drag.
