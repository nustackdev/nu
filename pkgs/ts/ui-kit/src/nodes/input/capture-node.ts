// The node half both capture nodes share (MicCaptureRef, CameraCaptureRef).
//
// A capture node is an upload node (./upload.tsx) whose file the kit control
// recorded, so `captureEntry` is `uploadEntry` with one change: the
// program's `reset` also releases the device. It reaches the drawn control
// through its `release()` handle, registered here by path while it is
// mounted, so a recording in progress is dropped (never kept) and the light
// goes off before the take is cleared.
//
// `useCaptureNode` gives the view the handle to pass as `ref` and the
// `onStatus` to pass on: each move goes out as `{event: "status", status,
// error}` (the controls already say each move once). A control that goes
// away while in use (a hidden branch, not a removed node) closes its device
// without a word, so the node says `idle` for it.

import type { Path } from "@nustackdev/ui-core";
import { useCallback, useEffect, useRef } from "react";
import type { CaptureError, CaptureStatus } from "../../lib/capture/support";
import { type NodeEntry, pathKey, useEmit } from "../../tree";
import { uploadEntry } from "./upload";
import { uploadHandlers } from "./upload-handles";

/** The event a capture node sends on each move of its device or recorder. */
const STATUS = "status";

/** What a capture control hands its `ref`. */
export interface Releasable {
	/** Drop a take being made and close the device. */
	release: () => void;
}

/** Each drawn capture node's way to let its device go, by path. */
const releasers = new Map<string, () => void>();

export function useCaptureNode(path: Path) {
	const emit = useEmit(path);
	const key = pathKey(path);
	const handle = useRef<Releasable>(null);
	const last = useRef<CaptureStatus>("idle");

	useEffect(() => {
		const release = () => handle.current?.release();
		releasers.set(key, release);
		return () => {
			if (releasers.get(key) === release) releasers.delete(key);
			if (last.current !== "idle") {
				last.current = "idle";
				emit(STATUS, { status: "idle", error: "" });
			}
		};
	}, [key, emit]);

	const onStatus = useCallback(
		(status: CaptureStatus, error: CaptureError) => {
			last.current = status;
			emit(STATUS, { status, error });
		},
		[emit],
	);

	return { handle, onStatus };
}

/** The registry entry of a capture node: an upload entry whose reset frees the device. */
export function captureEntry(component: NodeEntry["component"]): NodeEntry {
	const entry = uploadEntry(component, () => null);
	return {
		...entry,
		handlers: {
			...entry.handlers,
			reset: (ctx, payload) => {
				releasers.get(pathKey(ctx.path))?.();
				uploadHandlers.reset?.(ctx, payload);
			},
		},
	};
}
