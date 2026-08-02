---
title: nu.flows
---

Command-composing atoms. A Flow owns no effects and yields nothing (VOID) -
either it fans out to mutating children directly (Strategy), or it steers a
mutating body under Query parameters (Control), or it drives a body off a
change subscription (the reactive Controls) or an ordered collection
(Stream). Flat-exported at `nu.*`.

`from nu import Sequential, Parallel, Race, Gather, AnyN, IfDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo, Delay, DelayedDo, SwitchDo, React, ReactWhile, ReactForever, Stream, Raise, raise_, Noop`

## Strategy

Compose mutating atoms directly, no Query parameters. `Sequential` runs
children in order (`>>`); `Parallel`/`Race`/`Gather`/`AnyN` run them
concurrently, dispatched through the Runtime's fan-in primitives. `Race` and
`AnyN` are async-only.

| Name       | Sort              | Signature                    | Effect  | Meaning                                                 |
| ---------- | ----------------- | ----------------------------- | ------- | -------------------------------------------------------- |
| Sequential | Flow(Strategy)    | `Sequential(*children)`        | mutates | run children in order (`>>`)                             |
| Parallel   | Flow(Strategy)    | `Parallel(*children)`          | mutates | run children concurrently, join on all (`\|`)             |
| Race       | Flow(Strategy)    | `Race(*children)`              | mutates, async-only | run children concurrently, first to finish wins (`&`), cancels the rest |
| Gather     | Flow(Strategy)    | `Gather(*children)`            | mutates | run children concurrently, join on all (yield-collecting twin of Parallel) |
| AnyN       | Flow(Strategy)    | `AnyN(*children)`               | mutates, async-only | run children concurrently, succeed on first success, cancels the rest |
| Noop       | Flow(Strategy)    | `Noop()`                        | none    | the empty Flow - identity of flow composition |

## Control

Compose a mutating body under Query parameters (a condition, an iterable, a
count). A Control owns no effects and yields nothing; param slots feed the
orchestration, body slots carry the writes.

| Name       | Sort            | Signature                                                    | Effect  | Meaning                                              |
| ---------- | --------------- | -------------------------------------------------------------- | ------- | ------------------------------------------------------ |
| IfDo       | Flow(Control)   | `IfDo(cond, then, else_=None)`                                  | mutates | run `then` if `cond` is truthy, else `else_`            |
| WhileDo    | Flow(Control)   | `WhileDo(cond, body)`                                           | mutates | run `body` while `cond` is truthy                      |
| ForeverDo  | Flow(Control)   | `ForeverDo(body)`                                               | mutates | run `body` endlessly                                    |
| ForEachDo  | Flow(Control)   | `ForEachDo(items, body, item="item")`                           | mutates | run `body` for each element, bound under name `item`    |
| ForRangeDo | Flow(Control)   | `ForRangeDo(start, stop, body, *, step=1, index="index")`       | mutates | counted loop over `range(start, stop, step)`, index bound under name `index` |
| Delay      | Flow(Control)   | `Delay(seconds)`                                                | none    | sleep `seconds`, no body                                |
| DelayedDo  | Flow(Control)   | `DelayedDo(delay, body)`                                        | mutates | sleep `delay` seconds, then run `body`                  |
| SwitchDo   | Flow(Control)   | `SwitchDo(selector, cases, default=None)`                       | mutates | branch on selector value, first matching case's body runs, else `default` |
| Raise      | Flow(Control)   | `Raise(msg, *, exc_cls=RuntimeError)`                            | none    | raise `exc_cls(msg)` at run time; skipped if `msg` resolves to EMPTY/INVALID |

`raise_(exc_cls, msg)` is a plain function wrapper around `Raise` - `raise_(ValueError, "bad")` builds `Raise("bad", exc_cls=ValueError)`. Wrap in `IfDo` to gate.

## Reactive

Subscribe to a change event and run a body in response; yields nothing. A
change notification bridges into async via `asyncio.Queue`. Async-only.

| Name        | Sort            | Signature                                                 | Effect  | Meaning                                                        |
| ----------- | --------------- | ------------------------------------------------------------ | ------- | ----------------------------------------------------------------- |
| React       | Flow(Control)   | `React(change, body=None, *, changed_key=None)`               | mutates, async-only | wait for one change event, run `body` once (if given)             |
| ReactWhile  | Flow(Control)   | `ReactWhile(change, condition, body, *, changed_key=None)`    | mutates, async-only | run `body` on each change event while `condition` is truthy       |
| ReactForever| Flow(Control)   | `ReactForever(change, body, *, changed_key=None)`              | mutates, async-only | run `body` on every change event, forever                         |

## Stream

Drain-then-follow over an ordered collection - the `cat file; tail -f` of Nu. Observes via a cursor and a reactive subscription, yielding body results across the batch-catch-up-then-live-follow transition.

| Name   | Sort         | Signature                                              | Effect | Meaning                                                        |
| ------ | ------------ | --------------------------------------------------------- | ------ | ----------------------------------------------------------------- |
| Stream | StreamQuery  | `Stream(source, body, *, key="stream_key", log_key="stream_log_key")` | pure, async-only | drain existing items via cursor, then follow new ones reactively |
