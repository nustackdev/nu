# Design — Constraints

Non-negotiable. These are not preferences — they are load-bearing.

## Scale

The tree can have billions of entries. The UI must handle this without degradation. No operation — navigation, rendering, editing — may depend on total tree size. Every interaction is O(visible), never O(total).

## Lazy

Nothing loads until explicitly requested by a user action. No background prefetching. No recursive tree walks. Each level fetches independently. A container with 1 billion children renders as fast as one with 10.

## Bounded

Every collection view has a hard page size. Load a page, discard previous when navigating forward. Memory footprint stays constant regardless of how deep or wide the user navigates.
