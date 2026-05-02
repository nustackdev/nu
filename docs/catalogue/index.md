# Nu docs

Everything is a Nu. There are two top-level kinds: **Ref** (an address) and **Interaction** (Query, Command, Flow, Span).

A flat catalog of every atom and Form, with one-line meanings.

## Pages

| Doc                          | What                                                |
| ---------------------------- | --------------------------------------------------- |
| [query.md](query.md)         | Value-producing atoms - ScalarQuery, StreamQuery    |
| [command.md](command.md)     | Mutating atoms - ScalarCommand                      |
| [flow.md](flow.md)           | Command composers - Strategy, Control               |
| [span.md](span.md)           | Transparent wrappers - Bracket, Policy              |
| [forms.md](forms.md)         | Forms - primitives, collections                     |
| [meta.md](meta.md)           | Tree meta-programming - walk, query, rewrite        |

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
