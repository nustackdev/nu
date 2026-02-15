# Architecture — Flow

## On Connect

Frontend fetches the full Shape schema — every Shape, slot, type, nesting. One request. This is metadata, not data — it's small and static (Shapes are defined in code). Cached for the session.

## The Loop

```text
User gesture
    → Term constructed (frontend)
    → Term sent to backend (WebSocket)
    → Term evaluated against the storage (backend)
    → Result streamed back
    → State updated (frontend)
    → UI re-renders
```

This is the only loop. Navigation, editing, filtering, pagination — all go through it.

## State in the Browser

Two stores:

**Schema store** — the Shape tree. Immutable after initial fetch. Answers "what exists here and what type is it."

**Data store** — Term evaluation results. Populated as the user executes Term. Evicted when the user navigates away from the result.

The model is: immutable schema + data state → render. State changes → re-render.

## Backend Evaluation

The backend receives serialized Terms over WebSocket, deserializes into the Term tree, and evaluates against the PV storage.

- Reads use snapshots (consistent, non-blocking)
- Writes use transactions (atomic, auto-commit)
- Results stream back on the same WebSocket

The backend has no route handlers, no controllers, no endpoint-per-operation. One handler: receive Term, evaluate, respond.

## What Flows Where

```text
    static               lazy, on demand
Schema ──────────────────────► Term requests
                                        │
                                evaluated on
                                    backend
                                        │
Data store ◄──────────────────── Term results
    │
re-render
```
