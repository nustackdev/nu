"""Sampled: kh57-backed series grows forever; the chart repaints a live reservoir sample."""

from pathlib import Path

import nu


_DB = Path.home() / ".nu" / "demos" / "sampled"
_DB.parent.mkdir(parents=True, exist_ok=True)


class State(nu.Shape):
    """Persistent series and write cursor."""

    nums = nu.kv.Kh57Ref.slot(int)
    cursor = nu.kv.IntRef.slot()


class Links(nu.ui.Row):
    docs = nu.ui.LinkRef.slot(
        label="Read the docs", href="https://nustack.dev/docs", target="_blank"
    )
    github = nu.ui.LinkRef.slot(
        label="Star on GitHub", href="https://github.com/nustackdev/nu", target="_blank"
    )
    examples = nu.ui.LinkRef.slot(
        label="Browse more demos",
        href="https://github.com/nustackdev/nu/tree/main/examples",
        target="_blank",
    )


class Dashboard(nu.ui.Page):
    """Live chart page with description and source."""

    heading = nu.ui.HeadingRef.slot(label="Unbounded series, instant chart")
    chart = nu.ui.LineChart.slot()
    about_heading = nu.ui.HeadingRef.slot(label="How it works")
    about = nu.ui.MarkdownRef.slot(
        value=(
            "- Writes 50 numbers a second into a **kh57-backed** series. Grows without limit.\n"
            "- Chart repaints from a 200-point reservoir sample. Same cost at 1k rows or 1B.\n"
            "- `ReactForever` triggers the resample on every write.\n"
            "- Same Ref system used for storage, sampling, and chart.\n"
            "- Same Interactions used to orchestrate the feed and the redraw.\n"
        ),
    )
    links_heading = nu.ui.HeadingRef.slot(label="Try Nu yourself")
    links_intro = nu.ui.TextRef.slot(
        value="Billion-row backends, live UIs, no glue. See how far the primitive goes.",
    )
    links = Links.slot(gap=4, align="center", wrap=True)
    source_heading = nu.ui.HeadingRef.slot(label="Source")
    source_intro = nu.ui.TextRef.slot(
        value="The whole app, one file. Storage, UI, and the wires between them.",
    )
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
