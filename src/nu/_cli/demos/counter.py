"""Counter: rocksdb-backed counter ticking every second, live in the browser."""

from pathlib import Path

import nu


_DB = Path.home() / ".nu" / "demos" / "counter"
_DB.parent.mkdir(parents=True, exist_ok=True)


class Counter(nu.Shape):
    """Persistent counter state."""

    value: nu.kv.IntRef


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
    """Live counter page with description and source."""

    heading = nu.ui.HeadingRef.slot(label="Persistent counter, live")
    count = nu.ui.StatRef.slot(label="Count")
    about_heading = nu.ui.HeadingRef.slot(label="How it works")
    about = nu.ui.MarkdownRef.slot(
        value=(
            "- Stores counter value in rocksdb.\n"
            "- App increments the counter once a second.\n"
            "- `ReactForever` pushes every change to the browser.\n"
            "- Same Ref system used for rocksdb and UI.\n"
            "- Same Interactions used to orchestrate storage and UI update.\n"
        ),
    )
    links_heading = nu.ui.HeadingRef.slot(label="Try Nu yourself")
    links_intro = nu.ui.TextRef.slot(
        value="Persistent state, live browser, no glue. See how far the primitive goes.",
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


app = nu.With(
    nu.kv.rocksdb_navigator(str(_DB)),
    nu.ui.server(
        nu.kv.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                Dashboard.count.set_value(nu.str(Counter.value)),
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
