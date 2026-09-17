"""Prose: type rich text in the browser, read the markdown back in the program.

The demo is the round trip, nothing else. `Editor.body` is a ProseRef: the
server seeds it with markdown, the browser renders that as a live document
(headings, lists, bold, links, undo), and every commit ships the edited
markdown back. The right pane is the proof -- it is drawn from what the
program read, not from what the browser is holding.

Run: uv run python examples/prose.py   ->   http://localhost:8080
"""

import nu
import nustd


SEED = """# Prose ref

Type in here. It is a real document, not a textarea: `# ` makes a heading,
`- ` starts a list, cmd+b bolds the selection.

- markdown in, markdown out
- last actor wins, no merge
- the source is what the program sees
"""


class Editor(nustd.ui.Card):
    body = nustd.ui.ProseRef.slot(value=SEED, placeholder="Write, or type # for a heading")


class Mirror(nustd.ui.Card):
    chars = nustd.ui.StatRef.slot(label="characters")
    source = nustd.ui.CodeBlockRef.slot(code=SEED, language="markdown")


class Split(nustd.ui.Row):
    editor = Editor.slot()
    mirror = Mirror.slot()


class Home(nustd.ui.Page):
    split = Split.slot()


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Prose")
    home = Home.slot("/")


# Every commit from the browser lands here. `nu.Str(App.home.split.editor.body)` is the read
# back through the session: same Ref, other direction.
on_edit = nu.ReactForever(
    App.home.split.editor.body.on_change(),
    App.home.split.mirror.source.set(code=nu.Str(App.home.split.editor.body))
    | App.home.split.mirror.chars.set_value(nu.str(nu.Len(nu.Str(App.home.split.editor.body)))),
)

ui = App.home.split.mirror.chars.set_value(str(len(SEED))) >> on_edit

# No navigator anywhere in this tree: the round trip is browser-only, and the
# sessions registry stands up its own in-memory store when it finds no kv stack.
app = nustd.ui.serve(App, ui)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
