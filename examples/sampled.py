"""Sampled: kh57-backed series grows forever; the chart repaints a live reservoir sample."""

import nu


class State(nu.Shape):
    nums = nu.kv.Kh57Ref.slot(int)
    cursor = nu.kv.IntRef.slot()


class Dashboard(nu.ui.Page):
    chart = nu.ui.LineChart.slot()


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


# reactive wire: repaint the chart on every write to `nums`
ui = nu.ReactForever(
    State.nums.on_change(),
    Dashboard.chart.set_points(
        nu.Collect(nu.Sorted(nu.Iter(State.nums.sample(200, 0, State.cursor)))),
    ),
)

# feed: append one number to `nums` at 50 Hz, forever
feed = State.cursor.init(0) >> nu.ForeverDo(
    State.nums.set_item(State.cursor, State.cursor) >> State.cursor.inc() >> nu.Delay(0.02),
)

# assemble: rocksdb-backed, served over the browser
app = nu.With(
    nu.kv.rocksdb_navigator(".dbsampled"),
    nu.ui.server(nu.kv.auto_flow_atomic(ui)),
    body=nu.kv.auto_flow_atomic(feed),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
