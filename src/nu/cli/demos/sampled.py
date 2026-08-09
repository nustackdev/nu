"""Sampled: kh57-backed series grows forever; the chart repaints a live reservoir sample."""

from pathlib import Path

import nu


_DB = Path.home() / ".nu" / "demos" / "sampled"
_DB.parent.mkdir(parents=True, exist_ok=True)


_ABOUT = """\
- `nums` is a **kh57-backed** series growing at 50 Hz — a new integer every 20 ms.
- `cursor` tracks the write position; each tick writes `nums[cursor] = cursor` and increments it.
- The chart repaints from a **200-point reservoir sample** of `nums` — the cost is the same
  whether the series holds 1k or 1B rows.
- `ReactForever` fires the resample on every change.
- Persistent: stop and restart, `cursor` and `nums` carry over from `~/.nu/demos/sampled`.
"""


class State(nu.Shape):
    """Persistent series and write cursor."""

    nums = nu.kv.Kh57Ref.slot(int)
    cursor = nu.kv.IntRef.slot()


class Dashboard(nu.ui.Page):
    """Live chart page with description and source."""

    heading = nu.ui.HeadingRef.slot(label="Infinite series, live-sampled")
    chart = nu.ui.LineChart.slot()
    about_heading = nu.ui.HeadingRef.slot(label="What's happening")
    about = nu.ui.MarkdownRef.slot(value=_ABOUT)
    source_heading = nu.ui.HeadingRef.slot(label="Source")
    source = nu.ui.CodeBlockRef.slot(
        code=Path(__file__).read_text(),
        language="python",
    )


class App(nu.ui.Index):
    """UI index with one page."""

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
    nu.kv.rocksdb_navigator(str(_DB)),
    nu.ui.server(nu.kv.auto_flow_atomic(ui)),
    body=nu.kv.auto_flow_atomic(feed),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
