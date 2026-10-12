// The Chart node and its helpers, with ECharts stood in by a fake.
//
// jsdom has no canvas, so `lib/chart/load` is mocked: `init` hands back an
// instance that records what it is given. That is enough to check what the
// node and the primitive ask of ECharts: the option, the stream patches (one
// per frame), the re-init on a theme change, a click turned into a notify.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mergeOption, needsFull, seriesWithData } from "../../lib/chart/option";
import { Ring } from "../../lib/chart/ring";
import { chartTheme, readChartTokens, resolveVars } from "../../lib/chart/theme";
import { NodeView, tree } from "../../tree";
import "../index";
import { peekStream, streamData } from "./stream";

type Fake = {
	options: { option: Record<string, unknown>; opts: unknown }[];
	handlers: Record<string, (p: unknown) => void>;
	disposed: boolean;
	theme: Record<string, unknown>;
};

const fakes: Fake[] = [];

vi.mock("../../lib/chart/load", () => {
	const lib = {
		init: (_el: unknown, theme: Record<string, unknown>) => {
			const f: Fake = { options: [], handlers: {}, disposed: false, theme };
			fakes.push(f);
			return {
				setOption: (option: Record<string, unknown>, opts: unknown) =>
					f.options.push({ option, opts }),
				on: (name: string, cb: (p: unknown) => void) => {
					f.handlers[name] = cb;
				},
				dispose: () => {
					f.disposed = true;
				},
				resize: () => {},
			};
		},
	};
	return { loadECharts: () => Promise.resolve(lib), registerChartMap: () => {} };
});

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// --- pure helpers -----------------------------------------------------------------

describe("Ring", () => {
	it("keeps the newest items, oldest first", () => {
		const r = new Ring<number>(3);
		for (const n of [1, 2, 3, 4, 5]) r.push(n);
		expect(r.toArray()).toEqual([3, 4, 5]);
		expect(r.size).toBe(3);
	});

	it("seeds from the tail and re-windows", () => {
		const r = Ring.from([1, 2, 3, 4], 3);
		expect(r.toArray()).toEqual([2, 3, 4]);
		r.resize(2);
		expect(r.toArray()).toEqual([3, 4]);
		r.resize(4);
		r.push(5);
		expect(r.toArray()).toEqual([3, 4, 5]);
	});
});

describe("mergeOption", () => {
	it("matches by id, then name, then the first free slot", () => {
		const base = { series: [{ id: "a", v: 1 }, { name: "b", v: 2 }, { v: 3 }] };
		const out = mergeOption(base, { series: [{ name: "b", w: 2 }, { id: "a", w: 1 }, { w: 3 }] });
		expect(out.series).toEqual([
			{ id: "a", v: 1, w: 1 },
			{ name: "b", v: 2, w: 2 },
			{ v: 3, w: 3 },
		]);
		expect(base.series[0]).toEqual({ id: "a", v: 1 });
	});

	it("replaces value arrays and appends past the free slots", () => {
		const out = mergeOption(
			{ color: ["#000"], series: [{ name: "a", data: [1, 2] }] },
			{ color: ["#fff"], series: [{ name: "a", data: [3] }, { name: "z" }] },
		);
		expect(out.color).toEqual(["#fff"]);
		expect(out.series).toEqual([{ name: "a", data: [3] }, { name: "z" }]);
	});

	it("treats one object and a list as the same component", () => {
		expect(mergeOption({ xAxis: [{ type: "time" }] }, { xAxis: { name: "t" } }).xAxis).toEqual([
			{ type: "time", name: "t" },
		]);
	});

	it("says which series a patch gives data", () => {
		const base = { series: [{ name: "a" }, { name: "b" }] };
		// "c" matches no name, so like ECharts it takes the first free slot.
		expect(
			seriesWithData(base, {
				series: [
					{ name: "b", data: [] },
					{ name: "c", data: [] },
				],
			}),
		).toEqual([1, 0]);
		expect(seriesWithData(base, { series: [{ id: "q", data: [] }] })).toEqual([2]);
	});

	it("knows what needs the full build", () => {
		expect(needsFull({ series: [{ type: "line" }, { type: "sankey" }] })).toBe(false);
		expect(needsFull({ series: [{ type: "map" }] })).toBe(true);
		expect(needsFull({ dataZoom: [{}], series: [] })).toBe(true);
	});
});

describe("theme", () => {
	it("reads the tokens where the chart sits and falls back to Dawn", () => {
		const el = document.createElement("div");
		el.style.setProperty("--chart-1", "#123456");
		document.body.appendChild(el);
		const t = readChartTokens(el);
		expect(t.palette[0]).toBe("#123456");
		expect(t.palette[1]).toBe("#a67e1b");
		const theme = chartTheme(t);
		expect((theme.color as string[])[0]).toBe("#123456");
		expect(resolveVars(el, { color: ["var(--chart-1)", "#fff"], data: [1, 2] })).toEqual({
			color: ["#123456", "#fff"],
			data: [1, 2],
		});
		el.remove();
	});
});

// --- the node ---------------------------------------------------------------------

const LINE = {
	series: [
		{ type: "line", name: "cpu", data: [] },
		{ type: "line", name: "mem", data: [[0, 1]] },
	],
};

let host: HTMLDivElement;
let root: Root;
let sent: unknown[];

function props(path: string[]) {
	return tree.getState().getIn(path)?.props ?? {};
}

function dispatch(op: string, ref: string[], payload: unknown) {
	act(() => tree.getState().dispatch({ op, ref, payload }));
}

async function draw(path: string[]) {
	await act(async () => root.render(<NodeView path={path} />));
	await act(async () => {});
}

beforeEach(() => {
	vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame"] });
	fakes.length = 0;
	sent = [];
	tree.getState().setSender((f) => sent.push(f));
	tree.getState().remove([]);
	tree.getState().write([["c", "Chart", { option: LINE, max_points: 3 }]]);
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
	vi.useRealTimers();
});

describe("Chart node handlers", () => {
	it("appends into a ring, windowed, without touching the store", () => {
		const before = props(["c"]).option;
		dispatch("append", ["c"], {
			series: "cpu",
			points: [
				[1, 1],
				[2, 2],
			],
		});
		dispatch("append", ["c"], {
			series: 0,
			points: [
				[3, 3],
				[4, 4],
			],
		});
		expect(props(["c"]).option).toBe(before);
		expect(streamData(["c"]).get(0)).toEqual([
			[2, 2],
			[3, 3],
			[4, 4],
		]);
	});

	it("seeds a ring from the series' own data", () => {
		dispatch("append", ["c"], { series: "mem", points: [[1, 2]] });
		expect(streamData(["c"]).get(1)).toEqual([
			[0, 1],
			[1, 2],
		]);
	});

	it("adds a series for an unknown name, styled like the last", () => {
		dispatch("append", ["c"], { series: "gpu", points: [[1, 5]] });
		const series = props(["c"]).option as typeof LINE;
		expect(series.series[2]).toEqual({ type: "line", name: "gpu", data: [] });
		expect(streamData(["c"]).get(2)).toEqual([[1, 5]]);
		dispatch("append", ["c"], { series: 7, points: [[1, 5]] });
		expect(streamData(["c"]).has(7)).toBe(false);
	});

	it("merges a patch, and new data takes the series back from its ring", () => {
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		dispatch("append", ["c"], { series: "mem", points: [[1, 1]] });
		dispatch("merge", ["c"], {
			title: { text: "Load" },
			series: [{ name: "cpu", data: [[9, 9]] }],
		});
		const option = props(["c"]).option as Record<string, unknown>;
		expect(option.title).toEqual({ text: "Load" });
		expect((option.series as { data: unknown }[])[0].data).toEqual([[9, 9]]);
		expect([...streamData(["c"]).keys()]).toEqual([1]);
	});

	it("clears one series or all, rings with them", () => {
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		dispatch("clear", ["c"], { series: "mem" });
		let series = (props(["c"]).option as typeof LINE).series;
		expect(series[1].data).toEqual([]);
		expect(streamData(["c"]).has(0)).toBe(true);
		dispatch("clear", ["c"], { series: null });
		series = (props(["c"]).option as typeof LINE).series;
		expect(series.map((s) => s.data)).toEqual([[], []]);
		expect(streamData(["c"]).size).toBe(0);
	});

	it("replaces the whole option on write and starts over", () => {
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		dispatch("write", ["c"], { option: { series: [{ type: "bar", data: [1] }] }, max_points: 10 });
		expect(props(["c"]).revision).toBe(1);
		expect(props(["c"]).max_points).toBe(10);
		expect(streamData(["c"]).size).toBe(0);
	});

	it("drops the rings when the node goes", () => {
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		act(() => tree.getState().remove(["c"]));
		expect(peekStream(["c"])).toBeUndefined();
	});
});

describe("Chart node drawing", () => {
	it("draws the option with aria on and streamed points swapped in", async () => {
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		await draw(["c"]);
		expect(fakes).toHaveLength(1);
		const first = fakes[0].options[0];
		expect(first.opts).toEqual({ notMerge: true });
		expect(first.option.aria).toEqual({ enabled: true });
		expect((first.option.series as { data: unknown }[])[0].data).toEqual([[1, 1]]);
	});

	it("redraws a stream once per frame, however many points land", async () => {
		await draw(["c"]);
		const f = fakes[0];
		const before = f.options.length;
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		dispatch("append", ["c"], { series: "cpu", points: [[2, 2]] });
		dispatch("append", ["c"], { series: "mem", points: [[3, 3]] });
		expect(f.options.length).toBe(before);
		act(() => vi.advanceTimersToNextFrame());
		expect(f.options.length).toBe(before + 1);
		const patch = f.options[before];
		expect(patch.option).toEqual({
			series: [
				{
					data: [
						[1, 1],
						[2, 2],
					],
				},
				{
					data: [
						[0, 1],
						[3, 3],
					],
				},
			],
		});
		expect(patch.opts).toEqual({ lazyUpdate: true, silent: true });
	});

	it("merges a new option into the instance, list-replacing series", async () => {
		await draw(["c"]);
		dispatch("merge", ["c"], { title: { text: "Load" } });
		await act(async () => {});
		const last = fakes[0].options.at(-1);
		expect(last?.opts).toEqual({ replaceMerge: ["series"] });
		expect(last?.option.title).toEqual({ text: "Load" });
	});

	it("keeps each series' id across a set, so it moves rather than redraws", async () => {
		tree.getState().write([
			[
				"n",
				"Chart",
				{
					option: {
						series: [
							{ type: "line", name: "cpu", data: [1] },
							{ type: "line", name: "cpu", data: [2] },
							{ type: "gauge", data: [3] },
						],
					},
				},
			],
		]);
		await draw(["n"]);
		const ids = () =>
			(fakes[0].options.at(-1)?.option.series as { id?: string }[]).map((s) => s.id);
		const first = ids();
		dispatch("merge", ["n"], { series: [{ name: "cpu", data: [4] }] });
		await act(async () => {});
		expect(fakes[0].options.at(-1)?.opts).toEqual({ replaceMerge: ["series"] });
		expect(ids()).toEqual(first);
		expect(first).toEqual(["__s0", "__s1", "__s2"]);
	});

	it("ids a series by its name when the name is its own", async () => {
		tree.getState().write([
			["u", "Chart", { option: { series: [{ type: "line", name: "cpu", data: [1] }, { type: "line", data: [2] }] } }],
		]);
		await draw(["u"]);
		const series = fakes[0].options.at(-1)?.option.series as { id?: string }[];
		expect(series.map((s) => s.id)).toEqual(["__n:cpu", "__s1"]);
	});

	it("re-inits with the new theme when <html> changes", async () => {
		await draw(["c"]);
		dispatch("append", ["c"], { series: "cpu", points: [[1, 1]] });
		act(() => vi.advanceTimersToNextFrame());
		// jsdom does not inherit custom properties, so the rule targets the
		// chart element itself, under the class the switch toggles.
		const style = document.createElement("style");
		style.textContent = ".dark [data-slot=chart] { --chart-1: #abcdef; }";
		document.head.appendChild(style);
		await act(async () => {
			document.documentElement.classList.add("dark");
			// The observer reports on a microtask; let it land inside act.
			await Promise.resolve();
		});
		await act(async () => {});
		expect(fakes).toHaveLength(2);
		expect(fakes[0].disposed).toBe(true);
		expect((fakes[1].theme.color as string[])[0]).toBe("#abcdef");
		// The redraw keeps what streamed in before the switch.
		const series = fakes[1].options[0].option.series as { data: unknown }[];
		expect(series[0].data).toEqual([[1, 1]]);
		await act(async () => {
			document.documentElement.classList.remove("dark");
			style.remove();
			await Promise.resolve();
		});
	});

	it("turns a click on a data item into a notify", async () => {
		await draw(["c"]);
		act(() =>
			fakes[0].handlers.click({
				componentType: "series",
				seriesName: "cpu",
				seriesIndex: 0,
				name: "",
				dataIndex: 2,
				value: [2, 5],
			}),
		);
		expect(sent).toEqual([
			{
				op: "notify",
				ref: ["c"],
				payload: {
					event: "click",
					series: "cpu",
					series_index: 0,
					name: "",
					index: 2,
					value: [2, 5],
				},
				id: undefined,
			},
		]);
	});
});
