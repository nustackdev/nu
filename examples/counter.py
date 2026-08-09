"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

import nu


class Counter(nu.Shape):
    value = nu.kv.IntRef.slot()


class Dashboard(nu.ui.Page):
    count = nu.ui.StatRef.slot(label="Count")


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


# reactive wire: whenever `value` changes, mirror it into `count`
ui = nu.ReactForever(
    Counter.value.on_change(),
    Dashboard.count.set_value(nu.str(Counter.value)),
)

# updater: tick `value` up once a second, forever
tick = Counter.value.init(0) >> nu.ForeverDo(Counter.value.inc() >> nu.Delay(1.0))

# assemble: rocksdb-backed, served over the browser
app = nu.With(
    nu.kv.rocksdb_navigator(".dbcounter"),
    nu.ui.server(nu.kv.auto_flow_atomic(ui)),
    body=nu.kv.auto_flow_atomic(tick),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
