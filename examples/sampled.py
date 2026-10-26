"""Sampled: kh57-backed series grows forever; the chart repaints a live reservoir sample."""

import nu
import nustd


class State(nu.Shape):
    nums = nustd.kv.Kh57Ref.slot(int)
    cursor = nustd.kv.IntRef.slot()


class Dashboard(nustd.ui.Container):
    chart = nustd.ui.LineChart.slot()


class App(nu.Shape):
    home = Dashboard.slot(size="dashboard")


# reactive wire: repaint the chart on every write to `nums`
ui = nu.ReactForever(
    State.nums.on_change(),
    App.home.chart.set(
        nu.sorted(State.nums.sample(200, 0, State.cursor)),
    ),
)

# feed: append one number to `nums` at 50 Hz, forever
feed = State.cursor.init(0) >> nu.ForeverDo(
    State.nums.set_item(State.cursor, State.cursor) >> State.cursor.inc() >> nu.Delay(0.02),
)

# assemble: rocksdb-backed, served over the browser
app = nu.With(
    nustd.kv.rocksdb_navigator(".dbsampled"),
    body=nu.ParallelAsync(
        nustd.ui.serve(nustd.ui.boot(App.home) >> nustd.kv.auto_flow_atomic(ui)),
        nustd.kv.auto_flow_atomic(feed),
    ),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
