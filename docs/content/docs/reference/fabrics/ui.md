---
title: nu.ui
---

Reactive UI fabric: Shape trees rendered live in the browser. Refs are
backed by a client rendering surface (a browser tab), Interactions describe
mutations the server ships as wire frames, and the host (nudle) owns the
transport. Async-only. The widget kit lives under `nu.ui.refs` and is a
separate reference; this page covers the fabric primitives.

## Base

`from nu.ui import Ref`

| Name | Sort  | Signature                                                        | Effect     | Meaning                                                                                          |
| ---- | ----- | ------------------------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------------- |
| Ref  | class | `Ref(address, *, parent_ref=None, owner_shape=None)`                | read/write | base Ref backed by a client rendering surface. Class name is the wire type; async-only.               |

## Sections

`from nu.ui import Section, SectionRef`

| Name       | Sort  | Signature                                                                                     | Effect     | Meaning                                                                                       |
| ---------- | ----- | ----------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------- |
| Section    | Shape | `class MySection(Section): ...`                                                                 | pure       | Shape base for layout containers. Subclass to declare child Slots and pin chrome defaults.       |
| SectionRef | class | `SectionRef(address, *, section_cls, parent_ref=None, owner_shape=None)`                        | read/write | substrate Ref backing a Section Slot; attribute access descends into the bound Section's Slots. |

## Session

`from nu.ui import Session, Subscription`

| Name         | Sort     | Signature                              | Effect     | Meaning                                                                                                |
| ------------ | -------- | ---------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------- |
| Session      | abstract | `Session()`                              | read/write | wire transport for one client connection. Host binds a concrete impl on Context via `ctx.bind(Session, ...)`. |
| Subscription | Protocol | `Subscription()` with `bind`/`unbind`/`close` | read/write | observer handle returned by `session.subscribe(path)`; callbacks fire when the client notifies on that path. |

## Wire

`from nu.ui.core import Frame`

| Name  | Sort  | Signature                                             | Effect | Meaning                                                                                                     |
| ----- | ----- | ------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| Frame | class | `Frame(op, *, ref="", payload=None, id=None)`           | pure   | one wire envelope, same shape both directions. `op` is a lifecycle string or an interaction instance (its lowercased class name becomes the wire op). |

## Interactions

`from nu.ui import Write, Append, Changed`

| Name    | Sort          | Signature              | Effect         | Meaning                                                                                             |
| ------- | ------------- | ------------------------ | -------------- | ----------------------------------------------------------------------------------------------------- |
| Write   | Command       | `Write(ref, value)`      | mutates slot 0 | server-to-client: replace the Ref's value. Ships a `write` Frame on the bound Session.                 |
| Append  | Command       | `Append(ref, *values)`   | mutates slot 0 | server-to-client: push onto a sequence-typed Ref. Multi-arg form ships the tuple, single-arg the value. |
| Changed | ScalarQuery   | `Changed(ref)`           | pure           | subscribe to client-side change notifications. Resolves to a Subscription; sends no outbound Frame.    |

## Nudle host

`from nu.ui import Index, Page, Pages`

| Name  | Sort  | Signature                                     | Effect     | Meaning                                                                                            |
| ----- | ----- | ----------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| Index | Shape | `class App(Index): pages = Pages({...})`        | read/write | browser entrypoint. One per app. Declares structural Refs and a `pages` map; Refs on it use bare slot names as wire paths. |
| Page  | Shape | `class Home(Page): ...`                         | read/write | sub-Shape mounted at a route. Refs rooted on a Page resolve to `<PageShapeName>.<slot>`.               |
| Pages | class | `Pages({"/": Home, "/feed": Feed})`             | pure       | declarative URI-to-Page map. Class-attribute holder, not a Slot.                                     |

## Nudle server

`from nu.ui import NudleServer, NudleSession`
`from nu.ui.nudle import server`

| Name         | Sort            | Signature                                                                                             | Effect     | Meaning                                                                                                        |
| ------------ | --------------- | ------------------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| NudleServer  | FabricLifecycle | `NudleServer(app, *, host="127.0.0.1", port=8080, log_level="info", ready_timeout=10.0, shutdown_timeout=5.0)` | read/write | boots the FastAPI + uvicorn stack that serves a nudle Index. Async-only; enters via `Provide(NudleServer, {...})`. |
| server       | fn              | `server(app, *, host="127.0.0.1", port=8080, ...)`                                                     | pure       | convenience wrapper: returns `Provide(NudleServer, {...})` around a body.                                        |
| NudleSession | Session         | `NudleSession(ws)`                                                                                     | read/write | concrete `Session` over a FastAPI websocket. One per connection; owns the observer registry and pending reads.    |

## Layout

`from nu.ui import Row, Column, Container, Card, DividerRef, Field, Fieldset, Form, Modal, NavRef, Tabs, Accordion`

Layout widgets are `Section` subclasses (Shape-based mounts) except `DividerRef` and `NavRef`, which are plain Refs. Sections use `Cls.slot(**chrome)` at declaration.

| Name       | Sort | Signature                                                                                             | Effect | Meaning                                                                          |
| ---------- | ---- | ------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| Row        | Ref  | `Row.slot(*, gap=4, align="center", justify="start", wrap=False, padding=0)`                            | pure   | horizontal flex Section.                                                          |
| Column     | Ref  | `Column.slot(*, gap=4, align="stretch", justify="start", padding=0)`                                    | pure   | vertical flex Section.                                                            |
| Container  | Ref  | `Container.slot(*, title="", padding="md", border="hairline", background="none", shadow="none", gap="md")` | pure   | styled box Section, pinned chrome.                                                |
| Card       | Ref  | `Card.slot(*, title="", subtitle="", footer="")`                                                        | pure   | card Section with title, subtitle, body slots, footer.                            |
| DividerRef | Ref  | `DividerRef.slot(*, label="", align="center")`                                                          | pure   | horizontal rule with optional label.                                              |
| Field      | Ref  | `Field.slot(*, label="", help="", error="", required=False)`                                            | pure   | label plus one input child plus help/error text. Exactly one child slot.          |
| Fieldset   | Ref  | `Fieldset.slot(*, legend="", gap="md", disabled=False)`                                                 | pure   | grouped fields with a legend.                                                     |
| Form       | Ref  | `Form.slot(*, title="", gap=4, padding=0, align="stretch")`                                             | pure   | semantic form wrapper; submit lives on a child ButtonRef.                         |
| Modal      | Ref  | `Modal.slot(*, open=False, title="", dismissible=True)`                                                 | pure   | dialog overlay; body Refs declared as child slots.                                |
| NavRef     | Ref  | `NavRef()`                                                                                              | read/write | Index-level Ref bound to `window.history` + `window.location`. Push, replace, back, forward. |
| Tabs       | Ref  | `Tabs.slot(*, tabs=None, active="")`                                                                    | pure   | tab strip plus active body; one child slot per tab.                               |
| Accordion  | Ref  | `Accordion.slot(*, sections=None, open=None, multi=True)`                                               | pure   | stack of collapsible sections; tab owns open state.                               |

## Content

`from nu.ui import TextRef, HeadingRef, TitleRef, MarkdownRef, ImageRef, LinkRef, BadgeRef, AlertRef, CodeBlockRef, JsonViewerRef`

Server-owned display sinks (plus `TitleRef`, bound to `document.title`). Server pushes via `write`; browser renders, never reads back.

| Name          | Sort | Signature                                                                                          | Effect | Meaning                                                              |
| ------------- | ---- | ---------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| TextRef       | Ref  | `TextRef.slot(*, value="")`                                                                          | pure   | plain body copy string.                                                |
| HeadingRef    | Ref  | `HeadingRef.slot(*, label="", level=1, align="left")`                                                | pure   | heading text with level and alignment.                                 |
| TitleRef      | Ref  | `TitleRef.slot(*, default="", suffix="")`                                                            | pure   | Index-level Ref bound to `document.title`. Write-only.                 |
| MarkdownRef   | Ref  | `MarkdownRef.slot(*, value="")`                                                                      | pure   | commonmark source rendered inline.                                     |
| ImageRef      | Ref  | `ImageRef.slot(*, src="", alt="", fit="contain", width=None, height=None, rounded=False)`            | pure   | image sink with fit and sizing.                                        |
| LinkRef       | Ref  | `LinkRef.slot(*, href="", label="", target="_self", external=None)`                                  | pure   | hyperlink with target and external hint.                               |
| BadgeRef      | Ref  | `BadgeRef.slot(*, label="", variant="neutral")`                                                      | pure   | small tone-tagged label.                                               |
| AlertRef      | Ref  | `AlertRef.slot(*, variant="info", title="", body="", dismissible=False)`                             | read/write | banner with tone, title, body; `notify` fires on dismiss.          |
| CodeBlockRef  | Ref  | `CodeBlockRef.slot(*, code="", language="", show_copy=True)`                                         | pure   | fenced code block with optional copy control.                          |
| JsonViewerRef | Ref  | `JsonViewerRef.slot(*, value=None, expand_depth=1, theme="light", copyable=False, sortable=False, max_height=None)` | pure | collapsible JSON tree with depth and theme.                        |

## Input

`from nu.ui import ButtonRef, InputRef, TextAreaRef, NumberInputRef, CheckboxRef, SwitchRef, RadioGroupRef, SelectRef, SliderRef, DatePickerRef, TagInputRef`

Tab-owned Refs: browser holds the live value; host reads on demand via the Ref and subscribes to `changed()` / `clicked()`.

| Name           | Sort | Signature                                                                                              | Effect     | Meaning                                                                        |
| -------------- | ---- | -------------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------- |
| ButtonRef      | Ref  | `ButtonRef.slot(*, label="", variant="primary", disabled=False, icon=None)`                              | read/write | click trigger; subscribe via `.clicked()`.                                      |
| InputRef       | Ref  | `InputRef.slot(*, label="", placeholder="", value="", type="text", max_length=None, mono=False)`         | read/write | single-line text input.                                                          |
| TextAreaRef    | Ref  | `TextAreaRef.slot(*, value="", placeholder="", rows=4, max_length=None, auto_resize=False, mono=False)`  | read/write | multi-line text input.                                                           |
| NumberInputRef | Ref  | `NumberInputRef.slot(*, label="", placeholder="", min=None, max=None, step=1.0, default=0.0)`            | read/write | numeric input with step and bounds.                                              |
| CheckboxRef    | Ref  | `CheckboxRef.slot(*, label="", checked=False)`                                                           | read/write | boolean toggle.                                                                  |
| SwitchRef      | Ref  | `SwitchRef.slot(*, label="", default=False)`                                                             | read/write | on/off switch.                                                                   |
| RadioGroupRef  | Ref  | `RadioGroupRef.slot(*, options=None, selected="", orientation="vertical")`                               | read/write | single-choice radio group.                                                       |
| SelectRef      | Ref  | `SelectRef.slot(*, options=None, selected="", placeholder="")`                                           | read/write | dropdown single-select.                                                          |
| SliderRef      | Ref  | `SliderRef.slot(*, min=0.0, max=100.0, step=1.0, value=0.0, label="", show_value=True)`                  | read/write | numeric slider with range and step.                                              |
| DatePickerRef  | Ref  | `DatePickerRef.slot(*, label="", placeholder="", min="", max="", default="")`                            | read/write | date input with ISO yyyy-mm-dd value.                                            |
| TagInputRef    | Ref  | `TagInputRef.slot(*, label="", placeholder="", value=None, max_tags=None, allow_duplicates=False)`       | read/write | multi-tag entry field.                                                           |

## Data display

`from nu.ui import TableRef, StatRef, ProgressRef, GaugeRef`

Server-owned sinks with structured payloads.

| Name        | Sort | Signature                                                                                                     | Effect     | Meaning                                                                    |
| ----------- | ---- | --------------------------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------- |
| TableRef    | Ref  | `TableRef.slot(*, columns=None, striped=True, dense=False, max_rows=0, sort_column="", sort_direction="asc", clickable_rows=False)` | read/write | tabular data with optional sort and row click.                              |
| StatRef     | Ref  | `StatRef.slot(*, label="", value="", delta="", trend="flat")`                                                   | pure       | single KPI tile: label, value, delta, trend.                                |
| ProgressRef | Ref  | `ProgressRef.slot(*, value=0.0, caption="", indeterminate=False)`                                               | pure       | linear progress bar with optional indeterminate mode.                       |
| GaugeRef    | Ref  | `GaugeRef.slot(*, value=0.0, caption="", variant="neutral")`                                                    | pure       | arc gauge with tone variant.                                                |

## Charts

`from nu.ui import LineChart, BarChart, AreaChart, PieChart, Sparkline`

Typed visualization sinks over series payloads. Server pushes via `write` (full/partial) and `append` (one row/point).

| Name      | Sort | Signature                                                                                                        | Effect | Meaning                                                     |
| --------- | ---- | ------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------- |
| LineChart | Ref  | `LineChart.slot(*, x_label="", y_label="", color="#2563eb", max_points=500, x_format="number", show_legend=False, show_tooltip=True, palette=None)` | pure | single- or multi-series line chart.                          |
| BarChart  | Ref  | `BarChart.slot(*, x_label="", y_label="", color="#2563eb", orientation="vertical", max_bars=200)`                  | pure   | vertical or horizontal bar chart.                            |
| AreaChart | Ref  | `AreaChart.slot(*, x_label="", y_label="", series=None, colors=None, stacked=False, max_points=500, x_format="number")` | pure | area chart, stackable across series.                         |
| PieChart  | Ref  | `PieChart.slot(*, slices=None, colors=None, inner_radius=0.0, show_labels=True, show_legend=True, total_label="")` | pure   | pie or donut chart with legend.                              |
| Sparkline | Ref  | `Sparkline.slot(*, color="#2563eb", height=32, max_points=100)`                                                    | pure   | inline trend line.                                           |
