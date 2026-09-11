"""Prose: type rich text in the browser, read the markdown back in the program.

The demo is the round trip, nothing else. `Editor.body` is a ProseRef: the
server seeds it with markdown, the browser renders that as a live document
(headings, lists, bold, links, undo), and every commit ships the edited
markdown back. The right pane is the proof -- it is drawn from what the
program read, not from what the browser is holding.

Run: uv run python examples/prose.py   ->   http://localhost:8080
"""

import nu


SEED = """# Prose ref

Type in here. It is a real document, not a textarea: `# ` makes a heading,
`- ` starts a list, cmd+b bolds the selection.

- markdown in, markdown out
- last actor wins, no merge
- the source is what the program sees
"""


class Editor(nu.ui.Card):
    body = nu.ui.ProseRef.slot(value=SEED, placeholder="Write, or type # for a heading")


class Mirror(nu.ui.Card):
    chars = nu.ui.StatRef.slot(label="characters")
    source = nu.ui.CodeBlockRef.slot(code=SEED, language="markdown")


class Split(nu.ui.Row):
    editor = Editor.slot()
    mirror = Mirror.slot()


class Home(nu.ui.Page):
    split = Split.slot()


class App(nu.ui.Index):
    title = nu.ui.TitleRef.slot(default="Prose")
    pages = nu.ui.Pages({"/": Home})


# Every commit from the browser lands here. `nu.Str(Home.split.editor.body)` is the read
# back through the session: same Ref, other direction.
on_edit = nu.ReactForever(
    Home.split.editor.body.changed(),
    Home.split.mirror.source.set(code=nu.Str(Home.split.editor.body))
    | Home.split.mirror.chars.set_value(nu.str(nu.Len(nu.Str(Home.split.editor.body)))),
)

ui = Home.split.mirror.chars.set_value(str(len(SEED))) >> on_edit

app = nu.With(
    nu.ui.server(ui),
    body=nu.ForeverDo(nu.Delay(3600)),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
