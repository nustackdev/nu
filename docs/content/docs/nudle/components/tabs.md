---
title: TabsRef
---

Tab strip plus active tab body. `TabsRef` is a Shape (Section), not a leaf
Ref. Children declared as slots on the subclass become the per-tab bodies,
paired with the `tabs` list **by index**.

## kind

section (layout-with-children)

## defaults (class-level)

| field | type | default | notes |
| --- | --- | --- | --- |
| `tabs` | `list[dict[str, str]]` | `[]` | each entry `{id: str, label: str}`. defines tab strip order. server-owned, mutated by `store_tabs`. |
| `active` | `str` | `""` | id of the currently shown tab. empty -> first entry in `tabs` (if any). server pins via `store_active`; tab updates locally on click. |

Children are declared as ordinary slots on the Section body and ship on
the mount entry as `fields` (Section pattern). `children[i]` pairs with
`tabs[i]`; matching is purely positional, slot names are not inspected.
When `tabs.length != children.length`, the renderer pairs `min(len(tabs),
len(children))` and silently drops extras.

## interactions

| op | dir | payload | nu method | notes |
| --- | --- | --- | --- | --- |
| `store_tabs` | server -> tab | `list[dict[str, str]]` | `store_tabs(list)` | replaces the `tabs` list wholesale. seeded via mount `props`. |
| `store_active` | server -> tab | `str` | `store_active(str)` | sets the active tab id. server pin / confirmation. seeded via mount `props`. |
| `notify` | tab -> server | `str` (tab id the user clicked) | `changed()` | fired on user click. tab updates local `active` first for responsiveness; server may mirror back with `store_active` to confirm. |

The tab-to-server frame uses the standard `notify` op (existing nudle
convention for tab-originated change events); `changed()` subscribes via
`session.subscribe(path)` and fires whenever a `notify` arrives with the
clicked tab id as payload.

## wire payloads

mount entry (Section-style, nested `fields`):

```
{
  "path": "HomePage.sections",
  "type": "TabsRef",
  "props": {
    "tabs":   [{"id": "overview", "label": "Overview"}, {"id": "details", "label": "Details"}],
    "active": "overview"
  },
  "fields": [
    {"path": "HomePage.sections.overview", "type": "TextRef",      "props": {...}},
    {"path": "HomePage.sections.details",  "type": "ContainerRef", "props": {...}, "fields": [...]}
  ]
}
```

```
// store_tabs([...])
{"op": "store_tabs", "ref": "HomePage.sections", "payload": [
  {"id": "overview", "label": "Overview"},
  {"id": "details",  "label": "Details"}
]}

// store_active("details")
{"op": "store_active", "ref": "HomePage.sections", "payload": "details"}

// user clicks the "details" tab (tab -> server)
{"op": "notify", "ref": "HomePage.sections", "payload": "details"}
```

Nu sentinel (`EMPTY` / `INVALID`) on either prop decodes to msgpack nil.
`tabs` nil -> `[]`. `active` nil -> `""`. Each label nil -> `""`. Each id
nil -> the entry is dropped from the strip.

Example:

```python
class HomeTabs(nudle.TabsRef):
    tabs = [{"id": "overview", "label": "Overview"},
            {"id": "details",  "label": "Details"}]
    active = "overview"

    overview = nudle.TextRef.slot()
    details  = nudle.TextRef.slot()


class HomePage(nudle.Page):
    sections = HomeTabs.slot()


# server-side handles
HomeTabs.store_tabs([{"id": "a", "label": "A"}, {"id": "b", "label": "B"}])
HomeTabs.store_active("b")
sub = HomeTabs.changed()  # Subscription, fires on each tab click
```

## renderer

`web/src/refs/tabs.tsx`. Plain styled `<button role="tab">` strip with a
bottom border on the active button; bodies are `<div>`s wrapped in
`ErrorBoundary`. **All** child bodies are mounted on first paint;
inactive ones are hidden with `display: none` so their slices keep their
local state across tab switches.

## slice shape

```
{
  type: "TabsRef",
  value: null,
  tabs: { id: string; label: string }[],
  active: string,
  children: string[],                                       // wire paths, frozen for the life of the mount
  store_tabs:   (v) => void,                                // replace tabs[]
  store_active: (v) => void,                                // set active id
  setActive:    (id: string) => void,                       // local-only setter used by the click handler before notify
}
```

`active` is tab-mirrored: the server holds the canonical value, but the
tab writes it optimistically on click and emits `notify`. There is no
`read` op; the server learns the new id solely via `notify`. To confirm a
round-trip the server can reply with `store_active`.

## edge cases

- `tabs == []`: empty strip and no body. no active id resolved.
- `active` does not match any `tabs[].id`: fall back to `tabs[0].id` for
  display only; do not mutate the stored `active`. only `store_active` or
  a local click mutates it.
- `children.length != tabs.length`: render `min(len(tabs), len(children))`
  pairs. extras are silently dropped at the renderer; no error frame.
- `store_tabs` shrinks the list and the current `active` id is no longer
  present: keep `active` as-is (server will likely follow up with
  `store_active`); the fallback rule handles display.
- Nu sentinels: `tabs` nil -> `[]`, `active` nil -> `""`, each label nil
  -> `""`, each id nil -> entry dropped from the strip.
- duplicate ids in `tabs`: first occurrence wins for the active match;
  the renderer keys bodies by child wire path, so duplicates do not break
  React keys.
- click on the already-active tab: still emits `notify` (server may want
  the event); local `active` is unchanged.

## non-goals

- no closable tabs, no add / remove via tab-side ops. mutation is
  server-driven through `store_tabs`.
- no drag-to-reorder.
- no lazy mount of inactive bodies. bodies stay mounted for state
  preservation.
- no per-tab disabled / badge / icon. labels only.
- no vertical / side-tabs variant. horizontal strip only.
- no keyboard navigation beyond native button focus; arrow-key roving
  tabindex is out of scope for v0.1.
- no `read` op. tab-side optimism plus `notify` is the only feedback
  channel.
