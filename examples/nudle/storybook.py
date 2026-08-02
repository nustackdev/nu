"""Storybook -- one-page tour of every nudle component, with variations.

One Index, one Page, sectioned by component family. Most cells are static
(snapshotted once on mount) so the variations are easy to read. The live
chart, sparkline, gauge, and the interactive section exercise the dynamic
interactions.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import nu
import nu.virtuals as nv
from nu import ReactForever


# ---- Ref customizations -----------------------------------------------------
# Per-instance defaults are class-level. Subclass to pin a default; the wire
# type the browser sees is still the nearest packaged ancestor's name (see
# page._wire_type), so the renderer resolves automatically.


class InfoBadge(nu.ui.BadgeRef):
    """Info-variant badge."""

    variant: ClassVar[str] = "info"


class OkBadge(nu.ui.BadgeRef):
    """Ok-variant badge."""

    variant: ClassVar[str] = "ok"


class WarnBadge(nu.ui.BadgeRef):
    """Warn-variant badge."""

    variant: ClassVar[str] = "warn"


class DangerBadge(nu.ui.BadgeRef):
    """Danger-variant badge."""

    variant: ClassVar[str] = "danger"


class NeutralBadge(nu.ui.BadgeRef):
    """Neutral-variant badge."""

    variant: ClassVar[str] = "neutral"


class SubscribeCheckbox(nu.ui.CheckboxRef):
    """Pre-checked checkbox with a label."""

    label: ClassVar[str] = "subscribe to weekly digest"
    checked: ClassVar[bool] = True


class IndeterminateProgress(nu.ui.ProgressRef):
    """Indeterminate progress bar with a caption."""

    indeterminate: ClassVar[bool] = True
    caption: ClassVar[str] = "loading..."


# ---- alert variants ---------------------------------------------------------


class InfoAlert(nu.ui.AlertRef):
    """Info-variant alert."""

    variant: ClassVar[str] = "info"
    title: ClassVar[str] = "heads up"
    body: ClassVar[str] = "this is an info banner. nothing on fire."


class OkAlert(nu.ui.AlertRef):
    """Ok-variant alert."""

    variant: ClassVar[str] = "ok"
    title: ClassVar[str] = "all green"
    body: ClassVar[str] = "every job passed; no action needed."


class WarnAlert(nu.ui.AlertRef):
    """Warn-variant alert."""

    variant: ClassVar[str] = "warn"
    title: ClassVar[str] = "slow down"
    body: ClassVar[str] = "queue is backing up. check the workers."
    dismissible: ClassVar[bool] = True


class DangerAlert(nu.ui.AlertRef):
    """Danger-variant alert."""

    variant: ClassVar[str] = "danger"
    title: ClassVar[str] = "something broke"
    body: ClassVar[str] = "see the logs and try again."


# ---- input defaults ---------------------------------------------------------


class SizeRadioGroup(nu.ui.RadioGroupRef):
    """Size picker radio group."""

    options: ClassVar[list] = [
        {"value": "s", "label": "small"},
        {"value": "m", "label": "medium"},
        {"value": "l", "label": "large"},
    ]
    selected: ClassVar[str] = "m"
    orientation: ClassVar[str] = "horizontal"


class NotifySwitch(nu.ui.SwitchRef):
    """Notifications toggle."""

    label: ClassVar[str] = "notifications"
    default: ClassVar[bool] = True


class QtyNumberInput(nu.ui.NumberInputRef):
    """Quantity number input with bounds."""

    label: ClassVar[str] = "quantity"
    placeholder: ClassVar[str] = "0"
    min: ClassVar[float | None] = 0.0
    max: ClassVar[float | None] = 100.0
    step: ClassVar[float] = 1.0
    default: ClassVar[float] = 7.0


class BirthdayDatePicker(nu.ui.DatePickerRef):
    """Date picker with a min/max."""

    label: ClassVar[str] = "birthday"
    min: ClassVar[str] = "1900-01-01"
    max: ClassVar[str] = "2099-12-31"
    default: ClassVar[str] = "2000-01-01"


class TagsInput(nu.ui.TagInputRef):
    """Tag input pre-seeded with two tags."""

    label: ClassVar[str] = "tags"
    placeholder: ClassVar[str] = "add a tag..."
    value: ClassVar[list[str]] = ["nu", "nudle"]
    allow_duplicates: ClassVar[bool] = False


# ---- Layout sections --------------------------------------------------------
# Sections are Shape subclasses. Child slots live INSIDE the Section body.
# Wire paths are: <PageName>.<section_slot>.<child_slot>


class StatRow(nu.ui.Row):
    """Inline strip: label, value, status badge."""

    gap: ClassVar[int] = 3
    align: ClassVar[str] = "center"

    stat_label = nu.ui.TextRef.slot()
    stat_value = nu.ui.TextRef.slot()
    stat_badge = OkBadge.slot()


class BadgeRow(nu.ui.Row):
    """Horizontal row of all five badge variants."""

    gap: ClassVar[int] = 2
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    info = InfoBadge.slot()
    ok = OkBadge.slot()
    warn = WarnBadge.slot()
    danger = DangerBadge.slot()
    neutral = NeutralBadge.slot()


class FeatureColumn(nu.ui.Column):
    """Tight vertical stack used inside the hero card."""

    gap: ClassVar[int] = 2

    feature_heading = nu.ui.HeadingRef.slot()
    feature_text = nu.ui.TextRef.slot()
    feature_badge = InfoBadge.slot()


class HeroCard(nu.ui.Container):
    """Card wrapping the FeatureColumn."""

    title: ClassVar[str] = "feature card"
    padding: ClassVar[str] = "lg"
    background: ClassVar[str] = "muted"
    border: ClassVar[str] = "card"

    feature_col = FeatureColumn.slot()


class MetricsRow(nu.ui.Row):
    """Three metric cells side by side."""

    gap: ClassVar[int] = 6
    align: ClassVar[str] = "center"

    uptime = nu.ui.TextRef.slot()
    latency = nu.ui.TextRef.slot()
    qps = nu.ui.TextRef.slot()


class MetricsCard(nu.ui.Container):
    """Card showing a row of metrics."""

    title: ClassVar[str] = "metrics"
    padding: ClassVar[str] = "md"
    border: ClassVar[str] = "hairline"
    background: ClassVar[str] = "none"

    metrics_row = MetricsRow.slot()


# ---- alerts column ----------------------------------------------------------


class AlertColumn(nu.ui.Column):
    """Vertical stack of all four alert variants."""

    gap: ClassVar[int] = 3

    info = InfoAlert.slot()
    ok = OkAlert.slot()
    warn = WarnAlert.slot()
    danger = DangerAlert.slot()


# ---- stats row --------------------------------------------------------------


class StatsRow(nu.ui.Row):
    """Three stat cells: up, down, flat."""

    gap: ClassVar[int] = 6
    align: ClassVar[str] = "center"
    wrap: ClassVar[bool] = True

    revenue = nu.ui.StatRef.slot()
    churn = nu.ui.StatRef.slot()
    sessions = nu.ui.StatRef.slot()


# ---- tabs section -----------------------------------------------------------


class DemoTabs(nu.ui.Tabs):
    """Three-tab strip showing different content."""

    tabs: ClassVar[list] = [
        {"id": "overview", "label": "overview"},
        {"id": "details", "label": "details"},
        {"id": "extras", "label": "extras"},
    ]
    active: ClassVar[str] = "overview"

    overview = nu.ui.TextRef.slot()
    details = nu.ui.MarkdownRef.slot()
    extras_badge = InfoBadge.slot()


# ---- accordion section ------------------------------------------------------


class DemoAccordion(nu.ui.Accordion):
    """Three collapsible sections."""

    sections: ClassVar[list] = [
        {"id": "what", "label": "what is nudle"},
        {"id": "how", "label": "how does it wire"},
        {"id": "why", "label": "why this shape"},
    ]
    open: ClassVar[list[str]] = ["what"]
    multi: ClassVar[bool] = True

    what = nu.ui.TextRef.slot()
    how = nu.ui.MarkdownRef.slot()
    why = nu.ui.TextRef.slot()


# ---- card section -----------------------------------------------------------


class CardBody(nu.ui.Column):
    """Inner column inside the demo card."""

    gap: ClassVar[int] = 2

    line1 = nu.ui.TextRef.slot()
    line2 = nu.ui.TextRef.slot()
    badge = OkBadge.slot()


class DemoCard(nu.ui.Card):
    """Card with title, subtitle, footer wrapping a column body."""

    title: ClassVar[str] = "release notes"
    subtitle: ClassVar[str] = "v0.2.0 -- task 100"
    footer: ClassVar[str] = "updated just now"

    body = CardBody.slot()


# ---- modal section ----------------------------------------------------------


class DemoModal(nu.ui.Modal):
    """Dialog with a body text and a close button."""

    title: ClassVar[str] = "hello from a modal"
    dismissible: ClassVar[bool] = True

    body = nu.ui.TextRef.slot()
    close = nu.ui.ButtonRef.slot()


# ---- form section -----------------------------------------------------------


class FormNameField(nu.ui.Field):
    """Name field wrapping a single input."""

    label: ClassVar[str] = "name"
    help: ClassVar[str] = "your full name"
    required: ClassVar[bool] = True

    input = nu.ui.InputRef.slot()


class FormAgeField(nu.ui.Field):
    """Age field wrapping a single number input."""

    label: ClassVar[str] = "age"
    help: ClassVar[str] = "years on this rock"

    input = nu.ui.NumberInputRef.slot()


class FormFieldset(nu.ui.Fieldset):
    """Group of two labelled fields."""

    legend: ClassVar[str] = "your details"
    gap: ClassVar[str] = "md"

    name_field = FormNameField.slot()
    age_field = FormAgeField.slot()


class DemoForm(nu.ui.Form):
    """Form wrapping a fieldset and a submit button."""

    title: ClassVar[str] = "sign up"
    gap: ClassVar[int] = 4
    padding: ClassVar[int] = 0

    fields = FormFieldset.slot()
    submit = nu.ui.ButtonRef.slot()


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    """Server-side ticker. Drives the live chart, sparkline, gauge, bar."""

    tick = nv.IntRef.slot()


# ---- Page -------------------------------------------------------------------


class Showcase(nu.ui.Page):
    """Every component, sectioned."""

    # intro
    title = nu.ui.HeadingRef.slot()
    intro = nu.ui.TextRef.slot()

    # text
    section_text = nu.ui.HeadingRef.slot()
    text_short = nu.ui.TextRef.slot()
    text_long = nu.ui.TextRef.slot()

    # markdown
    section_markdown = nu.ui.HeadingRef.slot()
    markdown_demo = nu.ui.MarkdownRef.slot()

    # badges
    section_badges = nu.ui.HeadingRef.slot()
    badge_info = InfoBadge.slot()
    badge_ok = OkBadge.slot()
    badge_warn = WarnBadge.slot()
    badge_danger = DangerBadge.slot()
    badge_neutral = NeutralBadge.slot()

    # image
    section_image = nu.ui.HeadingRef.slot()
    image_demo = nu.ui.ImageRef.slot()

    # link
    section_link = nu.ui.HeadingRef.slot()
    link_internal = nu.ui.LinkRef.slot()
    link_external = nu.ui.LinkRef.slot()

    # progress
    section_progress = nu.ui.HeadingRef.slot()
    progress_quarter = nu.ui.ProgressRef.slot()
    progress_half = nu.ui.ProgressRef.slot()
    progress_full = nu.ui.ProgressRef.slot()
    progress_loading = IndeterminateProgress.slot()

    # ---- divider between groups ----
    div_charts = nu.ui.DividerRef.slot()

    # charts heading group
    section_charts = nu.ui.HeadingRef.slot()

    # line chart (multi-series, live)
    section_chart = nu.ui.HeadingRef.slot()
    chart_live = nu.ui.LineChart.slot()

    # area chart (live, sliding window)
    section_area = nu.ui.HeadingRef.slot()
    area_demo = nu.ui.AreaChart.slot()

    # bar chart (categorical)
    section_bar = nu.ui.HeadingRef.slot()
    bar_demo = nu.ui.BarChart.slot()

    # pie chart
    section_pie = nu.ui.HeadingRef.slot()
    pie_demo = nu.ui.PieChart.slot()

    # sparkline (live, inline)
    section_sparkline = nu.ui.HeadingRef.slot()
    sparkline_demo = nu.ui.Sparkline.slot()

    # gauge (live)
    section_gauge = nu.ui.HeadingRef.slot()
    gauge_demo = nu.ui.GaugeRef.slot()

    # ---- divider before tables / json ----
    div_data = nu.ui.DividerRef.slot()

    # table
    section_table = nu.ui.HeadingRef.slot()
    table_demo = nu.ui.TableRef.slot()

    # json viewer
    section_json = nu.ui.HeadingRef.slot()
    json_demo = nu.ui.JsonViewerRef.slot()

    # ---- divider before display extras ----
    div_display = nu.ui.DividerRef.slot()

    # display extras heading group
    section_display = nu.ui.HeadingRef.slot()

    # alerts
    section_alerts = nu.ui.HeadingRef.slot()
    alerts = AlertColumn.slot()

    # stats
    section_stats = nu.ui.HeadingRef.slot()
    stats_row = StatsRow.slot()

    # dividers
    section_dividers = nu.ui.HeadingRef.slot()
    divider_labelled = nu.ui.DividerRef.slot()
    divider_plain = nu.ui.DividerRef.slot()

    # code block
    section_code = nu.ui.HeadingRef.slot()
    code_demo = nu.ui.CodeBlockRef.slot()

    # ---- divider before layout ----
    div_layout = nu.ui.DividerRef.slot()

    # ---- layout section ----
    section_layout = nu.ui.HeadingRef.slot()
    layout_intro = nu.ui.TextRef.slot()

    # 1. inline strip: label + value + badge
    stat_layout_heading = nu.ui.HeadingRef.slot()
    stat_row = StatRow.slot()

    # 2. all-badges horizontal row
    badge_row_heading = nu.ui.HeadingRef.slot()
    badge_row = BadgeRow.slot()

    # 3. card with inner column (feature card)
    hero_heading = nu.ui.HeadingRef.slot()
    hero = HeroCard.slot()

    # 4. card with inner row of metrics
    metrics_heading = nu.ui.HeadingRef.slot()
    metrics_card = MetricsCard.slot()

    # 5. tabs
    tabs_heading = nu.ui.HeadingRef.slot()
    tabs_demo = DemoTabs.slot()

    # 6. accordion
    accordion_heading = nu.ui.HeadingRef.slot()
    accordion_demo = DemoAccordion.slot()

    # 7. card with title/subtitle/footer
    card_heading = nu.ui.HeadingRef.slot()
    card_demo = DemoCard.slot()

    # 8. modal
    modal_heading = nu.ui.HeadingRef.slot()
    modal_open_button = nu.ui.ButtonRef.slot()
    modal_demo = DemoModal.slot()

    # ---- divider before inputs ----
    div_inputs = nu.ui.DividerRef.slot()

    # inputs
    section_inputs = nu.ui.HeadingRef.slot()
    input_name = nu.ui.InputRef.slot()
    textarea_note = nu.ui.TextAreaRef.slot()
    select_mode = nu.ui.SelectRef.slot()
    slider_volume = nu.ui.SliderRef.slot()
    checkbox_subscribe = SubscribeCheckbox.slot()
    button_greet = nu.ui.ButtonRef.slot()
    button_reset = nu.ui.ButtonRef.slot()

    # input extras
    section_inputs_extra = nu.ui.HeadingRef.slot()
    radio_size = SizeRadioGroup.slot()
    switch_notify = NotifySwitch.slot()
    number_qty = QtyNumberInput.slot()
    date_birthday = BirthdayDatePicker.slot()
    tag_tags = TagsInput.slot()

    # ---- form ----
    section_form = nu.ui.HeadingRef.slot()
    form_demo = DemoForm.slot()
    form_echo = nu.ui.TextRef.slot()

    # echo target for the interactive section
    echo = nu.ui.TextRef.slot()


# ---- Index ------------------------------------------------------------------


class App(nu.ui.Index):
    """Browser entrypoint."""

    title = nu.ui.TitleRef.slot()
    nav = nu.ui.NavRef.slot()
    pages = nu.ui.Pages({"/": Showcase})


# ---- Static showcase --------------------------------------------------------

LONG_TEXT = (
    "Nudle is the UI fabric for Nu. Every cell on this page is a Ref, every "
    "mutation is a wire frame, and every renderer is a thin slice over a "
    "zustand store. Scroll through to see what is available."
)

LAYOUT_INTRO = (
    "Layout sections are Shape subclasses (Row, Column, Container, Card, "
    "Tabs, Accordion, Modal, Form, Fieldset, Field). Child slots live "
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

class Counter(nu.ui.Page):
    n = nu.ui.TextRef.slot()
    inc = nu.ui.ButtonRef.slot()
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
- server may confirm via `set_active`
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
    "one source of truth. one rendering model. one place to look when something goes weird."
)

showcase_snapshot = nv.Snapshot(
    # intro
    Showcase.title.set("nudle component storybook")
    | Showcase.intro.set(LONG_TEXT)
    # text
    | Showcase.section_text.set("text")
    | Showcase.text_short.set("a short caption")
    | Showcase.text_long.set(
        "a longer paragraph showing how TextRef wraps. text is a display ref, "
        "server-owned, one write op carries the new value.",
    )
    # markdown
    | Showcase.section_markdown.set("markdown")
    | Showcase.markdown_demo.set(MARKDOWN_BODY)
    # badges
    | Showcase.section_badges.set("badges")
    | Showcase.badge_info.set_label("info")
    | Showcase.badge_ok.set_label("ok")
    | Showcase.badge_warn.set_label("warn")
    | Showcase.badge_danger.set_label("danger")
    | Showcase.badge_neutral.set_label("neutral")
    # image
    | Showcase.section_image.set("image")
    | Showcase.image_demo.set(
        "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d?w=400",
    )
    # link
    | Showcase.section_link.set("link")
    | Showcase.link_internal.set(label="docs (internal)", href="/docs")
    | Showcase.link_external.set(
        label="example.com",
        href="https://example.com",
        target="_blank",
    )
    # progress
    | Showcase.section_progress.set("progress")
    | Showcase.progress_quarter.set(0.25, caption="25%")
    | Showcase.progress_half.set(0.5, caption="50%")
    | Showcase.progress_full.set(1.0, caption="done")
    # ---- charts group ----
    | Showcase.section_charts.set("charts")
    # line chart heading
    | Showcase.section_chart.set("line chart (live, multi-series)")
    | Showcase.chart_live.set(
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
    | Showcase.section_area.set("area chart (live, sliding window)")
    | Showcase.area_demo.set(
        x_label="tick",
        y_label="value",
        series=["value"],
        colors=["#7c3aed"],
        max_points=40,
    )
    # bar chart
    | Showcase.section_bar.set("bar chart (categorical)")
    | Showcase.bar_demo.set(
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
    | Showcase.section_pie.set("pie chart")
    | Showcase.pie_demo.set(
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
    | Showcase.section_sparkline.set("sparkline (live)")
    | Showcase.sparkline_demo.set([], color="#dc2626", height=40, max_points=30)
    # gauge
    | Showcase.section_gauge.set("gauge (live)")
    | Showcase.gauge_demo.set(0.0, caption="tick %", variant="ok")
    # table
    | Showcase.section_table.set("table")
    | Showcase.table_demo.set(
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
                ["Card", "section", "-"],
                ["Tabs", "section", "-"],
                ["Accordion", "section", "-"],
                ["Modal", "section", "-"],
                ["Form", "section", "-"],
                ["Fieldset", "section", "-"],
                ["Field", "section", "-"],
                ["TitleRef", "structural", "browser"],
                ["NavRef", "structural", "browser"],
            ],
            "sort_column": "component",
            "sort_direction": "asc",
        },
    )
    # json viewer
    | Showcase.section_json.set("json viewer")
    | Showcase.json_demo.set(
        DEMO_JSON,
        expand_depth=2,
        copyable=True,
    )
    # ---- display extras group ----
    | Showcase.section_display.set("display extras")
    # alerts
    | Showcase.section_alerts.set("alerts")
    # stats (row pinned below)
    | Showcase.section_stats.set("stats")
    | StatsRow.revenue.set_label("revenue")
    | StatsRow.revenue.set_value("$42,108")
    | StatsRow.revenue.set_delta("+12.4%")
    | StatsRow.revenue.set_trend("up")
    | StatsRow.churn.set_label("churn")
    | StatsRow.churn.set_value("2.1%")
    | StatsRow.churn.set_delta("-0.3pp")
    | StatsRow.churn.set_trend("down")
    | StatsRow.sessions.set_label("sessions")
    | StatsRow.sessions.set_value("1,240")
    | StatsRow.sessions.set_delta("flat")
    | StatsRow.sessions.set_trend("flat")
    # dividers
    | Showcase.section_dividers.set("dividers")
    | Showcase.divider_labelled.set("section break", align="center")
    | Showcase.divider_plain.set("")
    # code block
    | Showcase.section_code.set("code block")
    | Showcase.code_demo.set({"code": CODE_SNIPPET, "language": "python"})
    # ---- layout ----
    | Showcase.section_layout.set("layout")
    | Showcase.layout_intro.set(LAYOUT_INTRO)
    # 1. stat row
    | Showcase.stat_layout_heading.set_label("1. row: label, value, badge")
    | Showcase.stat_layout_heading.set_level(3)
    | StatRow.stat_label.set("uptime")
    | StatRow.stat_value.set("99.8%")
    | StatRow.stat_badge.set_label("healthy")
    # 2. badge row
    | Showcase.badge_row_heading.set_label("2. row of badges")
    | Showcase.badge_row_heading.set_level(3)
    | BadgeRow.info.set_label("info")
    | BadgeRow.ok.set_label("ok")
    | BadgeRow.warn.set_label("warn")
    | BadgeRow.danger.set_label("danger")
    | BadgeRow.neutral.set_label("neutral")
    # 3. hero card
    | Showcase.hero_heading.set_label("3. container with column inside")
    | Showcase.hero_heading.set_level(3)
    | FeatureColumn.feature_heading.set_label("composable refs")
    | FeatureColumn.feature_heading.set_level(4)
    | FeatureColumn.feature_text.set(
        "Subclass a Ref to pin defaults. The wire type the browser sees is "
        "the nearest packaged ancestor, so renderers resolve automatically.",
    )
    | FeatureColumn.feature_badge.set_label("nu native")
    # 4. metrics card
    | Showcase.metrics_heading.set_label("4. container with row of metrics")
    | Showcase.metrics_heading.set_level(3)
    | MetricsRow.uptime.set("uptime  99.8%")
    | MetricsRow.latency.set("p95  12 ms")
    | MetricsRow.qps.set("qps  1,240")
    # 5. tabs
    | Showcase.tabs_heading.set_label("5. tabs")
    | Showcase.tabs_heading.set_level(3)
    | DemoTabs.overview.set(TABS_OVERVIEW)
    | DemoTabs.details.set(TABS_DETAILS_MD)
    | DemoTabs.extras_badge.set_label("just a badge in here")
    # 6. accordion
    | Showcase.accordion_heading.set_label("6. accordion")
    | Showcase.accordion_heading.set_level(3)
    | DemoAccordion.what.set(ACCORDION_WHAT)
    | DemoAccordion.how.set(ACCORDION_HOW_MD)
    | DemoAccordion.why.set(ACCORDION_WHY)
    # 7. card
    | Showcase.card_heading.set_label("7. card with title / subtitle / footer")
    | Showcase.card_heading.set_level(3)
    | CardBody.line1.set("a card wraps a body Section.")
    | CardBody.line2.set(
        "title, subtitle, and footer are plain strings on the Card itself.",
    )
    | CardBody.badge.set_label("composable")
    # 8. modal
    | Showcase.modal_heading.set_label("8. modal")
    | Showcase.modal_heading.set_level(3)
    | Showcase.modal_open_button.set(label="open modal")
    | DemoModal.body.set(
        "this is a modal body. server controls visibility; tab notifies on user dismissal.",
    )
    | DemoModal.close.set(label="close")
    # inputs
    | Showcase.section_inputs.set("inputs")
    | Showcase.input_name.set("world")
    | Showcase.echo.set("type a name and press greet.")
    # input extras
    | Showcase.section_inputs_extra.set("inputs (extras)")
    # form
    | Showcase.section_form.set("form")
    | Showcase.form_demo.submit.set(label="submit")
    | Showcase.form_echo.set("submit the form to see the values echoed here."),
)


# Initialize SelectRef options + slider bounds + textarea via store calls.
options_snapshot = nv.Snapshot(
    Showcase.select_mode.set(
        {"options": ["draft", "review", "published"], "selected": "draft"},
    )
    | Showcase.slider_volume.set(
        {"min": 0, "max": 100, "step": 5, "value": 40, "label": "volume"},
    )
    | Showcase.textarea_note.set("")
    # form children defaults: name input and age number input
    | FormNameField.input.set("ada")
    | FormAgeField.input.set_value(30),
)


# ---- Live tickers -----------------------------------------------------------

init_state = nv.Transaction(
    nu.IfDo(State.tick.missing(), State.tick.set(0)),
)


ticker_bg = init_state >> nu.ForeverDo(
    nv.Transaction(State.tick.set(State.tick + 1)) >> nu.Delay(1.0),
)


# Multi-series line chart: alpha increases by tick, beta by tick * 0.5 (offset).
tick_chart = nu.ForeverDo(
    nv.Snapshot(
        Showcase.chart_live.append_series("alpha", State.tick, State.tick)
        | Showcase.chart_live.append_series("beta", State.tick, State.tick + 5),
    )
    >> nu.Delay(1.0),
)


tick_area = nu.ForeverDo(
    nv.Snapshot(Showcase.area_demo.append(State.tick, State.tick)) >> nu.Delay(1.0),
)


tick_sparkline = nu.ForeverDo(
    nv.Snapshot(Showcase.sparkline_demo.append(State.tick, State.tick)) >> nu.Delay(1.0),
)


# Gauge: tick % 100 / 100 -> [0, 1].
tick_gauge = nu.ForeverDo(
    nv.Snapshot(Showcase.gauge_demo.set_value((State.tick % 100) / 100.0)) >> nu.Delay(1.0),
)


# ---- Buttons ----------------------------------------------------------------

on_greet = ReactForever(
    Showcase.button_greet.clicked(),
    nv.Snapshot(Showcase.echo.set(Showcase.input_name)),
)


on_reset = ReactForever(
    Showcase.button_reset.clicked(),
    nv.Snapshot(Showcase.echo.set("(reset)")),
)


# Modal open / close
on_modal_open = ReactForever(
    Showcase.modal_open_button.clicked(),
    nv.Snapshot(Showcase.modal_demo.set_open(True)),
)


on_modal_close = ReactForever(
    DemoModal.close.clicked(),
    nv.Snapshot(Showcase.modal_demo.set_open(False)),
)


# Form submit: echo name + age into form_echo.
on_form_submit = ReactForever(
    Showcase.form_demo.submit.clicked(),
    nv.Snapshot(
        Showcase.form_echo.set(FormNameField.input),
    ),
)


# ---- Compose ----------------------------------------------------------------

ui = (
    App.title.set("nudle storybook")
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

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbstorybook"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=nu.ForeverDo(
        nu.Delay(3600)
    ),  # everything above already ticks inside ui; just hold the server open
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
