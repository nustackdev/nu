// Browser-side store. zustand + immer.
//
// One global store, keyed by ref path. The dispatcher is a one-liner over
// the slice for that path: `store.refs[ref][op](payload)`. The dispatcher
// understands only the three reserved lifecycle ops (mount, unmount, error).
// Everything else is routed to the slice's matching method.

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
	type ErrorCode,
	type Frame,
	type MountPayload,
	OP_ERROR,
	OP_MOUNT,
	OP_UNMOUNT,
} from "./protocol";
import { factories, type RefSlice } from "./slices";

type Status = "connecting" | "connected" | "disconnected";

type State = {
	status: Status;
	page: MountPayload | null;
	refs: Record<string, RefSlice>;
};

type Actions = {
	setStatus: (s: Status) => void;
	dispatch: (frame: Frame) => void;
	mount: (payload: MountPayload) => void;
	unmount: () => void;
	logError: (code: ErrorCode, message: string, ref?: string) => void;
};

export const useStore = create<State & Actions>()(
	immer((set, get) => ({
		status: "connecting",
		page: null,
		refs: {},

		setStatus: (s) =>
			set((draft) => {
				draft.status = s;
			}),

		mount: (payload) =>
			set((draft) => {
				draft.page = payload;
				draft.refs = {};
				const setter = (mutator: (refs: Record<string, RefSlice>) => void) =>
					set((d) => {
						mutator(d.refs);
					});
				for (const field of payload.fields) {
					const factory = factories[field.type];
					if (!factory) {
						console.warn(`nudle: no factory for Ref type "${field.type}"`);
						continue;
					}
					draft.refs[field.path] = factory(field.path, setter);
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
