// Barrel for the tree store bindings.
//
//   store.ts    : the store instance + useTree
//   hooks.ts    : useNode / useChildren / useSend / ...
//   registry.ts : register(type, { component, handlers, dispose, fill })
//   NodeView.tsx: type lookup and recursion
//   flow.tsx    : the flow a container hands its children, and `useFill`
//
// Registering a type = drop a module under ../nodes/ and add one line to
// ../nodes/index.ts.

export type { Flow } from "./flow";
export { FlowProvider, useFill, useFlow } from "./flow";
export {
	nodeAt,
	pathKey,
	useBoolProp,
	useChildren,
	useExists,
	useListProp,
	useNode,
	useNumberProp,
	useProp,
	useProps,
	useSend,
	useSetProps,
	useSetValue,
	useStringProp,
	useValue,
} from "./hooks";
export type { CellProps } from "./NodeView";
export { BareCell, BlockCell, ChildView, NodeChildren, NodeView } from "./NodeView";
export type { NodeEntry, NodeProps } from "./registry";
export { componentFor, isFill, register, registry, resolve } from "./registry";
export { tree, useTree } from "./store";
