// Per-Ref-type module contract.
//
// Each refs/<type>.tsx exports a `RefEntry`: the slice factory plus the
// React component. refs/index.ts collects them into name-keyed registries.

import type { ComponentType } from "react";
import type { Frame } from "@nustackdev/ui-core";

export type RefSlice = {
	type: string;
	value: unknown;
	// Inbound interaction methods (server -> tab).
	write?: (value: unknown) => void;
	append?: (value: unknown) => void;
	// Server-initiated read: return the current local value.
	get?: () => unknown;
	// Called by the store on unmount / re-mount so a slice can release
	// resources (e.g. detach window event listeners).
	dispose?: () => void;
	// Per-Ref slice extras: state fields beyond the canonical `value`
	// (e.g. BadgeRef carries `label` and `variant` directly on the slice).
	[key: string]: unknown;
};

export type SliceCtx = {
	set: (mutator: (refs: Record<string, RefSlice>) => void) => void;
	send: (frame: Frame) => void;
};

export type SliceFactory = (
	path: string,
	ctx: SliceCtx,
	props?: Record<string, unknown>,
	children?: string[],
) => RefSlice;

export type RefEntry = {
	factory: SliceFactory;
	component: ComponentType<{ path: string }>;
};
