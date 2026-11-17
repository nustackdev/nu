// MicCaptureRef -- a person records a sound and the program reads the take.
// Browser is source of truth.
//
// An upload node whose file the browser recorded: the take is kept in the
// node's handle map (./upload-handles.ts) as a picked file is, so every
// upload command (pull, slice, cancel, discard, reset) and every python read
// works on it unchanged. The value is the take's file dict plus `duration`,
// `width` and `height` (0 and 0 for sound), null while there is none.
//
// The kit MicCapture draws the control. A kept take lands as the value with
// one `{event: "change"}`; Delete clears it with one too. The device and the
// recorder report every move as `{event: "status", status, error}`, never the
// same status and error twice in a row.
//
// The program's `reset` drops the take and releases the microphone, a
// recording in progress dropped with it (./capture-node.ts). A Form's reset
// moves only the value; the handles follow it (`prune`).

import { useEffect, useMemo } from "react";
import { Label } from "../../components/ui/field";
import { type CaptureMeta, MicCapture, type MicTake } from "../../components/ui/mic-capture";
import { type NodeEntry, type NodeProps, pathKey, useProp } from "../../tree";
import { captureEntry, useCaptureNode } from "./capture-node";
import { useCommit, useControl } from "./control";
import { addFiles, fileOf, prune, removeFile } from "./upload-handles";

function seconds(raw: unknown): number | null {
	return typeof raw === "number" && Number.isFinite(raw) && raw > 0 ? raw : null;
}

function MicCaptureView({ path }: NodeProps) {
	const raw = useProp<unknown>(path, "value", null);
	const maxDuration = seconds(useProp<unknown>(path, "max_duration", null));
	const processing = useProp<unknown>(path, "processing", true) !== false;
	const c = useControl(path);
	const { pick } = useCommit(path);
	const { handle, onStatus } = useCaptureNode(path);
	const key = pathKey(path);

	// A Form's reset moves the value without asking the node: the handles follow.
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	useEffect(() => prune(path), [key, raw]);

	const fileKey =
		raw && typeof raw === "object" ? (raw as { key?: unknown }).key : (undefined as unknown);
	const duration = raw && typeof raw === "object" ? (raw as { duration?: unknown }).duration : 0;
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	const take = useMemo<MicTake | null>(() => {
		const file = typeof fileKey === "string" ? fileOf(path, fileKey) : null;
		return file ? { blob: file, duration: typeof duration === "number" ? duration : 0 } : null;
	}, [key, fileKey, duration]);

	const onTake = (file: File, meta: CaptureMeta) => {
		pick(addFiles(path, [file], true, { ...meta }));
	};

	const onDiscard = () => {
		if (typeof fileKey === "string") pick(removeFile(path, fileKey));
	};

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<MicCapture
				ref={handle}
				{...c.aria}
				aria-labelledby={c.labelledBy}
				take={take}
				onTake={onTake}
				onDiscard={onDiscard}
				onStatus={onStatus}
				maxDuration={maxDuration}
				processing={processing}
				size={c.size}
				disabled={c.disabled}
				readOnly={c.readOnly}
				invalid={c.invalid}
				autoFocus={c.autoFocus}
			/>
		</div>
	);
}

export const MicCaptureRef: NodeEntry = captureEntry(MicCaptureView);
