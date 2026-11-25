// The outbox: moving `input` events wait for the flush window, any other
// event flushes the queue at once with itself last, and each flush is one
// frame (a plain notify for a lone event, a batch otherwise).

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { emit } from "./emit";
import { EVENTS } from "./events";
import { enqueue, FLUSH_MS, flushOutbox, unbatch } from "./outbox";
import { tree } from "./store";

let sent: TreeFrame[] = [];

beforeEach(() => {
	vi.useFakeTimers();
	sent = [];
	tree.getState().setSender((f) => sent.push(f));
});

afterEach(() => {
	flushOutbox();
	tree.getState().setSender(null);
	vi.useRealTimers();
});

const tick = (value: number) => emit(["s"], EVENTS.input, { value });

describe("outbox", () => {
	it("holds an input until the window closes", () => {
		tick(1);
		expect(sent).toEqual([]);
		vi.advanceTimersByTime(FLUSH_MS - 1);
		expect(sent).toEqual([]);
		vi.advanceTimersByTime(1);
		expect(sent).toEqual([{ op: OPS.notify, ref: ["s"], payload: { event: "input", value: 1 } }]);
	});

	it("sends a lone non-input event as a plain notify, right away", () => {
		emit(["b"], EVENTS.click);
		expect(sent).toEqual([{ op: OPS.notify, ref: ["b"], payload: { event: "click" } }]);
	});

	it("sends one batch frame per window, every tick kept", () => {
		tick(1);
		tick(2);
		tick(3);
		vi.advanceTimersByTime(FLUSH_MS);
		expect(sent).toEqual([
			{
				op: OPS.batch,
				ref: [],
				payload: [
					[["s"], { event: "input", value: 1 }],
					[["s"], { event: "input", value: 2 }],
					[["s"], { event: "input", value: 3 }],
				],
			},
		]);
		tick(4);
		vi.advanceTimersByTime(FLUSH_MS);
		expect(sent).toHaveLength(2);
		expect(sent[1].op).toBe(OPS.notify);
	});

	it("does not push the window back while ticks keep coming", () => {
		for (let i = 0; i < 10; i++) {
			tick(i);
			vi.advanceTimersByTime(FLUSH_MS / 4);
		}
		// 250 ms of ticks every 25 ms: two full windows sent, the third still open.
		expect(sent.map((f) => (f.payload as unknown[]).length)).toEqual([4, 4]);
	});

	it("lands a click right after a drag tick, after it, with no wait", () => {
		tick(1);
		emit(["b"], EVENTS.click);
		expect(sent).toEqual([
			{
				op: OPS.batch,
				ref: [],
				payload: [
					[["s"], { event: "input", value: 1 }],
					[["b"], { event: "click" }],
				],
			},
		]);
		vi.advanceTimersByTime(FLUSH_MS);
		expect(sent).toHaveLength(1);
	});

	it("keeps order across mixed events and frames", () => {
		tick(1);
		tick(2);
		emit(["s"], EVENTS.change, { value: 2 });
		tick(3);
		emit(["f"], EVENTS.submit);
		emit(["b"], EVENTS.click);
		tick(4);
		vi.advanceTimersByTime(FLUSH_MS);
		const events = sent.flatMap((f) =>
			f.op === OPS.batch
				? (f.payload as [string[], { event: string }][]).map(([ref, p]) => `${ref}:${p.event}`)
				: [`${f.ref}:${(f.payload as { event: string }).event}`],
		);
		expect(events).toEqual([
			"s:input",
			"s:input",
			"s:change",
			"s:input",
			"f:submit",
			"b:click",
			"s:input",
		]);
		expect(sent.map((f) => f.op)).toEqual([OPS.batch, OPS.batch, OPS.notify, OPS.notify]);
	});

	it("flushes on demand and cancels the pending window", () => {
		tick(1);
		flushOutbox();
		expect(sent).toHaveLength(1);
		vi.advanceTimersByTime(FLUSH_MS);
		expect(sent).toHaveLength(1);
		flushOutbox();
		expect(sent).toHaveLength(1);
	});

	it("copies the path, so a caller reusing its array cannot rewrite a queued ref", () => {
		const path = ["a"];
		enqueue(path, { event: "input" }, EVENTS.input);
		path[0] = "z";
		flushOutbox();
		expect(sent[0].ref).toEqual(["a"]);
	});

	it("opens a batch back into the notifies it carried", () => {
		tick(1);
		emit(["b"], EVENTS.click);
		emit(["b"], EVENTS.click);
		expect(unbatch(sent)).toEqual([
			{ op: OPS.notify, ref: ["s"], payload: { event: "input", value: 1 } },
			{ op: OPS.notify, ref: ["b"], payload: { event: "click" } },
			{ op: OPS.notify, ref: ["b"], payload: { event: "click" } },
		]);
	});
});
