// CameraCaptureRef: a photo or a video the person takes, held in the tab
// like a picked file. Browser is source of truth.
//
// The kit CameraCapture draws it. A kept take is wrapped as a File and put in
// the node's handle map (./upload-handles.ts) in place of the old one, with
// its `duration`, `width` and `height` as meta, so the value is the upload
// file dict plus those three and every upload command (pull, slice, cancel,
// discard) works on it unchanged. Bytes move only when the program asks.
//
// A kept take and a delete send `{event: "change"}`; every move of the
// camera or the recorder sends `{event: "status", status, error}`, whoever
// caused it. A program cannot put a take in, so a write takes chrome only
// (`mode`, `facing`, `label`, ...). `reset` drops the take, drops a take
// being made and closes the camera, with no change (./capture-node.ts).

import type { Path } from "@nustackdev/ui-core";
import { useEffect, useMemo } from "react";
import {
	CameraCapture,
	type CameraFacing,
	type CameraMode,
	type CameraResolution,
	type CameraTake,
	type CameraTakeMeta,
} from "../../components/ui/camera-capture";
import { Label } from "../../components/ui/field";
import type { PhotoFormat } from "../../lib/capture/support";
import {
	type NodeEntry,
	type NodeProps,
	pathKey,
	useBoolProp,
	useEnumProp,
	useProp,
	useStringProp,
} from "../../tree";
import { captureEntry, useCaptureNode } from "./capture-node";
import { useCommit, useControl } from "./control";
import { addFiles, fileOf, prune, removeFile } from "./upload-handles";

const MODES = ["photo", "video"] as const satisfies readonly CameraMode[];
const FACINGS = ["user", "environment"] as const satisfies readonly CameraFacing[];
const RESOLUTIONS = ["sd", "hd", "fhd"] as const satisfies readonly CameraResolution[];
const FORMATS = ["jpeg", "webp", "png"] as const satisfies readonly PhotoFormat[];

function num(v: unknown): number {
	return typeof v === "number" && Number.isFinite(v) ? v : 0;
}

/** The take the value names, with its file from the handle map; null when none. */
function takeOf(path: Path, raw: unknown): CameraTake | null {
	if (!raw || typeof raw !== "object") return null;
	const v = raw as Record<string, unknown>;
	if (typeof v.key !== "string") return null;
	const file = fileOf(path, v.key);
	if (!file) return null;
	return {
		blob: file,
		mime: file.type,
		duration: num(v.duration),
		width: num(v.width),
		height: num(v.height),
	};
}

function CameraCaptureView({ path }: NodeProps) {
	const raw = useProp<unknown>(path, "value", null);
	const c = useControl(path);
	const { pick } = useCommit(path);
	const { handle, onStatus } = useCaptureNode(path);
	const mode = useEnumProp(path, "mode", MODES, "photo");
	const facing = useEnumProp(path, "facing", FACINGS, "user");
	const resolution = useEnumProp(path, "resolution", RESOLUTIONS, "hd");
	const format = useEnumProp(path, "format", FORMATS, "jpeg");
	const audio = useBoolProp(path, "audio", true);
	const max = num(useProp<unknown>(path, "max_duration", null));
	const aspect = useStringProp(path, "aspect");
	const key = pathKey(path);

	// A Form's reset moves the value without asking the node: the handles follow.
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	useEffect(() => prune(path), [key, raw]);

	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	const take = useMemo(() => takeOf(path, raw), [key, raw]);

	const onTake = (file: File, meta: CameraTakeMeta) =>
		pick(addFiles(path, [file], true, { ...meta }));

	const onDiscard = () => {
		const at = raw && typeof raw === "object" ? (raw as { key?: unknown }).key : null;
		if (typeof at === "string") pick(removeFile(path, at));
	};

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<CameraCapture
				ref={handle}
				{...c.aria}
				label={c.label || (mode === "video" ? "Video camera" : "Camera")}
				take={take}
				onTake={onTake}
				onDiscard={onDiscard}
				onStatus={onStatus}
				mode={mode}
				facing={facing}
				resolution={resolution}
				format={format}
				audio={audio}
				maxDuration={max > 0 ? max : null}
				aspect={aspect}
				disabled={c.disabled}
				readOnly={c.readOnly}
				invalid={c.invalid}
				size={c.size}
				autoFocus={c.autoFocus}
			/>
		</div>
	);
}

export const CameraCaptureRef: NodeEntry = captureEntry(CameraCaptureView);
