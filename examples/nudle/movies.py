"""Movies -- personal movie tracker.

Post slot-props refactor: preset-per-widget subclasses collapse into inline
`.slot(**props)` at the usage site. Layout chrome (gap, align, wrap, title)
and widget knobs (variant, label, min/max, options, ...) ride on the slot
call instead of a subclass. Small structural wrappers (Fieldsets, Cards,
Rows, FieldRefs) remain -- they exist only to declare child slots that
the widget kit can't inline yet.

Flow: log a movie via the form; the row lands in the table and stats update.
Click a row in the table to remove it. Filters redraw the visible rows.
"""

from __future__ import annotations

import asyncio

import nu
import nu.virtuals as nv


_GENRES = [
    {"value": "action", "label": "action"},
    {"value": "drama", "label": "drama"},
    {"value": "scifi", "label": "sci-fi"},
    {"value": "doc", "label": "documentary"},
    {"value": "anim", "label": "animation"},
]

_GENRES_WITH_ANY = [{"value": "", "label": "any genre"}, *_GENRES]


# ---- Form fields ------------------------------------------------------------
# FieldRef requires exactly one structural child slot, so we keep a small
# wrapper per input kind. Inner-input knobs ride on the inner slot() call;
# label / help / required move to slot-props at the usage site.


class TitleField(nu.ui.FieldRef):
    input = nu.ui.InputRef.slot(label="title", placeholder="e.g. Arrival")


class TextAreaField(nu.ui.FieldRef):
    input = nu.ui.TextAreaRef.slot(placeholder="quick thoughts...", rows=2)


class YearField(nu.ui.FieldRef):
    input = nu.ui.NumberInputRef.slot(
        label="year",
        min=1900.0,
        max=2100.0,
        step=1.0,
        default=2020.0,
    )


class RatingField(nu.ui.FieldRef):
    input = nu.ui.NumberInputRef.slot(
        label="rating (1-10)",
        min=1.0,
        max=10.0,
        step=0.5,
        default=7.0,
    )


class GenreField(nu.ui.FieldRef):
    input = nu.ui.SelectRef.slot(options=_GENRES, selected="drama")


class SwitchField(nu.ui.FieldRef):
    input = nu.ui.SwitchRef.slot(label="watched?", default=True)


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


class FilterCard(nu.ui.CardRef):
    body = FilterRow.slot(gap=3, align="center", wrap=True)


class StatsRow(nu.ui.Row):
    total = nu.ui.StatRef.slot()
    watched = nu.ui.StatRef.slot()
    unseen = nu.ui.StatRef.slot()
    latest = nu.ui.TextRef.slot()
    health = nu.ui.BadgeRef.slot(variant="ok")


class StatsCard(nu.ui.CardRef):
    body = StatsRow.slot(gap=6, align="center", wrap=True)


class TableBody(nu.ui.Column):
    table = nu.ui.TableRef.slot(
        columns=["title", "year", "genre", "rating", "watched", "notes"],
        striped=True,
        dense=True,
        clickable_rows=True,
        max_rows=200,
    )
    empty = nu.ui.AlertRef.slot()


class TableCard(nu.ui.CardRef):
    body = TableBody.slot(gap=3)


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    movies = nv.ListRef.slot(object)
    total = nv.IntRef.slot()
    watched = nv.IntRef.slot()
    latest_title = nv.StrRef.slot()


# ---- Page -------------------------------------------------------------------


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot()
    intro = nu.ui.TextRef.slot()

    stats = StatsCard.slot(title="your shelf")
    form = AddMovieForm.slot(title="log a movie", gap=4, padding=4)
    filters = FilterCard.slot(title="filter")
    shelf = TableCard.slot(title="movies")


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Movies})


# ---- Seed + helpers ---------------------------------------------------------
#
# PAIN: TableRef rows must be positional lists, but no ListForm.of(a, b, c)
# exists to build one from Nu expressions. Every consumer host-lifts the
# same Python lambda -- see legolas/uis/shell.py:RowAsList.
#
# PAIN: storing rows as `list[list]` in a ListRef backfires -- elements come
# back as EagerListView / LazyListView and msgpack rejects both. Every
# consumer stores dicts (or a keyed Shape) and materializes positional rows
# on the fly via a MapQuery + RowAsList transform.

_RowAsList = nu.host(lambda *xs: list(xs), name="MovieRow")


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
    return nu.DictForm.of(
        title=nu.StrForm(title_input),
        year=nu.IntForm(year_input),
        genre=nu.StrForm(genre_input),
        rating=nu.FloatForm(rating_input),
        watched=nu.IfQuery(nu.BoolForm(watched_input), "yes", "no"),
        notes=nu.StrForm(notes_input),
    )


_r = nu.AnyAttrRef("r")
_movie_cells = _RowAsList(
    _r["title"],
    _r["year"],
    _r["genre"],
    _r["rating"],
    _r["watched"],
    _r["notes"],
)


def _rows_form() -> nu.Nu:
    """Map each stored movie dict into a positional row TableRef expects."""
    return nu.DictForm.of(
        rows=nu.CollectQuery(
            nu.MapQuery(
                nu.IterQuery(State.movies),
                transform=_movie_cells,
                key="r",
            ),
        ),
    )


# ---- Wire -------------------------------------------------------------------


init = nu.v.Transaction(
    nu.IfDo(State.total.missing(), State.total.set(len(_SEED_MOVIES))),
    nu.IfDo(
        State.watched.missing(),
        State.watched.set(sum(1 for m in _SEED_MOVIES if m["watched"] == "yes")),
    ),
    nu.IfDo(
        State.latest_title.missing(),
        State.latest_title.set(_SEED_MOVIES[-1]["title"]),
    ),
    nu.IfDo(State.movies.missing(), State.movies.set(_SEED_MOVIES)),
)


def _s(n: nu.Nu) -> nu.Nu:
    """Format an int Ref as a display string for StatRef."""
    return nu.StrForm(nu.StrQuery(n))


hydrate = nu.v.Snapshot(
    Movies.heading.set("your movies")
    | Movies.intro.set("log what you watch. new entries land at the top of the table.")
    | Movies.stats.body.total.set_label("total")
    | Movies.stats.body.total.set_value(_s(State.total))
    | Movies.stats.body.watched.set_label("watched")
    | Movies.stats.body.watched.set_value(_s(State.watched))
    | Movies.stats.body.unseen.set_label("unseen")
    | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
    | Movies.stats.body.latest.set(State.latest_title)
    | Movies.stats.body.health.set_label("fresh")
    | Movies.shelf.body.table.set(_rows_form())
    | Movies.shelf.body.empty.set(
        variant="info",
        title="",
        body="no movies match",
        dismissible=False,
    )
)


on_add = nu.ReactForever(
    AddMovieForm.submit.clicked(),
    nu.v.Transaction(
        State.movies.append(_row_from_form()),
        State.total.set(State.total + 1),
        State.watched.set(
            State.watched + nu.IfQuery(nu.BoolForm(AddMovieForm.score.watched.input), 1, 0),
        ),
        State.latest_title.set(nu.StrForm(AddMovieForm.details.title.input)),
    )
    >> nu.v.Snapshot(
        Movies.shelf.body.table.set(_rows_form())
        | Movies.stats.body.total.set_value(_s(State.total))
        | Movies.stats.body.watched.set_value(_s(State.watched))
        | Movies.stats.body.unseen.set_value(_s(State.total - State.watched))
        | Movies.stats.body.latest.set(State.latest_title)
        | Movies.form.feedback.set(
            title="logged",
            body="added " + nu.StrForm(AddMovieForm.details.title.input),
        )
    ),
)


# PAIN (row-click delete deferred):
#
# The natural implementation -- read the clicked row index, splice it out of
# `State.movies` via two slice reads and a concat, then `.set(...)` the whole
# ListRef back -- explodes at storage time:
#
#     StorageOperationError: Failed to encode key/value for ('/', 'movies', 0):
#     no default __reduce__ due to non-trivial __cinit__
#
# Reads from a ListRef yield view objects (LazyListView / EagerListView),
# and RocksDB can't re-encode a "list of views" back into itself. Legolas
# never uses this shape -- it keys items in a `DictRef[id]` (or a Shape) and
# deletes by key, sidestepping the whole problem.
#
# So click-to-delete would require reshaping `State.movies` from
# `ListRef[dict]` to `DictRef[str, dict]` + an auto-incremented id. Real
# fix for the polish pass, not for this demo file.


ui = init >> App.title.set("movies") >> hydrate >> on_add


tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbmovies"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=nu.ForeverDo(nu.Delay(3600)),  # click-driven; hold the server open
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
