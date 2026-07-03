# DatePickerRef

Single date picker. Tab-owned: the browser holds the canonical value. ISO 8601 `yyyy-mm-dd` on the wire.

## kind

input

## defaults (class-level)

| field         | type  | default | notes                                                                       |
| ------------- | ----- | ------- | --------------------------------------------------------------------------- |
| `label`       | `str` | `""`    | visible label rendered above the input. empty means no label node.          |
| `placeholder` | `str` | `""`    | passed to `<input placeholder=...>`. shown when value is empty.             |
| `min`         | `str` | `""`    | ISO `yyyy-mm-dd` lower bound (inclusive). empty means no lower bound.       |
| `max`         | `str` | `""`    | ISO `yyyy-mm-dd` upper bound (inclusive). empty means no upper bound.       |
| `default`     | `str` | `""`    | ISO `yyyy-mm-dd` initial value seeded into the slice on mount. `""` = none. |

Class attributes on the python `DatePickerRef`. Shipped on `mount` under the field entry's `props` key and used to seed the slice. Later server -> tab `write`s override slice `value`; `label`, `placeholder`, `min`, `max` are mount-time only.

## interactions

| op       | dir            | payload                          | nu method     | notes                                                                  |
| -------- | -------------- | -------------------------------- | ------------- | ---------------------------------------------------------------------- |
| `write`  | server -> tab  | `str` (ISO `yyyy-mm-dd` or `""`) | `store`       | canonical push or reset; replaces the local value.                     |
| `read`   | server -> tab  | request `null`; resp `str`       | (via `aeval`) | request/response, correlated by `id`. resolves the live value.         |
| `notify` | tab -> server  | `null`                           | `changed`     | emitted when the user picks a new date (native `change` event).        |

`DatePickerRef.aeval` ships a `read` via `session.aread` and returns the ISO string (`""` if no date is selected). `DatePickerRef.store(value)` compiles to `write`. `DatePickerRef.changed()` is the standard `Changed` subscription.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.birthday", "type": "DatePickerRef",
 "props": {"label": "birthday", "placeholder": "",
           "min": "1900-01-01", "max": "2099-12-31", "default": ""}}

// server pushes a value
{"op": "write",  "ref": "HomePage.birthday", "payload": "2026-05-23"}

// server resets
{"op": "write",  "ref": "HomePage.birthday", "payload": ""}

// server fetches
{"op": "read",   "ref": "HomePage.birthday", "payload": null,         "id": "ab12"}
{"op": "read",   "ref": "HomePage.birthday", "payload": "2026-05-23", "id": "ab12"}

// browser tells server the user picked a date
{"op": "notify", "ref": "HomePage.birthday", "payload": null}
```

`write` and `read`-response payloads are msgpack strings (always ISO `yyyy-mm-dd` or empty `""`). `notify` and `read`-request payloads are msgpack nil.

## renderer

`web/src/refs/date-picker.tsx`. A `<label>` block wrapping a label span above a native `<input type="date">`. Tailwind utility classes; no shadcn dep for v1. The native picker honors `min` / `max` for keyboard navigation and disables out-of-range cells in the popup. Commit emits one `notify` on the native `change` event (fires when the user picks a date or clears the field).

## slice shape

```
{
  type: "DatePickerRef",
  value: string,        // ISO yyyy-mm-dd or ""
  label: string,
  placeholder: string,
  min: string,          // ISO yyyy-mm-dd or ""
  max: string,          // ISO yyyy-mm-dd or ""
  write: (v: unknown) => void,
  get: () => string,
}
```

Seeded from `field.props` on mount; `value` seeds from `props.default`. `write` coerces nil to `""` and non-string payloads via `String(v)`. `get` reads the live slice to avoid stale closures.

## edge cases

- `write` payload is msgpack nil (Nu sentinel): coerced to `""` (no date selected).
- `write` payload is non-string: stored as `String(v)`. No format validation on the wire; bad strings render as empty in the native picker.
- slot never written and no `props` on mount: slice defaults to `value=""`, `label=""`, `placeholder=""`, `min=""`, `max=""`.
- empty `label`: the label span is omitted; only the input renders.
- empty `min` / `max`: corresponding attribute omitted from the `<input>`.
- user clears the field: native `change` fires with `""`; `notify` sent and slice updates to `""`.
- value outside `[min, max]`: stored as sent. Browser-side native validation marks the input invalid (`:invalid` pseudo-class) but does not block the write. `notify` still reports the user-committed value.
- no per-keystroke notify (native `<input type="date">` only fires `change` on commit).

## non-goals

- no date range picker (two dates). That belongs to a separate `DateRangePickerRef`.
- no time-of-day component. Use a separate `DateTimePickerRef` or `TimePickerRef` later.
- no timezone awareness. The value is a calendar date, not an instant.
- no localization of the input format on the wire. Wire is always ISO `yyyy-mm-dd`; the browser may render it in the user's locale via the native picker.
- no shadcn calendar popover in v1. A v2 may swap to shadcn `Calendar` + `Popover` while keeping the wire shape.
- no custom validation rules beyond `min` / `max`.
- no readonly / disabled flags.
