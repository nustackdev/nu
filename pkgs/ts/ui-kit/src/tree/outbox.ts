// Where an event goes on its way to the server.
//
// Every emitted event lands here with its path, its payload and its name,
// and waits in one queue, in the order it happened. A moving `input` event
// (a drag tick, a keystroke) waits for the flush window, so a run of them
// shares one frame. Any other event flushes the queue right away and goes
// with it, last: order holds and a click or a submit costs no wait.
//
// A flush sends one frame through the store's sender, the same channel as
// every other outbound frame: a plain `notify` when the queue holds one
// event, a `batch` of `[ref, payload]` pairs otherwise. Every tick is sent,
// nothing is merged; slowing a stream down is the server's call.

import { OPS, type Path, type TreeFrame } from "@nustackdev/ui-core";
import { EVENTS } from "./events";
import { tree } from "./store";

/** How long a moving `input` event may wait for company, in ms. */
export const FLUSH_MS = 100;

type Pending = [ref: Path, payload: Record<string, unknown>];

let queue: Pending[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;

/** Queue a notify from the node at `path`. `event` is the payload's own event name. */
export function enqueue(path: Path, payload: Record<string, unknown>, event: string): void {
	queue.push([[...path], payload]);
	if (event !== EVENTS.input) flushOutbox();
	else if (timer === null) timer = setTimeout(flushOutbox, FLUSH_MS);
}

/**
 * Send what is queued now, as one frame. The window runs it on its own;
 * call it where waiting is wrong (a test asserting a sent `input`, a page
 * going away).
 */
export function flushOutbox(): void {
	if (timer !== null) {
		clearTimeout(timer);
		timer = null;
	}
	if (queue.length === 0) return;
	const out = queue;
	queue = [];
	const { send } = tree.getState();
	if (out.length === 1) {
		const [ref, payload] = out[0];
		send({ op: OPS.notify, ref, payload });
	} else {
		send({ op: OPS.batch, ref: [], payload: out });
	}
}

/**
 * Frames as the server sees them: each batch opened into its notifies, in
 * order, every other frame as it was. For code (tests mostly) that counts
 * notifies and should not care how they were packed.
 */
export function unbatch(frames: TreeFrame[]): TreeFrame[] {
	return frames.flatMap((f) =>
		f.op === OPS.batch
			? (f.payload as Pending[]).map(([ref, payload]) => ({ op: OPS.notify, ref, payload }))
			: [f],
	);
}
