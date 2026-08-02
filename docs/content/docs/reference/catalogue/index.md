---
title: Nu docs
---

Everything is a Nu. There are two top-level kinds: **Ref** (an address) and **Interaction** (Query, Command, Flow, Span).

A flat catalog of every atom and Form, with one-line meanings.

## Pages

| Doc                     | Module      | What                                                |
| ----------------------- | ----------- | --------------------------------------------------- |
| [core.md](core.md)     | `nu.core`   | Atom interactions on host values - arithmetic, logical, comparison, cast, reduction, transform, iteration, access, reflection, repr, sentinel, conditional, dynamic, reactive, io, bitwise, literal |
| [forms.md](forms.md)   | `nu.forms`  | Typed value interfaces - primitives, collections    |
| [flows.md](flows.md)   | `nu.flows`  | Command composers - Sequential, Parallel, Race, IfDo, WhileDo, ForEachDo, Stream |
| [spans.md](spans.md)   | `nu.spans`  | Transparent wrappers - Snapshot, Transaction, Retry, TryCatch, Timeout, Throttle, Debounce |
| [context.md](context.md) | `nu.context` | The Context fabric - attrs, fabric               |
| [shape.md](shape.md)   | `nu.shape`  | Shape DSL - Shape, Slot, and fabric atoms           |
| [mem.md](mem.md)       | `nu.mem`    | In-process fabric refs and interactions             |
| [std.md](std.md)       | `nu.std`    | Standard library wrappers - itertools, functools, math, uuid, decimal, fractions, datetime, pathlib, asyncio, random, time, logging, cmath, fin |

## Spine

### Kinds

| Kind        | Yields                  | Effects allowed   | Role                                                       |
| ----------- | ----------------------- | ----------------- | ---------------------------------------------------------- |
| Ref         | a value at an address   | RESOLVE, READ     | Address atom - dynamic resolution into the Fabric.         |
| Query       | a value or a stream     | READ              | Value-producing atom. ScalarQuery, StreamQuery.            |
| Command     | nothing                 | WRITE             | Mutating atom. ScalarCommand.                              |
| Flow        | nothing                 | composes Commands | Command composer. Strategy, Control.                       |
| Span        | what its body yields    | transparent       | Wraps any Nu. Bracket, Policy.                             |

### Effects

| Effect  | Means                                |
| ------- | ------------------------------------ |
| RESOLVE | touch a fabric for an address        |
| READ    | materialize a value from the Context |
| WRITE   | transform the Context                |
| pure    | atom or composition with no effects  |

### Composition operators

| Op       | What                                   |
| -------- | -------------------------------------- |
| `a >> b` | sequential (Strategy Flow)             |
| `a \| b` | parallel (Strategy Flow)               |
| `a & b`  | race (Strategy Flow)                   |

### Naming

- Bare verb (`If`, `ForEach`, `Map`) - Query. Yields a value or stream.
- `*Do` suffix (`IfDo`, `ForEachDo`, `WhileDo`) - Flow. Composes Commands.

## Conventions

- **Name** - the class as written in code.
- **Sub-shape** - which sub-shape of the kind it is.
- **Signature** - constructor args, abbreviated.
- **Effect** - `pure`, `RESOLVE`, `READ`, `WRITE`, or a combination.
- **Meaning** - one short line.
