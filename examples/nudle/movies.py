"""Movies - personal movie tracker.

Flow: log a movie via the form; the row lands in the table and stats update.
Click a row in the table to remove it. Filters redraw the visible rows.
"""

from __future__ import annotations

import asyncio

import nu


_GENRES = [
    {"value": "action", "label": "action"},
    {"value": "drama", "label": "drama"},
    {"value": "scifi", "label": "sci-fi"},
    {"value": "doc", "label": "documentary"},
    {"value": "anim", "label": "animation"},
]

_GENRES_WITH_ANY = [{"value": "", "label": "any genre"}, *_GENRES]


class TitleField(nu.ui.Field):
    input = nu.ui.InputRef.slot(placeholder="e.g. Arrival")


class TextAreaField(nu.ui.Field):
    input = nu.ui.TextAreaRef.slot(placeholder="quick thoughts...", rows=2)


class YearField(nu.ui.Field):
    input = nu.ui.NumberInputRef.slot(
        min=1900.0,
        max=2100.0,
        step=1.0,
        default=2020.0,
    )


class RatingField(nu.ui.Field):
    input = nu.ui.NumberInputRef.slot(
        min=1.0,
        max=10.0,
        step=0.5,
        default=7.0,
    )


class GenreField(nu.ui.Field):
    input = nu.ui.SelectRef.slot(options=_GENRES, selected="drama")


class SwitchField(nu.ui.Field):
    input = nu.ui.SwitchRef.slot(default=True)


# ---- Composites -------------------------------------------------------------


class DetailsFieldset(nu.ui.Fieldset):
    title = TitleField.slot(label="title", help="movie title", required=True)
    year = YearField.slot(label="year")
    genre = GenreField.slot(label="genre")


class ScoreFieldset(nu.ui.Fieldset):
    rating = RatingField.slot(label="rating", help="how much you liked it")
    watched = SwitchField.slot(label="watched?", help="off means still on the pile")
    notes = TextAreaField.slot(label="notes")


class AddMovieForm(nu.ui.Form):
    details = DetailsFieldset.slot(legend="movie", gap="md")
    score = ScoreFieldset.slot(legend="your take", gap="md")
    submit = nu.ui.ButtonRef.slot(label="log it", variant="primary")
    feedback = nu.ui.AlertRef.slot(variant="ok", dismissible=True)


class FilterRow(nu.ui.Row):
    min_rating = nu.ui.NumberInputRef.slot(
        label="min rating",
        min=1.0,
        max=10.0,
        step=0.5,
        default=1.0,
    )
    genre = nu.ui.SelectRef.slot(options=_GENRES_WITH_ANY, selected="")
    watched_only = nu.ui.SwitchRef.slot(label="watched only", default=False)
    apply = nu.ui.ButtonRef.slot(label="apply", variant="secondary")
    clear = nu.ui.ButtonRef.slot(label="clear", variant="ghost")


class FilterCard(nu.ui.Card):
    body = FilterRow.slot(gap=3, align="center", wrap=True)


class StatsRow(nu.ui.Row):
    total = nu.ui.StatRef.slot(label="total")
    watched = nu.ui.StatRef.slot(label="watched")
    unseen = nu.ui.StatRef.slot(label="unseen")
    latest = nu.ui.TextRef.slot()
    health = nu.ui.BadgeRef.slot(label="fresh", variant="ok")


class StatsCard(nu.ui.Card):
    body = StatsRow.slot(gap=6, align="center", wrap=True)


class TableBody(nu.ui.Column):
    table = nu.ui.TableRef.slot(
        columns=["title", "year", "genre", "rating", "watched", "notes"],
        striped=True,
        dense=True,
        clickable_rows=True,
        max_rows=200,
    )
    empty = nu.ui.AlertRef.slot(
        variant="info",
        body="no movies match",
        dismissible=False,
    )


class TableCard(nu.ui.Card):
    body = TableBody.slot(gap=3)


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    movies = nu.v.ListRef.slot(object)
    total = nu.v.IntRef.slot()
    watched = nu.v.IntRef.slot()
    latest_title = nu.v.StrRef.slot()


# ---- Page -------------------------------------------------------------------


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot(label="your movies")
    intro = nu.ui.TextRef.slot(
        value="log what you watch. new entries land at the top of the table.",
    )

    stats = StatsCard.slot(title="your shelf")
    form = AddMovieForm.slot(title="log a movie", gap=4, padding=4)
    filters = FilterCard.slot(title="filter")
    shelf = TableCard.slot(title="movies")


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Movies})


# ---- Seed + helpers ---------------------------------------------------------

# Splice one item out of a list by index. Read through `.eager` first so the
# list lands as plain dicts (not LazyDictView) and re-encodes on write-back.
_SpliceAt = nu.host(lambda xs, i: [*list(xs)[:i], *list(xs)[i + 1 :]], name="SpliceAt")


_SEED_MOVIES: list[dict] = [
    {
        "title": "Arrival",
        "year": 2016,
        "genre": "scifi",
        "rating": 8.5,
        "watched": "yes",
        "notes": "linguists save the world",
    },
    {
        "title": "Dune: Part Two",
        "year": 2024,
        "genre": "scifi",
        "rating": 9.0,
        "watched": "yes",
        "notes": "worm ride > sequel",
    },
    {
        "title": "The Menu",
        "year": 2022,
        "genre": "drama",
        "rating": 7.0,
        "watched": "yes",
        "notes": "eat the rich, literally",
    },
    {
        "title": "Perfect Days",
        "year": 2023,
        "genre": "drama",
        "rating": 8.0,
        "watched": "no",
        "notes": "tokyo, tapes, toilets",
    },
]


def _row_from_form() -> nu.Nu:
    """Dict row read from the live form inputs."""
    title_input = AddMovieForm.details.title.input
    year_input = AddMovieForm.details.year.input
    genre_input = AddMovieForm.details.genre.input
    rating_input = AddMovieForm.score.rating.input
    watched_input = AddMovieForm.score.watched.input
    notes_input = AddMovieForm.score.notes.input
    return nu.Dict.of(
        title=nu.Str(title_input),
        year=nu.Int(year_input),
        genre=nu.Str(genre_input),
        rating=nu.Float(rating_input),
        watched=nu.If(nu.Bool(watched_input), "yes", "no"),
        notes=nu.Str(notes_input),
    )


_r = nu.AnyAttrRef("r")
_movie_cells = nu.List.of(
    _r["title"],
    _r["year"],
    _r["genre"],
    _r["rating"],
    _r["watched"],
    _r["notes"],
)


def _rows_form() -> nu.Nu:
    """Map each stored movie dict into a positional row TableRef expects."""
    return nu.Dict.of(
        rows=nu.Collect(
            nu.Map(
                nu.Iter(State.movies),
                transform=_movie_cells,
                key="r",
            ),
        ),
    )


# ---- Wire -------------------------------------------------------------------


init = nu.v.Transaction(
    State.total.set(len(_SEED_MOVIES))
    | State.watched.set(sum(1 for m in _SEED_MOVIES if m["watched"] == "yes"))
    | State.latest_title.set(_SEED_MOVIES[-1]["title"])
    | State.movies.set(_SEED_MOVIES),
)


hydrate = nu.v.Snapshot(
    Movies.stats.body.total.set_value(nu.str(State.total))
    | Movies.stats.body.watched.set_value(nu.str(State.watched))
    | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
    | Movies.stats.body.latest.set(State.latest_title)
    | Movies.shelf.body.table.set(_rows_form())
)


on_add = nu.ReactForever(
    AddMovieForm.submit.clicked(),
    nu.v.Transaction(
        State.movies.append(_row_from_form())
        | State.total.set(State.total + 1)
        | State.watched.set(
            State.watched + nu.If(nu.Bool(AddMovieForm.score.watched.input), 1, 0),
        )
        | State.latest_title.set(nu.Str(AddMovieForm.details.title.input)),
    )
    >> nu.v.Snapshot(
        Movies.shelf.body.table.set(_rows_form())
        | Movies.stats.body.total.set_value(nu.str(State.total))
        | Movies.stats.body.watched.set_value(nu.str(State.watched))
        | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
        | Movies.stats.body.latest.set(State.latest_title)
        | Movies.form.feedback.set(
            title="logged",
            body="added " + nu.Str(AddMovieForm.details.title.input),
        )
    ),
)


# row_clicked() delivers the raw notify payload: {"row_index": int} for row
# clicks, {"sort_column": ..., "sort_direction": ...} for header clicks. Both
# share the channel; branch on shape to skip header clicks.
_click = nu.DictAttrRef("row_click")

on_row_click = nu.ReactForever(
    Movies.shelf.body.table.row_clicked(),
    nu.IfDo(
        nu.Contains(_click, "row_index"),
        nu.v.Transaction(
            State.movies.set(_SpliceAt(State.movies.eager, _click["row_index"]))
            >> State.total.set(nu.Len(State.movies)),
        )
        >> nu.v.Snapshot(
            Movies.shelf.body.table.set(_rows_form())
            | Movies.stats.body.total.set_value(nu.str(State.total))
            | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
        ),
    ),
    changed_key="row_click",
)


ui = init >> App.title.set("movies") >> hydrate >> (on_add | on_row_click)


tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbmovies"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=nu.ForeverDo(nu.Delay(3600)),  # click-driven; hold the server open
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
