# everylens — Model

## Core Idea

everylens is two things:

1. **A visual Term builder** — every user interaction constructs a Term expression
2. **A data visualizer** — results of Term evaluation are rendered as UI

That's the whole model. The UI builds Terms, the backend evaluates them, the frontend draws the results.

## Shapes Are the Schema

The Shape tree is defined in code and fetched once on connect. It tells the frontend what exists, what types, what nesting. Shapes don't change at runtime — they are structure, not content.

The Shape schema drives everything: which components to render, what's editable, what's navigable, what Terms are valid at each location.

## Every Interaction Is a Term

Navigation, editing, filtering, pagination — all are Term construction.

| User action | Term constructed |
| --- | --- |
| Open a Shape | `Shape.slot.get()` for each slot |
| Edit a field | `Shape.slot.set(value)` |
| Navigate into a child | `Shape.children["key"].get()` |
| Scroll a list | `Shape.items[offset:offset+limit]` |
| Delete an entry | `Shape.items["key"].remove()` |
| Append to a list | `Shape.items.append(value)` |
| Filter a collection | `Shape.items.filter(predicate)` |

The frontend maps gestures to Terms automatically. The user doesn't see Terms — they see buttons, inputs, and lists. But the wire protocol is always Terms.

## Built-in and Extensible

everylens ships with built-in Terms for standard Shape operations — get, set, slice, append, remove, filter. These cover navigation and editing out of the box.

Users can extend with custom Terms — for complex queries, domain-specific queries, computed views, or batch operations. Same pipeline: construct Term → evaluate → render result.

## Data Flow

```text
Shape schema ──► component tree (what to render)
                      │
User gesture ──► Term construction
                      │
                 Term ──► backend evaluates ──► result stream
                                                     │
                                              frontend renders
```

Schema is static. Data flows through Terms. The UI is a live projection of Term evaluation results.

## Live

When external writers (agents, machines, flows) mutate the tree, the UI receives deltas scoped to visible paths. No polling, no full refresh. The projection stays current.
