"""Movies - personal movie tracker.

Flow: log a movie via the form; the row lands in the table and stats update.
Click a row to open its movie at `/movie?id=<n>`; delete from there. The
movie is in the URL, not in the store, so a movie's page can be reloaded,
copied or opened in another tab. Filters redraw the visible rows.

Two pages, routed in Python: `nustd.ui.route` follows the History and shows
the page the pathname names. The nav bar on top is drawn by the program like
everything else. Everything visible sits in one Container, the page frame;
the title and the History stay at the root. The movies page is kept between
visits (`keep=True`), so a half-typed form and the filters are still there
when you come back.
"""

import nu
import nustd


_GENRES = [
    {"value": "action", "label": "Action"},
    {"value": "drama", "label": "Drama"},
    {"value": "scifi", "label": "Sci-fi"},
    {"value": "doc", "label": "Documentary"},
    {"value": "anim", "label": "Animation"},
]

_GENRES_WITH_ANY = [{"value": "", "label": "Any genre"}, *_GENRES]


# ---- UI ---------------------------------------------------------------------


class TitleField(nustd.ui.Field):
    input = nustd.ui.InputRef.slot(placeholder="e.g. Arrival")


class TextAreaField(nustd.ui.Field):
    input = nustd.ui.TextAreaRef.slot(placeholder="Quick thoughts...", rows=2)


class YearField(nustd.ui.Field):
    input = nustd.ui.NumberInputRef.slot(
        min=1900.0,
        max=2100.0,
        step=1.0,
        default=2020.0,
    )


class RatingField(nustd.ui.Field):
    input = nustd.ui.NumberInputRef.slot(
        min=1.0,
        max=10.0,
        step=0.5,
        default=7.0,
    )


class GenreField(nustd.ui.Field):
    input = nustd.ui.SelectRef.slot(options=_GENRES, selected="drama")


class SwitchField(nustd.ui.Field):
    input = nustd.ui.SwitchRef.slot(default=True)


class DetailsFieldset(nustd.ui.Fieldset):
    title = TitleField.slot(label="Title", help="Movie title", required=True)
    year = YearField.slot(label="Year")
    genre = GenreField.slot(label="Genre")


class ScoreFieldset(nustd.ui.Fieldset):
    rating = RatingField.slot(label="Rating", help="How much you liked it")
    watched = SwitchField.slot(label="Watched?", help="Off means still on the pile")
    notes = TextAreaField.slot(label="Notes")


class AddMovieForm(nustd.ui.Form):
    details = DetailsFieldset.slot(legend="Movie", gap="md")
    score = ScoreFieldset.slot(legend="Your take", gap="md")
    submit = nustd.ui.ButtonRef.slot(label="Log it", variant="primary")
    feedback = nustd.ui.AlertRef.slot(variant="ok", dismissible=True)


class MinRatingField(nustd.ui.Field):
    input = nustd.ui.NumberInputRef.slot(min=1.0, max=10.0, step=0.5, default=1.0)


class FilterGenreField(nustd.ui.Field):
    input = nustd.ui.SelectRef.slot(options=_GENRES_WITH_ANY, selected="")


class WatchedOnlyField(nustd.ui.Field):
    input = nustd.ui.SwitchRef.slot(default=False)


class FilterRow(nustd.ui.Row):
    min_rating = MinRatingField.slot(label="Min rating")
    genre = FilterGenreField.slot(label="Genre")
    watched_only = WatchedOnlyField.slot(label="Already watched")
    apply = nustd.ui.ButtonRef.slot(label="Apply", variant="secondary")
    reset = nustd.ui.ButtonRef.slot(label="Clear", variant="ghost")


class FilterCard(nustd.ui.Card):
    body = FilterRow.slot(gap=3, align="center", wrap=True)


class StatsRow(nustd.ui.Row):
    total = nustd.ui.StatRef.slot(label="Total")
    watched = nustd.ui.StatRef.slot(label="Watched")
    unseen = nustd.ui.StatRef.slot(label="Unseen")
    latest = nustd.ui.TextRef.slot()
    health = nustd.ui.BadgeRef.slot(label="Fresh", variant="ok")


class StatsCard(nustd.ui.Card):
    body = StatsRow.slot(gap=6, align="center", wrap=True)


class TableBody(nustd.ui.Column):
    table = nustd.ui.TableRef.slot(
        columns=["title", "year", "genre", "rating", "watched", "notes"],
        row_key="id",
        striped=True,
        dense=True,
        clickable_rows=True,
        max_rows=200,
    )
    empty = nustd.ui.AlertRef.slot(
        variant="info",
        body="No movies match",
        dismissible=False,
    )


class TableCard(nustd.ui.Card):
    body = TableBody.slot(gap=3)


# ---- Pages ------------------------------------------------------------------


class Movies(nustd.ui.Column):
    heading = nustd.ui.HeadingRef.slot(label="Your movies")
    intro = nustd.ui.TextRef.slot(
        value="Log what you watch. New entries land at the top of the table.",
    )

    stats = StatsCard.slot(title="Your shelf")
    form = AddMovieForm.slot(title="Log a movie", gap=4, padding=4)
    filters = FilterCard.slot(title="Filter")
    shelf = TableCard.slot(title="Movies")


class DetailRow(nustd.ui.Row):
    year = nustd.ui.StatRef.slot(label="Year")
    genre = nustd.ui.StatRef.slot(label="Genre")
    rating = nustd.ui.StatRef.slot(label="Rating")
    watched = nustd.ui.BadgeRef.slot(label="Watched", variant="ok")


class MetaCard(nustd.ui.Card):
    meta = DetailRow.slot(gap=6, align="center", wrap=True)


class NotesCard(nustd.ui.Card):
    body = nustd.ui.MarkdownRef.slot()


class DetailActions(nustd.ui.Row):
    back = nustd.ui.ButtonRef.slot(label="Back", variant="ghost")
    remove = nustd.ui.ButtonRef.slot(label="Delete", variant="danger")


class MovieDetail(nustd.ui.Column):
    heading = nustd.ui.HeadingRef.slot()
    meta = MetaCard.slot(title="Details")
    notes = NotesCard.slot(title="Notes")
    actions = DetailActions.slot(gap=3, align="center")


class Nav(nustd.ui.NavList):
    movies = nustd.ui.NavItemRef.slot(label="Movies", href="/")


class Page(nustd.ui.Container):
    """The frame every page sits in, under the nav bar."""

    nav = Nav.slot(variant="horizontal", label="Movies")
    movies = Movies.slot(gap=6)
    detail = MovieDetail.slot(gap=6)


class App(nu.Shape):
    title = nustd.ui.TitleRef.slot()
    history = nustd.ui.HistoryRef.slot()
    page = Page.slot(size="main")


# ---- State ------------------------------------------------------------------


class Movie(nu.Shape):
    title = nustd.kv.StrRef.slot()
    year = nustd.kv.IntRef.slot()
    genre = nustd.kv.StrRef.slot()
    rating = nustd.kv.FloatRef.slot()
    watched = nustd.kv.BoolRef.slot()
    notes = nustd.kv.StrRef.slot()


class State(nu.Shape):
    movies = nustd.kv.ListRef.slot(Movie)
    total = nustd.kv.IntRef.slot()
    watched = nustd.kv.IntRef.slot()
    latest_title = nustd.kv.StrRef.slot()


# ---- Seed ------------------------------------------------------------------

_SEED_MOVIES: list[dict] = [
    {
        "title": "Arrival",
        "year": 2016,
        "genre": "scifi",
        "rating": 8.5,
        "watched": True,
        "notes": "linguists save the world",
    },
    {
        "title": "Dune: Part Two",
        "year": 2024,
        "genre": "scifi",
        "rating": 9.0,
        "watched": True,
        "notes": "worm ride > sequel",
    },
    {
        "title": "The Menu",
        "year": 2022,
        "genre": "drama",
        "rating": 7.0,
        "watched": True,
        "notes": "eat the rich, literally",
    },
    {
        "title": "Perfect Days",
        "year": 2023,
        "genre": "drama",
        "rating": 8.0,
        "watched": False,
        "notes": "tokyo, tapes, toilets",
    },
]


# ---- Wire -------------------------------------------------------------------


def _row(entry: nu.Attr) -> nu.Nu:
    """One ``(index, movie)`` pair as a table row, keyed by the movie's index."""
    movie = entry[1]
    return nu.Dict.of(
        id=entry[0],
        title=movie["title"],
        year=movie["year"],
        genre=movie["genre"],
        rating=movie["rating"],
        watched=nu.If(movie["watched"], "yes", "no"),
        notes=movie["notes"],
    )


def _rows_form() -> nu.Nu:
    """Every stored movie as a table row."""
    return nu.Dict.of(rows=nu.Collect(nu.Map(nu.Enumerate(nu.Iter(State.movies)), _row)))


def _rows_filtered() -> nu.Nu:
    """Same shape as _rows_form, but honors the current FilterRow inputs.

    An input nobody has touched yet reads None: that filter is not set. Rows
    keep the movie's index as their key, so a click on a filtered table still
    opens the right movie.
    """
    min_r = nu.Float(App.page.movies.filters.body.min_rating.input)
    genre = nu.Str(App.page.movies.filters.body.genre.input)
    watched_only = nu.Bool(App.page.movies.filters.body.watched_only.input)
    shown = nu.Filter(
        nu.Enumerate(nu.Iter(State.movies)),
        lambda entry: nu.And(
            nu.Or(nu.Eq(min_r, None), nu.Ge(entry[1]["rating"], min_r)),
            nu.Or(nu.Eq(genre, None), nu.Eq(genre, ""), nu.Eq(entry[1]["genre"], genre)),
            nu.Or(nu.Not(watched_only), entry[1]["watched"]),
        ),
    )
    return nu.Dict.of(
        rows=nu.Collect(nu.Map(shown, _row)),
    )


# Seed once, on a store that has never been written. A restart then keeps what
# the user logged instead of replacing the shelf with the samples again.
init = nustd.kv.Transaction(
    nu.IfDo(
        State.total.missing(),
        State.total.set(len(_SEED_MOVIES))
        | State.watched.set(sum(1 for m in _SEED_MOVIES if m["watched"]))
        | State.latest_title.set(_SEED_MOVIES[-1]["title"])
        | State.movies.set(_SEED_MOVIES),
    ),
)


# Every visit to the movies page redraws what the store says, through the
# filters as they stand: a movie deleted on the detail page is gone from the
# table and the stats when you come back.
hydrate = nustd.kv.Snapshot(
    App.page.movies.stats.body.total.set_value(nu.str(State.total))
    | App.page.movies.stats.body.watched.set_value(nu.str(State.watched))
    | App.page.movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
    | App.page.movies.stats.body.latest.set(State.latest_title)
    | App.page.movies.shelf.body.table.set(_rows_filtered())
)


on_add = nu.ReactForever(
    App.page.movies.form.submit.on_click(),
    nustd.kv.Transaction(
        State.movies.append(
            nu.Dict.of(
                title=nu.Str(App.page.movies.form.details.title.input),
                year=nu.Int(App.page.movies.form.details.year.input),
                genre=nu.Str(App.page.movies.form.details.genre.input),
                rating=nu.Float(App.page.movies.form.score.rating.input),
                watched=nu.Bool(App.page.movies.form.score.watched.input),
                notes=nu.Str(App.page.movies.form.score.notes.input),
            ),
        )
        | State.total.set(State.total + 1)
        | State.watched.set(
            State.watched + nu.If(nu.Bool(App.page.movies.form.score.watched.input), 1, 0),
        )
        | State.latest_title.set(nu.Str(App.page.movies.form.details.title.input)),
    )
    >> nustd.kv.Snapshot(
        App.page.movies.shelf.body.table.set(_rows_form())
        | App.page.movies.stats.body.total.set_value(nu.str(State.total))
        | App.page.movies.stats.body.watched.set_value(nu.str(State.watched))
        | App.page.movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
        | App.page.movies.stats.body.latest.set(State.latest_title)
        | App.page.movies.form.feedback.set(
            title="Logged",
            body="Added " + nu.Str(App.page.movies.form.details.title.input),
        )
    ),
)


# A row opens its movie's page. The movie is in the URL, so the page is a
# place: reload it, copy it, open it in another tab.
on_row_click = nu.ReactForever(
    App.page.movies.shelf.body.table.on_row_click(),
    lambda click: App.history.push(nu.Str("/movie?id=") + nu.str(click["key"])),
)


@nu.host
def _index(query: object, count: int) -> int:
    """The movie ``?id=`` names, as an index into the shelf. -1 for none."""
    raw = query.get("id", "") if isinstance(query, dict) else ""
    return int(raw) if raw.isdigit() and int(raw) < count else -1


def _draw_detail(i: nu.Int) -> nu.Nu:
    movie = State.movies[i]
    return nustd.kv.Snapshot(
        App.page.detail.heading.set(movie.title)
        | App.page.detail.meta.meta.year.set_value(nu.str(movie.year))
        | App.page.detail.meta.meta.genre.set_value(movie.genre)
        | App.page.detail.meta.meta.rating.set_value(nu.str(movie.rating))
        | App.page.detail.meta.meta.watched.set(label=nu.If(movie.watched, "Watched", "Unseen"))
        | App.page.detail.notes.body.set(movie.notes)
    )


def _detail_actions(i: nu.Int) -> nu.Nu:
    on_delete = nu.ReactForever(
        App.page.detail.actions.remove.on_click(),
        nustd.kv.Transaction(State.movies.del_at(i) >> State.total.set(nu.Len(State.movies)))
        >> App.history.push("/"),
    )
    return on_delete | on_back


def _detail(held: nu.ObjectRef) -> nu.Nu:
    """The movie page for the index read off the URL; an unknown id draws a note."""
    i = nu.Int(held)
    missing = App.page.detail.heading.set("No such movie") >> on_back
    return nu.IfDo(i >= 0, _draw_detail(i) >> _detail_actions(i), missing)


on_back = nu.ReactForever(App.page.detail.actions.back.on_click(), App.history.push("/"))


on_filter_apply = nu.ReactForever(
    App.page.movies.filters.body.apply.on_click(),
    nustd.kv.Snapshot(App.page.movies.shelf.body.table.set(_rows_filtered())),
)


on_filter_clear = nu.ReactForever(
    App.page.movies.filters.body.reset.on_click(),
    nustd.kv.Snapshot(
        App.page.movies.filters.body.min_rating.input.set(1.0)
        | App.page.movies.filters.body.genre.input.set("")
        | App.page.movies.filters.body.watched_only.input.set(False)
        | App.page.movies.shelf.body.table.set(_rows_form())
    ),
)


movies_page = hydrate >> (on_add | on_row_click | on_filter_apply | on_filter_clear)

detail_page = nu.let(
    nustd.kv.Snapshot(_index(App.history.query(), nu.Len(State.movies))),
    _detail,
)

ui = App.title.set("Movies") >> nustd.ui.route(
    App.history,
    {
        "/": App.page.movies.showing(movies_page, keep=True),
        "/movie": App.page.detail.showing(detail_page),
    },
)


app = nu.With(
    nustd.kv.rocksdb_navigator(".dbmovies"),
    body=nu.ParallelAsync(
        nustd.ui.serve(
            nustd.ui.boot(App.title, App.history, App.page.nav) >> nustd.kv.auto_flow_atomic(ui)
        ),
        nustd.kv.auto_flow_atomic(init),
    ),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
