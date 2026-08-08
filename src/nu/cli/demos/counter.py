"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

from pathlib import Path

import nu


_DB = Path.home() / ".cache" / "nu" / "demos" / "counter"
_DB.parent.mkdir(parents=True, exist_ok=True)


_ABOUT = """\
- A single `IntRef` (`Counter.value`) lives in **rocksdb** at `~/.cache/nu/demos/counter`.
- The body loop increments it every second (`Counter.value.inc() >> Delay(1.0)`).
- A `ReactForever` subscribes to changes on that value and pushes them into
  the dashboard's text ref — the browser updates without polling.
- State is persistent: stop and restart the demo, the counter picks up where it left off.
"""


class Counter(nu.Shape):
    """Persistent counter state."""

    value: nu.kv.IntRef


class Dashboard(nu.ui.Page):
    """Live counter page with description and source."""

    heading = nu.ui.HeadingRef.slot(label="Rocksdb-backed counter, ticking live")
    count = nu.ui.TextRef.slot()
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


app = nu.With(
    nu.kv.rocksdb_navigator(str(_DB)),
    nu.ui.server(
        nu.kv.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                Dashboard.count.set(Counter.value),
            ),
        ),
    ),
    body=nu.kv.auto_flow_atomic(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)

if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
