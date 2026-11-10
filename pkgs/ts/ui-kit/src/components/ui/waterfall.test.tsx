// Waterfall: trace order, an honest cap, and the time axis.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Waterfall } from "./waterfall";
import {
	formatSpanTime,
	type WaterfallSpan,
	waterfallRows,
	waterfallTicks,
	waterfallWindow,
} from "./waterfall-model";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

const trace: WaterfallSpan[] = [
	{ id: "b", parent: "root", label: "second", start: 50, end: 90 },
	{ id: "root", label: "root", start: 0, end: 100, tone: "ok" },
	{ id: "a", parent: "root", label: "first", start: 10, end: 40 },
	{ id: "a1", parent: "a", label: "inner", start: 12, end: 20, tone: "danger" },
	{ id: "lone", parent: "gone", label: "orphan", start: 5, end: 8 },
];

describe("waterfallRows", () => {
	it("orders depth first, children by start, orphans as roots", () => {
		const { rows, hidden } = waterfallRows(trace);
		expect(rows.map((r) => `${r.span.id}:${r.depth}`)).toEqual([
			"root:0",
			"a:1",
			"a1:2",
			"b:1",
			"lone:0",
		]);
		expect(hidden).toBe(0);
	});

	it("never drops a span caught in a parent cycle", () => {
		const { rows } = waterfallRows([
			{ id: "x", parent: "y", label: "x", start: 0, end: 1 },
			{ id: "y", parent: "x", label: "y", start: 1, end: 2 },
		]);
		expect(rows).toHaveLength(2);
	});

	it("counts what the cap hides, failures apart", () => {
		const { rows, hidden, hiddenDanger } = waterfallRows(trace, 2);
		expect(rows).toHaveLength(2);
		expect(hidden).toBe(3);
		expect(hiddenDanger).toBe(1);
	});
});

describe("waterfallWindow", () => {
	it("spans the earliest start to the latest end", () => {
		expect(waterfallWindow(trace)).toEqual({ start: 0, end: 100 });
	});

	it("runs to now when a span is still running", () => {
		const spans = [{ id: "r", label: "r", start: 10 }];
		expect(waterfallWindow(spans, { now: 70 })).toEqual({ start: 10, end: 70 });
		expect(waterfallWindow(spans)).toEqual({ start: 10, end: 11 });
	});

	it("takes an explicit window", () => {
		expect(waterfallWindow(trace, { start: -10, end: 200 })).toEqual({ start: -10, end: 200 });
	});
});

describe("ticks and times", () => {
	it("steps on 1, 2, 5", () => {
		expect(waterfallTicks(100)).toEqual([0, 20, 40, 60, 80, 100]);
		expect(waterfallTicks(1840)).toEqual([0, 500, 1000, 1500]);
	});

	it("formats short", () => {
		expect(formatSpanTime(0)).toBe("0 ms");
		expect(formatSpanTime(8.5)).toBe("8.5 ms");
		expect(formatSpanTime(120)).toBe("120 ms");
		expect(formatSpanTime(1250)).toBe("1.25 s");
		expect(formatSpanTime(42_100)).toBe("42.1 s");
		expect(formatSpanTime(185_000)).toBe("3m 05s");
		expect(formatSpanTime(3_720_000)).toBe("1h 02m");
	});
});

describe("Waterfall", () => {
	it("draws a row per span with its tone in words", () => {
		mount(<Waterfall spans={trace} />);
		const bars = [...host.querySelectorAll("[data-slot=waterfall-bar]")];
		expect(bars).toHaveLength(5);
		expect(bars[2]?.getAttribute("data-tone")).toBe("danger");
		expect(bars[2]?.getAttribute("aria-label")).toBe("inner, failed, 8 ms, at 12 ms");
		expect(host.querySelector("[data-slot=waterfall-more]")).toBeNull();
	});

	it("shows the remainder past the cap", () => {
		mount(<Waterfall spans={trace} maxRows={2} />);
		expect(host.querySelectorAll("[data-slot=waterfall-row]")).toHaveLength(2);
		expect(host.querySelector("[data-slot=waterfall-more]")?.textContent).toBe(
			"+3 more spans · 1 failed",
		);
	});

	it("marks a running span and selects on click", () => {
		const onSelect = vi.fn();
		mount(
			<Waterfall
				spans={[{ id: "r", label: "live", start: 0 }]}
				now={500}
				selected="r"
				onSelect={onSelect}
			/>,
		);
		const bar = host.querySelector("[data-slot=waterfall-bar]");
		expect(bar?.getAttribute("data-running")).toBe("true");
		expect(bar?.getAttribute("aria-label")).toBe("live, running, 500 ms so far, at 0 ms");
		const btn = host.querySelector("button");
		expect(btn?.getAttribute("aria-pressed")).toBe("true");
		act(() => btn?.click());
		expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "r" }));
	});
});
