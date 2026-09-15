// Barrel for the tree store bindings.
//
//   store.ts     — the store instance + useTree
//   hooks.ts     — useNode / useChildren / useSend / ...
//   registry.ts  — register(type, { component, handlers, dispose })
//   NodeView.tsx — type lookup and recursion
//
// Registering a type = drop a module under ../nodes/ and add one line to
// ../nodes/index.ts.

export { tree, useTree } from "./store";
export {
	nodeAt,
	pathKey,
	useChildren,
	useExists,
	useNode,
	useBoolProp,
	useListProp,
	useNumberProp,
	useProp,
	useProps,
	useStringProp,
	useSend,
	useSetProps,
	useSetValue,
	useValue,
} from "./hooks";
export { componentFor, register, registry, resolve } from "./registry";
export type { NodeEntry, NodeProps } from "./registry";
export { ChildView, NodeChildren, NodeView } from "./NodeView";
