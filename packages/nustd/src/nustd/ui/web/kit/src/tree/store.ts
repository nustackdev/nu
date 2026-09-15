// The kit's tree store instance, wired to the type registry.
//
// The store itself is react-free and lives in core. This is the single
// browser-wide instance plus the React bindings over it. The old flat store
// (../store.ts) is still what the shipped apps run on; this is the one they
// move to.

import { createTreeStore, type TreeActions, type TreeState } from "@nustackdev/ui-core";
import { useStore } from "zustand";
import { resolve } from "./registry";

export const tree = createTreeStore({ resolve });

/** Subscribe to a slice of the tree. */
export function useTree<T>(selector: (state: TreeState & TreeActions) => T): T {
	return useStore(tree, selector);
}
