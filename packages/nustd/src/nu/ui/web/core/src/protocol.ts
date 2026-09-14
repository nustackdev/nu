// Wire protocol mirror of api/src/nudle/protocol.py.
// See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

import { decode as mpDecode, encode as mpEncode } from "@msgpack/msgpack";

// The op vocabulary lives in OPS (tree.ts). `error` is the one op the tree
// store has no member for -- nothing on this side handles one yet.
export const OP_ERROR = "error";

// A ref's address: the Ref chain's segments, root-first. Stays a list end
// to end -- a segment may contain any character, dots included, so there is
// no separator that could take it apart again.
export type RefPath = string[];

// One level of a ref chain: its segment, the type the browser renders it
// with, and the props its slot declared (empty object when it declared none).
// One level of a write's chain. The server always sends all three, but a chain
// synthesized locally from a bare `ref` has no type and no props to give, so the
// tail is optional. One type for both, or the two ends stop agreeing.
export type ChainLevel = [
	segment: string,
	type?: string | null,
	props?: Record<string, unknown>,
];

export type Frame = {
	op: string;
	ref: RefPath;
	payload: unknown;
	id?: string;
	// The `ref` path annotated, root-first. Present on writes; absent on
	// frames that carry no chain, so treat a missing one as empty.
	chain?: ChainLevel[];
};

export type ErrorCode =
	| "ref_not_found"
	| "op_not_allowed"
	| "payload_invalid"
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
