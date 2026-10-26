"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

import nu
import nustd


class Counter(nu.Shape):
    value = nustd.kv.IntRef.slot()


class Dashboard(nustd.ui.Container):
    count = nustd.ui.StatRef.slot(label="Count")


class App(nu.Shape):
    home = Dashboard.slot(size="panel")


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
        nustd.ui.serve(nustd.ui.boot(App.home) >> nustd.kv.auto_flow_atomic(ui)),
        nustd.kv.auto_flow_atomic(tick),
    ),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
