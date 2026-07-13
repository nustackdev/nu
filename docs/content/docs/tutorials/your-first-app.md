---
title: Your first app
---

A browser dashboard on a live counter. One Nu tree, two Fabrics.

```python
"""Memory navigator + UI server: browser dashboard on a live counter."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    heading: nu.ui.HeadingRef
    count:   nu.ui.TextRef
    history: nu.ui.LineChart
    name:    nu.ui.InputRef
    greet:   nu.ui.ButtonRef


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav:   nu.ui.NavRef
    pages = nu.ui.Pages({"/": Dashboard})


ui = (
    App.title.set("nudle bracket counter")
    >> Dashboard.heading.set("counter live")
    >> (
        nu.ForeverDo(
            nu.v.Snapshot(
                Dashboard.count.set(Counter.value + 1)
                | Dashboard.history.append(Counter.value, Counter.value),
            )
            >> nu.Delay(1.0),
        )
        | nu.ReactForever(
            Dashboard.greet.clicked(),
            Dashboard.heading.set(Dashboard.name),
        )
    )
)

bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

tree = nu.With(
    nu.v.presets.memory_navigator(),
    nu.ui.presets.server(ui),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(tree))
```

Save as `counter.py`, install with `pip install nu[nudle]`, run `python counter.py`, open the browser tab that appears.

The counter ticks once a second. The dashboard shows it live. Type a name, click greet, the heading changes.

## What happened

**Two Shapes, two Fabrics.** `Counter` is a data Shape on the virtuals Fabric, holding one int. `Dashboard` is a UI Page on the UI Fabric, holding a heading, text, chart, input, and button. Same declaration style, different Fabric. `App` is the site index with one page mounted at `/`.

**Two tree slots.** `ui` describes the interactive layer: repaint every second, react on button click. `bg` describes the background work: seed the counter, tick it in a loop.

**Composition.** `>>` runs children left-to-right. `|` runs them concurrently. `ForeverDo` loops its body forever. `ReactForever` subscribes to a change source and re-runs on every fire. `Snapshot` opens one atomic read region; `Transaction` opens one atomic write region.

**Presets stack.** `nu.With(...)` binds Fabrics before the body runs. The first opens an in-memory virtuals Navigator; the second boots a UI server for the `ui` tree. Both are visible to `body=bg`.

**`nu.arun` evaluates on the loop.** UI is async, so the whole tree runs under `asyncio.run(nu.arun(tree))`.

## One tree, two Fabrics

Same operators, same brackets, same loops. The Fabric changes; the composition doesn't. Swap the memory navigator for RocksDB and the counter persists across runs. Drop the UI preset and it becomes a headless script.
