// MicCapture: a person records a sound with a microphone and keeps the take.
//
// One dense row, framed like an input of the same size, that changes with
// where the recording is:
//
//   idle       Record (and "Up to 1:00" with a max), a device menu when there are two mics
//   asking     Record busy, "Waiting for the microphone…" (the browser's prompt is up)
//   recording  a red dot that pulses, the time, a level meter, pause, stop, cancel
//   paused     the dot still, the time held, resume, stop, cancel
//   take       the kit Audio row playing the take, Record again, Delete
//   blocked    Record (as "Try again" when trying can help), the reason under the row
//
// Nothing opens on mount: the first click on Record asks for the microphone,
// and recording starts as soon as it opens. The microphone closes again once
// the take is kept or canceled, on disable, on unmount, and when the tab is
// hidden while nothing is recording. A new take replaces the old one only
// once it is kept, so a cancel leaves the old take where it was.
//
// Props only, no tree: the caller holds the take (`take`, a Blob and its
// duration) and hears `onTake(file, meta)` when a recording is kept,
// `onDiscard()` on Delete, and `onStatus(status, error)` on each move of the
// device or the recorder (see lib/capture/support.ts for the words). A device
// lost mid take ends the recording with what it got: that is kept as the take
// and the row says the microphone was disconnected.
//
// `ref` takes `release()`: drop a recording being made and close the
// microphone, for a program's reset.
//
// `readOnly` plays the take and offers nothing else. `disabled` closes the
// microphone (a recording in progress is stopped and kept) and turns every
// control off. The status is said in a polite live region ("Recording",
// "Saved, 0:12"); the meter and the dot are decoration beside it.

import { ChevronDown, Mic, Pause, Play, Square, Trash2, TriangleAlert, X } from "lucide-react";
import * as React from "react";
import {
	blockedText,
	type CaptureError,
	type CaptureStatus,
	canRetry,
	captureBlocker,
	recorderMime,
	takeName,
} from "../../lib/capture/support";
import { useCaptureDevice } from "../../lib/capture/use-capture-device";
import { useLevel } from "../../lib/capture/use-level";
import { type RecordedTake, useRecorder } from "../../lib/capture/use-recorder";
import { formatTime } from "../../lib/media/model";
import { cn } from "../../lib/utils";
import { Audio } from "./audio";
import { Button } from "./button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuLabel,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuTrigger,
} from "./dropdown-menu";
import { IconButton } from "./icon-button";
import { LevelMeter } from "./level-meter";
import { StatusDot } from "./status-dot";
import { TooltipProvider } from "./tooltip";

type Size = "sm" | "md" | "lg";

/** The take the control shows: the recorded sound and how long it runs. */
export interface MicTake {
	blob: Blob;
	/** Seconds, pauses out. */
	duration: number;
}

/** What a kept take adds to its file's value. */
export interface CaptureMeta {
	duration: number;
	width: number;
	height: number;
}

export interface MicCaptureHandle {
	/** Drop a recording being made (never kept) and close the microphone. */
	release: () => void;
}

export interface MicCaptureProps {
	/** The take kept so far, or null. */
	take: MicTake | null;
	/** A recording was kept: the file to hold and its meta. */
	onTake: (file: File, meta: CaptureMeta) => void;
	/** The person deleted the take. */
	onDiscard: () => void;
	/** The device or the recorder moved. Called once per move, never twice the same. */
	onStatus?: (status: CaptureStatus, error: CaptureError) => void;
	/** The longest take in seconds; the recording stops itself there. */
	maxDuration?: number | null;
	/** The browser's voice cleanup (echo, noise, gain). False for music. */
	processing?: boolean;
	size?: Size;
	disabled?: boolean;
	readOnly?: boolean;
	invalid?: boolean;
	autoFocus?: boolean;
	/** Lands on the main button of the moment (Record, Stop, Record again). */
	id?: string;
	"aria-describedby"?: string;
	"aria-labelledby"?: string;
	"aria-required"?: boolean;
	className?: string;
	/** Takes `release()`, for a program's reset. */
	ref?: React.Ref<MicCaptureHandle>;
}

// One row tall at each size: a button of the size with 4px around it.
const FRAME: Record<Size, string> = {
	sm: "min-h-8 gap-1.5 p-1 text-sm",
	md: "min-h-10 gap-2 p-1 text-base",
	lg: "min-h-12 gap-2 p-1 text-lg",
};

const BUTTON: Record<Size, "sm" | "md" | "lg"> = { sm: "sm", md: "md", lg: "lg" };

function limit(raw: number | null | undefined): number | null {
	return typeof raw === "number" && Number.isFinite(raw) && raw > 0 ? raw : null;
}

/** The sound url of a take, made for its blob and revoked when it changes. */
function useBlobUrl(blob: Blob | null): string | undefined {
	const [url, setUrl] = React.useState<string>();
	React.useEffect(() => {
		if (!blob || typeof URL.createObjectURL !== "function") {
			setUrl(undefined);
			return;
		}
		const made = URL.createObjectURL(blob);
		setUrl(made);
		return () => URL.revokeObjectURL(made);
	}, [blob]);
	return url;
}

export function MicCapture({
	take,
	onTake,
	onDiscard,
	onStatus,
	maxDuration,
	processing = true,
	size = "md",
	disabled = false,
	readOnly = false,
	invalid = false,
	autoFocus = false,
	id,
	"aria-describedby": describedBy,
	"aria-labelledby": labelledBy,
	"aria-required": ariaRequired,
	className,
	ref,
}: MicCaptureProps) {
	const max = limit(maxDuration);
	const button = BUTTON[size];

	// The latest callbacks and options, so the recorder's end and the device's
	// loss (which land long after the click) call today's, not the click's.
	const live = React.useRef({ onTake, onStatus, processing });
	live.current = { onTake, onStatus, processing };

	// The device went away mid use: its loss already said blocked, so the
	// take that the loss ends must not close it back to idle.
	const lost = React.useRef(false);
	const device = useCaptureDevice({
		kind: "audio",
		constraints: (deviceId) => {
			const clean = live.current.processing;
			return {
				audio: {
					...(deviceId ? { deviceId: { exact: deviceId } } : {}),
					echoCancellation: clean,
					noiseSuppression: clean,
					autoGainControl: clean,
				},
			};
		},
		onLost: () => {
			lost.current = true;
		},
	});
	const recorder = useRecorder();
	const level = useLevel(device.stream, recorder.state === "recording");

	// A recorder that would not start: the device is closed, the reason kept here.
	const [failure, setFailure] = React.useState<CaptureError>("");
	const [chosen, setChosen] = React.useState<string | null>(null);
	const [said, setSaid] = React.useState("");

	const status: CaptureStatus = failure
		? "blocked"
		: device.status === "blocked"
			? "blocked"
			: recorder.state !== "inactive"
				? recorder.state
				: device.status;
	const error: CaptureError = failure || (device.status === "blocked" ? device.error : "");

	// Focus follows the main button (Record, Stop, Record again) when the row
	// changes shape under it: set when a move starts with focus in the row.
	const root = React.useRef<HTMLDivElement>(null);
	const main = React.useRef<HTMLButtonElement>(null);
	const follow = React.useRef(false);
	const hold = React.useCallback(() => {
		const at = typeof document !== "undefined" ? document.activeElement : null;
		follow.current = Boolean(at && root.current?.contains(at));
	}, []);

	// --- status out: one call per move -------------------------------------------

	const last = React.useRef<{ status: CaptureStatus; error: CaptureError }>({
		status: "idle",
		error: "",
	});
	const report = React.useCallback((s: CaptureStatus, e: CaptureError = "") => {
		if (last.current.status === s && last.current.error === e) return;
		last.current = { status: s, error: e };
		live.current.onStatus?.(s, e);
	}, []);

	// Blocked lands from the device hook (a refusal, a loss) or from a recorder
	// that would not start; every other move is reported where it is made.
	React.useEffect(() => {
		if (status !== "blocked") return;
		report("blocked", error);
		setSaid(
			error === "lost"
				? "Microphone disconnected"
				: `Microphone blocked: ${blockedText("Microphone", error)}`,
		);
	}, [status, error, report]);

	// The device the next open asks for: the one picked, else the one last used.
	React.useEffect(() => {
		if (device.deviceId) setChosen(device.deviceId);
	}, [device.deviceId]);
	const want = chosen && device.devices.some((d) => d.deviceId === chosen) ? chosen : null;

	// --- the take ends -------------------------------------------------------------

	const close = React.useCallback(() => {
		device.close();
		report("idle");
	}, [device.close, report]);

	const done = React.useCallback(
		(got: RecordedTake | null) => {
			hold();
			if (got) {
				const file = new File([got.blob], takeName("recording", got.mime), { type: got.mime });
				live.current.onTake(file, { duration: got.duration, width: 0, height: 0 });
			}
			if (lost.current) {
				if (got) setSaid(`Microphone disconnected. Kept ${formatTime(got.duration)}`);
				return;
			}
			close();
			setSaid(got ? `Saved, ${formatTime(got.duration)}` : "Nothing was recorded");
		},
		[close, hold],
	);

	// --- the person's moves ----------------------------------------------------------

	const opening = React.useRef(false);
	const record = async () => {
		if (disabled || readOnly || opening.current || recorder.state !== "inactive") return;
		hold();
		lost.current = false;
		setFailure("");
		if (!captureBlocker("audio")) {
			report("asking");
			setSaid("Waiting for the microphone");
		}
		opening.current = true;
		const stream = await device.open(want);
		opening.current = false;
		// Refused (the effect above says blocked) or overtaken by a close.
		if (!stream) return;
		report("live");
		const started = recorder.start(stream, {
			mime: recorderMime("audio"),
			maxSeconds: max,
			onDone: done,
		});
		if (!started) {
			device.close();
			setFailure("failed");
			return;
		}
		report("recording");
		setSaid("Recording");
	};

	const stop = () => {
		hold();
		recorder.stop();
	};

	const pause = () => {
		recorder.pause();
		report("paused");
		setSaid("Paused");
	};

	const resume = () => {
		recorder.resume();
		report("recording");
		setSaid("Recording");
	};

	const cancel = () => {
		hold();
		recorder.cancel();
		close();
		setSaid("Recording canceled");
	};

	React.useImperativeHandle(
		ref,
		() => ({
			release: () => {
				recorder.cancel();
				close();
			},
		}),
		[recorder.cancel, close],
	);

	const discard = () => {
		hold();
		onDiscard();
		setSaid("Recording deleted");
	};

	// --- the device closes when it is not in use ----------------------------------------

	// Disabled: a recording in progress is stopped and kept, an idle device closed.
	// biome-ignore lint/correctness/useExhaustiveDependencies: runs when disabled turns on.
	React.useEffect(() => {
		if (!disabled) return;
		if (recorder.state !== "inactive") recorder.stop();
		else if (device.status === "live" || device.status === "asking") close();
	}, [disabled]);

	// Hidden tab: the light goes off unless a take is being made.
	const idleOpen =
		recorder.state === "inactive" && (device.status === "live" || device.status === "asking");
	React.useEffect(() => {
		if (!idleOpen || typeof document === "undefined") return;
		const onHide = () => {
			if (document.hidden) close();
		};
		document.addEventListener("visibilitychange", onHide);
		return () => document.removeEventListener("visibilitychange", onHide);
	}, [idleOpen, close]);

	// --- focus follows the main button as the row changes ---------------------------------

	const url = useBlobUrl(take?.blob ?? null);
	const shape = take && status !== "recording" && status !== "paused" ? "take" : status;
	React.useLayoutEffect(() => {
		if (!follow.current) return;
		const at = document.activeElement;
		if (!(at && at !== document.body && root.current?.contains(at))) main.current?.focus();
		// The open is still on its way: Record comes back as Stop.
		if (shape !== "asking") follow.current = false;
	}, [shape]);

	// --- drawing ------------------------------------------------------------------------

	const recording = status === "recording" || status === "paused";
	const blocked = status === "blocked";
	const retry = blocked && canRetry(error);
	const noTry = blocked && !canRetry(error);
	const reasonId = React.useId();
	const reason = blocked
		? error === "lost"
			? take
				? "The microphone was disconnected. The recording so far was kept."
				: "The microphone was disconnected."
			: blockedText("Microphone", error)
		: "";
	const described = [describedBy, reason ? reasonId : null].filter(Boolean).join(" ") || undefined;
	const mainAria = {
		id,
		"aria-describedby": described,
		"aria-labelledby": labelledBy,
		"aria-invalid": invalid || undefined,
		"aria-required": ariaRequired,
	};

	// The microphone menu: a caret beside the main button, as a split button.
	const names = device.devices.map((d, i) => ({
		id: d.deviceId,
		name: d.label || `Microphone ${i + 1}`,
	}));
	const current = want ?? names[0]?.id ?? "";
	const menu =
		!readOnly && !recording && names.length > 1 ? (
			<DropdownMenu modal={false}>
				<DropdownMenuTrigger asChild>
					<IconButton
						variant="ghost"
						size={button}
						aria-label={`Microphone, ${names.find((n) => n.id === current)?.name ?? ""}`}
						tip="Microphone"
						disabled={disabled || status === "asking"}
					>
						<ChevronDown aria-hidden />
					</IconButton>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end" className="min-w-48">
					<DropdownMenuLabel>Microphone</DropdownMenuLabel>
					<DropdownMenuRadioGroup value={current} onValueChange={setChosen}>
						{names.map((n) => (
							<DropdownMenuRadioItem key={n.id} value={n.id}>
								{n.name}
							</DropdownMenuRadioItem>
						))}
					</DropdownMenuRadioGroup>
				</DropdownMenuContent>
			</DropdownMenu>
		) : null;

	let row: React.ReactNode;
	if (recording) {
		const paused = status === "paused";
		row = (
			<>
				<span className="flex shrink-0 items-center gap-2 pl-2">
					<StatusDot tone="danger" pulse={!paused} />
					<span
						data-slot="mic-capture-time"
						className="whitespace-nowrap font-mono text-xs tabular-nums text-text-primary"
					>
						{formatTime(recorder.elapsed, max ?? 0)}
						{max ? <span className="text-text-muted"> / {formatTime(max)}</span> : null}
					</span>
				</span>
				<LevelMeter level={level} quiet={paused} className="min-w-0 flex-1 overflow-hidden" />
				<IconButton
					variant="ghost"
					size={button}
					aria-label={paused ? "Resume recording" : "Pause recording"}
					tip={paused ? "Resume" : "Pause"}
					disabled={disabled}
					onClick={paused ? resume : pause}
				>
					{paused ? <Play aria-hidden /> : <Pause aria-hidden />}
				</IconButton>
				<Button
					ref={main}
					variant="secondary"
					size={button}
					disabled={disabled}
					{...mainAria}
					onClick={stop}
				>
					<Square aria-hidden className="fill-current" />
					Stop
				</Button>
				<IconButton
					variant="ghost"
					size={button}
					aria-label="Cancel recording"
					tip="Cancel, keep nothing"
					disabled={disabled}
					onClick={cancel}
				>
					<X aria-hidden />
				</IconButton>
			</>
		);
	} else if (take && readOnly) {
		row = (
			<div id={id} className="min-w-0 flex-1">
				<Audio src={url} label="Recording" className={size === "lg" ? "h-10" : "h-8"} />
			</div>
		);
	} else if (readOnly) {
		row = (
			<span id={id} className="px-2 text-text-muted">
				No recording
			</span>
		);
	} else if (take) {
		row = (
			<>
				<div className="min-w-0 flex-1" inert={disabled || undefined}>
					<Audio src={url} label="Recording" className={size === "lg" ? "h-10" : "h-8"} />
				</div>
				<Button
					ref={main}
					variant="ghost"
					size={button}
					disabled={disabled || noTry}
					loading={status === "asking"}
					autoFocus={autoFocus}
					{...mainAria}
					onClick={() => void record()}
				>
					<Mic aria-hidden />
					Record again
				</Button>
				{menu}
				<IconButton
					variant="ghost"
					size={button}
					aria-label="Delete recording"
					tip="Delete"
					disabled={disabled || status === "asking"}
					onClick={discard}
				>
					<Trash2 aria-hidden />
				</IconButton>
			</>
		);
	} else {
		row = (
			<>
				<Button
					ref={main}
					variant="secondary"
					size={button}
					disabled={disabled || noTry}
					loading={status === "asking"}
					autoFocus={autoFocus}
					{...mainAria}
					onClick={() => void record()}
				>
					<Mic aria-hidden />
					{retry ? "Try again" : "Record"}
				</Button>
				{menu}
				<span className="min-w-0 flex-1 truncate text-xs text-text-muted">
					{status === "asking"
						? "Waiting for the microphone…"
						: max
							? `Up to ${formatTime(max)}`
							: ""}
				</span>
			</>
		);
	}

	return (
		<TooltipProvider>
			<div
				data-slot="mic-capture"
				data-status={status}
				className={cn("flex flex-col gap-1", className)}
			>
				<div
					ref={root}
					data-slot="mic-capture-row"
					className={cn(
						"flex w-full min-w-0 items-center rounded-md border bg-bg-surface",
						"transition-[border-color,background-color] duration-fast ease-out",
						FRAME[size],
						disabled
							? "border-border-default bg-bg-sunken opacity-50"
							: invalid
								? "border-status-danger"
								: recording
									? "border-border-strong"
									: "border-border-default",
					)}
				>
					{row}
				</div>
				{reason ? (
					<p
						id={reasonId}
						data-slot="mic-capture-reason"
						className="flex items-start gap-1 text-xs text-status-danger"
					>
						<TriangleAlert aria-hidden className="mt-px size-3 shrink-0" />
						<span>{reason}</span>
					</p>
				) : null}
				<span className="sr-only" aria-live="polite" data-slot="mic-capture-said">
					{said}
				</span>
			</div>
		</TooltipProvider>
	);
}
