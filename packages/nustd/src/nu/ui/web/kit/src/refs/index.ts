// Barrel for the Ref registry. Consumers pick the slice they need:
//
//   factories.ts  — string → SliceFactory (used by the store)
//   renderers.ts  — string → React component (used by App shells)
//   types.ts      — RefEntry / RefSlice / SliceCtx / SliceFactory
//
// Adding a new Ref type = drop a new module under one of chart/, input/,
// layout/, output/, structural/ and add one line to `entries` in factories.ts.

export { entries, factories, registerRefEntry, renderers } from "./factories";
export type { RefEntry, RefSlice, SliceCtx, SliceFactory } from "./types";
