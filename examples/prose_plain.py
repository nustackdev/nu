"""Prose, plain: one ProseRef on a page, nothing around it.

No card, no row, no mirror. What you see is the kit's Prose exactly as it
renders on its own: its type scale, its block margins, its first and last
edges.

Run: uv run python examples/prose_plain.py   ->   http://localhost:8080
"""

import nu
import nustd


SEED = """# Heading one

A paragraph of body text. It wraps like a paragraph does, so the line height
and the measure are both on show. **Bold**, *italic*, `inline code` and a
[link](https://nustack.dev).

## Heading two

- a list item
- another one

- [ ] a checklist item
- [x] a done one

A last paragraph, so the bottom edge has something to sit on.
"""


class Home(nustd.ui.Page):
    body = nustd.ui.ProseRef.slot(value=SEED)


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Prose, plain")
    home = Home.slot("/")


app = nustd.ui.serve(App, nu.Noop())


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
