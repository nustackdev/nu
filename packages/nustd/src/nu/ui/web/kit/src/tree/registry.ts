// Type registry for the tree store.
//
// One entry per Ref type, and it is three separable things: the React
// component that draws the node, the handlers that answer inbound ops, and
// an optional dispose for a node that holds a resource. Data and behaviour
// no longer share an object -- state is the node's props, plain data, and
// the behaviour is looked up by type when a frame arrives.

import type { Behaviour, DisposeCtx, NodeHandler, Path } from "@nustackdev/ui-core";
import type { ComponentType } from "react";

export type NodeProps = { path: Path };

export type NodeEntry = Behaviour & {
	component?: ComponentType<NodeProps>;
};

export type { DisposeCtx, NodeHandler };

export const registry: Record<string, NodeEntry> = {};

/** Register a type. Downstream packages (nuspace, apps) call this at boot. */
export function register(type: string, entry: NodeEntry): void {
	registry[type] = entry;
}

/** Behaviour lookup handed to the store. */
export function resolve(type: string): NodeEntry | undefined {
	return registry[type];
}

export function componentFor(type: string | null): ComponentType<NodeProps> | undefined {
	return type ? registry[type]?.component : undefined;
}
