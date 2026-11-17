// CameraCapture: a photo or a video a person takes with a camera, in place.
//
// Props only, no tree. The take comes in as `take` (a Blob and its meta) and
// goes out through `onTake(file, meta)` and `onDiscard()`; the
// CameraCaptureRef node (nodes/input/camera-capture.tsx) keeps it in its
// handle map. `onStatus` hears every move of the device and the recorder,
// once per move.
//
// One frame holds every state, so the page does not jump between them:
//
//   idle      a quiet empty well with "Open camera"; or the take, with
//             Retake and Delete under it
//   asking    a spinner while the browser asks for the camera
//   live      the preview, a bar with close, the shutter (photo) or record
//             (video), flip with two cameras or more, a camera menu with
//             more than one listed
//   recording a red dot and the time, pause or resume, stop (keeps) and
//             discard (drops)
//   blocked   why, in words, and Retry when trying again can help
//
// Nothing opens on mount: the first click asks. The camera closes as soon as
// it is not in use: a take kept or dropped, close, disable, read only,
// unmount, and the tab hidden while not recording. A new take stays out of
// the value until it is kept, so Retake never loses the old one.
//
// The preview of a camera that faces the person is mirrored, as a mirror
// reads. The photo is the camera's full frame at its own size, never
// mirrored, and so is the video. The preview shows the whole frame
// (contain), so what the frame shows is what the take holds.
//
// The frame keeps `aspect` when given, else the camera's own shape once it
// is known (the take's, while one shows), 4/3 until then. It is a dark stage
// while it shows a picture, like the kit Video; the bar sits on the same
// scrim, in an `.on-media` subtree.
//
// `ref` takes `release()`: drop a take being made and close the camera, for
// a reset that comes from outside.

import {
	Camera,
	CameraOff,
	Circle,
	Pause,
	Play,
	RotateCcw,
	Square,
	SwitchCamera,
	Trash2,
	Video as VideoGlyph,
	Webcam,
	X,
} from "lucide-react";
import * as React from "react";
import {
	blockedText,
	type CaptureError,
	type CaptureStatus,
	canRecord,
	canRetry,
	type PhotoFormat,
	photoMime,
	recorderMime,
	takeName,
} from "../../lib/capture/support";
import { useCaptureDevice } from "../../lib/capture/use-capture-device";
import { useRecorder } from "../../lib/capture/use-recorder";
import { formatTime } from "../../lib/media/model";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuLabel,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuTrigger,
} from "./dropdown-menu";
import { EmptyState } from "./empty-state";
import { IconButton } from "./icon-button";
import { Image } from "./image";
import { ImageViewer } from "./image-viewer";
import { Spinner } from "./spinner";
import { TooltipProvider } from "./tooltip";
import { Video } from "./video";

export type CameraMode = "photo" | "video";
export type CameraFacing = "user" | "environment";
export type CameraResolution = "sd" | "hd" | "fhd";

/** What a take carries beside its bytes. `duration` is 0 for a photo. */
export interface CameraTakeMeta {
	duration: number;
	width: number;
	height: number;
}

/** The take on show: the file the node holds, and its meta. */
export interface CameraTake extends CameraTakeMeta {
	blob: Blob;
	mime: string;
}

export interface CameraCaptureHandle {
	/** Drop a take being made and close the camera. */
	release: () => void;
}

export interface CameraCaptureProps {
	take: CameraTake | null;
	/** A take was kept: the file and its meta. */
	onTake: (file: File, meta: CameraTakeMeta) => void;
	/** The person deleted the take. */
	onDiscard: () => void;
	/** Every move of the device or the recorder, once each. */
	onStatus?: (status: CaptureStatus, error: CaptureError) => void;
	mode?: CameraMode;
	/** The camera the first open asks for. */
	facing?: CameraFacing;
	resolution?: CameraResolution;
	format?: PhotoFormat;
	/** A video records sound too. */
	audio?: boolean;
	/** The longest video, in seconds; null for no limit. */
	maxDuration?: number | null;
	/** The frame's css ratio ("4/3"); "" follows the camera. */
	aspect?: string;
	/** The control's accessible name. */
	label?: string;
	disabled?: boolean;
	readOnly?: boolean;
	invalid?: boolean;
	size?: "sm" | "md" | "lg";
	autoFocus?: boolean;
	/** Lands on the control's main button, so a `<label for>` names it. */
	id?: string;
	"aria-describedby"?: string;
	"aria-invalid"?: boolean;
	"aria-required"?: boolean;
	className?: string;
	ref?: React.Ref<CameraCaptureHandle>;
}

const RESOLUTIONS: Record<CameraResolution, [number, number]> = {
	sd: [640, 480],
	hd: [1280, 720],
	fhd: [1920, 1080],
};

/** Bar glyph buttons, the round main button, and the buttons under the frame. */
const BAR: Record<"sm" | "md" | "lg", "xs" | "sm" | "md"> = { sm: "xs", md: "sm", lg: "md" };
const MAIN: Record<"sm" | "md" | "lg", "md" | "lg"> = { sm: "md", md: "lg", lg: "lg" };

/** Formats a video records in with no sound: no audio codec named. */
const SILENT_VIDEO = [
	"video/webm;codecs=vp9",
	"video/webm;codecs=vp8",
	"video/webm",
	"video/mp4;codecs=avc1",
	"video/mp4",
];

function videoMime(sound: boolean): string {
	if (sound) return recorderMime("video");
	if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
	return SILENT_VIDEO.find((m) => MediaRecorder.isTypeSupported(m)) ?? "";
}

function videoSettings(stream: MediaStream | null): MediaTrackSettings {
	return stream?.getVideoTracks()[0]?.getSettings?.() ?? {};
}

function deviceOf(stream: MediaStream | null): string | null {
	const id = videoSettings(stream).deviceId;
	return typeof id === "string" && id !== "" ? id : null;
}

/**
 * The frame on show, at the camera's own size, as an encoded image. Null
 * when there is no frame yet or the browser cannot encode it.
 */
export function grabFrame(
	video: HTMLVideoElement,
	fallback: { width?: number; height?: number },
	mime: string,
): Promise<{ blob: Blob; width: number; height: number } | null> {
	const width = video.videoWidth || fallback.width || 0;
	const height = video.videoHeight || fallback.height || 0;
	if (!width || !height) return Promise.resolve(null);
	const canvas = document.createElement("canvas");
	canvas.width = width;
	canvas.height = height;
	const g = canvas.getContext("2d");
	if (!g) return Promise.resolve(null);
	g.drawImage(video, 0, 0, width, height);
	return new Promise((resolve) => {
		// png ignores the quality.
		canvas.toBlob((blob) => resolve(blob ? { blob, width, height } : null), mime, 0.92);
	});
}

/** An object url for the take, revoked when it changes and on unmount. */
function useObjectUrl(blob: Blob | null): string | undefined {
	const [url, setUrl] = React.useState<string | undefined>(undefined);
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

export function CameraCapture({
	take,
	onTake,
	onDiscard,
	onStatus,
	mode = "photo",
	facing: facingProp = "user",
	resolution = "hd",
	format = "jpeg",
	audio = true,
	maxDuration = null,
	aspect = "",
	label = "Camera",
	disabled = false,
	readOnly = false,
	invalid = false,
	size = "md",
	autoFocus,
	id,
	"aria-describedby": describedBy,
	"aria-invalid": ariaInvalid,
	"aria-required": ariaRequired,
	className,
	ref,
}: CameraCaptureProps) {
	const video = mode === "video";
	const sound = video && audio;

	// What an open asks for, read at the time of the open (a flip sets the
	// facing and opens in one go, before a render).
	const facingRef = React.useRef<CameraFacing>(facingProp);
	const chosen = React.useRef<string | null>(null);
	const wants = React.useRef({ sound, resolution });
	wants.current = { sound, resolution };
	const [facing, setFacing] = React.useState<CameraFacing>(facingProp);
	const lost = React.useRef(false);

	const rec = useRecorder();
	const dev = useCaptureDevice({
		kind: "video",
		constraints: (deviceId) => {
			const [w, h] = RESOLUTIONS[wants.current.resolution];
			return {
				video: {
					width: { ideal: w },
					height: { ideal: h },
					...(deviceId
						? { deviceId: { exact: deviceId } }
						: { facingMode: { ideal: facingRef.current } }),
				},
				audio: wants.current.sound,
			};
		},
		onLost: () => {
			lost.current = true;
			// A take in progress keeps what it has.
			rec.stop();
		},
	});

	const [failed, setFailed] = React.useState<CaptureError>("");
	const [note, setNote] = React.useState("");
	// A take that did not happen: said under the frame, not only to a screen reader.
	const [trouble, setTrouble] = React.useState("");
	const [flash, setFlash] = React.useState(0);
	const [viewing, setViewing] = React.useState(false);
	const [shape, setShape] = React.useState<string | null>(null);
	const preview = React.useRef<HTMLVideoElement | null>(null);
	const main = React.useRef<HTMLButtonElement | null>(null);
	const refocus = React.useRef(false);

	const status: CaptureStatus = failed
		? "blocked"
		: rec.state === "recording"
			? "recording"
			: rec.state === "paused"
				? "paused"
				: dev.status;
	const error: CaptureError = status === "blocked" ? failed || dev.error : "";
	const making = rec.state !== "inactive";

	// The latest callbacks, for a take that lands after the render it began in.
	const said = React.useRef({ onTake, onStatus });
	said.current = { onTake, onStatus };

	const close = React.useCallback(() => {
		rec.cancel();
		dev.close();
		setFailed("");
	}, [rec.cancel, dev.close]);

	React.useImperativeHandle(ref, () => ({ release: close }), [close]);

	// One status out per move, never a repeat; the first idle is no move.
	const last = React.useRef({ status: "idle" as CaptureStatus, error: "" as CaptureError });
	React.useEffect(() => {
		if (last.current.status === status && last.current.error === error) return;
		last.current = { status, error };
		said.current.onStatus?.(status, error);
	}, [status, error]);

	// The prop moves the next open, and drops a camera the person chose.
	React.useEffect(() => {
		facingRef.current = facingProp;
		chosen.current = null;
		setFacing(facingProp);
	}, [facingProp]);

	// Off, or nothing to change: the camera closes. A video being made is
	// stopped and kept, never thrown away (as the mic does).
	// biome-ignore lint/correctness/useExhaustiveDependencies: runs when disabled or readOnly turns on.
	React.useEffect(() => {
		if (!disabled && !readOnly) return;
		if (rec.state !== "inactive") rec.stop();
		else close();
	}, [disabled, readOnly]);

	// A hidden tab does not keep the light on, unless a take is being made.
	const idleOpen = React.useRef(false);
	idleOpen.current = (status === "live" || status === "asking") && !making;
	React.useEffect(() => {
		const onHide = () => {
			if (document.visibilityState === "hidden" && idleOpen.current) close();
		};
		document.addEventListener("visibilitychange", onHide);
		return () => document.removeEventListener("visibilitychange", onHide);
	}, [close]);

	// A mode or sound change while live keeps the camera open, with or without
	// its microphone as the new mode needs.
	const devRef = React.useRef(dev);
	devRef.current = dev;
	React.useEffect(() => {
		const d = devRef.current;
		if (d.status !== "live" || !d.stream) return;
		if (d.stream.getAudioTracks().length > 0 !== sound) void d.open(d.deviceId);
	}, [sound]);

	// A new stream has a shape of its own.
	// biome-ignore lint/correctness/useExhaustiveDependencies: reset on stream change only.
	React.useEffect(() => setShape(null), [dev.stream]);

	// After a person's action the view changes under the focus: the new main button takes it.
	React.useEffect(() => {
		if (!refocus.current || !main.current) return;
		refocus.current = false;
		if (document.activeElement !== main.current) main.current.focus();
	});

	const open = (deviceId: string | null = chosen.current) => {
		setNote("");
		setTrouble("");
		setFailed("");
		lost.current = false;
		refocus.current = true;
		if (video && !canRecord()) {
			setFailed("unsupported");
			return;
		}
		void dev.open(deviceId);
	};

	const settings = videoSettings(dev.stream);
	// A camera that does not say which way it faces faces the way it was asked to.
	const mirrored = settings.facingMode ? settings.facingMode === "user" : facing === "user";

	const shoot = async () => {
		const v = preview.current;
		if (!v || !dev.stream) return;
		setFlash((n) => n + 1);
		const mime = photoMime(format);
		const got = await grabFrame(v, settings, mime);
		if (!got) {
			setTrouble("The photo could not be taken. Try again.");
			return;
		}
		const type = got.blob.type || mime;
		const file = new File([got.blob], takeName("photo", type), { type });
		said.current.onTake(file, { duration: 0, width: got.width, height: got.height });
		setNote("Photo taken");
		refocus.current = true;
		dev.close();
	};

	const record = () => {
		const stream = dev.stream;
		if (!stream) return;
		const v = preview.current;
		const dims = {
			width: v?.videoWidth || settings.width || 0,
			height: v?.videoHeight || settings.height || 0,
		};
		const started = rec.start(stream, {
			mime: videoMime(stream.getAudioTracks().length > 0),
			maxSeconds: maxDuration,
			onDone: (t) => {
				if (t) {
					const file = new File([t.blob], takeName("video", t.mime), { type: t.mime });
					said.current.onTake(file, { duration: t.duration, ...dims });
					setNote(`Saved, ${formatTime(t.duration)}`);
				} else {
					setTrouble("Nothing was recorded. Try again.");
				}
				refocus.current = true;
				// A lost camera stays blocked, so the person hears why.
				if (!lost.current) dev.close();
			},
		});
		if (!started) setFailed("failed");
		else refocus.current = true;
	};

	const flip = async () => {
		const before = dev.deviceId;
		const now = settings.facingMode;
		if (now === "user" || now === "environment") {
			const next: CameraFacing = now === "user" ? "environment" : "user";
			facingRef.current = next;
			chosen.current = null;
			setFacing(next);
			const got = await dev.open(null);
			// A camera that answered with the same device has no other facing: walk the list.
			if (!got || deviceOf(got) !== before) return;
		}
		const list = dev.devices;
		if (list.length < 2) return;
		const at = list.findIndex((d) => d.deviceId === before);
		const next = list[(at + 1) % list.length];
		if (!next) return;
		chosen.current = next.deviceId;
		void dev.open(next.deviceId);
	};

	const pickDevice = (deviceId: string) => {
		chosen.current = deviceId;
		void dev.open(deviceId);
	};

	const remove = () => {
		onDiscard();
		setNote(video ? "Video deleted" : "Photo deleted");
		refocus.current = true;
	};

	const url = useObjectUrl(take?.blob ?? null);
	const takeShape =
		take && take.width > 0 && take.height > 0 ? `${take.width} / ${take.height}` : null;
	const liveShape =
		shape ?? (settings.width && settings.height ? `${settings.width} / ${settings.height}` : null);

	// What shows in the frame.
	const capturing = !disabled && !readOnly && status !== "idle";
	const media = capturing ? status !== "asking" && status !== "blocked" : Boolean(take && url);
	const ratio = aspect || (capturing ? liveShape : null) || takeShape || "4 / 3";

	// The main button of the view carries the id and the aria a label and a
	// Field point at; with none (read only, asking) the frame carries them.
	const showsTake = !capturing && Boolean(take);
	const takeRow = showsTake && !readOnly;
	let placed = takeRow;
	const mainProps = {
		ref: main,
		id,
		"aria-describedby": describedBy,
		"aria-invalid": ariaInvalid,
		"aria-required": ariaRequired,
	};
	const mainFor = () => {
		placed = true;
		return mainProps;
	};
	const noun = video ? "video" : "photo";
	const live =
		status === "asking"
			? "Waiting for the camera"
			: status === "live"
				? video
					? "Camera on, ready to record"
					: "Camera on, ready to take a photo"
				: status === "recording"
					? "Recording"
					: status === "paused"
						? "Paused"
						: status === "blocked"
							? `Camera blocked: ${blockedText("Camera", error)}`
							: note;
	const time = `${formatTime(rec.elapsed, maxDuration ?? 0)}${
		maxDuration ? ` / ${formatTime(maxDuration, maxDuration)}` : ""
	}`;

	let body: React.ReactNode;
	if (capturing && status === "asking") {
		body = (
			<EmptyState
				className="absolute inset-0"
				size="sm"
				icon={<Spinner size="lg" tone="neutral" label="Waiting for the camera" />}
			>
				Waiting for the camera…
			</EmptyState>
		);
	} else if (capturing && status === "blocked") {
		const retry = canRetry(error);
		body = (
			<EmptyState
				className="absolute inset-0"
				size="sm"
				icon={<CameraOff aria-hidden="true" />}
				action={
					retry || take ? (
						<div className="flex items-center gap-2">
							{retry ? (
								<Button {...mainFor()} variant="secondary" size={BAR[size]} onClick={() => open()}>
									<RotateCcw aria-hidden="true" />
									Try again
								</Button>
							) : null}
							{take ? (
								<Button
									variant="ghost"
									size={BAR[size]}
									onClick={() => {
										refocus.current = true;
										close();
									}}
									{...(retry ? {} : mainFor())}
								>
									Back to the {noun}
								</Button>
							) : null}
						</div>
					) : undefined
				}
			>
				{blockedText("Camera", error)}
			</EmptyState>
		);
	} else if (capturing) {
		body = (
			<>
				<video
					ref={(el) => {
						preview.current = el;
						if (el && el.srcObject !== dev.stream) el.srcObject = dev.stream;
					}}
					data-slot="camera-preview"
					aria-label="Camera preview"
					autoPlay
					muted
					playsInline
					onLoadedMetadata={(e) => {
						const v = e.currentTarget;
						if (v.videoWidth > 0 && v.videoHeight > 0)
							setShape(`${v.videoWidth} / ${v.videoHeight}`);
					}}
					className={cn("absolute inset-0 size-full object-contain", mirrored && "-scale-x-100")}
				/>
				{making ? (
					<div
						data-slot="camera-time"
						className="on-media absolute top-2 left-2 flex items-center gap-1.5 rounded-sm bg-media-scrim px-1.5 py-0.5 font-mono text-xs tabular-nums"
					>
						<span
							aria-hidden="true"
							className={cn(
								"size-2 rounded-full bg-status-danger",
								status === "recording" ? "animate-pulse motion-reduce:animate-none" : "opacity-60",
							)}
						/>
						{status === "paused" ? <span className="sr-only">Paused, </span> : null}
						{time}
					</div>
				) : null}
				<div
					data-slot="camera-bar"
					className={cn(
						"on-media absolute inset-x-0 bottom-0 grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-2.5 pt-8 pb-2",
						"bg-linear-to-t from-media-scrim via-media-scrim/45 to-transparent",
					)}
				>
					<div className="flex items-center justify-start">
						{making ? (
							<IconButton
								variant="ghost"
								size={BAR[size]}
								aria-label="Discard recording"
								tip="Discard recording"
								tipSide="top"
								onClick={() => {
									refocus.current = true;
									close();
								}}
							>
								<Trash2 />
							</IconButton>
						) : (
							<IconButton
								variant="ghost"
								size={BAR[size]}
								aria-label="Close camera"
								tip="Close camera"
								tipSide="top"
								onClick={() => {
									refocus.current = true;
									close();
								}}
							>
								<X />
							</IconButton>
						)}
					</div>
					<div className="flex items-center justify-center">
						{making ? (
							<IconButton
								{...mainFor()}
								variant="secondary"
								size={MAIN[size]}
								className="rounded-full"
								aria-label="Stop and keep"
								tip="Stop and keep"
								tipSide="top"
								onClick={rec.stop}
							>
								<Square className="fill-status-danger text-status-danger" />
							</IconButton>
						) : video ? (
							<IconButton
								{...mainFor()}
								variant="secondary"
								size={MAIN[size]}
								className="rounded-full"
								aria-label="Start recording"
								tip="Start recording"
								tipSide="top"
								disabled={status !== "live"}
								onClick={record}
							>
								<Circle className="fill-status-danger text-status-danger" />
							</IconButton>
						) : (
							<IconButton
								{...mainFor()}
								variant="secondary"
								size={MAIN[size]}
								className="rounded-full"
								aria-label="Take photo"
								tip="Take photo"
								tipSide="top"
								disabled={status !== "live"}
								onClick={() => void shoot()}
							>
								<Circle className="fill-current" />
							</IconButton>
						)}
					</div>
					<div className="flex items-center justify-end gap-0.5">
						{making ? (
							status === "paused" ? (
								<IconButton
									variant="ghost"
									size={BAR[size]}
									aria-label="Resume recording"
									tip="Resume"
									tipSide="top"
									onClick={rec.resume}
								>
									<Play className="fill-current" />
								</IconButton>
							) : (
								<IconButton
									variant="ghost"
									size={BAR[size]}
									aria-label="Pause recording"
									tip="Pause"
									tipSide="top"
									onClick={rec.pause}
								>
									<Pause className="fill-current" />
								</IconButton>
							)
						) : (
							<>
								{dev.devices.length > 1 ? (
									<IconButton
										variant="ghost"
										size={BAR[size]}
										aria-label="Switch camera"
										tip="Switch camera"
										tipSide="top"
										onClick={() => void flip()}
									>
										<SwitchCamera />
									</IconButton>
								) : null}
								{dev.devices.length > 1 ? (
									<DropdownMenu modal={false}>
										<DropdownMenuTrigger asChild>
											<IconButton
												variant="ghost"
												size={BAR[size]}
												aria-label="Choose camera"
												tip="Choose camera"
												tipSide="top"
											>
												<Webcam />
											</IconButton>
										</DropdownMenuTrigger>
										<DropdownMenuContent align="end" side="top" className="min-w-40">
											<DropdownMenuLabel>Camera</DropdownMenuLabel>
											<DropdownMenuRadioGroup value={dev.deviceId ?? ""} onValueChange={pickDevice}>
												{dev.devices.map((d, i) => (
													<DropdownMenuRadioItem key={d.deviceId} value={d.deviceId}>
														{d.label || `Camera ${i + 1}`}
													</DropdownMenuRadioItem>
												))}
											</DropdownMenuRadioGroup>
										</DropdownMenuContent>
									</DropdownMenu>
								) : null}
							</>
						)}
					</div>
				</div>
			</>
		);
	} else if (take && url) {
		body = take.mime.startsWith("video/") ? (
			<Video
				src={url}
				label="Recorded video"
				radius="none"
				aspectRatio={ratio}
				className="absolute inset-0 size-full"
			/>
		) : (
			<button
				type="button"
				data-slot="camera-photo"
				aria-label="View the photo full size"
				disabled={disabled}
				onClick={() => setViewing(true)}
				className={cn(
					"absolute inset-0 size-full cursor-zoom-in outline-hidden",
					"focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
				)}
			>
				<Image
					src={url}
					alt="The photo taken"
					radius="none"
					fit="contain"
					loading="eager"
					className="size-full bg-transparent"
				/>
			</button>
		);
	} else if (readOnly) {
		body = (
			<EmptyState
				className="absolute inset-0"
				size="sm"
				icon={video ? <VideoGlyph aria-hidden="true" /> : <Camera aria-hidden="true" />}
			>
				{video ? "No video" : "No photo"}
			</EmptyState>
		);
	} else {
		body = (
			<EmptyState
				className="absolute inset-0"
				size="sm"
				icon={video ? <VideoGlyph aria-hidden="true" /> : <Camera aria-hidden="true" />}
				action={
					<Button
						{...mainFor()}
						variant="secondary"
						size={BAR[size]}
						disabled={disabled}
						// The frame fades as a whole; the button does not fade twice.
						className="disabled:opacity-100"
						autoFocus={autoFocus}
						onClick={() => open()}
					>
						<Camera aria-hidden="true" />
						Open camera
					</Button>
				}
			/>
		);
	}

	return (
		<TooltipProvider>
			<div
				data-slot="camera-capture"
				data-status={status}
				className={cn("flex w-full flex-col gap-1.5", className)}
			>
				{/* biome-ignore lint/a11y/useSemanticElements: a labelled region, not a form section */}
				<div
					data-slot="camera-frame"
					role="group"
					aria-label={label}
					id={placed ? undefined : id}
					aria-describedby={placed ? undefined : describedBy}
					inert={disabled || undefined}
					className={cn(
						"relative w-full overflow-hidden rounded-md border bg-bg-sunken text-text-primary",
						media && "dark",
						invalid
							? "border-status-danger"
							: media
								? "border-transparent"
								: "border-border-default",
						disabled && "cursor-not-allowed opacity-50",
					)}
					style={{ aspectRatio: ratio }}
				>
					{body}
					{flash > 0 ? (
						<span
							key={flash}
							aria-hidden="true"
							className="pointer-events-none absolute inset-0 bg-media-fg fill-mode-forwards animate-out fade-out duration-slow ease-in motion-reduce:hidden"
						/>
					) : null}
				</div>
				{takeRow ? (
					<div data-slot="camera-take" className="flex items-center gap-2">
						<span className="min-w-0 flex-1 truncate font-mono text-xs tabular-nums text-text-muted">
							{take && take.duration > 0
								? formatTime(take.duration)
								: take && take.width > 0
									? `${take.width} × ${take.height}`
									: ""}
						</span>
						<Button
							{...mainFor()}
							variant="secondary"
							size={BAR[size]}
							disabled={disabled}
							onClick={() => open()}
						>
							<RotateCcw aria-hidden="true" />
							Retake
						</Button>
						<Button variant="ghost" size={BAR[size]} disabled={disabled} onClick={remove}>
							<Trash2 aria-hidden="true" />
							Delete
						</Button>
					</div>
				) : null}
				{trouble ? <p className="text-sm text-text-secondary">{trouble}</p> : null}
				<span className="sr-only" aria-live="polite">
					{trouble || live}
				</span>
				{viewing && url ? (
					<ImageViewer
						src={url}
						alt="The photo taken"
						className="hidden"
						expanded
						onExpandedChange={setViewing}
					/>
				) : null}
			</div>
		</TooltipProvider>
	);
}
