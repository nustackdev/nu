// The arithmetic of a media transport, kept apart from the DOM so it is easy
// to test: how a time reads on screen and aloud, where a seek may land, what a
// key does to the playhead, and how decoded audio becomes a waveform.
//
// Times are seconds, the unit `HTMLMediaElement` speaks. A duration that is
// not known yet (NaN) or has no end (a live stream, Infinity) is "unknown":
// fractions read 0 and seeks clamp only at the start.

/** Playback speeds the rate menu offers, slowest first. */
export const RATES = [0.5, 0.75, 1, 1.25, 1.5, 2] as const;

/** Seconds a plain seek key moves the playhead, and a shifted one. */
export const SEEK_STEP = 5;
export const SEEK_STEP_BIG = 15;

/** How much one volume key moves the volume, in [0, 1]. */
export const VOLUME_STEP = 0.1;

/** Whether `d` is a duration you can divide by: finite and above zero. */
export function knownDuration(d: number): boolean {
	return Number.isFinite(d) && d > 0;
}

/** `t` held to [0, duration], or to [0, inf) when the duration is unknown. */
export function clampTime(t: number, duration: number): number {
	if (!Number.isFinite(t) || t < 0) return 0;
	return knownDuration(duration) ? Math.min(t, duration) : t;
}

/** How far `t` is through `duration`, in [0, 1]; 0 when the duration is unknown. */
export function fractionOf(t: number, duration: number): number {
	if (!knownDuration(duration) || !Number.isFinite(t)) return 0;
	return Math.min(1, Math.max(0, t / duration));
}

/** The time at fraction `f` of `duration`, clamped; 0 when the duration is unknown. */
export function timeAt(f: number, duration: number): number {
	if (!knownDuration(duration) || !Number.isFinite(f)) return 0;
	return Math.min(1, Math.max(0, f)) * duration;
}

/**
 * A time as a clock reads it: `0:07`, `3:45`, `1:02:09`. Hours show when the
 * time or `scale` (the duration it sits next to) reaches one, so both sides of
 * `0:12 / 1:02:09` line up. Unknown reads `--:--`.
 */
export function formatTime(t: number, scale = 0): string {
	if (!Number.isFinite(t)) return "--:--";
	const s = Math.max(0, Math.floor(t));
	const h = Math.floor(s / 3600);
	const m = Math.floor((s % 3600) / 60);
	const sec = String(s % 60).padStart(2, "0");
	const hours = h > 0 || (Number.isFinite(scale) && scale >= 3600);
	return hours ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

const unit = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** A time in words for a screen reader: "1 minute 5 seconds". Unknown reads "unknown". */
export function spokenTime(t: number): string {
	if (!Number.isFinite(t)) return "unknown";
	const s = Math.max(0, Math.floor(t));
	const h = Math.floor(s / 3600);
	const m = Math.floor((s % 3600) / 60);
	const sec = s % 60;
	const parts: string[] = [];
	if (h) parts.push(unit(h, "hour"));
	if (m) parts.push(unit(m, "minute"));
	if (sec || parts.length === 0) parts.push(unit(sec, "second"));
	return parts.join(" ");
}

/** A rate as the speed menu prints it: `1x`, `1.25x`, `0.5x`. */
export function formatRate(r: number): string {
	return `${Number(r.toFixed(2))}x`;
}

/** The ranges a media element has buffered, as `TimeRanges` hands them over. */
export interface Ranges {
	readonly length: number;
	start(i: number): number;
	end(i: number): number;
}

/**
 * Where the buffered run under `t` ends: what the scrub bar draws as loaded
 * ahead of the playhead. A gap at `t` (a seek past what has loaded) reads `t`,
 * so nothing is drawn as ready that is not.
 */
export function bufferedEnd(ranges: Ranges | null | undefined, t: number): number {
	if (!ranges) return 0;
	for (let i = 0; i < ranges.length; i++) {
		// A hair of slack: a playhead at a range's very end still sits in it.
		if (ranges.start(i) <= t + 0.05 && t <= ranges.end(i)) return ranges.end(i);
	}
	return t;
}

/** What a key asks of the transport. The hook carries it out. */
export type MediaCommand =
	| { kind: "toggle" }
	| { kind: "seek"; to: number }
	| { kind: "volume"; to: number }
	| { kind: "mute" }
	| { kind: "fullscreen" };

/** The slice of transport state a key reads. */
export interface KeyState {
	time: number;
	duration: number;
	playing: boolean;
	volume: number;
	muted: boolean;
}

export interface KeyOptions {
	/** Seconds `,` and `.` step while paused: one frame for video. */
	fineStep: number;
	/** Whether `f` means something here. */
	fullscreen?: boolean;
}

/**
 * The transport's keyboard, one key at a time.
 *
 * - space, `k`: play or pause
 * - `j` `l`, left right: back or ahead 5s, 15s with shift
 * - home end: to the start or the end
 * - `0` to `9`: to that tenth of the way through
 * - `,` `.`: back or ahead one fine step (a frame), paused only
 * - up down: volume, `m`: mute
 * - `f`: full screen, where there is one
 *
 * Null means the key is not the transport's, so it should pass through.
 */
export function keyCommand(
	key: string,
	shift: boolean,
	s: KeyState,
	opts: KeyOptions,
): MediaCommand | null {
	const by = (dt: number): MediaCommand => ({
		kind: "seek",
		to: clampTime(s.time + dt, s.duration),
	});
	const step = shift ? SEEK_STEP_BIG : SEEK_STEP;
	switch (key) {
		case " ":
		case "k":
		case "K":
			return { kind: "toggle" };
		case "j":
		case "J":
		case "ArrowLeft":
			return by(-step);
		case "l":
		case "L":
		case "ArrowRight":
			return by(step);
		case "Home":
			return { kind: "seek", to: 0 };
		case "End":
			return knownDuration(s.duration) ? { kind: "seek", to: s.duration } : null;
		case ",":
		case "<":
			return s.playing ? null : by(-opts.fineStep);
		case ".":
		case ">":
			return s.playing ? null : by(opts.fineStep);
		case "ArrowUp":
			return {
				kind: "volume",
				to: Math.min(1, roundVolume((s.muted ? 0 : s.volume) + VOLUME_STEP)),
			};
		case "ArrowDown":
			return {
				kind: "volume",
				to: Math.max(0, roundVolume((s.muted ? 0 : s.volume) - VOLUME_STEP)),
			};
		case "m":
		case "M":
			return { kind: "mute" };
		case "f":
		case "F":
			return opts.fullscreen ? { kind: "fullscreen" } : null;
	}
	if (key.length === 1 && key >= "0" && key <= "9") {
		return knownDuration(s.duration)
			? { kind: "seek", to: timeAt(Number(key) / 10, s.duration) }
			: null;
	}
	return null;
}

// Steps of 0.1 summed in floats drift (0.30000000000000004); a volume keeps two places.
function roundVolume(v: number): number {
	return Math.round(v * 100) / 100;
}

/**
 * Decoded audio as `buckets` peaks in [0, 1]: the loudest sample of each
 * slice, across every channel, scaled so the loudest slice is 1. A silent
 * file is all zeros rather than a division by nothing.
 */
export function computePeaks(
	channels: readonly ArrayLike<number>[],
	buckets: number,
): Float32Array {
	const out = new Float32Array(Math.max(0, buckets));
	const length = channels.reduce((n, c) => Math.max(n, c.length), 0);
	if (out.length === 0 || length === 0) return out;
	let top = 0;
	for (let b = 0; b < out.length; b++) {
		const from = Math.floor((b * length) / out.length);
		const to = Math.max(from + 1, Math.floor(((b + 1) * length) / out.length));
		let peak = 0;
		for (const c of channels) {
			const end = Math.min(to, c.length);
			for (let i = from; i < end; i++) {
				const v = Math.abs(c[i]);
				if (v > peak) peak = v;
			}
		}
		out[b] = peak;
		if (peak > top) top = peak;
	}
	if (top > 0) for (let b = 0; b < out.length; b++) out[b] /= top;
	return out;
}

/**
 * `peaks` redrawn as `n` bars, each the loudest of the peaks it covers, so a
 * short spike survives being drawn narrow. More bars than peaks repeat them.
 */
export function resamplePeaks(peaks: ArrayLike<number>, n: number): number[] {
	const count = Math.max(0, Math.floor(n));
	if (count === 0 || peaks.length === 0) return new Array(count).fill(0);
	const out = new Array<number>(count);
	for (let b = 0; b < count; b++) {
		const from = Math.floor((b * peaks.length) / count);
		const to = Math.max(from + 1, Math.floor(((b + 1) * peaks.length) / count));
		let peak = 0;
		for (let i = from; i < to && i < peaks.length; i++) if (peaks[i] > peak) peak = peaks[i];
		out[b] = peak;
	}
	return out;
}
