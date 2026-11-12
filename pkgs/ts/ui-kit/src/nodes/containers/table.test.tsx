// Table (the content table) over the real tree store: rows and cells by
// position, any kind in a cell, column records (labels, alignment, widths,
// wrap, hide_below) and header cells, spans, and the set_child op.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

type Step = [string, string, Record<string, unknown>?];

function write(...chain: Step[]) {
	act(() => {
		tree
			.getState()
			.write(chain.map(([seg, type, props]) => (props ? [seg, type, props] : [seg, type])));
	});
}

/** A cell child at (row, col) under the table "t". */
function put(row: string, col: string, type: string, props: Record<string, unknown>) {
	write(["t", "Table"], [row, "TableRow"], [col, type, props]);
}

const bodyRows = () => [...host.querySelectorAll("tbody tr")];
const bodyText = () =>
	bodyRows().map((r) => [...r.querySelectorAll("td")].map((c) => c.textContent));
const headText = () => [...host.querySelectorAll("thead th")].map((c) => c.textContent);

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

function mount(props: Record<string, unknown> = {}) {
	write(["t", "Table", props]);
	act(() => root.render(<NodeView path={["t"]} />));
}

describe("Table", () => {
	it("draws cells by position, whatever order they were written in", () => {
		mount();
		put("1", "1", "TextRef", { value: "d" });
		put("0", "0", "TextRef", { value: "a" });
		put("1", "0", "TextRef", { value: "c" });
		put("0", "1", "BadgeRef", { label: "b" });
		expect(bodyText()).toEqual([
			["a", "b"],
			["c", "d"],
		]);
		expect(host.querySelector("table")?.getAttribute("aria-label")).toBe("Table");
	});

	it("fills every position up to the largest written", () => {
		mount();
		put("2", "1", "TextRef", { value: "x" });
		expect(bodyText()).toEqual([
			["", ""],
			["", ""],
			["", "x"],
		]);
	});

	it("draws header labels, and header cells with content over them", () => {
		mount({ columns: [{ label: "Part" }, { key: "Status" }] });
		put("0", "0", "TextRef", { value: "pump" });
		expect(headText()).toEqual(["Part", "Status"]);
		put("header", "1", "BadgeRef", { label: "State" });
		expect(headText()).toEqual(["Part", "State"]);
	});

	it("has no header without labels or a header row", () => {
		mount();
		put("0", "0", "TextRef", { value: "a" });
		expect(host.querySelector("thead")).toBeNull();
	});

	it("aligns columns", () => {
		mount({ columns: [{ key: "a" }, { key: "b", align: "end" }] });
		put("0", "1", "TextRef", { value: "9" });
		const tds = host.querySelectorAll("tbody td");
		expect(tds[0].className).toContain("text-start");
		expect(tds[1].className).toContain("text-end");
	});

	it("sizes a column: width on the header, min and max on the cell's box", () => {
		mount({ columns: [{ key: "a", width: 120, min_width: "4rem", max_width: "prose" }] });
		put("0", "0", "TextRef", { value: "x" });
		expect((host.querySelector("thead th") as HTMLElement).style.width).toBe("120px");
		const box = host.querySelector("[data-slot=table-column-box]") as HTMLElement;
		expect(box.style.minWidth).toBe("4rem");
		expect(box.style.maxWidth).toBe("40rem");
	});

	it("truncates a column to one line with the whole text as its title", () => {
		mount({
			columns: [
				{ key: "a", wrap: "truncate", max_width: 80 },
				{ key: "b", wrap: "nowrap" },
			],
		});
		put("0", "0", "TextRef", { value: "a long backend name" });
		put("0", "1", "TextRef", { value: "kept" });
		const [cut, kept] = [...host.querySelectorAll("[data-slot=table-column-box]")] as HTMLElement[];
		expect(cut.className).toContain("text-ellipsis");
		expect(cut.title).toBe("a long backend name");
		expect(kept.className).toContain("whitespace-nowrap");
		expect(kept.title).toBe("");
	});

	it("hides a column under its hide_below width, keeping its place", () => {
		let width = 400;
		vi.stubGlobal(
			"ResizeObserver",
			class {
				observe() {}
				disconnect() {}
			},
		);
		const spy = vi
			.spyOn(HTMLElement.prototype, "clientWidth", "get")
			.mockImplementation(() => width);
		try {
			mount({ columns: [{ key: "a" }, { key: "b", hide_below: 480 }, { key: "c" }] });
			for (const c of ["0", "1", "2"]) put("0", c, "TextRef", { value: c });
			const heads = [...host.querySelectorAll("thead th")] as HTMLElement[];
			const tds = [...host.querySelectorAll("tbody td")] as HTMLElement[];
			expect(heads.map((h) => h.style.display)).toEqual(["", "none", ""]);
			expect(tds.map((d) => d.style.display)).toEqual(["", "none", ""]);
			width = 600;
			act(() => root.unmount());
			root = createRoot(host);
			act(() => root.render(<NodeView path={["t"]} />));
			const shown = [...host.querySelectorAll("tbody td")] as HTMLElement[];
			expect(shown.map((d) => d.style.display)).toEqual(["", "", ""]);
		} finally {
			spy.mockRestore();
			vi.unstubAllGlobals();
		}
	});

	it("sizes its frame with the size layer", () => {
		mount({ max_height: 200, scroll: "y" });
		const box = host.querySelector("[data-slot=table-box]") as HTMLElement;
		expect(box.style.maxHeight).toBe("200px");
		expect(box.className).toContain("overflow-y-auto");
	});

	it("spans cells and leaves the covered ones out", () => {
		mount({ span: { "0,0": { cols: 2, rows: 2 } } });
		for (const r of ["0", "1"])
			for (const c of ["0", "1", "2"]) put(r, c, "TextRef", { value: r + c });
		expect(bodyText()).toEqual([["00", "02"], ["12"]]);
		const first = host.querySelector("tbody td");
		expect(first?.getAttribute("colspan")).toBe("2");
		expect(first?.getAttribute("rowspan")).toBe("2");
	});

	it("takes set_child and drops a 1 by 1 span", () => {
		mount();
		for (const c of ["0", "1"]) put("0", c, "TextRef", { value: c });
		act(() =>
			tree.getState().dispatch({
				op: "set_child",
				ref: ["t"],
				payload: { key: "0,0", span: { cols: 2, rows: 1 } },
			}),
		);
		expect(bodyText()).toEqual([["0"]]);
		act(() =>
			tree.getState().dispatch({
				op: "set_child",
				ref: ["t"],
				payload: { key: "0,0", span: { cols: 1, rows: 1 } },
			}),
		);
		expect(bodyText()).toEqual([["0", "1"]]);
	});

	it("leaves a hidden row out and an erased cell empty", () => {
		mount();
		put("0", "0", "TextRef", { value: "a" });
		put("1", "0", "TextRef", { value: "b" });
		act(() => tree.getState().setHidden(["t", "0"], true));
		expect(bodyText()).toEqual([["b"]]);
		act(() => tree.getState().setHidden(["t", "0"], false));
		act(() => tree.getState().remove(["t", "1", "0"]));
		expect(bodyText()).toEqual([["a"], [""]]);
	});

	it("nests: a row of children and another table in a cell", () => {
		mount();
		write(["t", "Table"], ["0", "TableRow"], ["0", "Row"], ["a", "TextRef", { value: "x" }]);
		write(
			["t", "Table"],
			["0", "TableRow"],
			["1", "Table"],
			["0", "TableRow"],
			["0", "TextRef", { value: "inner" }],
		);
		expect(host.querySelectorAll("table")).toHaveLength(2);
		expect(host.textContent).toContain("inner");
		expect(host.textContent).toContain("x");
	});
});
