// A source's waveform: fetch it, decode it with Web Audio, keep its peaks.
//
// Decoding needs the bytes, so the source has to allow a CORS fetch; the
// <audio> element plays without that, so a source can play and still have no
// waveform. Any failure (CORS, a 404, a codec Web Audio lacks, no Web Audio
// at all, a file past MAX_BYTES) reads as null and the player falls back to a
// plain scrub bar. Peaks are cached per source, failures too, so a list of
// rows or a re-render never fetches twice.

import { computePeaks } from "./model";

/** Peaks kept per source; bars are resampled from these to fit the width. */
export const PEAK_BUCKETS = 1024;

/** Past this a waveform is not worth the download and the decode. */
const MAX_BYTES = 48 * 1024 * 1024;

const cache = new Map<string, Promise<Float32Array | null>>();

async function decode(src: string): Promise<Float32Array | null> {
	if (typeof fetch === "undefined" || typeof OfflineAudioContext === "undefined") return null;
	const res = await fetch(src, { mode: "cors", credentials: "omit" });
	if (!res.ok) return null;
	if (Number(res.headers.get("content-length")) > MAX_BYTES) return null;
	const bytes = await res.arrayBuffer();
	// A one-frame offline context decodes at the file's own rate and needs no
	// user gesture, unlike a live AudioContext.
	const ctx = new OfflineAudioContext(1, 1, 44_100);
	const audio = await ctx.decodeAudioData(bytes);
	const channels = Array.from({ length: audio.numberOfChannels }, (_, i) =>
		audio.getChannelData(i),
	);
	return computePeaks(channels, PEAK_BUCKETS);
}

/** The peaks of `src` in [0, 1], or null when it cannot be decoded here. */
export function loadPeaks(src: string): Promise<Float32Array | null> {
	let pending = cache.get(src);
	if (!pending) {
		pending = decode(src).catch(() => null);
		cache.set(src, pending);
	}
	return pending;
}
