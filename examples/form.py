"""Form: one submit with every value in it, checks, errors, a disabled fieldset.

Enter in Title or Year, cmd/ctrl+Enter in Notes, or a click on Save submits
the form once, and the reaction reads the values from the payload: no read
per field. Cancel is a plain button and never submits. Title is required, so
an empty one stops the submit in the browser and the Field says why. A title
of "bad" comes back with an error from the program (`set_errors`). Lock
disables the Extras fieldset, every control in it. After a submit the form
puts its declared values back (`clear_on_submit`).
"""

import asyncio

import nu
from nustd import ui


class TitleField(ui.Field):
    input = ui.InputRef.slot(placeholder="e.g. Arrival")


class YearField(ui.Field):
    input = ui.NumberInputRef.slot(min=1900.0, max=2100.0)


class NotesField(ui.Field):
    input = ui.TextAreaRef.slot(rows=2, placeholder="cmd+Enter sends")


class Details(ui.Fieldset):
    title = TitleField.slot(label="Title", help="As released", required=True)
    year = YearField.slot(label="Year")


class Extras(ui.Fieldset):
    notes = NotesField.slot(label="Notes")
    seen = ui.SwitchRef.slot(label="Seen it")


class Actions(ui.Row):
    lock = ui.ButtonRef.slot(label="Lock extras", variant="ghost")
    cancel = ui.ButtonRef.slot(label="Cancel", variant="secondary")
    save = ui.ButtonRef.slot(label="Save", submit=True)


class AddForm(ui.Form):
    details = Details.slot(legend="Movie")
    extras = Extras.slot(legend="Extras")
    actions = Actions.slot(gap=2, justify="end")


class Page(ui.Column):
    add = AddForm.slot(title="Log a movie", clear_on_submit=True)
    last = ui.TextRef.slot(value="Nothing saved yet")


class App(nu.Shape):
    home = Page.slot(padding=6, gap=4, max_width="prose")


form = App.home.add


def _saved(sub: nu.Nu) -> nu.Nu:
    title = nu.Str(sub["values"]["details"]["title"])
    bad = form.set_errors({"details": {"title": "Not that one, pick another title"}})
    good = App.home.last.set("Saved " + title + " with " + nu.str(sub["button"]))
    return nu.IfDo(nu.Eq(title, "bad"), bad, good)


program = nu.ParallelAsync(
    nu.ReactEvery(form.on_submit(), _saved),
    nu.ReactEvery(form.actions.cancel.on_click(), App.home.last.set("Cancelled")),
    nu.ReactEvery(form.actions.lock.on_click(), form.extras.set_disabled(True)),
)

app = ui.serve(ui.boot(App.home) >> program)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
