// Barrel for the tree store bindings.
//
//   store.ts    : the store instance + useTree
//   hooks.ts    : useNode / useChildren / useSend / ...
//   registry.ts : register(type, { component, handlers, dispose, fill })
//   NodeView.tsx: type lookup and recursion
//   flow.tsx    : the flow a container hands its children, and `useFill`
//   navigate.ts : the navigator NavRef moves the page through (a host can swap
//                 it), and the one location source everything follows
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
	useEnumProp,
	useExists,
	useHidden,
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
export type { Navigator } from "./navigate";
export {
	activeNavigator,
	historyNavigator,
	matchesPath,
	setNavigator,
	subscribeLocation,
	usePathname,
} from "./navigate";
export type { CellProps } from "./NodeView";
export {
	ACTIONS_SLOT,
	BareCell,
	BlockCell,
	ChildView,
	indexedOrder,
	NodeChildren,
	NodeView,
	SlotView,
} from "./NodeView";
export type { NodeEntry, NodeProps } from "./registry";
export { componentFor, isFill, isGrow, register, registry, resolve } from "./registry";
export { tree, useTree } from "./store";
