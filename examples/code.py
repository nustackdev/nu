"""Code: edit source in the browser, read the text back in the program.

Three things worth watching, and the right pane is the proof for all of them
because it is drawn from what the program read, not from what the browser is
holding.

- **The round trip.** Type, then cmd+enter or click away. Commits land on
  blur and on cmd+enter, not on every keystroke, so a read between commits
  sees the last committed text.
- **Language is a prop.** Pick another from the dropdown and the highlighting
  changes under the same text. Each grammar is its own lazy chunk, so the
  first pick of a language fetches it and later ones are instant.
- **Editable is a prop too.** Flip the switch and the editor turns into the
  read-only block the right pane is, same view, nothing rebuilt. Both panes
  are one CodeRef type; only the flag differs.

Also worth a look: flip the page theme and both panes restain with it.

Run: uv run python examples/code.py   ->   http://localhost:8090
"""

import nu
import nustd


SEED = '''def fib(n):
    """The nth Fibonacci number, iteratively."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


print([fib(i) for i in range(10)])
'''

LANGUAGES = ["python", "javascript", "typescript", "sql", "yaml", "shell", "markdown"]


class Controls(nustd.ui.Row):
    language = nustd.ui.SelectRef.slot(options=LANGUAGES, selected="python")
    editable = nustd.ui.SwitchRef.slot(label="editable", default=True)


class Editor(nustd.ui.Card):
    controls = Controls.slot()
    source = nustd.ui.CodeRef.slot(value=SEED, language="python", editable=True, min_height=260)


class Mirror(nustd.ui.Card):
    chars = nustd.ui.StatRef.slot(label="characters")
    text = nustd.ui.CodeRef.slot(value=SEED, language="python")


class Split(nustd.ui.Column):
    editor = Editor.slot()
    mirror = Mirror.slot()


class Home(nustd.ui.Page):
    split = Split.slot()


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Code")
    home = Home.slot("/")


source = App.home.split.editor.source
language = App.home.split.editor.controls.language
editable = App.home.split.editor.controls.editable
mirror = App.home.split.mirror

# `nu.Str(source)` is the read back through the session: same Ref, other
# direction. The count comes off that read rather than off anything the
# browser sent alongside it.
on_edit = nu.ReactForever(
    source.on_change(),
    mirror.text.set(nu.Str(source)) | mirror.chars.set_value(nu.str(nu.Len(nu.Str(source)))),
)

# One pick restains both panes, so the display block is always reading the
# same grammar the editor is.
on_language = nu.ReactForever(
    language.on_change(),
    source.set_language(nu.Str(language)) | mirror.text.set_language(nu.Str(language)),
)

on_mode = nu.ReactForever(editable.on_change(), source.set_editable(nu.Bool(editable)))

ui = mirror.chars.set_value(str(len(SEED))) >> (on_edit | on_language | on_mode)

# No navigator anywhere in this tree: the round trip is browser-only, and the
# sessions registry stands up its own in-memory store when it finds no kv stack.
app = nustd.ui.serve(App, ui, port=8090)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
