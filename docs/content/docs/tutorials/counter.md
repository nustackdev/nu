---
title: Counter
---

Build a counter that ticks forever, survives restarts, mirrors to a browser, and reacts to clicks. Three stages, one new concept per stage.

Before you start: finish the [hello tutorial](/docs/tutorials/hello) and set up the `nu.ui` Fabric per [Install](/docs/how-to/install).

## Stage 1: Remember a number across restarts

The hello loop prints forever. You want it to tick a number, and to pick that number back up after you kill the process.

Save this as `counter.py`:

```python
import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    body=(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.print(Counter.value) >> nu.Delay(1.0),
        )
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
```

Run it:

```bash
python counter.py
```

You see `1`, `2`, `3`, ... one per second. Stop it with Ctrl-C. Run again. It resumes: `12`, `13`, `14`. The number lived through the restart, in a RocksDB directory called `.dbtest` next to your script.

### The new concepts

A **Shape** is a class that declares the data your program has. `Counter` has one **Slot** named `value`, and that slot holds a `nu.v.IntRef`.

A **Ref** is a typed address for a piece of data. `Counter.value` is not an integer; it is a handle that points at where the integer lives. To read it, some atom in the tree reads through it. To write it, some atom writes through it. `Counter.value.inc()` is a Command that reads-and-writes through the Ref.

`nu.With` binds Fabrics for the tree it wraps. Here it binds the RocksDB Navigator to the path `.dbtest`, and the tree in `body=` runs against it. `nu.IfDo(Counter.value.missing(), Counter.value.set(0))` seeds the counter to 0 the first time it runs, and does nothing on later runs.

Ignore `nu.v.auto_flow_atomic` for now. It wraps writes in the transactions the storage Fabric needs. You will meet it properly later.

## Stage 2: Mirror the counter in a browser, live

Now show the number in a browser tab, updating as it ticks. When you kill the process and restart, the tab reconnects and picks up from the current count.

Replace `counter.py` with:

```python
import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    count: nu.ui.TextRef


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


ui = nu.ReactForever(
    Counter.value.on_change(),
    Dashboard.count.set(Counter.value),
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
```

Run it. A browser tab opens on `http://localhost:8080`. The page shows the counter, ticking once a second. Kill the process, restart it, refresh the tab: same live mirror.

### The new concepts

A **Fabric** is a backend Nu talks to. Storage is one Fabric (RocksDB, in-memory). The browser UI is another. Each has its own Shapes: `nu.Shape` and `nu.v.IntRef` live on the storage Fabric; `nu.ui.Page` and `nu.ui.TextRef` live on the UI Fabric. Same declaration style, different Fabric. `App` is the site index, and `nu.ui.Pages({"/": Dashboard})` mounts `Dashboard` at `/`.

`nu.With` now binds two Fabrics: the RocksDB Navigator and the `nudle` UI server. The server takes a tree to run whenever it needs to update the UI.

That tree uses **reactivity**. `nu.ReactForever(source, body)` subscribes to a change source and re-runs the body every time it fires. `Counter.value.on_change()` is a change source that fires every time the int at `Counter.value` is written. The body copies the current value into the UI Ref: `Dashboard.count.set(Counter.value)`. That is what makes the browser mirror the tick.

## Stage 3: A click that changes the label

Add a heading, an input, and a button. Type a name, click the button, watch the heading change.

Replace `counter.py` with:

```python
import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    heading: nu.ui.HeadingRef
    count: nu.ui.TextRef
    name: nu.ui.InputRef
    greet: nu.ui.ButtonRef


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    pages = nu.ui.Pages({"/": Dashboard})


ui = (
    App.title.set("counter")
    >> Dashboard.heading.set("counter live")
    >> (
        nu.ReactForever(
            Counter.value.on_change(),
            Dashboard.count.set(Counter.value),
        )
        | nu.ReactForever(
            Dashboard.greet.clicked(),
            Dashboard.heading.set(Dashboard.name),
        )
    )
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
```

Run it. Type your name in the input, click the button, the heading swaps to what you typed. The counter keeps ticking.

### The new concept

Every read you have done so far, like `Counter.value` inside `Dashboard.count.set(...)`, is a **Query**: it materializes a value. Every write, like `.set(...)` or `.inc()`, is a **Command**: it changes state. The click reactor is two Commands, driven by a change source: on click, read `Dashboard.name` (Query), write it into `Dashboard.heading` (Command). `|` runs the two `ReactForever` branches in parallel, so ticks and clicks do not block each other.

## What you built

- A persistent int on a RocksDB Fabric.
- A browser dashboard that mirrors it live through a `ReactForever`.
- A click handler that rewrites a heading from an input.

## Next

Build a real app with lists, forms, and multiple pages: [Movies](/docs/tutorials/movies).
