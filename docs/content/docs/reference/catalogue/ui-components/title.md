---
title: TitleRef
---

Structural Ref bound to `document.title`. Lives on an Index, not a Page. Host-owned, write-only.

## kind

structural

## substrate

`document.title`. The slice mirrors the last written base string into the store under `value` (without the suffix) so devtools and future subscribers can observe it. No DOM observers are installed in this revision.

## defaults (class-level)

| field     | type  | default | notes                                                                  |
| --------- | ----- | ------- | ---------------------------------------------------------------------- |
| `default` | `str` | `""`    | initial title applied on mount before any host `write`.                |
| `suffix`  | `str` | `""`    | appended to every write (and to the default seed). Empty is a no-op.   |

Declared as `ClassVar[str]` on the python `TitleRef`. Shipped under the mount field entry's `props` only when at least one is non-empty; the empty-empty case omits `props` to keep mount frames lean.

```python
class App(nudle.Index):
    class title(nudle.TitleRef):
        default = "home"
        suffix = " | nudle"
```

On mount the browser sets `document.title = "home | nudle"`. A later `App.title.set("feed")` sets `document.title = "feed | nudle"`.

## interactions

| op      | dir           | payload      | nu method | notes                                                                  |
| ------- | ------------- | ------------ | --------- | ---------------------------------------------------------------------- |
| `write` | server -> tab | `str` or nil | `store`   | full replace of the base title. Suffix is appended on the browser side. |

Single op. The suffix lives only on the browser slice so host code never has to track whether the suffix is already present.

## wire payloads

```
// mount field entry (only when default or suffix is non-empty)
{"path": "title", "type": "TitleRef", "props": {"default": "home", "suffix": " | nudle"}}

// host pushes a new base title
{"op": "write", "ref": "title", "payload": "feed"}

// clear via Nu sentinel
{"op": "write", "ref": "title", "payload": null}
```

Path is `title`, not `App.title`. Structural Refs are Index-rooted; only Page-rooted Refs carry the page class prefix.

## renderer

`web/src/refs/title.tsx`. The view component returns `null`; TitleRef has no body output. The factory does the work: it seeds `document.title` from `props.default` on mount and updates it on each `write`.

## slice shape

```
{
  type: "TitleRef",
  value: string,           // current base (without suffix)
  suffix: string,
  write: (v: string | null) => void,
  dispose: () => void,
}
```

Seeded from `props.default` (or `""`) and `props.suffix` (or `""`). `write` coerces nil to `""`, stores the base on the slice, and sets `document.title = base + suffix`.

`dispose` is a no-op today. It exists so a future mutation observer (mirroring third-party title writes back into the slice) has a documented detach point. The store calls `dispose` on unmount and re-mount.

## edge cases

- `default` and `suffix` both empty: `mount_props` returns `{}`; no `props` ship; slice seeds as `("", "")`; `document.title` is not touched until a host `write`.
- `default` non-empty, `suffix` empty: on mount, `document.title = default`.
- `default` empty, `suffix` non-empty: the auto-seed is skipped, so the title bar does not read like `" | nudle"`. A later `set("home")` produces `"home | nudle"`.
- payload nil on `write`: base becomes `""`. Result: `document.title = suffix` (or `""` when suffix is empty).
- multi-tab: each tab owns its own slice and its own `document.title`. No cross-tab coordination.
- re-mount: `dispose` runs; the next mount re-seeds from the new `props`. If the new `default` is empty, the previous `document.title` is left in place.

## non-goals

- no `append`, no `read`, no `notify`. Title is host-owned.
- no per-page titles via TitleRef itself. TitleRef is structural and lives on Index. A host pattern is to call `App.title.set(...)` on nav changes.
- no favicon, no head meta. Future structural Refs.
- no html escaping. `document.title` is text already.
- no mutation observer on `document.title` in this revision. The `dispose` slot is reserved.
