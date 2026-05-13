// Wire protocol mirror of api/src/nudle/protocol.py.
// See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

export const OP_MOUNT = "mount";
export const OP_UNMOUNT = "unmount";
export const OP_ERROR = "error";

export type Frame = {
	op: string;
	ref: string;
	payload: unknown;
	id?: string;
};

export type MountField = { path: string; type: string };
export type MountPayload = { page: string; fields: MountField[] };

export type ErrorCode =
	| "ref_not_found"
	| "op_not_allowed"
	| "payload_invalid"
	| "not_mounted"
	| "internal";

export type ErrorPayload = { code: ErrorCode; message: string };

export function encode(frame: Frame): string {
	return JSON.stringify(frame);
}

export function decode(raw: string): Frame {
	const d = JSON.parse(raw) as Partial<Frame> & { op: string };
	return {
		op: d.op,
		ref: d.ref ?? "",
		payload: d.payload,
		id: d.id,
	};
}
