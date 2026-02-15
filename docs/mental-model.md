# Mental Model

## everybase as OS

The mapping between everybase and an operating system is structural, not metaphorical:

| OS | everybase |
| --- | --- |
| Filesystem | PV hierarchy — tuple keys, containers, views |
| Files | Shapes with typed slots |
| File types | Views — DictView, ListView, SetView, ... |
| Processes | Flows — computations with lifecycle |
| Kernel | Term/Flow/Span algebra, execution engine |
| Drivers | Services — RocksDB, Ollama, Claude, HTTP, vector search |
| Users | Human, agent, machine — all read/write the same tree |
| IPC | Reactive graph — one change triggers dependent recomputation |

## What Lives in the Tree

Everything.
