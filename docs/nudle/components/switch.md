# SwitchRef

On/off toggle. Semantic alternative to `CheckboxRef`: same wire shape, different affordance (shadcn `Switch`).

## kind

input

## defaults (class-level)

| field     | type   | default | notes                                                  |
| --------- | ------ | ------- | ------------------------------------------------------ |
| `label`   | `str`  | `""`    | text next to the switch; empty means no label.         |
| `default` | `bool` | `False` | initial on/off state seeded on mount.                  |

Class attributes on the python `SwitchRef`. The python class uses `default` (not `checked`) to keep the wording neutral; on the wire / slice the canonical state field is `checked`. `mount_props` emits `{"label": cls.label, "checked": cls.default}` so the slice factory is identical to `CheckboxRef`.

## interactions

| op       | dir            | payload                     | nu method     | notes                                                              |
| -------- | -------------- | --------------------------- | ------------- | ------------------------------------------------------------------ |
| `write`  | server -> tab  | `bool`                      | `store`       | canonical push or reset; replaces the local checked state.         |
| `read`   | server -> tab  | request `null`; resp `bool` | (via `aeval`) | request/response, correlated by `id`; resolves the live value.     |
| `notify` | tab -> server  | `null`                      | `changed`     | emitted on every user toggle of the switch.                        |

`SwitchRef.aeval` ships a `read` via `session.aread` and returns the bool. `SwitchRef.store(value)` compiles to `write`. `SwitchRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.notify", "type": "SwitchRef", "props": {"label": "Notifications", "checked": false}}

// server pushes a value
{"op": "write",  "ref": "HomePage.notify", "payload": true}

// server fetches
{"op": "read",   "ref": "HomePage.notify", "payload": null, "id": "ab12"}
{"op": "read",   "ref": "HomePage.notify", "payload": true, "id": "ab12"}

// browser tells server the user toggled
{"op": "notify", "ref": "HomePage.notify", "payload": null}
```

`write` and `read`-response payloads are msgpack bools. `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/switch.tsx`. shadcn `Switch` (from `@/components/ui/switch`, wrapping `radix-ui`'s `Switch.Root` + `Switch.Thumb`) wrapped in a `<label>` so the label text is also a click target.

## slice shape

```
{
  type: "SwitchRef",
  value: null,
  label: string,
  checked: boolean,
  write: (v: unknown) => void,
  get: () => boolean,
}
```

Seeded from `field.props` on mount. `write` coerces non-bool / nil payloads via `Boolean(v)`. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` payload is msgpack nil (Nu sentinel): coerced to `false`.
- `write` payload is non-bool: `Boolean(v)` coercion; no error frame.
- slot never written and no `props` on mount: slice defaults to `checked=false`, `label=""`.
- empty `label`: the trailing `<span>` is omitted; only the switch is clickable.
- no debounce: each user toggle emits one `notify`.

## non-goals

- no tri-state / indeterminate variant.
- no size / color variants on the python side; renderer uses shadcn defaults.
- no icon slots inside the switch thumb.
- no disabled prop on the Ref; disabled state belongs to a future form-level concern.
