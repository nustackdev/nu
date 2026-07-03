#!/usr/bin/env python3
"""Storybook -- one-page tour of every nudle component, with variations.

One Index, one Page, sectioned by component family. Most cells are static
(snapshotted once on mount) so the variations are easy to read. The live
chart, sparkline, gauge, and the interactive section exercise the dynamic
interactions.

Run:
    nudle run examples/storybook.py
    # or, with hot reload:
    nudle dev examples/storybook.py

Then open http://127.0.0.1:8080.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, ClassVar

import nu
import nu.virtuals as nv
from nu import ReactForever
from nu.std.asyncio import sleep
from nu.virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator

from nu import nudle


if TYPE_CHECKING:
    from collections.abc import Iterator


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


# ---- alert variants ---------------------------------------------------------


class InfoAlert(nudle.AlertRef):
    """Info-variant alert."""

    variant: ClassVar[str] = "info"
    title: ClassVar[str] = "heads up"
    body: ClassVar[str] = "this is an info banner. nothing on fire."


class OkAlert(nudle.AlertRef):
    """Ok-variant alert."""

    variant: ClassVar[str] = "ok"
    title: ClassVar[str] = "all green"
    body: ClassVar[str] = "every job passed; no action needed."


class WarnAlert(nudle.AlertRef):
    """Warn-variant alert."""

    variant: ClassVar[str] = "warn"
    title: ClassVar[str] = "slow down"
    body: ClassVar[str] = "queue is backing up. check the workers."
    dismissible: ClassVar[bool] = True


class DangerAlert(nudle.AlertRef):
    """Danger-variant alert."""

    variant: ClassVar[str] = "danger"
    title: ClassVar[str] = "something broke"
    body: ClassVar[str] = "see the logs and try again."


# ---- input defaults ---------------------------------------------------------


class SizeRadioGroup(nudle.RadioGroupRef):
    """Size picker radio group."""

    options: ClassVar[list] = [
        {"value": "s", "label": "small"},
        {"value": "m", "label": "medium"},
        {"value": "l", "label": "large"},
    ]
    selected: ClassVar[str] = "m"
    orientation: ClassVar[str] = "horizontal"


class NotifySwitch(nudle.SwitchRef):
    """Notifications toggle."""

    label: ClassVar[str] = "notifications"
    default: ClassVar[bool] = True


class QtyNumberInput(nudle.NumberInputRef):
    """Quantity number input with bounds."""

    label: ClassVar[str] = "quantity"
    placeholder: ClassVar[str] = "0"
    min: ClassVar[float | None] = 0.0
    max: ClassVar[float | None] = 100.0
    step: ClassVar[float] = 1.0
    default: ClassVar[float] = 7.0


class BirthdayDatePicker(nudle.DatePickerRef):
    """Date picker with a min/max."""

    label: ClassVar[str] = "birthday"
    min: ClassVar[str] = "1900-01-01"
    max: ClassVar[str] = "2099-12-31"
    default: ClassVar[str] = "2000-01-01"


class TagsInput(nudle.TagInputRef):
    """Tag input pre-seeded with two tags."""

    label: ClassVar[str] = "tags"
    placeholder: ClassVar[str] = "add a tag..."
    value: ClassVar[list[str]] = ["nu", "nudle"]
    allow_duplicates: ClassVar[bool] = False


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


# ---- alerts column ----------------------------------------------------------


class AlertColumn(nudle.Column):
    """Vertical stack of all four alert variants."""

    gap: ClassVar[int] = 3

    info = InfoAlert.slot()
    ok = OkAlert.slot()
    warn = WarnAlert.slot()
    danger = DangerAlert.slot()


# ---- stats row --------------------------------------------------------------


class StatsRow(nudle.Row):
    """Three stat cells: up, down, flat."""

    gap: ClassVar[int] = 6
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    revenue = nudle.StatRef.slot()
    churn = nudle.StatRef.slot()
    sessions = nudle.StatRef.slot()


# ---- tabs section -----------------------------------------------------------


class DemoTabs(nudle.TabsRef):
    """Three-tab strip showing different content."""

    tabs: ClassVar[list] = [
        {"id": "overview", "label": "overview"},
        {"id": "details", "label": "details"},
        {"id": "extras", "label": "extras"},
    ]
    active: ClassVar[str] = "overview"

    overview = nudle.TextRef.slot()
    details = nudle.MarkdownRef.slot()
    extras_badge = InfoBadge.slot()


# ---- accordion section ------------------------------------------------------


class DemoAccordion(nudle.AccordionRef):
    """Three collapsible sections."""

    sections: ClassVar[list] = [
        {"id": "what", "label": "what is nudle"},
        {"id": "how", "label": "how does it wire"},
        {"id": "why", "label": "why this shape"},
    ]
    open: ClassVar[list[str]] = ["what"]
    multi: ClassVar[bool] = True

    what = nudle.TextRef.slot()
    how = nudle.MarkdownRef.slot()
    why = nudle.TextRef.slot()


# ---- card section -----------------------------------------------------------


class CardBody(nudle.Column):
    """Inner column inside the demo card."""

    gap: ClassVar[int] = 2

    line1 = nudle.TextRef.slot()
    line2 = nudle.TextRef.slot()
    badge = OkBadge.slot()


class DemoCard(nudle.CardRef):
    """Card with title, subtitle, footer wrapping a column body."""

    title: ClassVar[str] = "release notes"
    subtitle: ClassVar[str] = "v0.2.0 -- task 100"
    footer: ClassVar[str] = "updated just now"

    body = CardBody.slot()


# ---- modal section ----------------------------------------------------------


class DemoModal(nudle.Modal):
    """Dialog with a body text and a close button."""

    title: ClassVar[str] = "hello from a modal"
    dismissible: ClassVar[bool] = True

    body = nudle.TextRef.slot()
    close = nudle.ButtonRef.slot()


# ---- form section -----------------------------------------------------------


class FormNameField(nudle.FieldRef):
    """Name field wrapping a single input."""

    label: ClassVar[str] = "name"
    help: ClassVar[str] = "your full name"
    required: ClassVar[bool] = True

    input = nudle.InputRef.slot()


class FormAgeField(nudle.FieldRef):
    """Age field wrapping a single number input."""

    label: ClassVar[str] = "age"
    help: ClassVar[str] = "years on this rock"

    input = nudle.NumberInputRef.slot()


class FormFieldset(nudle.Fieldset):
    """Group of two labelled fields."""

    legend: ClassVar[str] = "your details"
    gap: ClassVar[str] = "md"

    name_field = FormNameField.slot()
    age_field = FormAgeField.slot()


class DemoForm(nudle.Form):
    """Form wrapping a fieldset and a submit button."""

    title: ClassVar[str] = "sign up"
    gap: ClassVar[int] = 4
    padding: ClassVar[int] = 0

    fields = FormFieldset.slot()
    submit = nudle.ButtonRef.slot()


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    """Server-side ticker. Drives the live chart, sparkline, gauge, bar."""

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

    # ---- divider between groups ----
    div_charts = nudle.DividerRef.slot()

    # charts heading group
    section_charts = nudle.HeadingRef.slot()

    # line chart (multi-series, live)
    section_chart = nudle.HeadingRef.slot()
    chart_live = nudle.LineChart.slot()

    # area chart (live, sliding window)
    section_area = nudle.HeadingRef.slot()
    area_demo = nudle.AreaChart.slot()

    # bar chart (categorical)
    section_bar = nudle.HeadingRef.slot()
    bar_demo = nudle.BarChart.slot()

    # pie chart
    section_pie = nudle.HeadingRef.slot()
    pie_demo = nudle.PieChart.slot()

    # sparkline (live, inline)
    section_sparkline = nudle.HeadingRef.slot()
    sparkline_demo = nudle.Sparkline.slot()

    # gauge (live)
    section_gauge = nudle.HeadingRef.slot()
    gauge_demo = nudle.GaugeRef.slot()

    # ---- divider before tables / json ----
    div_data = nudle.DividerRef.slot()

    # table
    section_table = nudle.HeadingRef.slot()
    table_demo = nudle.TableRef.slot()

    # json viewer
    section_json = nudle.HeadingRef.slot()
    json_demo = nudle.JsonViewerRef.slot()

    # ---- divider before display extras ----
    div_display = nudle.DividerRef.slot()

    # display extras heading group
    section_display = nudle.HeadingRef.slot()

    # alerts
    section_alerts = nudle.HeadingRef.slot()
    alerts = AlertColumn.slot()

    # stats
    section_stats = nudle.HeadingRef.slot()
    stats_row = StatsRow.slot()

    # dividers
    section_dividers = nudle.HeadingRef.slot()
    divider_labelled = nudle.DividerRef.slot()
    divider_plain = nudle.DividerRef.slot()

    # code block
    section_code = nudle.HeadingRef.slot()
    code_demo = nudle.CodeBlockRef.slot()

    # ---- divider before layout ----
    div_layout = nudle.DividerRef.slot()

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

    # 5. tabs
    tabs_heading = nudle.HeadingRef.slot()
    tabs_demo = DemoTabs.slot()

    # 6. accordion
    accordion_heading = nudle.HeadingRef.slot()
    accordion_demo = DemoAccordion.slot()

    # 7. card with title/subtitle/footer
    card_heading = nudle.HeadingRef.slot()
    card_demo = DemoCard.slot()

    # 8. modal
    modal_heading = nudle.HeadingRef.slot()
    modal_open_button = nudle.ButtonRef.slot()
    modal_demo = DemoModal.slot()

    # ---- divider before inputs ----
    div_inputs = nudle.DividerRef.slot()

    # inputs
    section_inputs = nudle.HeadingRef.slot()
    input_name = nudle.InputRef.slot()
    textarea_note = nudle.TextAreaRef.slot()
    select_mode = nudle.SelectRef.slot()
    slider_volume = nudle.SliderRef.slot()
    checkbox_subscribe = SubscribeCheckbox.slot()
    button_greet = nudle.ButtonRef.slot()
    button_reset = nudle.ButtonRef.slot()

    # input extras
    section_inputs_extra = nudle.HeadingRef.slot()
    radio_size = SizeRadioGroup.slot()
    switch_notify = NotifySwitch.slot()
    number_qty = QtyNumberInput.slot()
    date_birthday = BirthdayDatePicker.slot()
    tag_tags = TagsInput.slot()

    # ---- form ----
    section_form = nudle.HeadingRef.slot()
    form_demo = DemoForm.slot()
    form_echo = nudle.TextRef.slot()

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
    "Layout sections are Shape subclasses (Row, Column, Container, Card, "
    "Tabs, Accordion, Modal, Form, Fieldset, FieldRef). Child slots live "
    "inside the section body. The mount payload is recursive: each section "
    "ships its own fields list, and the renderer walks the tree."
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
    "version": "0.2.0",
    "features": ["refs", "shapes", "layout", "json-viewer", "charts", "form"],
    "limits": {"max_clients": 100, "max_payload_kb": 256},
    "live": True,
    "owner": None,
}

CODE_SNIPPET = """\
from nu import nudle

class Counter(nudle.Page):
    n = nudle.TextRef.slot()
    inc = nudle.ButtonRef.slot()
"""

TABS_OVERVIEW = (
    "tabs are a Section. each tab body is an ordinary child slot paired "
    "with the entry in tabs[] by index."
)

TABS_DETAILS_MD = """\
**details tab**

bodies stay mounted across switches, so local state is preserved.

- click a header to switch
- server gets a `notify` with the clicked id
- server may confirm via `store_active`
"""

ACCORDION_WHAT = (
    "nudle is the UI fabric for Nu. one Ref per cell, one wire frame per "
    "mutation, one zustand slice per Ref."
)

ACCORDION_HOW_MD = """\
**how it wires**

- python declares Shapes and Refs
- server mounts a Page; tab receives a recursive payload
- writes flow server -> tab, notifies flow tab -> server
"""

ACCORDION_WHY = (
    "one source of truth. one rendering model. one place to look when "
    "something goes weird."
)

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
    # ---- charts group ----
    | Showcase.section_charts.store("charts")
    # line chart heading
    | Showcase.section_chart.store("line chart (live, multi-series)")
    | Showcase.chart_live.store(
        x_label="tick",
        y_label="value",
        show_legend=True,
        palette=["#2563eb", "#16a34a"],
        series=[
            {"name": "alpha", "points": [], "color": "#2563eb"},
            {"name": "beta", "points": [], "color": "#16a34a"},
        ],
    )
    # area chart
    | Showcase.section_area.store("area chart (live, sliding window)")
    | Showcase.area_demo.store(
        x_label="tick",
        y_label="value",
        series=["value"],
        colors=["#7c3aed"],
        max_points=40,
    )
    # bar chart
    | Showcase.section_bar.store("bar chart (categorical)")
    | Showcase.bar_demo.store(
        bars=[
            ["jan", 12],
            ["feb", 19],
            ["mar", 7],
            ["apr", 24],
            ["may", 15],
        ],
        x_label="month",
        y_label="count",
        color="#16a34a",
    )
    # pie chart
    | Showcase.section_pie.store("pie chart")
    | Showcase.pie_demo.store(
        slices=[
            ["rent", 1200],
            ["food", 450],
            ["transit", 80],
            ["other", 220],
        ],
        inner_radius=0.45,
        total_label="monthly",
    )
    # sparkline
    | Showcase.section_sparkline.store("sparkline (live)")
    | Showcase.sparkline_demo.store([], color="#dc2626", height=40, max_points=30)
    # gauge
    | Showcase.section_gauge.store("gauge (live)")
    | Showcase.gauge_demo.store(0.0, caption="tick %", variant="ok")
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
                ["AreaChart", "display", "server"],
                ["BarChart", "display", "server"],
                ["PieChart", "display", "server"],
                ["Sparkline", "display", "server"],
                ["GaugeRef", "display", "server"],
                ["AlertRef", "display", "server"],
                ["StatRef", "display", "server"],
                ["DividerRef", "display", "server"],
                ["CodeBlockRef", "display", "server"],
                ["TableRef", "display", "server"],
                ["JsonViewerRef", "display", "server"],
                ["InputRef", "input", "tab"],
                ["TextAreaRef", "input", "tab"],
                ["ButtonRef", "input", "tab"],
                ["CheckboxRef", "input", "tab"],
                ["SelectRef", "input", "tab"],
                ["SliderRef", "input", "tab"],
                ["RadioGroupRef", "input", "tab"],
                ["SwitchRef", "input", "tab"],
                ["NumberInputRef", "input", "tab"],
                ["DatePickerRef", "input", "tab"],
                ["TagInputRef", "input", "tab"],
                ["Column", "section", "-"],
                ["Row", "section", "-"],
                ["Container", "section", "-"],
                ["CardRef", "section", "-"],
                ["TabsRef", "section", "-"],
                ["AccordionRef", "section", "-"],
                ["Modal", "section", "-"],
                ["Form", "section", "-"],
                ["Fieldset", "section", "-"],
                ["FieldRef", "section", "-"],
                ["TitleRef", "structural", "browser"],
                ["NavRef", "structural", "browser"],
            ],
            "sort_column": "component",
            "sort_direction": "asc",
        },
    )
    # json viewer
    | Showcase.section_json.store("json viewer")
    | Showcase.json_demo.store(
        DEMO_JSON,
        expand_depth=2,
        copyable=True,
    )
    # ---- display extras group ----
    | Showcase.section_display.store("display extras")
    # alerts
    | Showcase.section_alerts.store("alerts")
    # stats (row pinned below)
    | Showcase.section_stats.store("stats")
    | StatsRow.revenue.store_label("revenue")
    | StatsRow.revenue.store_value("$42,108")
    | StatsRow.revenue.store_delta("+12.4%")
    | StatsRow.revenue.store_trend("up")
    | StatsRow.churn.store_label("churn")
    | StatsRow.churn.store_value("2.1%")
    | StatsRow.churn.store_delta("-0.3pp")
    | StatsRow.churn.store_trend("down")
    | StatsRow.sessions.store_label("sessions")
    | StatsRow.sessions.store_value("1,240")
    | StatsRow.sessions.store_delta("flat")
    | StatsRow.sessions.store_trend("flat")
    # dividers
    | Showcase.section_dividers.store("dividers")
    | Showcase.divider_labelled.store("section break", align="center")
    | Showcase.divider_plain.store("")
    # code block
    | Showcase.section_code.store("code block")
    | Showcase.code_demo.store({"code": CODE_SNIPPET, "language": "python"})
    # ---- layout ----
    | Showcase.section_layout.store("layout")
    | Showcase.layout_intro.store(LAYOUT_INTRO)
    # 1. stat row
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
    # 3. hero card
    | Showcase.hero_heading.store_label("3. container with column inside")
    | Showcase.hero_heading.store_level(3)
    | FeatureColumn.feature_heading.store_label("composable refs")
    | FeatureColumn.feature_heading.store_level(4)
    | FeatureColumn.feature_text.store(
        "Subclass a Ref to pin defaults. The wire type the browser sees is "
        "the nearest packaged ancestor, so renderers resolve automatically.",
    )
    | FeatureColumn.feature_badge.store_label("nu native")
    # 4. metrics card
    | Showcase.metrics_heading.store_label("4. container with row of metrics")
    | Showcase.metrics_heading.store_level(3)
    | MetricsRow.uptime.store("uptime  99.8%")
    | MetricsRow.latency.store("p95  12 ms")
    | MetricsRow.qps.store("qps  1,240")
    # 5. tabs
    | Showcase.tabs_heading.store_label("5. tabs")
    | Showcase.tabs_heading.store_level(3)
    | DemoTabs.overview.store(TABS_OVERVIEW)
    | DemoTabs.details.store(TABS_DETAILS_MD)
    | DemoTabs.extras_badge.store_label("just a badge in here")
    # 6. accordion
    | Showcase.accordion_heading.store_label("6. accordion")
    | Showcase.accordion_heading.store_level(3)
    | DemoAccordion.what.store(ACCORDION_WHAT)
    | DemoAccordion.how.store(ACCORDION_HOW_MD)
    | DemoAccordion.why.store(ACCORDION_WHY)
    # 7. card
    | Showcase.card_heading.store_label("7. card with title / subtitle / footer")
    | Showcase.card_heading.store_level(3)
    | CardBody.line1.store("a card wraps a body Section.")
    | CardBody.line2.store(
        "title, subtitle, and footer are plain strings on the CardRef itself.",
    )
    | CardBody.badge.store_label("composable")
    # 8. modal
    | Showcase.modal_heading.store_label("8. modal")
    | Showcase.modal_heading.store_level(3)
    | Showcase.modal_open_button.store(label="open modal")
    | DemoModal.body.store(
        "this is a modal body. server controls visibility; tab notifies on "
        "user dismissal.",
    )
    | DemoModal.close.store(label="close")
    # inputs
    | Showcase.section_inputs.store("inputs")
    | Showcase.input_name.store("world")
    | Showcase.echo.store("type a name and press greet.")
    # input extras
    | Showcase.section_inputs_extra.store("inputs (extras)")
    # form
    | Showcase.section_form.store("form")
    | Showcase.form_demo.submit.store(label="submit")
    | Showcase.form_echo.store("submit the form to see the values echoed here."),
)


# Initialize SelectRef options + slider bounds + textarea via store calls.
options_snapshot = nv.Snapshot(
    Showcase.select_mode.store(
        {"options": ["draft", "review", "published"], "selected": "draft"},
    )
    | Showcase.slider_volume.store(
        {"min": 0, "max": 100, "step": 5, "value": 40, "label": "volume"},
    )
    | Showcase.textarea_note.store("")
    # form children defaults: name input and age number input
    | FormNameField.input.store("ada")
    | FormAgeField.input.store_value(30),
)


# ---- Live tickers -----------------------------------------------------------

init_state = nv.Transaction(
    nu.IfDo(State.tick.missing(), State.tick.store(0)),
)


ticker_bg = init_state >> nu.ForeverDo(
    nv.Transaction(State.tick.store(State.tick + 1)) >> sleep(1.0),
)


# Multi-series line chart: alpha increases by tick, beta by tick * 0.5 (offset).
tick_chart = nu.ForeverDo(
    nv.Snapshot(
        Showcase.chart_live.append_series("alpha", State.tick, State.tick)
        | Showcase.chart_live.append_series("beta", State.tick, State.tick + 5),
    )
    >> sleep(1.0),
)


tick_area = nu.ForeverDo(
    nv.Snapshot(Showcase.area_demo.append(State.tick, State.tick)) >> sleep(1.0),
)


tick_sparkline = nu.ForeverDo(
    nv.Snapshot(Showcase.sparkline_demo.append(State.tick, State.tick))
    >> sleep(1.0),
)


# Gauge: tick % 100 / 100 -> [0, 1].
tick_gauge = nu.ForeverDo(
    nv.Snapshot(Showcase.gauge_demo.store_value((State.tick % 100) / 100.0))
    >> sleep(1.0),
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


# Modal open / close
on_modal_open = ReactForever(
    Showcase.modal_open_button.clicked(),
    nv.Snapshot(Showcase.modal_demo.store_open(True)),
)


on_modal_close = ReactForever(
    DemoModal.close.clicked(),
    nv.Snapshot(Showcase.modal_demo.store_open(False)),
)


# Form submit: echo name + age into form_echo.
on_form_submit = ReactForever(
    Showcase.form_demo.submit.clicked(),
    nv.Snapshot(
        Showcase.form_echo.store(FormNameField.input),
    ),
)


# ---- Compose ----------------------------------------------------------------

app = (
    App.title.store("nudle storybook")
    >> showcase_snapshot
    >> options_snapshot
    >> (
        ticker_bg
        | tick_chart
        | tick_area
        | tick_sparkline
        | tick_gauge
        | on_greet
        | on_reset
        | on_modal_open
        | on_modal_close
        | on_form_submit
    )
)


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open rocksdb storage and yield a bound Context."""
    with rocksdb_storage_inmemory(".dbstorybook") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
