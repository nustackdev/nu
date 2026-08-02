---
title: "A real app: movies"
---

Build a personal movie tracker. Stats up top, a form to log what you watched, a table below. One Nu tree, one page, live updates.

You finished [Your first app](./your-first-app), so you know Shape, Ref, `ReactForever`, `nu.With`, and `nu.ui.Page`. Everything new gets introduced as you meet it.

The final program lives at `examples/nudle/movies.py`. You build it in four stages. Each stage runs and shows something.

## Stage 1: the shape of the data

Start headless. Declare state, seed it, print it.

A **collection Ref** holds many values under one slot. `nv.ListRef` is the list flavor. `nv.IntRef` and `nv.StrRef` are the scalar flavors you already know from the counter.

Save as `movies.py`:

```python
import nu
import nu.virtuals as nv


class State(nu.Shape):
    movies = nv.ListRef.slot(object)
    total = nv.IntRef.slot()
    watched = nv.IntRef.slot()


SEED = [
    {"title": "Arrival", "rating": 8.5, "watched": "yes"},
    {"title": "Dune: Part Two", "rating": 9.0, "watched": "yes"},
    {"title": "Perfect Days", "rating": 8.0, "watched": "no"},
]


seed = nu.v.Transaction(
    State.movies.set(SEED),
    State.total.set(len(SEED)),
    State.watched.set(sum(1 for m in SEED if m["watched"] == "yes")),
)


tree = nu.With(
    nu.v.presets.memory_navigator(),
    body=seed >> nu.v.Snapshot(nu.print(State.movies, State.total, State.watched)),
)


if __name__ == "__main__":
    nu.run(tree)
```

Run it:

```bash
python movies.py
```

You see the seed list, `3`, `2`.

Nothing in the file "does" anything at import time. `State.movies` is a tree node, not a Python list. `seed` is a tree node too. Only `nu.run(tree)` walks it.

## Stage 2: a page with stats

Now open a browser. Add a page with a stats card, hydrate the numbers from state.

**Slot composition.** A UI is a tree of slots. You declare the shape by class, then hydrate each slot with `.set(...)`. Slots hold widgets, and widgets take knobs (`variant`, `label`, `title`) via `.slot(**props)` at the declaration site.

Replace `movies.py` with:

```python
import asyncio
import nu
import nu.virtuals as nv


class State(nu.Shape):
    movies = nv.ListRef.slot(object)
    total = nv.IntRef.slot()
    watched = nv.IntRef.slot()


class StatsRow(nu.ui.Row):
    total = nu.ui.StatRef.slot()
    watched = nu.ui.StatRef.slot()
    unseen = nu.ui.StatRef.slot()


class StatsCard(nu.ui.CardRef):
    body = StatsRow.slot(gap=6, align="center", wrap=True)


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot()
    stats = StatsCard.slot(title="your shelf")


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Movies})


SEED = [
    {"title": "Arrival", "rating": 8.5, "watched": "yes"},
    {"title": "Dune: Part Two", "rating": 9.0, "watched": "yes"},
]

init = nu.v.Transaction(
    nu.IfDo(State.movies.missing(), State.movies.set(SEED)),
    nu.IfDo(State.total.missing(), State.total.set(len(SEED))),
    nu.IfDo(State.watched.missing(),
            State.watched.set(sum(1 for m in SEED if m["watched"] == "yes"))),
)


def _s(n): return nu.Str(nu.ToStr(n))


hydrate = nu.v.Snapshot(
    Movies.heading.set("your movies")
    | Movies.stats.body.total.set_label("total")
    | Movies.stats.body.total.set_value(_s(State.total))
    | Movies.stats.body.watched.set_label("watched")
    | Movies.stats.body.watched.set_value(_s(State.watched))
    | Movies.stats.body.unseen.set_label("unseen")
    | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
)

ui = init >> App.title.set("movies") >> hydrate

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbmovies"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=nu.ForeverDo(nu.Delay(3600)),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
```

Run again. A browser tab opens. Heading up top, a stats card with three numbers.

Read `Movies.stats.body.total.set_value(_s(State.total))` as: reach into `Movies`, into its `stats` slot, into that card's `body`, into the `total` stat, set its value to the Str form of `State.total`. Slot paths are attribute chains on the class.

The `body` at the bottom holds the server open. Nothing to loop yet, so it sleeps.

## Stage 3: a form that logs a movie

Add a form. Submit appends a row and updates the stats live.

**Form and Fieldset.** `nu.ui.Form` groups inputs and a submit button. `nu.ui.Fieldset` groups a subset under a legend. `nu.ui.FieldRef` wraps one input with a label and help slot. Widget knobs ride on `.slot(**props)` at the declaration site.

**Transaction and Snapshot.** A `nu.v.Transaction(...)` collects writes into one atomic commit. A `nu.v.Snapshot(...)` collects reads into one atomic view. Wire the React body as `Transaction(...) >> Snapshot(...)`: commit new state, then hydrate the UI from it.

Add three form-input wrappers, a fieldset, and the form. Widget knobs ride on `.slot(**props)`:

```python
class TitleField(nu.ui.FieldRef):
    input = nu.ui.InputRef.slot(label="title", placeholder="e.g. Arrival")

class RatingField(nu.ui.FieldRef):
    input = nu.ui.NumberInputRef.slot(label="rating", min=1.0, max=10.0, step=0.5, default=7.0)

class SwitchField(nu.ui.FieldRef):
    input = nu.ui.SwitchRef.slot(label="watched?", default=True)

class DetailsFieldset(nu.ui.Fieldset):
    title = TitleField.slot(label="title", required=True)
    rating = RatingField.slot(label="rating")
    watched = SwitchField.slot(label="watched?")

class AddMovieForm(nu.ui.Form):
    details = DetailsFieldset.slot(legend="movie", gap="md")
    submit = nu.ui.ButtonRef.slot(label="log it", variant="primary")
    feedback = nu.ui.AlertRef.slot(variant="ok", dismissible=True)
```

Mount the form on the page. Add one line to `Movies`:

```python
    form = AddMovieForm.slot(title="log a movie", gap=4, padding=4)
```

Read the live form into a Nu dict:

```python
def _row_from_form():
    d = AddMovieForm.details
    return nu.Dict.of(
        title=nu.Str(d.title.input),
        rating=nu.Float(d.rating.input),
        watched=nu.If(nu.Bool(d.watched.input), "yes", "no"),
    )
```

React on submit: commit new state in a Transaction, then rehydrate the stats and feedback in a Snapshot:

```python
on_add = nu.ReactForever(
    AddMovieForm.submit.clicked(),
    nu.v.Transaction(
        State.movies.append(_row_from_form()),
        State.total.set(State.total + 1),
        State.watched.set(State.watched
                          + nu.If(nu.Bool(AddMovieForm.details.watched.input), 1, 0)),
    )
    >> nu.v.Snapshot(
        Movies.stats.body.total.set_value(_s(State.total))
        | Movies.stats.body.watched.set_value(_s(State.watched))
        | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
        | Movies.form.feedback.set(title="logged",
                                   body="added " + nu.Str(AddMovieForm.details.title.input))
    ),
)
```

Extend the `ui`:

```python
ui = init >> App.title.set("movies") >> hydrate >> on_add
```

Run. Fill in a title, hit "log it". Stats bump. A green alert says "logged: added <title>".

`_row_from_form` returns a Nu tree, not a Python dict. `nu.Dict.of(...)` builds a dict-shaped node whose values are pulled from live form inputs at commit time. Same laziness as before, one layer up.

## Stage 4: the table

Show the shelf as a table. Each stored dict has to be reshaped into a positional row.

**Query composition on a Ref.** `nu.Iter(ref)` streams items from a collection Ref. `nu.Map(source, transform=..., key=...)` transforms each item under a bound name. `nu.Collect(stream)` gathers a stream back into a list.

**Host lift.** Some transforms are still Python. `nu.host(fn, name=...)` lifts a plain Python function into a Nu operator you can call inside a tree.

Full file for the final program:

```python
import asyncio
import nu
import nu.virtuals as nv


class State(nu.Shape):
    movies = nv.ListRef.slot(object)
    total = nv.IntRef.slot()
    watched = nv.IntRef.slot()


class TitleField(nu.ui.FieldRef):
    input = nu.ui.InputRef.slot(label="title", placeholder="e.g. Arrival")

class RatingField(nu.ui.FieldRef):
    input = nu.ui.NumberInputRef.slot(label="rating", min=1.0, max=10.0, step=0.5, default=7.0)

class SwitchField(nu.ui.FieldRef):
    input = nu.ui.SwitchRef.slot(label="watched?", default=True)

class DetailsFieldset(nu.ui.Fieldset):
    title = TitleField.slot(label="title", required=True)
    rating = RatingField.slot(label="rating")
    watched = SwitchField.slot(label="watched?")

class AddMovieForm(nu.ui.Form):
    details = DetailsFieldset.slot(legend="movie", gap="md")
    submit = nu.ui.ButtonRef.slot(label="log it", variant="primary")
    feedback = nu.ui.AlertRef.slot(variant="ok", dismissible=True)


class StatsRow(nu.ui.Row):
    total = nu.ui.StatRef.slot()
    watched = nu.ui.StatRef.slot()
    unseen = nu.ui.StatRef.slot()

class StatsCard(nu.ui.CardRef):
    body = StatsRow.slot(gap=6, align="center", wrap=True)


class TableBody(nu.ui.Column):
    table = nu.ui.TableRef.slot(columns=["title", "rating", "watched"],
                                striped=True, dense=True, max_rows=200)

class TableCard(nu.ui.CardRef):
    body = TableBody.slot(gap=3)


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot()
    stats = StatsCard.slot(title="your shelf")
    form = AddMovieForm.slot(title="log a movie", gap=4, padding=4)
    shelf = TableCard.slot(title="movies")


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Movies})


SEED = [
    {"title": "Arrival", "rating": 8.5, "watched": "yes"},
    {"title": "Dune: Part Two", "rating": 9.0, "watched": "yes"},
]

_RowAsList = nu.host(lambda *xs: list(xs), name="MovieRow")
_r = nu.AnyAttrRef("r")
_movie_cells = _RowAsList(_r["title"], _r["rating"], _r["watched"])

def _rows_form():
    return nu.Dict.of(
        rows=nu.Collect(
            nu.Map(nu.Iter(State.movies), transform=_movie_cells, key="r"),
        ),
    )


init = nu.v.Transaction(
    nu.IfDo(State.movies.missing(), State.movies.set(SEED)),
    nu.IfDo(State.total.missing(), State.total.set(len(SEED))),
    nu.IfDo(State.watched.missing(),
            State.watched.set(sum(1 for m in SEED if m["watched"] == "yes"))),
)


def _s(n): return nu.Str(nu.ToStr(n))


def _row_from_form():
    d = AddMovieForm.details
    return nu.Dict.of(
        title=nu.Str(d.title.input),
        rating=nu.Float(d.rating.input),
        watched=nu.If(nu.Bool(d.watched.input), "yes", "no"),
    )


hydrate = nu.v.Snapshot(
    Movies.heading.set("your movies")
    | Movies.stats.body.total.set_label("total")
    | Movies.stats.body.total.set_value(_s(State.total))
    | Movies.stats.body.watched.set_label("watched")
    | Movies.stats.body.watched.set_value(_s(State.watched))
    | Movies.stats.body.unseen.set_label("unseen")
    | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
    | Movies.shelf.body.table.set(_rows_form())
)


on_add = nu.ReactForever(
    AddMovieForm.submit.clicked(),
    nu.v.Transaction(
        State.movies.append(_row_from_form()),
        State.total.set(State.total + 1),
        State.watched.set(State.watched
                          + nu.If(nu.Bool(AddMovieForm.details.watched.input), 1, 0)),
    )
    >> nu.v.Snapshot(
        Movies.shelf.body.table.set(_rows_form())
        | Movies.stats.body.total.set_value(_s(State.total))
        | Movies.stats.body.watched.set_value(_s(State.watched))
        | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
        | Movies.form.feedback.set(title="logged",
                                   body="added " + nu.Str(AddMovieForm.details.title.input))
    ),
)


ui = init >> App.title.set("movies") >> hydrate >> on_add

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbmovies"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=nu.ForeverDo(nu.Delay(3600)),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
```

Run. The table shows the seed. Log a new movie. It lands in the table, stats bump, alert fires.

Read `_movie_cells` as a tiny sub-tree bound to the name `"r"`. `Map` streams movies through it and rebinds `r` for each one. `Collect` gathers the results into a list the table can render.

> **Row-click deletion is deferred.** `TableRef` emits row clicks, but the clean write-back path needs `.eager` reads through msgpack plus a host splice. It works in `examples/nudle/movies.py`; the mechanics are ugly enough to keep out of your first real app. Read that file when you want the pattern.

## What you built

A persistent movie tracker: seeded state, a form that commits atomically, a stats card and a table that rehydrate from state on every change. One tree, no callback graph.

## Try it yourself

Add a filter row: min rating, genre select, watched-only switch, apply and clear. The full reference lives in `examples/nudle/movies.py`.

If you still need to install anything for this tutorial, see [Install](../how-to/install).
