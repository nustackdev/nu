// Browser-side store. zustand + immer.
//
// One global store keyed by ref path. A path is a list of segments, so the
// key is its `refKey` serialization -- slices carry that key around and
// `send` turns it back into a path on the way out. Dispatcher routes inbound
// frames to per-slice methods. Outbound frames go through `send` (set by App
// once the ws is open). Server-initiated reads are answered by calling the
// slice's optional `get()` and shipping back a frame with the same id.

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
	type ErrorCode,
	type Frame,
	type KeyedFrame,
	type MountField,
	type MountPayload,
	OP_ERROR,
	OP_MOUNT,
	OP_READ,
	OP_UNMOUNT,
	refKey,
	refPath,
} from "@nustackdev/ui-core";
import { factories } from "./refs";
import type { RefSlice } from "./refs/types";

type Status = "connecting" | "connected" | "disconnected" | "reconnecting";

type State = {
	status: Status;
	page: MountPayload | null;
	refs: Record<string, RefSlice>;
};

type Actions = {
	setStatus: (s: Status) => void;
	setSender: (send: (f: Frame) => void) => void;
	send: (frame: KeyedFrame) => void;
	setLocal: (path: string, value: unknown) => void;
	dispatch: (frame: Frame) => void;
	mount: (payload: MountPayload) => void;
	unmount: () => void;
	logError: (code: ErrorCode, message: string, ref?: string) => void;
};

let outbound: ((f: Frame) => void) | null = null;

function disposeAll(refs: Record<string, RefSlice>): void {
	for (const path in refs) {
		const dispose = refs[path].dispose;
		if (dispose) {
			try {
				dispose();
			} catch (err) {
				console.warn(`nudle: dispose threw for ${path}`, err);
			}
		}
	}
}

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
			if (outbound) outbound({ ...frame, ref: refPath(frame.ref) });
		},

		setLocal: (path, value) =>
			set((draft) => {
				if (draft.refs[path]) draft.refs[path].value = value;
			}),

		mount: (payload) =>
			set((draft) => {
				disposeAll(draft.refs);
				draft.page = payload;
				draft.refs = {};
				const ctx = {
					set: (mutator: (refs: Record<string, RefSlice>) => void) =>
						set((d) => {
							mutator(d.refs);
						}),
					send: (f: KeyedFrame) => {
						if (outbound) outbound({ ...f, ref: refPath(f.ref) });
					},
				};
				const build = (field: MountField) => {
					const factory = factories[field.type];
					if (!factory) {
						console.warn(`nudle: no factory for Ref type "${field.type}"`);
						return;
					}
					// Layout entries (Section subclasses) carry nested `fields`.
					// Pass child paths to the factory so layout slices know what
					// to render. Then recurse so every leaf gets registered.
					const key = refKey(field.path);
					const childPaths = (field.fields ?? []).map((f) => refKey(f.path));
					draft.refs[key] = factory(key, ctx, field.props, childPaths);
					for (const child of field.fields ?? []) build(child);
				};
				// Structural Refs (Index-level: TitleRef, NavRef, ...).
				for (const f of payload.fields) build(f);
				// Page subtrees: every page mounted, flat-keyed by prefixed path.
				for (const p of payload.pages ?? []) {
					for (const f of p.fields) build(f);
				}
			}),

		unmount: () =>
			set((draft) => {
				disposeAll(draft.refs);
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
			const key = refKey(frame.ref);
			if (frame.op === OP_ERROR) {
				const p = frame.payload as { code: ErrorCode; message: string };
				get().logError(p.code, p.message, key);
				return;
			}
			if (frame.op === OP_READ) {
				// Server is asking for our current value. Reply with the
				// same id so the server's future resolves.
				const slice = get().refs[key];
				const value = slice?.get ? slice.get() : (slice?.value ?? null);
				get().send({ op: OP_READ, ref: key, payload: value, id: frame.id });
				return;
			}
			const slice = get().refs[key];
			if (!slice) {
				get().logError("ref_not_found", `ref ${key} not on mounted page`, key);
				return;
			}
			const fn = (slice as unknown as Record<string, ((v: unknown) => void) | undefined>)[frame.op];
			if (!fn) {
				get().logError(
					"op_not_allowed",
					`op "${frame.op}" not supported by ${slice.type}`,
					key,
				);
				return;
			}
			fn(frame.payload);
		},
	})),
);
