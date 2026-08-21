"""Movies: personal tracker. Form, filterable table, detail pages, all persisted."""

from pathlib import Path

import nu


_DB = Path.home() / ".nu" / "demos" / "movies"
_DB.parent.mkdir(parents=True, exist_ok=True)


_GENRES = [
    {"value": "action", "label": "Action"},
    {"value": "drama", "label": "Drama"},
    {"value": "scifi", "label": "Sci-fi"},
    {"value": "doc", "label": "Documentary"},
    {"value": "anim", "label": "Animation"},
]

_GENRES_WITH_ANY = [{"value": "", "label": "Any genre"}, *_GENRES]


# ---- UI ---------------------------------------------------------------------


class TitleField(nu.ui.Field):
    input = nu.ui.InputRef.slot(placeholder="e.g. Arrival")


class TextAreaField(nu.ui.Field):
    input = nu.ui.TextAreaRef.slot(placeholder="Quick thoughts...", rows=2)


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


class DetailsFieldset(nu.ui.Fieldset):
    title = TitleField.slot(label="Title", help="Movie title", required=True)
    year = YearField.slot(label="Year")
    genre = GenreField.slot(label="Genre")


class ScoreFieldset(nu.ui.Fieldset):
    rating = RatingField.slot(label="Rating", help="How much you liked it")
    watched = SwitchField.slot(label="Watched?", help="Off means still on the pile")
    notes = TextAreaField.slot(label="Notes")


class AddMovieForm(nu.ui.Form):
    details = DetailsFieldset.slot(legend="Movie", gap="md")
    score = ScoreFieldset.slot(legend="Your take", gap="md")
    submit = nu.ui.ButtonRef.slot(label="Log it", variant="primary")
    feedback = nu.ui.AlertRef.slot(variant="ok", dismissible=True)


class MinRatingField(nu.ui.Field):
    input = nu.ui.NumberInputRef.slot(min=1.0, max=10.0, step=0.5, default=1.0)


class FilterGenreField(nu.ui.Field):
    input = nu.ui.SelectRef.slot(options=_GENRES_WITH_ANY, selected="")


class WatchedOnlyField(nu.ui.Field):
    input = nu.ui.SwitchRef.slot(default=False)


class FilterRow(nu.ui.Row):
    min_rating = MinRatingField.slot(label="Min rating")
    genre = FilterGenreField.slot(label="Genre")
    watched_only = WatchedOnlyField.slot(label="Already watched")
    apply = nu.ui.ButtonRef.slot(label="Apply", variant="secondary")
    clear = nu.ui.ButtonRef.slot(label="Clear", variant="ghost")


class FilterCard(nu.ui.Card):
    body = FilterRow.slot(gap=3, align="center", wrap=True)


class StatsRow(nu.ui.Row):
    total = nu.ui.StatRef.slot(label="Total")
    watched = nu.ui.StatRef.slot(label="Watched")
    unseen = nu.ui.StatRef.slot(label="Unseen")
    latest = nu.ui.TextRef.slot()
    health = nu.ui.BadgeRef.slot(label="Fresh", variant="ok")


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
        body="No movies match",
        dismissible=False,
    )


class TableCard(nu.ui.Card):
    body = TableBody.slot(gap=3)


class Links(nu.ui.Row):
    docs = nu.ui.LinkRef.slot(
        label="Read the docs", href="https://nustack.dev/docs", target="_blank"
    )
    github = nu.ui.LinkRef.slot(
        label="Star on GitHub", href="https://github.com/nustackdev/nu", target="_blank"
    )
    examples = nu.ui.LinkRef.slot(
        label="Browse more demos",
        href="https://github.com/nustackdev/nu/tree/main/examples",
        target="_blank",
    )


# ---- Pages ------------------------------------------------------------------


class TopBar(nu.ui.Row):
    about = nu.ui.ButtonRef.slot(label="About this demo", variant="ghost")


class Movies(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot(label="Your movies")
    intro = nu.ui.TextRef.slot(
        value="Log what you watch. Filter the shelf, click a row for details.",
    )
    topbar = TopBar.slot(gap=3, align="center")

    stats = StatsCard.slot(title="Your shelf")
    form = AddMovieForm.slot(title="Log a movie", gap=4, padding=4)
    filters = FilterCard.slot(title="Filter")
    shelf = TableCard.slot(title="Movies")


class AboutActions(nu.ui.Row):
    back = nu.ui.ButtonRef.slot(label="Back to app", variant="ghost")


class About(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot(label="How it works")
    about = nu.ui.MarkdownRef.slot(
        value=(
            "- Real app: form, filterable table, stats row, per-item detail page.\n"
            "- Every row lives in rocksdb. Restart, everything is still there.\n"
            "- Same Ref system used for storage, form inputs, table, and navigation.\n"
            "- Same Interactions handle add, delete, filter, and page routing.\n"
        ),
    )
    links_heading = nu.ui.HeadingRef.slot(label="Try Nu yourself")
    links_intro = nu.ui.TextRef.slot(
        value="Full apps, forms, routing, no glue. See how far the primitive goes.",
    )
    links = Links.slot(gap=4, align="center", wrap=True)
    source_heading = nu.ui.HeadingRef.slot(label="Source")
    source_intro = nu.ui.TextRef.slot(
        value="The whole app, one file. Storage, UI, and the wires between them.",
    )
    source = nu.ui.CodeBlockRef.slot(
        code=Path(__file__).read_text(),
        language="python",
    )
    actions = AboutActions.slot(gap=3, align="center")


class DetailRow(nu.ui.Row):
    year = nu.ui.StatRef.slot(label="Year")
    genre = nu.ui.StatRef.slot(label="Genre")
    rating = nu.ui.StatRef.slot(label="Rating")
    watched = nu.ui.BadgeRef.slot(label="Watched", variant="ok")


class MetaCard(nu.ui.Card):
    meta = DetailRow.slot(gap=6, align="center", wrap=True)


class NotesCard(nu.ui.Card):
    body = nu.ui.MarkdownRef.slot()


class DetailActions(nu.ui.Row):
    back = nu.ui.ButtonRef.slot(label="Back", variant="ghost")
    remove = nu.ui.ButtonRef.slot(label="Delete", variant="danger")


class MovieDetail(nu.ui.Page):
    heading = nu.ui.HeadingRef.slot()
    meta = MetaCard.slot(title="Details")
    notes = NotesCard.slot(title="Notes")
    actions = DetailActions.slot(gap=3, align="center")


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Movies, "/detail": MovieDetail, "/about": About})


# ---- State ------------------------------------------------------------------


class Movie(nu.Shape):
    title = nu.kv.StrRef.slot()
    year = nu.kv.IntRef.slot()
    genre = nu.kv.StrRef.slot()
    rating = nu.kv.FloatRef.slot()
    watched = nu.kv.BoolRef.slot()
    notes = nu.kv.StrRef.slot()


class State(nu.Shape):
    movies = nu.kv.ShapesListRef.slot(Movie)
    total = nu.kv.IntRef.slot()
    watched = nu.kv.IntRef.slot()
    latest_title = nu.kv.StrRef.slot()
    selected = nu.kv.IntRef.slot()  # index of the movie open in MovieDetail


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


_ROW_TRANSFORM = nu.List.of(
    nu.DictAttrRef("r")["title"],
    nu.DictAttrRef("r")["year"],
    nu.DictAttrRef("r")["genre"],
    nu.DictAttrRef("r")["rating"],
    nu.If(nu.DictAttrRef("r")["watched"], "yes", "no"),
    nu.DictAttrRef("r")["notes"],
)


def _rows_form() -> nu.Nu:
    """Map each stored movie dict into a positional row TableRef expects."""
    return nu.Dict.of(
        rows=nu.Collect(
            nu.Map(nu.Iter(State.movies), transform=_ROW_TRANSFORM, key="r"),
        ),
    )


def _rows_filtered() -> nu.Nu:
    """Same shape as _rows_form, but honors the current FilterRow inputs."""
    min_r = nu.Float(FilterRow.min_rating.input)
    genre = nu.Str(FilterRow.genre.input)
    watched_only = nu.Bool(FilterRow.watched_only.input)
    predicate = nu.And(
        nu.Ge(nu.DictAttrRef("r")["rating"], min_r),
        nu.Or(nu.Eq(genre, ""), nu.Eq(nu.DictAttrRef("r")["genre"], genre)),
        nu.Or(nu.Not(watched_only), nu.DictAttrRef("r")["watched"]),
    )
    return nu.Dict.of(
        rows=nu.Collect(
            nu.Map(
                nu.Filter(nu.Iter(State.movies), predicate=predicate, key="r"),
                transform=_ROW_TRANSFORM,
                key="r",
            ),
        ),
    )


# Seed once, on a store that has never been written. A restart then keeps what
# the user logged instead of replacing the shelf with the samples again.
# `selected` stays unconditional: it is a cursor into the detail page, not data.
init = nu.kv.Transaction(
    nu.IfDo(
        State.total.missing(),
        State.total.set(len(_SEED_MOVIES))
        | State.watched.set(sum(1 for m in _SEED_MOVIES if m["watched"]))
        | State.latest_title.set(_SEED_MOVIES[-1]["title"])
        | State.movies.set(_SEED_MOVIES),
    )
    | State.selected.set(0),
)


hydrate = nu.kv.Snapshot(
    Movies.stats.body.total.set_value(nu.str(State.total))
    | Movies.stats.body.watched.set_value(nu.str(State.watched))
    | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
    | Movies.stats.body.latest.set(State.latest_title)
    | Movies.shelf.body.table.set(_rows_form())
)


on_add = nu.ReactForever(
    AddMovieForm.submit.clicked(),
    nu.kv.Transaction(
        State.movies.append(
            nu.Dict.of(
                title=nu.Str(AddMovieForm.details.title.input),
                year=nu.Int(AddMovieForm.details.year.input),
                genre=nu.Str(AddMovieForm.details.genre.input),
                rating=nu.Float(AddMovieForm.score.rating.input),
                watched=nu.Bool(AddMovieForm.score.watched.input),
                notes=nu.Str(AddMovieForm.score.notes.input),
            ),
        )
        | State.total.set(State.total + 1)
        | State.watched.set(
            State.watched + nu.If(nu.Bool(AddMovieForm.score.watched.input), 1, 0),
        )
        | State.latest_title.set(nu.Str(AddMovieForm.details.title.input)),
    )
    >> nu.kv.Snapshot(
        Movies.shelf.body.table.set(_rows_form())
        | Movies.stats.body.total.set_value(nu.str(State.total))
        | Movies.stats.body.watched.set_value(nu.str(State.watched))
        | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
        | Movies.stats.body.latest.set(State.latest_title)
        | Movies.form.feedback.set(
            title="Logged",
            body="Added " + nu.Str(AddMovieForm.details.title.input),
        )
    ),
)


on_row_click = nu.ReactForever(
    Movies.shelf.body.table.row_clicked(),
    nu.IfDo(
        nu.Contains(nu.DictAttrRef("row_click"), "row_index"),
        nu.kv.Transaction(State.selected.set(nu.DictAttrRef("row_click")["row_index"]))
        >> nu.kv.Snapshot(
            MovieDetail.heading.set(State.movies[State.selected].title)
            | MovieDetail.meta.meta.year.set_value(nu.str(State.movies[State.selected].year))
            | MovieDetail.meta.meta.genre.set_value(State.movies[State.selected].genre)
            | MovieDetail.meta.meta.rating.set_value(nu.str(State.movies[State.selected].rating))
            | MovieDetail.meta.meta.watched.set(
                label=nu.If(State.movies[State.selected].watched, "Watched", "Unseen"),
            )
            | MovieDetail.notes.body.set(State.movies[State.selected].notes)
        )
        >> App.nav.set("/detail"),
    ),
    changed_key="row_click",
)


on_delete = nu.ReactForever(
    MovieDetail.actions.remove.clicked(),
    nu.kv.Transaction(
        State.movies.del_at(State.selected) >> State.total.set(nu.Len(State.movies)),
    )
    >> nu.kv.Snapshot(
        Movies.shelf.body.table.set(_rows_form())
        | Movies.stats.body.total.set_value(nu.str(State.total))
        | Movies.stats.body.unseen.set_value(nu.str(State.total - State.watched))
    )
    >> App.nav.set("/"),
)


on_back = nu.ReactForever(MovieDetail.actions.back.clicked(), App.nav.set("/"))


on_about_open = nu.ReactForever(Movies.topbar.about.clicked(), App.nav.set("/about"))


on_about_back = nu.ReactForever(About.actions.back.clicked(), App.nav.set("/"))


on_filter_apply = nu.ReactForever(
    FilterRow.apply.clicked(),
    nu.kv.Snapshot(Movies.shelf.body.table.set(_rows_filtered())),
)


on_filter_clear = nu.ReactForever(
    FilterRow.clear.clicked(),
    nu.kv.Snapshot(
        FilterRow.min_rating.input.set(1.0)
        | FilterRow.genre.input.set("")
        | FilterRow.watched_only.input.set(False)
        | Movies.shelf.body.table.set(_rows_form())
    ),
)


ui = (
    App.title.set("Movies")
    >> hydrate
    >> (
        on_add
        | on_row_click
        | on_delete
        | on_back
        | on_filter_apply
        | on_filter_clear
        | on_about_open
        | on_about_back
    )
)


app = nu.With(
    nu.kv.rocksdb_navigator(str(_DB)),
    nu.ui.server(nu.kv.auto_flow_atomic(ui)),
    body=nu.kv.auto_flow_atomic(init >> nu.ForeverDo(nu.Delay(3600))),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
