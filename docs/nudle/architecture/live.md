# Architecture — Live Updates

Hard problem. Parked here for thinking.

## The Challenge

A list slot has 1 billion items. The UI shows the first 10. A machine appends item 1,000,000,001. What happens?

Subscribing to "the whole list" is wrong — you'd drown in irrelevant deltas. Subscribing to nothing means stale UI. The granularity of subscription matters and it's not obvious what the right level is.

## Possible Approaches

**Polling fallback** — for complex views (filtered, sorted, sliced), just poll on an interval. Crude but honest about the difficulty.

**Invalidation, not delta** — don't push new values, push "this path is stale." The frontend re-evaluates its Term to get fresh data. Simpler subscription logic, but costs a round trip on every change.

**Per-visible-item subscriptions** — subscribe to each of the 10 visible items individually. Precise, no noise.

**Term-aware subscriptions** — analyze the Term that produced the current view (e.g. `items[0:10]`), derive what it touches, subscribe to those. Smart, but complex — the backend needs to introspect Terms and map them to subscription filters.
