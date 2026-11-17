// Fake microphones and cameras, for stories and tests.
//
//   const media = installFakeMedia({ mics: 2, cameras: 2 });
//   ...                       // the page asks getUserMedia as usual
//   media.lose();             // every live track ends, as an unplug
//   media.setFail("denied");  // the next opens throw NotAllowedError
//   media.restore();          // the browser's own objects come back
//
// Two backends, picked by what the page has:
//
// - in a browser (Storybook, the Firefox tests) the streams are real: a
//   canvas animation per camera (`captureStream`) and an oscillator whose
//   loudness moves like speech (Web Audio). A real MediaRecorder records them,
//   so a story makes real webm/mp4 takes that play back.
// - in jsdom there is no canvas stream, Web Audio or MediaRecorder, so
//   plain objects stand in: tracks that end, streams that hold them, and a
//   recorder whose takes are a few bytes of the asked mime. Tests drive it
//   by the hooks' own calls; `FakeRecorder.last` is the one running.
//
// Either way `getUserMedia` honors `fail`, `delayMs` (the time a permission
// prompt takes), `deviceId: {exact}` and `facingMode`, and `enumerateDevices`
// lists the devices with labels.

import type { CaptureError } from "./support";

export type FakeFail = Extract<CaptureError, "denied" | "no_device" | "busy">;

export interface FakeMediaOptions {
	/** Microphones listed. Default 1. */
	mics?: number;
	/** Cameras listed: the first faces the user, the second the room. Default 1. */
	cameras?: number;
	/** Every open throws this until `setFail("")`. */
	fail?: FakeFail | "";
	/** How long an open waits, as a permission prompt would. Default 0. */
	delayMs?: number;
	/** Force the jsdom backend even in a browser. */
	plain?: boolean;
}

export interface FakeMedia {
	/** Put the browser's own objects back and stop every fake stream. */
	restore: () => void;
	/** End every live track, as when the device is unplugged. */
	lose: () => void;
	setFail: (fail: FakeFail | "") => void;
	/** Every getUserMedia call's constraints, in order. */
	calls: MediaStreamConstraints[];
	/** Tracks not yet stopped or ended. */
	liveTracks: () => number;
	/** Add or remove devices, then fire `devicechange`. */
	setDevices: (mics: number, cameras: number) => void;
}

const FAIL_NAMES: Record<FakeFail, string> = {
	denied: "NotAllowedError",
	no_device: "NotFoundError",
	busy: "NotReadableError",
};

function domError(name: string): Error {
	if (typeof DOMException !== "undefined") return new DOMException(name, name);
	const err = new Error(name);
	err.name = name;
	return err;
}

type Device = {
	deviceId: string;
	kind: "audioinput" | "videoinput";
	label: string;
	facing: string;
};

function deviceList(mics: number, cameras: number): Device[] {
	const out: Device[] = [];
	for (let i = 0; i < mics; i++) {
		out.push({
			deviceId: `fake-mic-${i}`,
			kind: "audioinput",
			label: i === 0 ? "Built-in microphone" : `USB microphone ${i}`,
			facing: "",
		});
	}
	for (let i = 0; i < cameras; i++) {
		out.push({
			deviceId: `fake-cam-${i}`,
			kind: "videoinput",
			label: i === 0 ? "Front camera" : i === 1 ? "Back camera" : `Camera ${i + 1}`,
			facing: i === 0 ? "user" : i === 1 ? "environment" : "",
		});
	}
	return out;
}

function info(d: Device): MediaDeviceInfo {
	return {
		deviceId: d.deviceId,
		groupId: "fake",
		kind: d.kind,
		label: d.label,
		toJSON: () => ({ deviceId: d.deviceId, kind: d.kind, label: d.label }),
	} as MediaDeviceInfo;
}

/** The device an open asks for, from `deviceId: {exact}` or `facingMode`, else the first. */
function chosen(devices: Device[], kind: Device["kind"], c: boolean | MediaTrackConstraints) {
	const list = devices.filter((d) => d.kind === kind);
	if (typeof c !== "object") return list[0] ?? null;
	const exact = (v: unknown): string | null => {
		if (typeof v === "string") return v;
		if (v && typeof v === "object" && "exact" in v) return String((v as { exact: unknown }).exact);
		if (v && typeof v === "object" && "ideal" in v) return String((v as { ideal: unknown }).ideal);
		return null;
	};
	const id = exact(c.deviceId);
	if (id) return list.find((d) => d.deviceId === id) ?? null;
	const facing = exact(c.facingMode);
	if (facing) return list.find((d) => d.facing === facing) ?? list[0] ?? null;
	return list[0] ?? null;
}

// --- jsdom backend --------------------------------------------------------------

export class FakeTrack extends EventTarget {
	readonly id = `track-${Math.random().toString(36).slice(2, 8)}`;
	readyState: "live" | "ended" = "live";
	enabled = true;
	readonly kind: "audio" | "video";
	readonly label: string;
	readonly settings: MediaTrackSettings;
	constructor(kind: "audio" | "video", label: string, settings: MediaTrackSettings) {
		super();
		this.kind = kind;
		this.label = label;
		this.settings = settings;
	}
	stop(): void {
		this.readyState = "ended";
	}
	getSettings(): MediaTrackSettings {
		return this.settings;
	}
	/** End as the device going away does: `ended` fires. */
	end(): void {
		if (this.readyState === "ended") return;
		this.readyState = "ended";
		this.dispatchEvent(new Event("ended"));
	}
}

export class FakeStream extends EventTarget {
	readonly id = `stream-${Math.random().toString(36).slice(2, 8)}`;
	readonly tracks: FakeTrack[];
	constructor(tracks: FakeTrack[]) {
		super();
		this.tracks = tracks;
	}
	get active(): boolean {
		return this.tracks.some((t) => t.readyState === "live");
	}
	getTracks(): FakeTrack[] {
		return [...this.tracks];
	}
	getAudioTracks(): FakeTrack[] {
		return this.tracks.filter((t) => t.kind === "audio");
	}
	getVideoTracks(): FakeTrack[] {
		return this.tracks.filter((t) => t.kind === "video");
	}
}

/** A MediaRecorder for jsdom: each data slice is 64 bytes of the mime. */
export class FakeRecorder {
	static last: FakeRecorder | null = null;
	static isTypeSupported(mime: string): boolean {
		return /^(audio|video)\/webm/.test(mime);
	}
	state: RecordingState = "inactive";
	readonly mimeType: string;
	ondataavailable: ((e: { data: Blob }) => void) | null = null;
	onstop: (() => void) | null = null;
	readonly stream: FakeStream;
	constructor(stream: FakeStream, opts: MediaRecorderOptions = {}) {
		this.stream = stream;
		const video = stream.getVideoTracks().length > 0;
		this.mimeType = opts.mimeType ?? (video ? "video/webm" : "audio/webm");
		FakeRecorder.last = this;
		for (const t of stream.getTracks()) t.addEventListener("ended", () => this.stopIfAllEnded());
	}
	start(): void {
		if (!this.stream.active) throw domError("InvalidStateError");
		this.state = "recording";
	}
	pause(): void {
		if (this.state === "recording") this.state = "paused";
	}
	resume(): void {
		if (this.state === "paused") this.state = "recording";
	}
	/** Hand out a slice now, as the timeslice would. */
	emit(): void {
		this.ondataavailable?.({ data: new Blob([new Uint8Array(64)], { type: this.mimeType }) });
	}
	stop(): void {
		if (this.state === "inactive") return;
		this.state = "inactive";
		this.emit();
		this.onstop?.();
	}
	private stopIfAllEnded(): void {
		if (!this.stream.active) this.stop();
	}
}

// --- browser backend ------------------------------------------------------------

const HUES = [265, 25, 160, 330];

function cameraStream(d: Device, index: number, width: number, height: number): MediaStream {
	const canvas = document.createElement("canvas");
	canvas.width = width;
	canvas.height = height;
	const g = canvas.getContext("2d");
	const hue = HUES[index % HUES.length] ?? 265;
	const t0 = performance.now();
	let frame = 0;
	const draw = () => {
		if (!g) return;
		const t = (performance.now() - t0) / 1000;
		const grad = g.createLinearGradient(0, 0, width, height);
		grad.addColorStop(0, `hsl(${hue} 45% 18%)`);
		grad.addColorStop(1, `hsl(${(hue + 40) % 360} 55% 32%)`);
		g.fillStyle = grad;
		g.fillRect(0, 0, width, height);
		const r = Math.min(width, height) / 6;
		g.beginPath();
		g.arc(
			width / 2 + Math.cos(t) * width * 0.25,
			height / 2 + Math.sin(t * 1.3) * height * 0.2,
			r,
			0,
			Math.PI * 2,
		);
		g.fillStyle = `hsl(${(hue + 180) % 360} 70% 70% / 0.85)`;
		g.fill();
		g.fillStyle = "rgba(255,255,255,0.85)";
		g.font = `${Math.round(height / 18)}px ui-monospace, monospace`;
		g.fillText(`${d.label}  ${t.toFixed(1)}s`, 16, height - 20);
		// An arrow pointing right: a mirrored preview shows it pointing left.
		g.fillText("→ right", width - 140, 40);
		frame = requestAnimationFrame(draw);
	};
	draw();
	const stream = canvas.captureStream(30);
	for (const track of stream.getVideoTracks()) {
		const own = track.stop.bind(track);
		track.stop = () => {
			cancelAnimationFrame(frame);
			own();
		};
	}
	return stream;
}

function micStream(ctx: AudioContext): MediaStream {
	const osc = ctx.createOscillator();
	osc.type = "sawtooth";
	osc.frequency.value = 140;
	const lfo = ctx.createOscillator();
	lfo.frequency.value = 3.2;
	const lfoGain = ctx.createGain();
	lfoGain.gain.value = 0.12;
	const gain = ctx.createGain();
	gain.gain.value = 0.14;
	lfo.connect(lfoGain).connect(gain.gain);
	const dest = ctx.createMediaStreamDestination();
	osc.connect(gain).connect(dest);
	osc.start();
	lfo.start();
	const stream = dest.stream;
	for (const track of stream.getAudioTracks()) {
		const own = track.stop.bind(track);
		track.stop = () => {
			osc.stop();
			lfo.stop();
			own();
		};
	}
	return stream;
}

/** Set a real track's settings to name the fake device, as a real one would. */
function stamp(track: MediaStreamTrack, d: Device): void {
	const own = track.getSettings.bind(track);
	track.getSettings = () => ({ ...own(), deviceId: d.deviceId, facingMode: d.facing || undefined });
	Object.defineProperty(track, "label", { value: d.label, configurable: true });
}

function size(
	c: boolean | MediaTrackConstraints | undefined,
	key: "width" | "height",
	fallback: number,
) {
	if (!c || typeof c !== "object") return fallback;
	const v = c[key];
	if (typeof v === "number") return v;
	if (v && typeof v === "object") return Number(v.ideal ?? v.exact ?? v.max ?? fallback);
	return fallback;
}

// --- install --------------------------------------------------------------------

export function installFakeMedia(opts: FakeMediaOptions = {}): FakeMedia {
	const real =
		!opts.plain &&
		typeof HTMLCanvasElement !== "undefined" &&
		typeof HTMLCanvasElement.prototype.captureStream === "function" &&
		typeof AudioContext !== "undefined";
	let devices = deviceList(opts.mics ?? 1, opts.cameras ?? 1);
	let fail: FakeFail | "" = opts.fail ?? "";
	const delay = opts.delayMs ?? 0;
	const calls: MediaStreamConstraints[] = [];
	const tracks = new Set<MediaStreamTrack | FakeTrack>();
	const listeners = new Set<EventListener>();
	let audio: AudioContext | null = null;

	const nav = navigator as Navigator & { mediaDevices?: MediaDevices };
	const before = {
		mediaDevices: Object.getOwnPropertyDescriptor(nav, "mediaDevices"),
		recorder: (globalThis as { MediaRecorder?: unknown }).MediaRecorder,
		secure: Object.getOwnPropertyDescriptor(window, "isSecureContext"),
	};

	const getUserMedia = async (c: MediaStreamConstraints): Promise<MediaStream> => {
		calls.push(c);
		if (delay > 0) await new Promise((r) => setTimeout(r, delay));
		if (fail) throw domError(FAIL_NAMES[fail]);
		const parts: Array<MediaStreamTrack | FakeTrack> = [];
		const want = (kind: Device["kind"], tc: boolean | MediaTrackConstraints | undefined) => {
			if (!tc) return null;
			const d = chosen(devices, kind, tc);
			if (!d) throw domError(FAIL_NAMES.no_device);
			return d;
		};
		const mic = want("audioinput", c.audio);
		const cam = want("videoinput", c.video);
		const w = size(c.video, "width", 1280);
		const h = size(c.video, "height", 720);
		if (real) {
			if (cam) {
				const index = devices.filter((d) => d.kind === "videoinput").indexOf(cam);
				for (const t of cameraStream(cam, index, w, h).getVideoTracks()) {
					stamp(t, cam);
					parts.push(t);
				}
			}
			if (mic) {
				audio ??= new AudioContext();
				for (const t of micStream(audio).getAudioTracks()) {
					stamp(t, mic);
					parts.push(t);
				}
			}
			for (const t of parts) tracks.add(t);
			return new MediaStream(parts as MediaStreamTrack[]);
		}
		if (cam) {
			parts.push(
				new FakeTrack("video", cam.label, {
					deviceId: cam.deviceId,
					width: w,
					height: h,
					facingMode: cam.facing,
				}),
			);
		}
		if (mic) parts.push(new FakeTrack("audio", mic.label, { deviceId: mic.deviceId }));
		for (const t of parts) tracks.add(t);
		return new FakeStream(parts as FakeTrack[]) as unknown as MediaStream;
	};

	const mediaDevices = {
		getUserMedia,
		enumerateDevices: async () => devices.map(info),
		getSupportedConstraints: () => ({
			deviceId: true,
			facingMode: true,
			width: true,
			height: true,
		}),
		addEventListener: (_: string, fn: EventListener) => listeners.add(fn),
		removeEventListener: (_: string, fn: EventListener) => listeners.delete(fn),
	} as unknown as MediaDevices;

	Object.defineProperty(nav, "mediaDevices", { value: mediaDevices, configurable: true });
	Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
	if (!real) (globalThis as { MediaRecorder?: unknown }).MediaRecorder = FakeRecorder;

	const live = () => [...tracks].filter((t) => t.readyState === "live");

	return {
		calls,
		setFail: (f) => {
			fail = f;
		},
		liveTracks: () => live().length,
		lose: () => {
			for (const t of live()) {
				if (t instanceof FakeTrack) t.end();
				else {
					t.stop();
					t.dispatchEvent(new Event("ended"));
				}
			}
		},
		setDevices: (mics, cameras) => {
			devices = deviceList(mics, cameras);
			for (const fn of listeners) fn(new Event("devicechange"));
		},
		restore: () => {
			for (const t of tracks) t.stop();
			tracks.clear();
			void audio?.close().catch(() => {});
			if (before.mediaDevices) Object.defineProperty(nav, "mediaDevices", before.mediaDevices);
			else delete (nav as { mediaDevices?: unknown }).mediaDevices;
			if (before.secure) Object.defineProperty(window, "isSecureContext", before.secure);
			else delete (window as { isSecureContext?: unknown }).isSecureContext;
			(globalThis as { MediaRecorder?: unknown }).MediaRecorder = before.recorder;
		},
	};
}
