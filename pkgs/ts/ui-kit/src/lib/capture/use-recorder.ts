// A take from a stream: start, pause, resume, stop, with the time it ran.
//
//   const rec = useRecorder();
//   rec.start(stream, { mime: recorderMime("audio"), maxSeconds: 60, onDone: keep });
//   rec.pause(); rec.resume();
//   rec.stop();      // onDone({ blob, mime, duration }) once the last data lands
//   rec.cancel();    // stops and drops: onDone is never called
//
// `onDone` hears every end that leaves a take: a stop, the max duration
// reached, and the stream's tracks ending under it (a device lost mid take
// keeps what it got). It hears null when the take holds no bytes.
//
// The recorder hands out data every second (a timeslice), so a take cut
// short by a lost device still has what was recorded up to it. `elapsed` is
// the recording time in seconds, pauses out, updated about ten times a
// second while recording. The machinery is one object per hook, so the
// functions it hands out never change identity.

import * as React from "react";
import { bareMime } from "./support";

export type RecorderState = "inactive" | "recording" | "paused";

export interface RecordedTake {
	blob: Blob;
	/** What the recorder made, parameters stripped: `audio/webm`. */
	mime: string;
	/** Seconds recorded, pauses out. */
	duration: number;
}

export interface RecorderStart {
	/** The mime to ask for; "" lets the browser pick. */
	mime: string;
	/** Stop on its own after this many seconds; null for no limit. */
	maxSeconds?: number | null;
	/** Bits per second for the whole take; the browser's default when left out. */
	bitsPerSecond?: number;
	onDone: (take: RecordedTake | null) => void;
}

export interface Recorder {
	state: RecorderState;
	elapsed: number;
	/** Start a take. False when the recorder could not start (no MediaRecorder, a bad stream). */
	start: (stream: MediaStream, opts: RecorderStart) => boolean;
	pause: () => void;
	resume: () => void;
	stop: () => void;
	cancel: () => void;
}

const TICK_MS = 100;
const SLICE_MS = 1000;

function now(): number {
	return typeof performance !== "undefined" ? performance.now() : Date.now();
}

type Sink = { state: (s: RecorderState) => void; elapsed: (s: number) => void };

class Machine {
	rec: MediaRecorder | null = null;
	chunks: Blob[] = [];
	/** Ms recorded before the current run. */
	banked = 0;
	/** When the current run started; null while paused or stopped. */
	since: number | null = null;
	limit: number | null = null;
	timer: ReturnType<typeof setInterval> | null = null;
	dropped = false;

	readonly sink: Sink;

	constructor(sink: Sink) {
		this.sink = sink;
	}

	seconds(): number {
		return (this.banked + (this.since === null ? 0 : now() - this.since)) / 1000;
	}

	tick = (): void => {
		const s = this.seconds();
		this.sink.elapsed(s);
		if (this.limit !== null && s >= this.limit) this.stop();
	};

	startTimer(): void {
		this.stopTimer();
		this.timer = setInterval(this.tick, TICK_MS);
	}

	stopTimer(): void {
		if (this.timer !== null) clearInterval(this.timer);
		this.timer = null;
	}

	start = (stream: MediaStream, opts: RecorderStart): boolean => {
		if (typeof MediaRecorder === "undefined") return false;
		if (this.rec && this.rec.state !== "inactive") return false;
		let r: MediaRecorder;
		try {
			const init: MediaRecorderOptions = {};
			if (opts.mime) init.mimeType = opts.mime;
			if (opts.bitsPerSecond) init.bitsPerSecond = opts.bitsPerSecond;
			r = new MediaRecorder(stream, init);
		} catch {
			return false;
		}
		this.chunks = [];
		this.banked = 0;
		this.limit = opts.maxSeconds && opts.maxSeconds > 0 ? opts.maxSeconds : null;
		this.dropped = false;
		r.ondataavailable = (e) => {
			if (e.data && e.data.size > 0) this.chunks.push(e.data);
		};
		r.onstop = () => {
			const duration = Math.min(this.seconds(), this.limit ?? Number.POSITIVE_INFINITY);
			this.since = null;
			this.stopTimer();
			if (this.rec === r) this.rec = null;
			this.sink.state("inactive");
			this.sink.elapsed(duration);
			const chunks = this.chunks;
			this.chunks = [];
			if (this.dropped) return;
			const type = r.mimeType || opts.mime || "";
			const blob = new Blob(chunks, type ? { type } : undefined);
			opts.onDone(blob.size > 0 ? { blob, mime: bareMime(blob.type || type), duration } : null);
		};
		try {
			r.start(SLICE_MS);
		} catch {
			return false;
		}
		this.rec = r;
		this.since = now();
		this.sink.elapsed(0);
		this.sink.state("recording");
		this.startTimer();
		return true;
	};

	pause = (): void => {
		const r = this.rec;
		if (r?.state !== "recording") return;
		r.pause();
		this.banked = this.seconds() * 1000;
		this.since = null;
		this.stopTimer();
		this.sink.elapsed(this.banked / 1000);
		this.sink.state("paused");
	};

	resume = (): void => {
		const r = this.rec;
		if (r?.state !== "paused") return;
		r.resume();
		this.since = now();
		this.sink.state("recording");
		this.startTimer();
	};

	stop = (): void => {
		const r = this.rec;
		if (r && r.state !== "inactive") r.stop();
	};

	cancel = (): void => {
		this.dropped = true;
		this.stop();
	};

	dispose(): void {
		this.dropped = true;
		this.stopTimer();
		this.stop();
	}
}

export function useRecorder(): Recorder {
	const [state, setState] = React.useState<RecorderState>("inactive");
	const [elapsed, setElapsed] = React.useState(0);
	const machine = React.useRef<Machine | null>(null);
	if (machine.current === null) {
		machine.current = new Machine({ state: setState, elapsed: setElapsed });
	}
	const m = machine.current;
	React.useEffect(() => () => m.dispose(), [m]);
	return {
		state,
		elapsed,
		start: m.start,
		pause: m.pause,
		resume: m.resume,
		stop: m.stop,
		cancel: m.cancel,
	};
}
