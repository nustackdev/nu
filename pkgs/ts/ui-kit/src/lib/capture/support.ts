// What a capture needs from the browser, and the names for what goes wrong.
//
// Devices come only to a secure context (https, or localhost), through
// `navigator.mediaDevices`, and a take needs `MediaRecorder`. Each browser
// records its own formats: Chrome and Firefox webm with opus (and vp8/vp9),
// Safari mp4 with aac (and h264). So the mime is asked for, never assumed:
// `recorderMime` walks a list in order of preference and takes the first the
// browser says it can make.
//
// A failed `getUserMedia` throws a DOMException whose name says why;
// `mediaError` folds those names into the few codes a person can act on.

/** Where a capture node is. See the task contract, section 3. */
export type CaptureStatus = "idle" | "asking" | "live" | "recording" | "paused" | "blocked";

/** Why a device cannot be used, or went away. "" when nothing is wrong. */
export type CaptureError =
	| ""
	| "denied"
	| "no_device"
	| "busy"
	| "insecure"
	| "unsupported"
	| "lost"
	| "failed";

export type CaptureKind = "audio" | "video";

/** Why this page cannot capture at all, before anything is asked; "" when it can. */
export function captureBlocker(kind: CaptureKind = "audio"): "" | "insecure" | "unsupported" {
	if (typeof window === "undefined") return "unsupported";
	if (window.isSecureContext === false) return "insecure";
	if (!navigator.mediaDevices?.getUserMedia) return "unsupported";
	if (typeof MediaRecorder === "undefined") return kind === "video" ? "" : "unsupported";
	return "";
}

/** True when this page can record (a photo needs no recorder, a take does). */
export function canRecord(): boolean {
	return typeof MediaRecorder !== "undefined";
}

/** The code for what `getUserMedia` (or a track) threw. */
export function mediaError(err: unknown): Exclude<CaptureError, ""> {
	const name = err && typeof err === "object" && "name" in err ? String(err.name) : "";
	switch (name) {
		case "NotAllowedError":
		case "PermissionDeniedError":
		case "SecurityError":
			return "denied";
		case "NotFoundError":
		case "DevicesNotFoundError":
		case "OverconstrainedError":
			return "no_device";
		case "NotReadableError":
		case "TrackStartError":
		case "AbortError":
			return "busy";
		case "TypeError":
			return "unsupported";
		default:
			return "failed";
	}
}

const AUDIO_MIMES = [
	"audio/webm;codecs=opus",
	"audio/webm",
	"audio/mp4;codecs=mp4a.40.2",
	"audio/mp4",
	"audio/ogg;codecs=opus",
];

const VIDEO_MIMES = [
	"video/webm;codecs=vp9,opus",
	"video/webm;codecs=vp8,opus",
	"video/webm",
	"video/mp4;codecs=avc1,mp4a.40.2",
	"video/mp4",
];

/** The best format this browser records `kind` in; "" lets the recorder pick. */
export function recorderMime(kind: CaptureKind): string {
	if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
	const list = kind === "audio" ? AUDIO_MIMES : VIDEO_MIMES;
	return list.find((m) => MediaRecorder.isTypeSupported(m)) ?? "";
}

/** A mime without its parameters: `audio/webm;codecs=opus` is `audio/webm`. */
export function bareMime(mime: string): string {
	return mime.split(";")[0]?.trim().toLowerCase() ?? "";
}

export type PhotoFormat = "jpeg" | "webp" | "png";

/** The mime a photo is encoded as. */
export function photoMime(format: PhotoFormat): string {
	return `image/${format}`;
}

const EXTENSIONS: Record<string, string> = {
	"audio/webm": "webm",
	"audio/mp4": "m4a",
	"audio/ogg": "ogg",
	"audio/mpeg": "mp3",
	"audio/wav": "wav",
	"video/webm": "webm",
	"video/mp4": "mp4",
	"video/quicktime": "mov",
	"image/jpeg": "jpg",
	"image/webp": "webp",
	"image/png": "png",
};

/** The file extension for a mime, parameters ignored; "bin" when unknown. */
export function extension(mime: string): string {
	return EXTENSIONS[bareMime(mime)] ?? "bin";
}

function pad(n: number): string {
	return String(n).padStart(2, "0");
}

/** A take's file name from local time: `recording-2026-11-17-140322.webm`. */
export function takeName(prefix: string, mime: string, at: Date = new Date()): string {
	const day = `${at.getFullYear()}-${pad(at.getMonth() + 1)}-${pad(at.getDate())}`;
	const time = `${pad(at.getHours())}${pad(at.getMinutes())}${pad(at.getSeconds())}`;
	return `${prefix}-${day}-${time}.${extension(mime)}`;
}

/** What a person reads when a device is blocked. `what` is "Microphone" or "Camera". */
export function blockedText(what: string, error: CaptureError): string {
	const lower = what.toLowerCase();
	switch (error) {
		case "denied":
			return `${what} access is blocked. Allow it in the browser's site settings, then try again.`;
		case "no_device":
			return `No ${lower} found. Connect one, then try again.`;
		case "busy":
			return `The ${lower} is in use by another app, or could not start.`;
		case "insecure":
			return `The ${lower} works only over https or on localhost.`;
		case "unsupported":
			return `This browser cannot record from a ${lower}.`;
		case "lost":
			return `The ${lower} was disconnected.`;
		case "failed":
			return `The ${lower} could not start.`;
		default:
			return "";
	}
}

/** True when trying again can help: not for a page that cannot capture at all. */
export function canRetry(error: CaptureError): boolean {
	return error !== "insecure" && error !== "unsupported";
}
