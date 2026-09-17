"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

import nu
import nustd


class Counter(nu.Shape):
    value = nustd.kv.IntRef.slot()


class Dashboard(nustd.ui.Page):
    count = nustd.ui.StatRef.slot(label="Count")


class App(nustd.ui.Index):
    home = Dashboard.slot("/")


# reactive wire: whenever `value` changes, mirror it into `count`
ui = nu.ReactForever(
    Counter.value.on_change(),
    App.home.count.set_value(nu.str(Counter.value)),
)

# updater: tick `value` up once a second, forever
tick = Counter.value.init(0) >> nu.ForeverDo(Counter.value.inc() >> nu.Delay(1.0))

# assemble: rocksdb-backed, served over the browser
app = nu.With(
    nustd.kv.rocksdb_navigator(".dbcounter"),
    body=nu.ParallelAsync(
        nustd.ui.serve(App, nustd.kv.auto_flow_atomic(ui)),
        nustd.kv.auto_flow_atomic(tick),
    ),
)

print(app)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
