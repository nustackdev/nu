# Architecture — Data Flow

## On Connect

Frontend fetches the full Shape schema — every Shape, slot, type, nesting. One request. This is metadata, not data — it's small and static (Shapes are defined in code). Cached for the session.

The schema drives the entire component tree

## The Loop

```text
User gesture
    → Term constructed (frontend)
    → Term sent to backend (WebSocket)
    → Term evaluated against PV tree (backend)
    → Result streamed back
    → State updated (frontend)
    → UI re-renders
```

This is the only loop. Navigation, editing, filtering, pagination — all go through it.

## State in the Browser

Two stores:

**Schema store** — the Shape tree. Immutable after initial fetch. Answers "what exists here and what type is it."

**Data store** — Term evaluation results, keyed by path. Answers "what's the current value at this path." Populated lazily as the user navigates. Evicted when the user navigates away.

When a Term result arrives, it updates the data store at the relevant path. When a live delta arrives from the backend, same thing — update the path. In both cases the UI re-renders the affected subtree. Nothing else.

This is why React is a natural fit. The model is literally: immutable schema + mutable data state → render. State changes → re-render. React does exactly this. The Shape tree maps to the component tree. The data store maps to state. Deltas map to state updates.

## Live Updates

The backend pushes deltas for paths the frontend is subscribed to. Subscription scope = what's currently visible.

- Navigate into a Shape → subscribe to its slots
- Navigate away → unsubscribe
- Delta arrives → data store update → re-render

No polling. No full refresh. No stale data. Edits in flight (focused field) are not overwritten.

## Backend Evaluation

The backend receives serialized Terms over WebSocket, deserializes into the Term tree, and evaluates against the PV storage.

- Reads use snapshots (consistent, non-blocking)
- Writes use transactions (atomic, auto-commit)
- Results stream back on the same WebSocket

The backend has no route handlers, no controllers, no endpoint-per-operation. One handler: receive Term, evaluate, respond.

## What Flows Where

```text
                 static                    lazy, on demand
Schema ─────────────────► Component tree ─────────────────► Term requests
                                                                  │
                                                           evaluated on
                                                             backend
                                                                  │
Live deltas ──► Data store ◄──────────────────────────── Term results
                    │
                re-render
```
