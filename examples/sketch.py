"""Sketch: draw on a board in the browser, read the elements back in the program.

- **One send per element.** The board draws locally while the pointer moves
  and sends when it lifts, so the count only moves on pointer up, never
  mid-line. Undo, redo and clear send once each. The count is drawn from what
  the program read, not from the browser.
- **The program can draw too.** "Draw a diagram" writes elements from the
  server: plain JSON, the same `set` an agent or a replay would use.
- **Config is the board's shape.** The full toolbar here; a digit reader
  would take `tools=["pen"], controls=["clear"], defaults={"size": 0.07}`.

Run: uv run python examples/sketch.py   ->   http://localhost:8093
"""

import nu
import nustd


# A small flow, left to right. Coordinates are 0..1 of the board.
DIAGRAM = [
    {
        "type": "rect",
        "x": 0.06,
        "y": 0.3,
        "w": 0.24,
        "h": 0.26,
        "stroke": "blue",
        "fill": "blue-soft",
    },
    {"type": "arrow", "points": [[0.32, 0.43], [0.46, 0.43]]},
    {
        "type": "ellipse",
        "x": 0.48,
        "y": 0.28,
        "w": 0.2,
        "h": 0.3,
        "stroke": "violet",
        "fill": "violet-soft",
    },
    {"type": "arrow", "points": [[0.7, 0.43], [0.84, 0.43]]},
    {
        "type": "rect",
        "x": 0.86,
        "y": 0.33,
        "w": 0.1,
        "h": 0.2,
        "stroke": "green",
        "fill": "green-soft",
    },
    {
        "type": "path",
        "points": [[0.5, 0.68], [0.54, 0.7], [0.58, 0.67], [0.62, 0.71], [0.66, 0.68]],
        "stroke": "red",
    },
]


class Side(nustd.ui.Column):
    elements = nustd.ui.StatRef.slot(label="elements", value="0")
    diagram = nustd.ui.ButtonRef.slot(label="Draw a diagram", icon="pencil", variant="secondary")


class Board(nustd.ui.Row):
    board = nustd.ui.SketchRef.slot(label="Draw anything", width=560, height=380)
    side = Side.slot(align="start")


class Home(nustd.ui.Page):
    main = Board.slot(gap=6, align="start", wrap=True, min_width=200)


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Sketch")
    home = Home.slot("/")


board = App.home.main.board
side = App.home.main.side

# `nu.Len(board)` is a read back through the session: the elements as the
# browser holds them now.
count = side.elements.set_value(nu.str(nu.Len(board)))

on_draw = nu.ReactForever(board.on_change(), count)
on_diagram = nu.ReactForever(side.diagram.on_click(), board.set(DIAGRAM) >> count)

app = nustd.ui.serve(App, on_draw | on_diagram, port=8093)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
