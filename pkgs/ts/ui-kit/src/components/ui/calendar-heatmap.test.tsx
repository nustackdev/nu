// CalendarHeatmap: the window math, the quartile shades, the labels, and the
// node reading its props off the tree.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "../../nodes";
import { CalendarHeatmap } from "./calendar-heatmap";
import {
	buildModel,
	describeDay,
	describeParts,
	levelOf,
	parseDay,
	thresholds,
} from "./calendar-heatmap-model";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// 2026-11-10 is a Tuesday.
const END = new Date(2026, 10, 10);

describe("buildModel", () => {
	it("ends with the week of end, monday first", () => {
		const m = buildModel({}, END, 53, "mon");
		expect(m.days).toHaveLength(53 * 7);
		expect(m.days[0].date.getDay()).toBe(1);
		const last = m.days.map((d) => d.level !== null).lastIndexOf(true);
		expect(m.days[last].key).toBe("2026-11-10");
		// Wednesday to Sunday of the last week are padding.
		expect(m.days.slice(last + 1).every((d) => d.level === null)).toBe(true);
		expect(m.days.length - 1 - last).toBe(5);
	});

	it("starts the week on sunday when asked", () => {
		const m = buildModel({}, END, 2, "sun");
		expect(m.days[0].date.getDay()).toBe(0);
		expect(m.days[0].key).toBe("2026-11-01");
	});

	it("sums parts into totals and finds the peak", () => {
		const m = buildModel(
			{
				"2026-11-09": { jobs: 2, builds: 7 },
				"2026-11-10": { jobs: 1, builds: 30 },
				"2026-11-11": { jobs: 99, builds: 99 },
			},
			END,
			53,
			"mon",
		);
		expect(m.totals).toEqual([
			["jobs", 3],
			["builds", 37],
		]);
		expect(m.peak?.key).toBe("2026-11-10");
	});

	it("ignores junk values", () => {
		const m = buildModel({ "2026-11-10": -4, "2026-11-09": Number.NaN }, END, 1, "mon");
		expect(m.peak).toBeNull();
		expect(m.days.filter((d) => d.level !== null).every((d) => d.level === 0)).toBe(true);
	});

	it("labels a month at the first week that starts in it", () => {
		const m = buildModel({}, END, 53, "mon");
		expect(m.months.at(-1)?.label).toBe("Nov");
		expect(m.months.every((x) => x.week > 0)).toBe(true);
	});
});

describe("levels", () => {
	it("cuts at the quartiles of non-zero days", () => {
		const th = thresholds([0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 1000]);
		expect(levelOf(0, th)).toBe(0);
		expect(levelOf(1, th)).toBe(1);
		expect(levelOf(1000, th)).toBe(4);
		// One huge day does not wash the rest into level 1.
		expect(levelOf(7, th)).toBe(3);
	});
});

describe("labels", () => {
	it("names parts, drops the s for one, compacts big numbers", () => {
		expect(
			describeParts([
				["jobs", 1],
				["builds", 14380],
			]),
		).toBe("1 job, 14.4K builds");
		expect(describeParts([["", 12]], "commits")).toBe("12 commits");
		expect(describeParts([["", 12]])).toBe("12");
	});

	it("reads a day", () => {
		const m = buildModel({ "2026-11-10": { jobs: 2, builds: 7 } }, END, 1, "mon");
		const day = m.days.find((d) => d.key === "2026-11-10");
		const empty = m.days.find((d) => d.key === "2026-11-09");
		expect(day && describeDay(day, "", "finished")).toBe("Nov 10: 2 jobs, 7 builds finished");
		expect(empty && describeDay(empty, "", "finished")).toBe("Nov 9: nothing finished");
	});

	it("parses only full days", () => {
		expect(parseDay("2026-11-10")?.getDate()).toBe(10);
		expect(parseDay("2026-11")).toBeNull();
	});
});

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

describe("CalendarHeatmap", () => {
	it("draws a square per day, totals, peak and legend", () => {
		act(() =>
			root.render(
				<CalendarHeatmap
					values={{ "2026-11-10": { jobs: 2, builds: 7 } }}
					end="2026-11-10"
					title="Added per day"
					suffix="finished"
				/>,
			),
		);
		const grid = host.querySelector("[role=application]");
		expect(grid?.children).toHaveLength(53 * 7);
		expect(host.textContent).toContain("Added per day");
		expect(host.textContent).toContain("Busiest Nov 10: 2 jobs, 7 builds");
		expect(host.textContent).toContain("Less");
	});

	it("walks days with the arrows and shows the tooltip", () => {
		act(() =>
			root.render(<CalendarHeatmap values={{ "2026-11-09": 3 }} end="2026-11-10" unit="commits" />),
		);
		const grid = host.querySelector<HTMLElement>("[role=application]");
		act(() => {
			grid?.focus();
			grid?.dispatchEvent(new KeyboardEvent("keydown", { key: "End", bubbles: true }));
		});
		act(() => {
			grid?.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }));
		});
		const tip = document.querySelector("[data-slot=calendar-heatmap-tooltip]");
		expect(tip?.textContent).toBe("Nov 9: 3 commits");
	});
});

describe("CalendarHeatmapRef", () => {
	it("reads values and chrome off the node", () => {
		tree.getState().write([
			[
				"n",
				"CalendarHeatmapRef",
				{
					values: { "2026-11-10": 4 },
					end: "2026-11-10",
					weeks: 4,
					title: "Commits",
					peak_label: "",
				},
			],
		]);
		act(() => root.render(<NodeView path={["n"]} />));
		expect(host.querySelector("[role=application]")?.children).toHaveLength(28);
		expect(host.textContent).toContain("Commits");
		expect(host.textContent).not.toContain("Busiest");
	});

	it("survives a bad values payload", () => {
		tree.getState().write([["n", "CalendarHeatmapRef", { values: [1, 2], weeks: "x" }]]);
		act(() => root.render(<NodeView path={["n"]} />));
		expect(host.querySelector("[role=application]")?.children).toHaveLength(53 * 7);
	});
});
