"""Monaco: edit source in the browser, read the text back in the program.

Three things worth watching, and the right pane is the proof for all of them
because it is drawn from what the program read, not from what the browser is
holding.

- **The round trip.** Type, then cmd+enter or click away. Commits land on
  blur and on cmd+enter, not on every keystroke, so a read between commits
  sees the last committed text.
- **Language is a prop.** Pick another from the dropdown and the highlighting
  changes under the same text. Each grammar is its own lazy chunk, so the
  first pick of a language fetches it and later ones are instant.
- **Read only is a prop too.** Flip the switch and the buffer stops taking
  input without being torn down and rebuilt.

Also worth a look: flip the page theme and the editor restains with it.

Run: uv run python examples/monaco.py   ->   http://localhost:8080
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
    locked = nustd.ui.SwitchRef.slot(label="read only")


class Editor(nustd.ui.Card):
    controls = Controls.slot()
    source = nustd.ui.MonacoRef.slot(value=SEED, language="python", min_height=260)


class Mirror(nustd.ui.Card):
    chars = nustd.ui.StatRef.slot(label="characters")
    text = nustd.ui.CodeBlockRef.slot(code=SEED, language="python")


class Split(nustd.ui.Column):
    editor = Editor.slot()
    mirror = Mirror.slot()


class Home(nustd.ui.Page):
    split = Split.slot()


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Monaco")
    home = Home.slot("/")


source = App.home.split.editor.source
language = App.home.split.editor.controls.language
locked = App.home.split.editor.controls.locked
mirror = App.home.split.mirror

# `nu.Str(source)` is the read back through the session: same Ref, other
# direction. The count comes off that read rather than off anything the
# browser sent alongside it.
on_edit = nu.ReactForever(
    source.on_change(),
    mirror.text.set(code=nu.Str(source)) | mirror.chars.set_value(nu.str(nu.Len(nu.Str(source)))),
)

# One pick restains both panes, so the display block is always reading the
# same grammar the editor is.
on_language = nu.ReactForever(
    language.on_change(),
    source.set_language(nu.Str(language)) | mirror.text.set(language=nu.Str(language)),
)

on_lock = nu.ReactForever(locked.on_change(), source.set_read_only(nu.Bool(locked)))

ui = mirror.chars.set_value(str(len(SEED))) >> (on_edit | on_language | on_lock)

# No navigator anywhere in this tree: the round trip is browser-only, and the
# sessions registry stands up its own in-memory store when it finds no kv stack.
app = nustd.ui.serve(App, ui, port=8090)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
