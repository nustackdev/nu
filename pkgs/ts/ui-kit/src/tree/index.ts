// Barrel for the tree store bindings.
//
//   store.ts    : the store instance + useTree
//   hooks.ts    : useNode / useChildren / useSend / ...
//   emit.ts     : useEmit / emit, how a node sends `{event, ...fields}`
//   watch.ts    : isWatched, which events the server listens for
//   outbox.ts   : enqueue, where an emitted event waits for its frame
//   registry.ts : register(type, { component, handlers, reads, dispose, fill })
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

export type { AnchorRule, Gesture } from "./anchors";
export { AnchorCatcher, catchAnchors, defaultAnchorRule, useAnchorCatcher } from "./anchors";
export type { Emit, EventFields } from "./emit";
export { EVENTS, emit, useEmit } from "./emit";
export type { Flow } from "./flow";
export { FlowProvider, useFill, useFlow } from "./flow";
export type { Entry, Move, MoveKind, MoveOptions } from "./history";
export {
	History,
	matchesPath,
	TRAVERSE_WINDOW_MS,
	trimSlash,
	useEntry,
	usePathname,
} from "./history";
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
export { enqueue } from "./outbox";
export type { Query, QueryValue } from "./query";
export { mergeQuery, parseQuery, queryValue, serializeQuery } from "./query";
export type { InputSpec, NodeEntry, NodeProps, Reads } from "./registry";
export {
	componentFor,
	isFill,
	isGrow,
	mainRead,
	readOf,
	register,
	registry,
	resolve,
} from "./registry";
export type { RouteBranch, RouteMatch, RouteParams } from "./router";
export { matchRoute, useRoute } from "./router";
export { tree, useTree } from "./store";
export { ANY, isWatched } from "./watch";
