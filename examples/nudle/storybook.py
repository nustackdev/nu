#!/usr/bin/env python3
"""Storybook -- one-page tour of every nudle component, with variations.

One Index, one Page, sectioned by component family. Most cells are static
(snapshotted once on mount) so the variations are easy to read. The live
chart and the interactive section exercise the dynamic interactions.

Run:
    make build
    cd api && uv run python ../examples/storybook.py

Then open http://127.0.0.1:8080.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import ClassVar

import nu
import nu_virtuals as nv
from nu.shapes.flows.react import ReactForever
from nu.stdlib import TimeSleep
from nu.stdlib.asyncio import AsyncSleep
from nu_virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator

import nudle


WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


# ---- Ref customizations -----------------------------------------------------
# Per-instance defaults are class-level. Subclass to pin a default; the wire
# type the browser sees is still the nearest packaged ancestor's name (see
# page._wire_type), so the renderer resolves automatically.


class InfoBadge(nudle.BadgeRef):
    """Info-variant badge."""

    variant: ClassVar[str] = "info"


class OkBadge(nudle.BadgeRef):
    """Ok-variant badge."""

    variant: ClassVar[str] = "ok"


class WarnBadge(nudle.BadgeRef):
    """Warn-variant badge."""

    variant: ClassVar[str] = "warn"


class DangerBadge(nudle.BadgeRef):
    """Danger-variant badge."""

    variant: ClassVar[str] = "danger"


class NeutralBadge(nudle.BadgeRef):
    """Neutral-variant badge."""

    variant: ClassVar[str] = "neutral"


class SubscribeCheckbox(nudle.CheckboxRef):
    """Pre-checked checkbox with a label."""

    label: ClassVar[str] = "subscribe to weekly digest"
    checked: ClassVar[bool] = True


class IndeterminateProgress(nudle.ProgressRef):
    """Indeterminate progress bar with a caption."""

    indeterminate: ClassVar[bool] = True
    caption: ClassVar[str] = "loading..."


# ---- Layout sections --------------------------------------------------------
# Sections are Shape subclasses. Child slots live INSIDE the Section body.
# Wire paths are: <PageName>.<section_slot>.<child_slot>


class StatRow(nudle.Row):
    """Inline strip: label, value, status badge."""

    gap: ClassVar[int] = 3
    align: ClassVar[str] = "center"

    stat_label = nudle.TextRef.slot()
    stat_value = nudle.TextRef.slot()
    stat_badge = OkBadge.slot()


class BadgeRow(nudle.Row):
    """Horizontal row of all five badge variants."""

    gap: ClassVar[int] = 2
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    info = InfoBadge.slot()
    ok = OkBadge.slot()
    warn = WarnBadge.slot()
    danger = DangerBadge.slot()
    neutral = NeutralBadge.slot()


class FeatureColumn(nudle.Column):
    """Tight vertical stack used inside the hero card."""

    gap: ClassVar[int] = 2

    feature_heading = nudle.HeadingRef.slot()
    feature_text = nudle.TextRef.slot()
    feature_badge = InfoBadge.slot()


class HeroCard(nudle.Container):
    """Card wrapping the FeatureColumn."""

    title: ClassVar[str] = "feature card"
    padding: ClassVar[str] = "lg"
    background: ClassVar[str] = "muted"
    border: ClassVar[str] = "card"

    feature_col = FeatureColumn.slot()


class MetricsRow(nudle.Row):
    """Three metric cells side by side."""

    gap: ClassVar[int] = 6
    align: ClassVar[str] = "center"

    uptime = nudle.TextRef.slot()
    latency = nudle.TextRef.slot()
    qps = nudle.TextRef.slot()


class MetricsCard(nudle.Container):
    """Card showing a row of metrics."""

    title: ClassVar[str] = "metrics"
    padding: ClassVar[str] = "md"
    border: ClassVar[str] = "hairline"
    background: ClassVar[str] = "none"

    metrics_row = MetricsRow.slot()


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    """Server-side ticker. Drives the live chart."""

    tick = nv.IntRef.slot()


# ---- Page -------------------------------------------------------------------


class Showcase(nudle.Page):
    """Every component, sectioned."""

    # intro
    title = nudle.HeadingRef.slot()
    intro = nudle.TextRef.slot()

    # text
    section_text = nudle.HeadingRef.slot()
    text_short = nudle.TextRef.slot()
    text_long = nudle.TextRef.slot()

    # markdown
    section_markdown = nudle.HeadingRef.slot()
    markdown_demo = nudle.MarkdownRef.slot()

    # badges
    section_badges = nudle.HeadingRef.slot()
    badge_info = InfoBadge.slot()
    badge_ok = OkBadge.slot()
    badge_warn = WarnBadge.slot()
    badge_danger = DangerBadge.slot()
    badge_neutral = NeutralBadge.slot()

    # image
    section_image = nudle.HeadingRef.slot()
    image_demo = nudle.ImageRef.slot()

    # link
    section_link = nudle.HeadingRef.slot()
    link_internal = nudle.LinkRef.slot()
    link_external = nudle.LinkRef.slot()

    # progress
    section_progress = nudle.HeadingRef.slot()
    progress_quarter = nudle.ProgressRef.slot()
    progress_half = nudle.ProgressRef.slot()
    progress_full = nudle.ProgressRef.slot()
    progress_loading = IndeterminateProgress.slot()

    # chart
    section_chart = nudle.HeadingRef.slot()
    chart_live = nudle.LineChart.slot()

    # table
    section_table = nudle.HeadingRef.slot()
    table_demo = nudle.TableRef.slot()

    # json viewer
    section_json = nudle.HeadingRef.slot()
    json_demo = nudle.JsonViewerRef.slot()

    # ---- layout section ----
    section_layout = nudle.HeadingRef.slot()
    layout_intro = nudle.TextRef.slot()

    # 1. inline strip: label + value + badge
    stat_layout_heading = nudle.HeadingRef.slot()
    stat_row = StatRow.slot()

    # 2. all-badges horizontal row
    badge_row_heading = nudle.HeadingRef.slot()
    badge_row = BadgeRow.slot()

    # 3. card with inner column (feature card)
    hero_heading = nudle.HeadingRef.slot()
    hero = HeroCard.slot()

    # 4. card with inner row of metrics
    metrics_heading = nudle.HeadingRef.slot()
    metrics_card = MetricsCard.slot()

    # inputs
    section_inputs = nudle.HeadingRef.slot()
    input_name = nudle.InputRef.slot()
    textarea_note = nudle.TextAreaRef.slot()
    select_mode = nudle.SelectRef.slot()
    slider_volume = nudle.SliderRef.slot()
    checkbox_subscribe = SubscribeCheckbox.slot()
    button_greet = nudle.ButtonRef.slot()
    button_reset = nudle.ButtonRef.slot()

    # echo target for the interactive section
    echo = nudle.TextRef.slot()


# ---- Index ------------------------------------------------------------------


class App(nudle.Index):
    """Browser entrypoint."""

    title = nudle.TitleRef.slot()
    nav = nudle.NavRef.slot()
    pages = nudle.Pages({"/": Showcase})


# ---- Static showcase --------------------------------------------------------

LONG_TEXT = (
    "Nudle is the UI fabric for Nu. Every cell on this page is a Ref, every "
    "mutation is a wire frame, and every renderer is a thin slice over a "
    "zustand store. Scroll through to see what is available."
)

LAYOUT_INTRO = (
    "Layout sections are Shape subclasses (Row, Column, Container). Child "
    "slots live inside the section body. The mount payload is recursive: "
    "each section ships its own fields list, and the renderer walks the "
    "tree. Below: a row, a card with a column inside, and a card with a "
    "row of three metrics."
)

MARKDOWN_BODY = """\
### markdown sample

**bold**, _italic_, `inline code`, and a [link](https://example.com).

- bullet one
- bullet two
- bullet three

```python
def hello():
    return "world"
```

> blockquote: rendered via react-markdown.
"""

DEMO_JSON = {
    "service": "nudle",
    "version": "0.1.0",
    "features": ["refs", "shapes", "layout", "json-viewer"],
    "limits": {"max_clients": 100, "max_payload_kb": 256},
    "live": True,
    "owner": None,
}


showcase_snapshot = nv.Snapshot(
    # intro
    Showcase.title.store("nudle component storybook")
    | Showcase.intro.store(LONG_TEXT)
    # text
    | Showcase.section_text.store("text")
    | Showcase.text_short.store("a short caption")
    | Showcase.text_long.store(
        "a longer paragraph showing how TextRef wraps. text is a display ref, "
        "server-owned, one write op carries the new value.",
    )
    # markdown
    | Showcase.section_markdown.store("markdown")
    | Showcase.markdown_demo.store(MARKDOWN_BODY)
    # badges
    | Showcase.section_badges.store("badges")
    | Showcase.badge_info.store_label("info")
    | Showcase.badge_ok.store_label("ok")
    | Showcase.badge_warn.store_label("warn")
    | Showcase.badge_danger.store_label("danger")
    | Showcase.badge_neutral.store_label("neutral")
    # image
    | Showcase.section_image.store("image")
    | Showcase.image_demo.store(
        "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d?w=400",
    )
    # link
    | Showcase.section_link.store("link")
    | Showcase.link_internal.store(label="docs (internal)", href="/docs")
    | Showcase.link_external.store(
        label="example.com",
        href="https://example.com",
        target="_blank",
    )
    # progress
    | Showcase.section_progress.store("progress")
    | Showcase.progress_quarter.store(0.25, caption="25%")
    | Showcase.progress_half.store(0.5, caption="50%")
    | Showcase.progress_full.store(1.0, caption="done")
    # chart heading
    | Showcase.section_chart.store("chart (live)")
    # table
    | Showcase.section_table.store("table")
    | Showcase.table_demo.store(
        {
            "columns": ["component", "kind", "owner"],
            "rows": [
                ["HeadingRef", "display", "server"],
                ["TextRef", "display", "server"],
                ["MarkdownRef", "display", "server"],
                ["BadgeRef", "display", "server"],
                ["ImageRef", "display", "server"],
                ["LinkRef", "display", "server"],
                ["ProgressRef", "display", "server"],
                ["LineChart", "display", "server"],
                ["TableRef", "display", "server"],
                ["JsonViewerRef", "display", "server"],
                ["InputRef", "input", "tab"],
                ["TextAreaRef", "input", "tab"],
                ["ButtonRef", "input", "tab"],
                ["CheckboxRef", "input", "tab"],
                ["SelectRef", "input", "tab"],
                ["SliderRef", "input", "tab"],
                ["Column", "section", "-"],
                ["Row", "section", "-"],
                ["Container", "section", "-"],
                ["TitleRef", "structural", "browser"],
                ["NavRef", "structural", "browser"],
            ],
        },
    )
    # json viewer
    | Showcase.section_json.store("json viewer")
    | Showcase.json_demo.store(
        DEMO_JSON,
        expand_depth=2,
        copyable=True,
    )
    # ---- layout ----
    | Showcase.section_layout.store("layout")
    | Showcase.layout_intro.store(LAYOUT_INTRO)
    # 1. stat row (children are nested INSIDE StatRow)
    | Showcase.stat_layout_heading.store_label("1. row: label, value, badge")
    | Showcase.stat_layout_heading.store_level(3)
    | StatRow.stat_label.store("uptime")
    | StatRow.stat_value.store("99.8%")
    | StatRow.stat_badge.store_label("healthy")
    # 2. badge row
    | Showcase.badge_row_heading.store_label("2. row of badges")
    | Showcase.badge_row_heading.store_level(3)
    | BadgeRow.info.store_label("info")
    | BadgeRow.ok.store_label("ok")
    | BadgeRow.warn.store_label("warn")
    | BadgeRow.danger.store_label("danger")
    | BadgeRow.neutral.store_label("neutral")
    # 3. hero card (column inside container)
    | Showcase.hero_heading.store_label("3. card with column inside")
    | Showcase.hero_heading.store_level(3)
    | FeatureColumn.feature_heading.store_label("composable refs")
    | FeatureColumn.feature_heading.store_level(4)
    | FeatureColumn.feature_text.store(
        "Subclass a Ref to pin defaults. The wire type the browser sees is "
        "the nearest packaged ancestor, so renderers resolve automatically.",
    )
    | FeatureColumn.feature_badge.store_label("nu native")
    # 4. metrics card (row inside container)
    | Showcase.metrics_heading.store_label("4. card with row of metrics")
    | Showcase.metrics_heading.store_level(3)
    | MetricsRow.uptime.store("uptime  99.8%")
    | MetricsRow.latency.store("p95  12 ms")
    | MetricsRow.qps.store("qps  1,240")
    # inputs
    | Showcase.section_inputs.store("inputs")
    | Showcase.input_name.store("world")
    | Showcase.echo.store("type a name and press greet."),
)


# Initialize SelectRef options + slider bounds via store calls.
options_snapshot = nv.Snapshot(
    Showcase.select_mode.store(
        {"options": ["draft", "review", "published"], "selected": "draft"},
    )
    | Showcase.slider_volume.store(
        {"min": 0, "max": 100, "step": 5, "value": 40, "label": "volume"},
    )
    | Showcase.textarea_note.store(""),
)


# ---- Live chart -------------------------------------------------------------

init_state = nv.Transaction(
    nu.IfDo(State.tick.missing(), State.tick.store(0)),
)


tick_worker = init_state >> nu.ForeverDo(
    nv.Transaction(State.tick.store(State.tick + 1)) >> TimeSleep(1.0),
)


tick_chart = nu.ForeverDo(
    nv.Snapshot(Showcase.chart_live.append(State.tick, State.tick)) >> AsyncSleep(1.0),
)


# ---- Buttons ----------------------------------------------------------------

on_greet = ReactForever(
    Showcase.button_greet.clicked(),
    nv.Snapshot(Showcase.echo.store(Showcase.input_name)),
)


on_reset = ReactForever(
    Showcase.button_reset.clicked(),
    nv.Snapshot(Showcase.echo.store("(reset)")),
)


# ---- Compose ----------------------------------------------------------------

ui = (
    App.title.store("nudle storybook")
    >> showcase_snapshot
    >> options_snapshot
    >> (tick_chart | on_greet | on_reset)
)


async def main() -> None:
    with rocksdb_storage_inmemory(".dbstorybook") as storage:
        ctx = nu.Context().bind(Navigator, Navigator(storage))

        threading.Thread(
            target=lambda: nu.runtime.execute(tick_worker, ctx),
            daemon=True,
        ).start()

        await nudle.serve(ui, ctx, host="127.0.0.1", port=8080, static_dir=WEB_DIST)


if __name__ == "__main__":
    asyncio.run(main())
