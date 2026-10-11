// Row and Column over the real tree store: how each child is sized by its
// kind, the divider that turns with the row, the chart props a slot declares,
// and chrome that arrives on a frame before its container exists.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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

function draw(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

function dispatch(frame: Parameters<ReturnType<typeof tree.getState>["dispatch"]>[0]) {
	act(() => tree.getState().dispatch(frame));
}

const cells = () => [...host.querySelectorAll<HTMLElement>("[data-slot=row-cell]")];

describe("Row", () => {
	beforeEach(() => {
		const { write } = tree.getState();
		write([["r", "Row", { gap: 4, wrap: true }]]);
		write([
			["r", "Row"],
			["chart", "LineChart"],
		]);
		write([
			["r", "Row"],
			["btn", "ButtonRef", { label: "Go" }],
		]);
		write([
			["r", "Row"],
			["card", "Card", { title: "C" }],
		]);
	});

	it("wraps each child in a cell", () => {
		draw(["r"]);
		expect(cells()).toHaveLength(3);
	});

	it("grows a fill child's cell from the min width and keeps a content child's size", () => {
		draw(["r"]);
		const [chart, btn, card] = cells();
		expect(chart.style.flex).toBe("1 1 240px");
		expect(card.style.flex).toBe("1 1 240px");
		expect(btn.style.flex).toBe("0 1 auto");
		expect(chart.hasAttribute("data-fill")).toBe(true);
		expect(btn.hasAttribute("data-fill")).toBe(false);
	});

	it("reads the row's min width for the fill basis", () => {
		tree.getState().setProps(["r"], { min_width: 320 });
		draw(["r"]);
		expect(cells()[0].style.flex).toBe("1 1 320px");
	});

	it("snaps a gap off the ladder to the nearest step", () => {
		tree.getState().setProps(["r"], { gap: 7 });
		draw(["r"]);
		expect(host.firstElementChild?.className).toContain("gap-6");
	});
});

describe("DividerRef", () => {
	it("stands vertical in a Row and lies horizontal in a Column", () => {
		const { write } = tree.getState();
		write([
			["page", "Column"],
			["r", "Row"],
			["d", "DividerRef"],
		]);
		write([
			["page", "Column"],
			["d", "DividerRef"],
		]);
		draw(["page"]);
		const orientations = [...host.querySelectorAll("[data-slot=separator]")].map((el) =>
			el.getAttribute("data-orientation"),
		);
		expect(orientations).toEqual(["vertical", "horizontal"]);
	});
});

describe("Column", () => {
	it("keeps a content child's width and stretches a fill child", () => {
		const { write } = tree.getState();
		write([
			["c", "Column"],
			["btn", "ButtonRef", { label: "Go" }],
		]);
		write([
			["c", "Column"],
			["inp", "InputRef"],
		]);
		draw(["c"]);
		const wrapped = [...host.querySelectorAll("[data-slot=column-cell]")];
		expect(wrapped).toHaveLength(1);
		expect(wrapped[0].querySelector("button")?.textContent).toBe("Go");
	});

	it("leaves every child bare when it is not stretching", () => {
		tree.getState().write([
			["c", "Column", { align: "center" }],
			["btn", "ButtonRef", { label: "Go" }],
		]);
		draw(["c"]);
		expect(host.querySelector("[data-slot=column-cell]")).toBeNull();
	});
});

describe("charts", () => {
	it("draws PieChart slices written as maps", () => {
		tree.getState().write([["p", "PieChart"]]);
		dispatch({
			op: "write",
			ref: ["p"],
			payload: {
				slices: [
					{ label: "Birds", value: 3 },
					{ label: "Fish", value: "2" },
				],
			},
		});
		expect(tree.getState().getIn(["p"])?.props.value).toEqual({
			slices: [
				{ label: "Birds", value: 3 },
				{ label: "Fish", value: 2 },
			],
		});
	});

	it("still takes PieChart pairs", () => {
		tree.getState().write([["p", "PieChart"]]);
		dispatch({ op: "write", ref: ["p"], payload: { slices: [["a", 1]] } });
		expect(tree.getState().getIn(["p"])?.props.value).toEqual({
			slices: [{ label: "a", value: 1 }],
		});
	});

	it("takes BarChart orientation from the declared props, before any write", () => {
		tree.getState().write([["b", "BarChart", { orientation: "horizontal" }]]);
		draw(["b"]);
		const chart = host.querySelector("[data-slot=bar-chart]");
		expect(chart?.getAttribute("data-orientation")).toBe("horizontal");
	});
});

describe("Card chrome on a fresh store", () => {
	it("creates the card from a set_title frame's chain and draws the title", () => {
		dispatch({
			op: "set_title",
			ref: ["outer", "card"],
			payload: "Hello",
			chain: [
				["outer", "Column", { gap: 4 }],
				["card", "Card", { title: "", subtitle: "", footer: "" }],
			],
		});
		draw(["outer"]);
		expect(host.textContent).toContain("Hello");
		expect(tree.getState().getIn(["outer", "card"])?.type).toBe("Card");
	});
});
