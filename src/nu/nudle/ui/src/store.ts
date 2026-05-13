// Browser-side store. zustand + immer.
//
// One global store keyed by ref path. Dispatcher routes inbound frames to
// per-slice methods. Outbound frames go through `send` (set by App once
// the ws is open). Server-initiated reads are answered by calling the
// slice's optional `get()` and shipping back a frame with the same id.

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
	type ErrorCode,
	type Frame,
	type MountPayload,
	OP_ERROR,
	OP_MOUNT,
	OP_READ,
	OP_UNMOUNT,
} from "./protocol";
import { factories } from "./refs";
import type { RefSlice } from "./refs/types";

type Status = "connecting" | "connected" | "disconnected";

type State = {
	status: Status;
	page: MountPayload | null;
	refs: Record<string, RefSlice>;
};

type Actions = {
	setStatus: (s: Status) => void;
	setSender: (send: (f: Frame) => void) => void;
	send: (frame: Frame) => void;
	setLocal: (path: string, value: unknown) => void;
	dispatch: (frame: Frame) => void;
	mount: (payload: MountPayload) => void;
	unmount: () => void;
	logError: (code: ErrorCode, message: string, ref?: string) => void;
};

let outbound: ((f: Frame) => void) | null = null;

export const useStore = create<State & Actions>()(
	immer((set, get) => ({
		status: "connecting",
		page: null,
		refs: {},

		setStatus: (s) =>
			set((draft) => {
				draft.status = s;
			}),

		setSender: (sender) => {
			outbound = sender;
		},

		send: (frame) => {
			if (outbound) outbound(frame);
		},

		setLocal: (path, value) =>
			set((draft) => {
				if (draft.refs[path]) draft.refs[path].value = value;
			}),

		mount: (payload) =>
			set((draft) => {
				draft.page = payload;
				draft.refs = {};
				const ctx = {
					set: (mutator: (refs: Record<string, RefSlice>) => void) =>
						set((d) => {
							mutator(d.refs);
						}),
					send: (f: Frame) => {
						if (outbound) outbound(f);
					},
				};
				for (const field of payload.fields) {
					const factory = factories[field.type];
					if (!factory) {
						console.warn(`nudle: no factory for Ref type "${field.type}"`);
						continue;
					}
					draft.refs[field.path] = factory(field.path, ctx);
				}
			}),

		unmount: () =>
			set((draft) => {
				draft.page = null;
				draft.refs = {};
			}),

		logError: (code, message, ref) =>
			console.error(`nudle error [${code}] ref=${ref ?? ""}: ${message}`),

		dispatch: (frame) => {
			if (frame.op === OP_MOUNT) {
				get().mount(frame.payload as MountPayload);
				return;
			}
			if (frame.op === OP_UNMOUNT) {
				get().unmount();
				return;
			}
			if (frame.op === OP_ERROR) {
				const p = frame.payload as { code: ErrorCode; message: string };
				get().logError(p.code, p.message, frame.ref);
				return;
			}
			if (frame.op === OP_READ) {
				// Server is asking for our current value. Reply with the
				// same id so the server's future resolves.
				const slice = get().refs[frame.ref];
				const value = slice?.get ? slice.get() : (slice?.value ?? null);
				get().send({ op: OP_READ, ref: frame.ref, payload: value, id: frame.id });
				return;
			}
			const slice = get().refs[frame.ref];
			if (!slice) {
				get().logError("ref_not_found", `ref "${frame.ref}" not on mounted page`, frame.ref);
				return;
			}
			const fn = (slice as unknown as Record<string, ((v: unknown) => void) | undefined>)[frame.op];
			if (!fn) {
				get().logError(
					"op_not_allowed",
					`op "${frame.op}" not supported by ${slice.type}`,
					frame.ref,
				);
				return;
			}
			fn(frame.payload);
		},
	})),
);
