// React components keyed by Ref type name.
//
// Re-export of the live registry that lives in factories.ts. Kept as a
// separate module so App-shell code can import `renderers` on its own
// (the legacy import path) without pulling in the factory registry name.

export { renderers } from "./factories";
