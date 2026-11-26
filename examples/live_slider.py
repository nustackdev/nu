"""Live slider: hear a drag as it moves, read tabs and a modal from the program.

- **Moving and settled are two events.** Every drag tick is an `input`, heard
  by `on_input()`; the release is a `change`, heard by `on_change()`. Both
  carry the value, so neither handler reads back.
- **Slowing it down is the server's call.** The browser sends every tick (in
  100 ms batches); `nu.Throttle` keeps the live line to five repaints a
  second. Take the throttle out and it follows every tick.
- **Chrome state is readable.** "Where am I" reads the Tabs (the active tab's
  id) and the Modal (open or not) on the spot. Press it on the page, then
  again inside the modal: same code, the modal answers differently.
- **Nobody listens, nothing is sent.** The "About" tab has a slider nobody
  subscribed to: drag it and no frame leaves the browser.

Run: uv run python examples/live_slider.py   ->   http://localhost:8099
"""

import nu
from nustd import ui


class Live(ui.Column):
    level = ui.SliderRef.slot(label="Level", max=100.0)
    moving = ui.TextRef.slot(value="Drag the slider", tone="muted")
    settled = ui.TextRef.slot(value="Nothing settled yet")


class About(ui.Column):
    note = ui.TextRef.slot(value="A slider nobody listens to: dragging it sends nothing.")
    quiet = ui.SliderRef.slot(label="Quiet", max=100.0)


class Views(ui.Tabs):
    live = Live.slot(gap=3)
    about = About.slot(gap=3)


class Peek(ui.Modal):
    body = ui.TextRef.slot(value="The modal is open. Ask again from here.")
    ask = ui.ButtonRef.slot(label="Where am I", variant="secondary")
    done = ui.ButtonRef.slot(label="Close")


class Actions(ui.Row):
    ask = ui.ButtonRef.slot(label="Where am I", variant="secondary")
    show = ui.ButtonRef.slot(label="Open modal")


class Page(ui.Column):
    views = Views.slot()
    actions = Actions.slot(gap=2)
    seen = ui.TextRef.slot(value="")
    peek = Peek.slot(title="A modal")


class App(nu.Shape):
    title = ui.TitleRef.slot(default="Live slider")
    home = Page.slot(padding=6, gap=4, max_width="prose")


home = App.home
live = home.views.live


def heard(last: nu.Nu) -> nu.Nu:
    """Each tick, at most every 200 ms. `last` is the throttle's clock."""
    return nu.ReactEvery(
        live.level.on_input(),
        lambda ev: nu.Throttle(0.2, live.moving.set("Moving: " + nu.str(ev["value"])), last=last),
    )


settled = nu.ReactEvery(
    live.level.on_change(),
    lambda ev: live.settled.set("Settled at " + nu.str(ev["value"])),
)

# Two reads through the session: the browser answers with what it shows now.
where = home.seen.set(
    "Tab "
    + nu.Str(home.views)
    + ", modal "
    + nu.If(nu.Bool(home.peek), nu.Str("open"), nu.Str("closed"))
)

program = nu.ParallelAsync(
    nu.let(heard, last=None),
    settled,
    nu.ReactEvery(home.actions.ask.on_click(), where),
    nu.ReactEvery(home.peek.ask.on_click(), where),
    nu.ReactEvery(home.actions.show.on_click(), home.peek.set_open(True)),
    nu.ReactEvery(home.peek.done.on_click(), home.peek.set_open(False)),
)

app = ui.serve(ui.boot(App.title, App.home) >> program, port=8099)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
