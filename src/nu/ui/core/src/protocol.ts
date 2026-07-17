// Wire protocol mirror of api/src/nudle/protocol.py.
// See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

import { decode as mpDecode, encode as mpEncode } from "@msgpack/msgpack";

export const OP_MOUNT = "mount";
export const OP_UNMOUNT = "unmount";
export const OP_ERROR = "error";
export const OP_NOTIFY = "notify";
export const OP_READ = "read";

export type Frame = {
	op: string;
	ref: string;
	payload: unknown;
	id?: string;
};

export type MountField = {
	path: string;
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
		ref: d.ref ?? "",
		payload: d.payload,
		id: d.id,
	};
}
