# Design — Vocabulary

Use everybase terms only. No generic database or UI jargon.

## Terms Used

| Term | Meaning |
| --- | --- |
| **Shape** | A typed structure — the schema unit |
| **Slot** | A named field within a Shape |
| **Primitive** | A leaf value — str, int, float, bool |
| **Container** | A non-leaf that holds children |
| **View** | How a container is accessed — dict, list, set |
| **Ref** | A typed reference to a location in the tree |
| **Term** | An expression — what to compute |
| **Flow** | A running computation with lifecycle |

## Terms Not Used

Do not use these anywhere in the UI — labels, tooltips, empty states, error messages, documentation:

- node, item, record, row, cell
- field (use **slot**)
- type (use **shape** for structures, name the primitive directly for leaves)
- folder, file, page, document
- table, column
- object, entity, resource
- element, entry, property
