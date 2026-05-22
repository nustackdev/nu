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

export type MountField = { path: string; type: string };
export type MountPage = { route: string; name: string; fields: MountField[] };
// `name` is the Index class name; `fields` are Index-level structural
// slots (TitleRef, NavRef, ...); `pages` lists Page subtrees by route.
export type MountPayload = {
	name: string;
	fields: MountField[];
	pages?: MountPage[];
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
