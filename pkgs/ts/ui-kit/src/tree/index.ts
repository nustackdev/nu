// Barrel for the tree store bindings.
//
//   store.ts    : the store instance + useTree
//   hooks.ts    : useNode / useChildren / useSend / ...
//   registry.ts : register(type, { component, handlers, dispose, fill })
//   NodeView.tsx: type lookup and recursion
//   flow.tsx    : the flow a container hands its children, and `useFill`
//   history.ts  : History, the one writer of browser history and the one
//                 source of where the page is (useEntry, usePathname)
//   query.ts    : the query string encoding, shared with the Python side
//   router.ts   : matchRoute / useRoute, branch matching on the entry
//   anchors.tsx : AnchorCatcher, plain in-app <a> clicks into History moves
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
export type { AnchorRule, Gesture } from "./anchors";
export { AnchorCatcher, catchAnchors, defaultAnchorRule, useAnchorCatcher } from "./anchors";
export type { Entry, Move, MoveKind, MoveOptions } from "./history";
export {
	History,
	matchesPath,
	TRAVERSE_WINDOW_MS,
	trimSlash,
	useEntry,
	usePathname,
} from "./history";
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
export type { Query, QueryValue } from "./query";
export { mergeQuery, parseQuery, queryValue, serializeQuery } from "./query";
export { componentFor, isFill, isGrow, register, registry, resolve } from "./registry";
export type { RouteBranch, RouteMatch, RouteParams } from "./router";
export { matchRoute, useRoute } from "./router";
export { tree, useTree } from "./store";
