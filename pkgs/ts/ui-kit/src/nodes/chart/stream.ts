// Streamed points, kept beside the store rather than in it.
//
// The store is immutable (immer freezes what it holds), so an append through
// it would copy the series on every point and re-render the node. Instead a
// node's appended series live here, one ring per series index, keyed by the
// node's path. A push marks the series dirty and asks for one animation
// frame; that frame hands every dirty series to the node's listeners as a
// single patch. However many points land between two frames, the chart
// redraws once.
//
// The rings outlive the component (a node in a closed tab keeps streaming)
// and go with the node: the type's `dispose` drops them.

import type { Path } from "@nustackdev/ui-core";
import { Ring } from "../../lib/chart/ring";

export type StreamListener = (dirty: ReadonlySet<number>) => void;

export type Stream = {
	rings: Map<number, Ring<unknown>>;
	dirty: Set<number>;
	listeners: Set<StreamListener>;
	frame: number | null;
};

const streams = new Map<string, Stream>();

function keyOf(path: Path): string {
	return JSON.stringify(path);
}

const schedule: (cb: () => void) => number =
	typeof requestAnimationFrame === "function"
		? (cb) => requestAnimationFrame(cb)
		: (cb) => setTimeout(cb, 16) as unknown as number;

/** The node's stream, made on first use. */
export function streamAt(path: Path): Stream {
	const key = keyOf(path);
	let s = streams.get(key);
	if (!s) {
		s = { rings: new Map(), dirty: new Set(), listeners: new Set(), frame: null };
		streams.set(key, s);
	}
	return s;
}

/** The node's stream if it has one, without making it. */
export function peekStream(path: Path): Stream | undefined {
	return streams.get(keyOf(path));
}

/** Each streamed series' points, oldest first, by series index. */
export function streamData(path: Path): Map<number, unknown[]> {
	const out = new Map<number, unknown[]>();
	const s = peekStream(path);
	if (s) for (const [i, ring] of s.rings) out.set(i, ring.toArray());
	return out;
}

/** Push points onto one series, seeding its ring from `seed` the first time. */
export function pushPoints(
	path: Path,
	index: number,
	points: readonly unknown[],
	cap: number,
	seed: readonly unknown[],
): void {
	const s = streamAt(path);
	let ring = s.rings.get(index);
	if (!ring) {
		ring = Ring.from(seed, cap);
		s.rings.set(index, ring);
	}
	for (const p of points) ring.push(p);
	s.dirty.add(index);
	if (s.frame === null) {
		s.frame = schedule(() => {
			s.frame = null;
			const dirty = new Set(s.dirty);
			s.dirty.clear();
			for (const listen of s.listeners) listen(dirty);
		});
	}
}

/** Forget some series' rings (the option's own data takes over), or all of them. */
export function dropSeries(path: Path, indexes?: readonly number[]): void {
	const s = peekStream(path);
	if (!s) return;
	if (indexes === undefined) {
		s.rings.clear();
		s.dirty.clear();
		return;
	}
	for (const i of indexes) {
		s.rings.delete(i);
		s.dirty.delete(i);
	}
}

/** Re-window every ring of the node. */
export function resizeStream(path: Path, cap: number): void {
	const s = peekStream(path);
	if (s) for (const ring of s.rings.values()) ring.resize(cap);
}

export function listen(path: Path, cb: StreamListener): () => void {
	const s = streamAt(path);
	s.listeners.add(cb);
	return () => s.listeners.delete(cb);
}

/** The node is gone: its rings and any pending frame with it. */
export function disposeStream(path: Path): void {
	const key = keyOf(path);
	const s = streams.get(key);
	if (!s) return;
	if (s.frame !== null) {
		if (typeof cancelAnimationFrame === "function") cancelAnimationFrame(s.frame);
		else clearTimeout(s.frame);
	}
	streams.delete(key);
}
