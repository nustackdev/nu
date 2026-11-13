// Type registry for the tree store.
//
// One entry per Ref type, and it is three separable things: the React
// component that draws the node, the handlers that answer inbound ops, and
// an optional dispose for a node that holds a resource. State is the node's
// props, plain data, and the behaviour is looked up by type when a frame
// arrives.

import type { Behaviour, DisposeCtx, NodeHandler, Path } from "@nustackdev/ui-core";
import type { ComponentType } from "react";

export type NodeProps = { path: Path };

/**
 * What makes a node an input: it holds a value a Form gathers on submit and
 * a reset puts back. The value lives on `props.value` for every input.
 */
export type InputSpec = {
	/** The value with no seed: what a reset lands when the slot declared none. */
	empty: unknown | ((props: Record<string, unknown>) => unknown);
	/** What a form snapshot carries for this node. Unset is `props.value`. */
	read?: (props: Record<string, unknown>) => unknown;
	/** Whether a form gathers this node at all (a read-only document does not). */
	gathered?: (props: Record<string, unknown>) => boolean;
	/**
	 * The node draws its own `error` (and a form's failed `check`) under the
	 * control, so nothing frames it with Field chrome when it has no Field.
	 */
	ownsError?: boolean;
};

export type NodeEntry = Behaviour & {
	component?: ComponentType<NodeProps>;
	// The node has no intrinsic width (a chart, a table, an input), so a row
	// gives it a share of the free width rather than its content size. Read
	// by the parent through `useFill`; unset means "size to content". A
	// function decides per node from its props (a circle skeleton keeps its
	// size, a text skeleton fills).
	fill?: boolean | ((props: Record<string, unknown>) => boolean);
	// The node is empty room (a Spacer): a row grows its cell from nothing,
	// so it takes whatever the line has left. Read through `isGrow`.
	grow?: boolean;
	// The node is an input: a Form gathers its value and a reset restores it.
	input?: InputSpec;
	// The node wraps one control and stands for it in a form's values (a
	// Field): its value is its one child's, keyed at the wrapper's segment.
	wraps?: boolean;
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

/** Whether a node of `type` with `props` has no intrinsic width. Unknown types size to content. */
export function isFill(type: string | null, props: Record<string, unknown>): boolean {
	const fill = type ? registry[type]?.fill : undefined;
	return typeof fill === "function" ? fill(props) : fill === true;
}

/** Whether a node of `type` takes the room its row has left. */
export function isGrow(type: string | null): boolean {
	return type ? registry[type]?.grow === true : false;
}

export function componentFor(type: string | null): ComponentType<NodeProps> | undefined {
	return type ? registry[type]?.component : undefined;
}
