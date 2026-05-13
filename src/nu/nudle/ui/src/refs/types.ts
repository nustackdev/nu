// Per-Ref-type module contract.
//
// Each refs/<type>.tsx exports a `RefEntry`: the slice factory plus the
// React component. refs/index.ts collects them into name-keyed registries.

import type { ComponentType } from "react";
import type { Frame } from "../protocol";

export type RefSlice = {
	type: string;
	value: unknown;
	// Inbound interaction methods (server -> tab).
	write?: (value: unknown) => void;
	append?: (value: unknown) => void;
	// Server-initiated read: return the current local value.
	get?: () => unknown;
};

export type SliceCtx = {
	set: (mutator: (refs: Record<string, RefSlice>) => void) => void;
	send: (frame: Frame) => void;
};

export type SliceFactory = (path: string, ctx: SliceCtx) => RefSlice;

export type RefEntry = {
	factory: SliceFactory;
	component: ComponentType<{ path: string }>;
};
