// Timeline: where intervals land, how overlaps pack into rows, that capping
// never drops a danger item or a count, and that the node reads the wire
// leniently.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { formatCount } from "../../lib/count";
import { readItem, readLane, readLegend } from "../../nodes/output/timeline";
import {
	capItems,
	formatLength,
	layoutItems,
	Timeline,
	type TimelineItem,
	type TimelineLane,
	timelineTicks,
} from "./timeline";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures the tooltip through ResizeObserver, which jsdom lacks.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
};

const M = 60_000;
const END = 1_800_000_000_000;
const START = END - 60 * M;
const ago = (min: number) => END - min * M;

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

describe("layoutItems", () => {
	it("places an interval in percent of the window, clipped to it", () => {
		const [m] = layoutItems([{ start: ago(90), end: ago(30) }], START, END).marks;
		expect(m.left).toBe(0);
		expect(m.width).toBeCloseTo(50);
		expect(m.tone).toBe("neutral");
	});

	it("draws an open interval to the window's end", () => {
		const [m] = layoutItems([{ start: ago(15), end: null, tone: "ok" }], START, END).marks;
		expect(m.left).toBeCloseTo(75);
		expect(m.width).toBeCloseTo(25);
		expect(m.open).toBe(true);
	});

	it("keeps one row while nothing overlaps", () => {
		const l = layoutItems(
			[
				{ start: ago(50), end: ago(40) },
				{ start: ago(40), end: ago(30) },
			],
			START,
			END,
		);
		expect(l.rows).toBe(1);
	});

	it("packs overlaps into sub-rows, then stacks past three", () => {
		const two = layoutItems(
			[
				{ start: ago(50), end: ago(20) },
				{ start: ago(40), end: ago(10) },
			],
			START,
			END,
		);
		expect(two.rows).toBe(2);
		expect(two.marks.map((m) => m.row)).toEqual([0, 1]);
		expect(two.marks.some((m) => m.stacked)).toBe(false);

		const five = layoutItems(
			Array.from({ length: 5 }, (_, i) => ({ start: ago(50 - i), end: ago(5) })),
			START,
			END,
		);
		expect(five.rows).toBe(3);
		expect(five.marks).toHaveLength(5);
		expect(five.marks.every((m) => m.stacked)).toBe(true);
	});

	it("leaves out intervals wholly outside the window", () => {
		expect(layoutItems([{ start: ago(120), end: ago(90) }], START, END).marks).toEqual([]);
	});
});

describe("capItems", () => {
	it("keeps every danger item and fills with the newest", () => {
		const items: TimelineItem[] = Array.from({ length: 20 }, (_, i) => ({
			start: i,
			end: i + 0.5,
			tone: i === 2 ? "danger" : "ok",
		}));
		const kept = capItems(items, 5);
		expect(kept).toHaveLength(5);
		expect(kept.some((it) => it.tone === "danger")).toBe(true);
		expect(kept.filter((it) => it.tone === "ok").map((it) => it.start)).toEqual([19, 18, 17, 16]);
	});
});

describe("formatting", () => {
	it("compacts past 9,999", () => {
		expect(formatCount(9999)).toBe("9,999");
		expect(formatCount(48210)).toBe("48.2K");
	});

	it("words a length in two parts at most", () => {
		expect(formatLength(400)).toBe("0.4s");
		expect(formatLength(200_000)).toBe("3m 20s");
		expect(formatLength(27 * 3_600_000 + 5 * M)).toBe("1d 3h");
	});

	it("counts the axis back from now", () => {
		expect(timelineTicks(START, END, "relative")).toEqual(["60m ago", "45m", "30m", "15m", "now"]);
	});

	it("words the ticks to the span", () => {
		expect(timelineTicks(END - 3 * 86_400_000, END, "relative")[0]).toBe("3d ago");
		expect(timelineTicks(END - 5 * 86_400_000, END, "relative")[1]).toBe("3d 18h");
		expect(timelineTicks(END - 3 * 86_400_000, END, "relative")[3]).toBe("18h");
		expect(timelineTicks(END - 10 * 60_000, END, "relative")[1]).toBe("8m");
		expect(timelineTicks(END - 8 * 3_600_000, END, "relative")[1]).toBe("6h");
		expect(timelineTicks(END - 10 * 3_600_000, END, "relative")[1]).toBe("7h 30m");
	});
});

describe("Timeline", () => {
	const lane = (i: number, items: TimelineItem[] = [], extra: Partial<TimelineLane> = {}) => ({
		id: `l${i}`,
		title: `Lane ${i}`,
		items,
		...extra,
	});

	it("caps lanes and counts the rest from the total", () => {
		const lanes = Array.from({ length: 12 }, (_, i) => lane(i));
		mount(
			<Timeline start={START} end={END} lanes={lanes} totalLanes={2150} moreLabel="more lanes" />,
		);
		expect(host.querySelectorAll("[data-slot=timeline-lane]")).toHaveLength(10);
		expect(host.querySelector("[data-slot=timeline-more]")?.textContent).toBe("+2,140 more lanes");
	});

	it("draws no more row when nothing is left out", () => {
		mount(<Timeline start={START} end={END} lanes={[lane(0)]} />);
		expect(host.querySelector("[data-slot=timeline-more]")).toBeNull();
	});

	it("draws every lane at maxLanes 0, and the note under them", () => {
		const lanes = Array.from({ length: 20 }, (_, i) => lane(i));
		mount(<Timeline start={START} end={END} lanes={lanes} maxLanes={0} note="The last 20" />);
		expect(host.querySelectorAll("[data-slot=timeline-lane]")).toHaveLength(20);
		expect(host.querySelector("[data-slot=timeline-more]")).toBeNull();
		expect(host.querySelector("[data-slot=timeline-note]")?.textContent).toBe("The last 20");
	});

	it("draws at most maxItems bars, the count still the full one", () => {
		const items: TimelineItem[] = Array.from({ length: 300 }, (_, i) => ({
			start: ago(60 - i * 0.2),
			end: ago(60 - i * 0.2 - 0.1),
			tone: i % 50 === 0 ? "danger" : "ok",
		}));
		mount(<Timeline start={START} end={END} lanes={[lane(0, items, { count: 48210 })]} />);
		expect(host.querySelector("[data-slot=timeline-count]")?.textContent).toBe("48.2K items");
		const bars = host.querySelectorAll("[data-slot=timeline-bar]");
		expect(bars).toHaveLength(100);
		expect([...bars].filter((b) => b.getAttribute("data-tone") === "danger")).toHaveLength(6);
	});

	it("gives a too-short interval a minimum width", () => {
		mount(
			<Timeline
				start={START}
				end={END}
				lanes={[lane(0, [{ start: ago(10), end: ago(10) + 50 }])]}
			/>,
		);
		const bar = host.querySelector<HTMLElement>("[data-slot=timeline-bar]");
		expect(bar?.style.minWidth).toBe("3px");
	});

	it("keys only the tones it draws and names", () => {
		mount(
			<Timeline
				start={START}
				end={END}
				legend={{ ok: "done", danger: "failed", warn: "slow" }}
				lanes={[lane(0, [{ start: ago(10), end: ago(5), tone: "ok" }])]}
			/>,
		);
		expect(host.querySelector("[data-slot=timeline-legend]")?.textContent).toBe("done");
	});

	it("tells the hovered bar in one tooltip: label, tone name, when, how long", () => {
		mount(
			<Timeline
				start={START}
				end={END}
				legend={{ danger: "failed" }}
				lanes={[lane(0, [{ start: ago(10), end: ago(7), tone: "danger", label: "#41" }])]}
			/>,
		);
		const bar = host.querySelector("[data-slot=timeline-bar]") as HTMLElement;
		act(() => {
			bar.dispatchEvent(new PointerEvent("pointerover", { bubbles: true }));
		});
		const tip = document.querySelector("[data-slot=tooltip-content]");
		expect(tip?.textContent).toContain("#41");
		expect(tip?.textContent).toContain("failed");
		expect(tip?.textContent).toContain("3m");
	});

	it("links a lane with an href", () => {
		mount(<Timeline start={START} end={END} lanes={[lane(0, [], { href: "/p/deploys" })]} />);
		const a = host.querySelector("a[data-slot=timeline-label]");
		expect(a?.getAttribute("href")).toBe("/p/deploys");
		expect(a?.textContent).toBe("Lane 0");
	});

	it("says one item, not one items", () => {
		mount(<Timeline start={START} end={END} lanes={[lane(0, [{ start: ago(5) }])]} />);
		expect(host.querySelector("[data-slot=timeline-count]")?.textContent).toBe("1 item");
	});
});

describe("node readers", () => {
	it("reads lists and objects alike, an open end as null", () => {
		expect(readItem([1, null, "ok", "#41"])).toEqual({
			start: 1,
			end: null,
			tone: "ok",
			label: "#41",
		});
		expect(readItem({ start: 1, end: 2, tone: "nope" })).toEqual({
			start: 1,
			end: 2,
			tone: "neutral",
			label: undefined,
		});
		expect(readItem(["x"])).toBeNull();
	});

	it("says a lane's count in the host's words when it gives them", () => {
		const items: TimelineItem[] = [{ start: ago(30), end: ago(29), tone: "ok" }];
		mount(
			<Timeline
				start={START}
				end={END}
				lanes={[{ id: "a", title: "A", items, count: 100, countLabel: "100+ items" }]}
			/>,
		);
		const cell = host.querySelector("[data-slot=timeline-count]");
		expect(cell?.textContent).toBe("100+ items");
		expect(cell?.getAttribute("title")).toBe("100");
		expect(readLane({ title: "a", items: [], count_label: "100+ runs" }, 0)?.countLabel).toBe(
			"100+ runs",
		);
		expect(readLane({ title: "a", items: [] }, 0)?.countLabel).toBeUndefined();
	});

	it("reads a lane, an emoji icon as a mark, dropping bad items", () => {
		const l = readLane({ title: "Chat", icon: "🤖", items: [[1, 2, "ok"], "bad"], count: 7 }, 0);
		expect(l?.mark).toBe("🤖");
		expect(l?.icon).toBeUndefined();
		expect(l?.items).toHaveLength(1);
		expect(l?.count).toBe(7);
		expect(readLane("nope", 0)).toBeNull();
	});

	it("reads the legend, known tones only", () => {
		expect(readLegend({ ok: "done", purple: "x", danger: 3 })).toEqual({ ok: "done" });
		expect(readLegend(null)).toEqual({});
	});
});
