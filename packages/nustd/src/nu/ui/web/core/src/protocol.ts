// Wire protocol mirror of api/src/nudle/protocol.py.
// See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

import { decode as mpDecode, encode as mpEncode } from "@msgpack/msgpack";

export const OP_MOUNT = "mount";
export const OP_UNMOUNT = "unmount";
export const OP_ERROR = "error";
export const OP_NOTIFY = "notify";
export const OP_READ = "read";

// A ref's address: the Ref chain's segments, root-first. Stays a list end
// to end -- a segment may contain any character, dots included, so there is
// no separator that could take it apart again.
export type RefPath = string[];

/** Store key for a path. Round-trips through `refPath`; never split by hand. */
export function refKey(path: RefPath): string {
	return JSON.stringify(path);
}

/** The path a store key was made from. */
export function refPath(key: string): RefPath {
	return JSON.parse(key) as RefPath;
}

// One level of a ref chain: its segment, the type the browser renders it
// with, and the props its slot declared (empty object when it declared none).
export type ChainLevel = [segment: string, type: string, props: Record<string, unknown>];

export type Frame = {
	op: string;
	ref: RefPath;
	payload: unknown;
	id?: string;
	// The `ref` path annotated, root-first. Present on writes; absent on
	// frames that carry no chain, so treat a missing one as empty.
	chain?: ChainLevel[];
};

// A Frame as the store speaks it: `ref` is the store key rather than the
// path. Slices hold keys (that is what they index the store by), so they
// build these; `send` turns one into a wire Frame on the way out.
export type KeyedFrame = {
	op: string;
	ref: string;
	payload: unknown;
	id?: string;
};

export type MountField = {
	path: RefPath;
	type: string;
	// Optional class-level defaults for the Ref or Section. When present,
	// the slice factory seeds its state from these values.
	props?: Record<string, unknown>;
	// Optional nested fields. Layout entries (Row, Column, Container) carry
	// their child entries here. Leaf Ref entries omit this key. The browser
	// walks the tree recursively to register slices for every leaf.
	fields?: MountField[];
};
export type MountPage = {
	route: string;
	name: string;
	// Human label used by the built-in sidebar. Server derives it from the
	// Page's `nav_label` class attr or the route slug.
	label: string;
	fields: MountField[];
};
// `name` is the Index class name; `fields` are Index-level structural
// slots (TitleRef, NavRef, ...); `pages` lists Page subtrees by route.
// `sidebar` toggles the built-in left rail; server sets it only when the
// Index has multiple pages and hasn't opted out.
export type MountPayload = {
	name: string;
	fields: MountField[];
	pages?: MountPage[];
	sidebar?: boolean;
};

export type ErrorCode =
	| "ref_not_found"
	| "op_not_allowed"
	| "payload_invalid"
	| "not_mounted"
	| "internal";

export type ErrorPayload = { code: ErrorCode; message: string };

export function encode(frame: Frame): Uint8Array {
	return mpEncode(frame);
}

export function decode(raw: ArrayBuffer | Uint8Array): Frame {
	const bytes = raw instanceof Uint8Array ? raw : new Uint8Array(raw);
	const d = mpDecode(bytes) as Partial<Frame> & { op: string };
	return {
		op: d.op,
		ref: d.ref ?? [],
		payload: d.payload,
		id: d.id,
		...(d.chain ? { chain: d.chain } : {}),
	};
}
