"""Movies -- personal movie tracker.

This example exists as a DX benchmark for the upcoming nu.ui polish pass.
It is written in the current idiom on purpose: every knob is a ClassVar on
its own subclass because `slot()` takes no kwargs. Read the `PAIN:` notes
before touching the model -- they mark the places we want to fix.

Flow: log a movie via the form; the row lands in the table and stats update.
Click a row in the table to remove it. Filters redraw the visible rows.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import nu
import nu.virtuals as nv


# ---- Ref presets ------------------------------------------------------------
# PAIN: five almost-identical Refs, each a subclass because a `variant` /
# `label` / `default` on `.slot()` isn't a thing.


class OkBadge(nu.ui.BadgeRef):
    variant: ClassVar[str] = "ok"


class WarnBadge(nu.ui.BadgeRef):
    variant: ClassVar[str] = "warn"


class NeutralBadge(nu.ui.BadgeRef):
    variant: ClassVar[str] = "neutral"


class RatingInput(nu.ui.NumberInputRef):
    """Form rating slot: 1-10, half steps, default 7."""

    label: ClassVar[str] = "rating (1-10)"
    min: ClassVar[float] = 1.0
    max: ClassVar[float] = 10.0
    step: ClassVar[float] = 0.5
    default: ClassVar[float] = 7.0


class MinRatingInput(nu.ui.NumberInputRef):
    """Filter rating slot -- same knobs as RatingInput but a different label,
    so it needs its own class."""

    label: ClassVar[str] = "min rating"
    min: ClassVar[float] = 1.0
    max: ClassVar[float] = 10.0
    step: ClassVar[float] = 0.5
    default: ClassVar[float] = 1.0


class YearInput(nu.ui.NumberInputRef):
    label: ClassVar[str] = "year"
    min: ClassVar[float] = 1900.0
    max: ClassVar[float] = 2100.0
    step: ClassVar[float] = 1.0
    default: ClassVar[float] = 2020.0


class WatchedOnlySwitch(nu.ui.SwitchRef):
    label: ClassVar[str] = "watched only"
    default: ClassVar[bool] = False


class WatchedSwitch(nu.ui.SwitchRef):
    label: ClassVar[str] = "watched?"
    default: ClassVar[bool] = True


class TitleInput(nu.ui.InputRef):
    label: ClassVar[str] = "title"
    placeholder: ClassVar[str] = "e.g. Arrival"


class NotesInput(nu.ui.TextAreaRef):
    placeholder: ClassVar[str] = "quick thoughts..."
    rows: ClassVar[int] = 2


# PAIN: two SelectRefs with the same options list, differing only in whether
# they include an "any" sentinel. Two subclasses.


class FormGenreSelect(nu.ui.SelectRef):
    options: ClassVar[list] = [
        {"value": "action", "label": "action"},
        {"value": "drama", "label": "drama"},
        {"value": "scifi", "label": "sci-fi"},
        {"value": "doc", "label": "documentary"},
        {"value": "anim", "label": "animation"},
    ]
    selected: ClassVar[str] = "drama"


class FilterGenreSelect(nu.ui.SelectRef):
    options: ClassVar[list] = [
        {"value": "", "label": "any genre"},
        {"value": "action", "label": "action"},
        {"value": "drama", "label": "drama"},
        {"value": "scifi", "label": "sci-fi"},
        {"value": "doc", "label": "documentary"},
        {"value": "anim", "label": "animation"},
    ]
    selected: ClassVar[str] = ""


# PAIN: TableRef subclassed only to pin columns + striped + dense +
# clickable_rows. `TableRef.slot(columns=[...], striped=True)` would erase
# this class.


class MoviesTable(nu.ui.TableRef):
    columns: ClassVar[list[str]] = [
        "title",
        "year",
        "genre",
        "rating",
        "watched",
        "notes",
    ]
    striped: ClassVar[bool] = True
    dense: ClassVar[bool] = True
    clickable_rows: ClassVar[bool] = True
    max_rows: ClassVar[int] = 200


class SubmitButton(nu.ui.ButtonRef):
    label: ClassVar[str] = "log it"
    variant: ClassVar[str] = "primary"


class ApplyButton(nu.ui.ButtonRef):
    label: ClassVar[str] = "apply"
    variant: ClassVar[str] = "secondary"


class ClearButton(nu.ui.ButtonRef):
    label: ClassVar[str] = "clear"
    variant: ClassVar[str] = "ghost"


class OkAlert(nu.ui.AlertRef):
    variant: ClassVar[str] = "ok"
    title: ClassVar[str] = ""
    body: ClassVar[str] = ""
    dismissible: ClassVar[bool] = True


# ---- Form fields ------------------------------------------------------------
# PAIN: six FieldRef subclasses that carry nothing but a label, a help string,
# and the inner input Ref. Genuinely one-shot config, encoded as classes.


class TitleFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "title"
    help: ClassVar[str] = "movie title"
    required: ClassVar[bool] = True
    input = TitleInput.slot()


class YearFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "year"
    input = YearInput.slot()


class GenreFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "genre"
    input = FormGenreSelect.slot()


class RatingFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "rating"
    help: ClassVar[str] = "how much you liked it"
    input = RatingInput.slot()


class WatchedFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "watched?"
    help: ClassVar[str] = "off means still on the pile"
    input = WatchedSwitch.slot()


class NotesFormField(nu.ui.FieldRef):
    label: ClassVar[str] = "notes"
    input = NotesInput.slot()


# ---- Composites -------------------------------------------------------------
# PAIN: layout knobs (gap, align, wrap) are ClassVars, so every distinct
# Row/Column shape becomes its own subclass even when the only thing that
# varies is the children.


class DetailsFieldset(nu.ui.Fieldset):
    legend: ClassVar[str] = "movie"
    gap: ClassVar[str] = "md"

    title = TitleFormField.slot()
    year = YearFormField.slot()
    genre = GenreFormField.slot()


class ScoreFieldset(nu.ui.Fieldset):
    legend: ClassVar[str] = "your take"
    gap: ClassVar[str] = "md"

    rating = RatingFormField.slot()
    watched = WatchedFormField.slot()
    notes = NotesFormField.slot()


class AddMovieForm(nu.ui.Form):
    title: ClassVar[str] = "log a movie"
    gap: ClassVar[int] = 4
    padding: ClassVar[int] = 4

    details = DetailsFieldset.slot()
    score = ScoreFieldset.slot()
    submit = SubmitButton.slot()
    feedback = OkAlert.slot()


class FilterRow(nu.ui.Row):
    gap: ClassVar[int] = 3
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    min_rating = MinRatingInput.slot()
    genre = FilterGenreSelect.slot()
    watched_only = WatchedOnlySwitch.slot()
    apply = ApplyButton.slot()
    clear = ClearButton.slot()


class FilterCard(nu.ui.CardRef):
    title: ClassVar[str] = "filter"
    body = FilterRow.slot()


class StatsRow(nu.ui.Row):
    gap: ClassVar[int] = 6
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    total = nu.ui.StatRef.slot()
    watched = nu.ui.StatRef.slot()
    unseen = nu.ui.StatRef.slot()
    latest = nu.ui.TextRef.slot()
    health = OkBadge.slot()


class StatsCard(nu.ui.CardRef):
    title: ClassVar[str] = "your shelf"
    body = StatsRow.slot()


class TableBody(nu.ui.Column):
    gap: ClassVar[int] = 3

    table = MoviesTable.slot()
    empty = nu.ui.AlertRef.slot()


class TableCard(nu.ui.CardRef):
    title: ClassVar[str] = "movies"
    body = TableBody.slot()


# ---- State ------------------------------------------------------------------
# Rows land in `movies` as positional lists matching MoviesTable.columns.
# Parallel counters keep stats math trivial (avoid ListForm reductions).


class State(nu.Shape):
    movies = nv.ListRef.slot(object)
    total = nv.IntRef.slot()
    watched = nv.IntRef.slot()
    latest_title = nv.StrRef.slot()


# ---- Page -------------------------------------------------------------------


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot()
    intro = nu.ui.TextRef.slot()

    stats = StatsCard.slot()
    form = AddMovieForm.slot()
    filters = FilterCard.slot()
    shelf = TableCard.slot()


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
