"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

from pathlib import Path

import nu
import nustd


_DB = Path.home() / ".nu" / "demos" / "counter"
_DB.parent.mkdir(parents=True, exist_ok=True)


class Counter(nu.Shape):
    """Persistent counter state."""

    value: nustd.kv.IntRef


class Links(nustd.ui.Row):
    docs = nustd.ui.LinkRef.slot(
        label="Read the docs", href="https://nustack.dev/docs", target="_blank"
    )
    github = nustd.ui.LinkRef.slot(
        label="Star on GitHub", href="https://github.com/nustackdev/nu", target="_blank"
    )
    examples = nustd.ui.LinkRef.slot(
        label="Browse more demos",
        href="https://github.com/nustackdev/nu/tree/main/examples",
        target="_blank",
    )


class Dashboard(nustd.ui.Page):
    """Live counter page with description and source."""

    heading = nustd.ui.HeadingRef.slot(label="Persistent counter, live")
    count = nustd.ui.StatRef.slot(label="Count")
    about_heading = nustd.ui.HeadingRef.slot(label="How it works")
    about = nustd.ui.MarkdownRef.slot(
        value=(
            "- Stores counter value in rocksdb.\n"
            "- App increments the counter once a second.\n"
            "- `ReactForever` pushes every change to the browser.\n"
            "- Same Ref system used for rocksdb and UI.\n"
            "- Same Interactions used to orchestrate storage and UI update.\n"
        ),
    )
    links_heading = nustd.ui.HeadingRef.slot(label="Try Nu yourself")
    links_intro = nustd.ui.TextRef.slot(
        value="Persistent state, live browser, no glue. See how far the primitive goes.",
    )
    links = Links.slot(gap=4, align="center", wrap=True)
    source_heading = nustd.ui.HeadingRef.slot(label="Source")
    source_intro = nustd.ui.TextRef.slot(
        value="The whole app, one file. Storage, UI, and the wires between them.",
    )
    source = nustd.ui.CodeBlockRef.slot(
        code=Path(__file__).read_text(),
        language="python",
    )


class App(nustd.ui.Index):
    """UI index with one page."""

    home = Dashboard.slot("/")


app = nu.With(
    nustd.kv.rocksdb_navigator(str(_DB)),
    nustd.ui.server(
        nustd.kv.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                App.home.count.set_value(nu.str(Counter.value)),
            ),
        ),
    ),
    body=nustd.kv.auto_flow_atomic(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)

if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
