// The data table: the pure model (navigation, selection, delete, move and
// drop arithmetic, value text and parsing) and the component's behaviour
// (grid aria, roving focus, edits as requests, selection, the menu). The look
// is the story's job.

import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
	DataTable,
	type DataTableColumn,
	type DataTableProps,
	type DataTableRow,
} from "./data-table";
import {
	cellKey,
	cellText,
	clickSelection,
	deleteTargets,
	dropIndex,
	navigate,
	nextDirection,
	nextEditable,
	parseNumber,
	selectRange,
	spaceSelection,
	stepIndex,
} from "./data-table-model";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

describe("data table model", () => {
	const dims = { rows: 30, cols: 3, header: true };

	it("moves by arrows, row ends, grid ends and pages, clamped", () => {
		expect(navigate("ArrowDown", false, { row: 0, col: 1 }, dims)).toEqual({ row: 1, col: 1 });
		expect(navigate("ArrowUp", false, { row: 0, col: 1 }, dims)).toEqual({ row: -1, col: 1 });
		expect(navigate("ArrowUp", false, { row: -1, col: 1 }, dims)).toEqual({ row: -1, col: 1 });
		expect(navigate("ArrowUp", false, { row: 0, col: 1 }, { ...dims, header: false })).toEqual({
			row: 0,
			col: 1,
		});
		expect(navigate("ArrowRight", false, { row: 3, col: 2 }, dims)).toEqual({ row: 3, col: 2 });
		expect(navigate("Home", false, { row: 3, col: 2 }, dims)).toEqual({ row: 3, col: 0 });
		expect(navigate("End", false, { row: 3, col: 0 }, dims)).toEqual({ row: 3, col: 2 });
		expect(navigate("Home", true, { row: 3, col: 2 }, dims)).toEqual({ row: -1, col: 0 });
		expect(navigate("End", true, { row: 3, col: 0 }, dims)).toEqual({ row: 29, col: 2 });
		expect(navigate("PageDown", false, { row: 25, col: 0 }, dims)).toEqual({ row: 29, col: 0 });
		expect(navigate("PageUp", false, { row: 15, col: 0 }, dims)).toEqual({ row: 5, col: 0 });
		expect(navigate("x", false, { row: 0, col: 0 }, dims)).toBeNull();
	});

	it("finds the next editable cell across rows, null at the ends", () => {
		const can = (_r: number, c: number) => c !== 1;
		const d = { rows: 2, cols: 3, header: false };
		expect(nextEditable({ row: 0, col: 0 }, false, d, can)).toEqual({ row: 0, col: 2 });
		expect(nextEditable({ row: 0, col: 2 }, false, d, can)).toEqual({ row: 1, col: 0 });
		expect(nextEditable({ row: 1, col: 0 }, true, d, can)).toEqual({ row: 0, col: 2 });
		expect(nextEditable({ row: 1, col: 2 }, false, d, can)).toBeNull();
		expect(nextEditable({ row: 0, col: 0 }, true, d, can)).toBeNull();
	});

	it("selects by click, range, toggle and Space", () => {
		const order = ["a", "b", "c", "d"];
		expect(clickSelection("single", ["a"], order, "c", "a", { toggle: true })).toEqual(["c"]);
		expect(clickSelection("multi", ["a", "b"], order, "c", "a")).toEqual(["c"]);
		expect(clickSelection("multi", ["a"], order, "c", "a", { toggle: true })).toEqual(["a", "c"]);
		expect(clickSelection("multi", ["a", "c"], order, "c", "a", { toggle: true })).toEqual(["a"]);
		expect(clickSelection("multi", ["b"], order, "d", "b", { range: true })).toEqual([
			"b",
			"c",
			"d",
		]);
		expect(selectRange(order, "d", "b")).toEqual(["b", "c", "d"]);
		expect(spaceSelection("single", ["a"], "b")).toEqual(["b"]);
		expect(spaceSelection("multi", ["a", "b"], "b")).toEqual(["a"]);
		expect(spaceSelection("none", [], "b")).toEqual([]);
	});

	it("deletes the selection only when the row is in it", () => {
		expect(deleteTargets(["a", "b"], "b")).toEqual(["a", "b"]);
		expect(deleteTargets(["a", "b"], "c")).toEqual(["c"]);
	});

	it("counts move and drop indices among the rows without the moved one", () => {
		const order = ["a", "b", "c", "d"];
		expect(stepIndex(order, "b", -1)).toBe(0);
		expect(stepIndex(order, "b", 1)).toBe(2);
		expect(stepIndex(order, "a", -1)).toBeNull();
		expect(stepIndex(order, "d", 1)).toBeNull();
		expect(dropIndex(order, "a", "c", "before")).toBe(1);
		expect(dropIndex(order, "a", "d", "after")).toBe(3);
		expect(dropIndex(order, "d", "b", "before")).toBe(1);
		expect(dropIndex(order, "b", "a", "after")).toBeNull();
		expect(dropIndex(order, "b", "c", "before")).toBeNull();
	});

	it("reads values, parses numbers and turns the sort", () => {
		expect(cellText(null)).toBe("");
		expect(cellText({ a: 1 })).toBe('{"a":1}');
		expect(cellText(3)).toBe("3");
		expect(parseNumber(" 4.5 ")).toBe(4.5);
		expect(parseNumber("")).toBeNull();
		expect(parseNumber("12abc")).toBeNull();
		expect(parseNumber("Infinity")).toBeNull();
		expect(nextDirection(null, "a")).toBe("asc");
		expect(nextDirection({ column: "a", direction: "asc" }, "a")).toBe("desc");
		expect(nextDirection({ column: "a", direction: "desc" }, "a")).toBe("asc");
		expect(nextDirection({ column: "a", direction: "asc" }, "b")).toBe("asc");
		expect(cellKey(null, "a")).not.toBe(cellKey("", "a"));
	});
});

// --- The component -----------------------------------------------------------

beforeAll(() => {
	// Radix Select reaches for these; jsdom has none.
	const proto = Element.prototype as unknown as Record<string, unknown>;
	proto.hasPointerCapture ??= () => false;
	proto.releasePointerCapture ??= () => {};
	proto.scrollIntoView ??= () => {};
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
});

const COLUMNS: DataTableColumn[] = [
	{ key: "title" },
	{ key: "points", kind: "number" },
	{ key: "done", kind: "bool" },
	{ key: "state", kind: "select", options: ["todo", "doing", "done"] },
];

const ROWS: DataTableRow[] = [
	{ key: "r1", cells: ["Alpha", 3, false, "todo"] },
	{ key: "r2", cells: ["Beta", 5, true, "doing"] },
	{ key: "r3", cells: ["Gamma", 8, false, "done"] },
];

type Extra = Partial<DataTableProps>;

function mount(props: Extra = {}) {
	act(() => root.render(<DataTable aria-label="Tasks" columns={COLUMNS} rows={ROWS} {...props} />));
}

/** A host that keeps the selection, the way an app would. */
function Selecting({ mode, spy }: { mode: "single" | "multi"; spy: (keys: string[]) => void }) {
	const [selected, setSelected] = useState<string[]>([]);
	return (
		<DataTable
			aria-label="Tasks"
			columns={COLUMNS}
			rows={ROWS}
			selection={mode}
			selected={selected}
			onSelect={(keys) => {
				spy(keys);
				setSelected(keys);
			}}
		/>
	);
}

function cell(row: string | null, col: string): HTMLElement {
	const el = host.querySelector<HTMLElement>(`[data-key='${cellKey(row, col)}']`);
	if (!el) throw new Error(`no cell ${row}/${col}`);
	return el;
}

function rowEl(key: string): HTMLElement {
	const el = cell(key, "title").closest("tr");
	if (!el) throw new Error(`no row ${key}`);
	return el;
}

type Mods = { shiftKey?: boolean; metaKey?: boolean; ctrlKey?: boolean; altKey?: boolean };

function press(el: Element, key: string, mods: Mods = {}) {
	act(() => {
		el.dispatchEvent(
			new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...mods }),
		);
	});
}

function click(el: Element, mods: Mods = {}) {
	act(() => {
		el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, ...mods }));
	});
}

function input(): HTMLInputElement {
	const el = host.querySelector<HTMLInputElement>("input");
	if (!el) throw new Error("no editor");
	return el;
}

function type(value: string, key: string, mods: Mods = {}) {
	const el = input();
	act(() => {
		el.value = value;
	});
	press(el, key, mods);
}

describe("DataTable", () => {
	it("draws a read-only grid with its aria", () => {
		mount();
		const grid = host.querySelector("table");
		expect(grid?.getAttribute("role")).toBe("grid");
		expect(grid?.getAttribute("aria-label")).toBe("Tasks");
		expect(grid?.getAttribute("aria-rowcount")).toBe("4");
		expect(grid?.hasAttribute("aria-multiselectable")).toBe(false);
		expect(host.querySelectorAll('[role="columnheader"]')).toHaveLength(4);
		expect(host.querySelectorAll('[role="row"]')).toHaveLength(4);
		expect(host.querySelectorAll('[role="gridcell"]')).toHaveLength(12);
		expect(cell("r1", "title").getAttribute("aria-readonly")).toBe("true");
		expect(rowEl("r1").hasAttribute("aria-selected")).toBe(false);
		expect(rowEl("r2").getAttribute("aria-rowindex")).toBe("3");
		expect(cell("r1", "title").textContent).toBe("Alpha");
		expect(cell("r1", "points").className).toContain("text-right");
		// A read-only bool is a checkbox nobody can click.
		const box = cell("r2", "done").querySelector('[role="checkbox"]');
		expect(box?.getAttribute("aria-checked")).toBe("true");
		expect(box?.hasAttribute("disabled")).toBe(true);
		// No sort: the header is not in the grid.
		expect(cell("r1", "title").tabIndex).toBe(0);
		expect(cell("r1", "points").tabIndex).toBe(-1);
		expect(host.textContent).not.toContain("Add row");
	});

	it("shows the empty state with no rows", () => {
		mount({ rows: [] });
		expect(host.textContent).toContain("No rows");
	});

	it("moves the focus with arrows, Home, End and Ctrl+End", () => {
		mount();
		act(() => cell("r1", "title").focus());
		press(cell("r1", "title"), "ArrowRight");
		expect(document.activeElement).toBe(cell("r1", "points"));
		expect(cell("r1", "points").tabIndex).toBe(0);
		expect(cell("r1", "title").tabIndex).toBe(-1);
		press(cell("r1", "points"), "ArrowDown");
		expect(document.activeElement).toBe(cell("r2", "points"));
		press(cell("r2", "points"), "End");
		expect(document.activeElement).toBe(cell("r2", "state"));
		press(cell("r2", "state"), "Home");
		expect(document.activeElement).toBe(cell("r2", "title"));
		press(cell("r2", "title"), "End", { ctrlKey: true });
		expect(document.activeElement).toBe(cell("r3", "state"));
		press(cell("r3", "state"), "Home", { metaKey: true });
		expect(document.activeElement).toBe(cell("r1", "title"));
	});

	it("puts a sortable header in the grid and sorts from it", () => {
		const onSort = vi.fn();
		mount({ onSort, sort: { column: "points", direction: "asc" } });
		const head = cell(null, "points");
		expect(head.getAttribute("role")).toBe("columnheader");
		expect(head.getAttribute("aria-sort")).toBe("ascending");
		expect(cell(null, "title").getAttribute("aria-sort")).toBe("none");
		expect(cell(null, "title").tabIndex).toBe(0);
		press(cell("r1", "points"), "ArrowUp");
		expect(document.activeElement).toBe(head);
		press(head, "Enter");
		expect(onSort).toHaveBeenLastCalledWith("points", "desc");
		press(head, " ");
		expect(onSort).toHaveBeenCalledTimes(2);
		click(cell(null, "title"));
		expect(onSort).toHaveBeenLastCalledWith("title", "asc");
	});

	it("leaves out sorting a column that says so", () => {
		const onSort = vi.fn();
		mount({ onSort, columns: [{ key: "title", sortable: false }, ...COLUMNS.slice(1)] });
		expect(cell(null, "title").hasAttribute("aria-sort")).toBe(false);
		click(cell(null, "title"));
		expect(onSort).not.toHaveBeenCalled();
	});

	it("edits text on Enter, commits the typed value on Enter, focus back on the cell", () => {
		const onEdit = vi.fn();
		mount({ onEdit });
		expect(cell("r1", "title").hasAttribute("aria-readonly")).toBe(false);
		act(() => cell("r1", "title").focus());
		press(cell("r1", "title"), "Enter");
		expect(input().value).toBe("Alpha");
		expect(input().getAttribute("aria-label")).toBe("Edit title");
		type("Alpha two", "Enter");
		expect(onEdit).toHaveBeenCalledWith({
			key: "r1",
			index: 0,
			column: "title",
			value: "Alpha two",
			previous: "Alpha",
		});
		expect(host.querySelector("input")).toBeNull();
		expect(document.activeElement).toBe(cell("r1", "title"));
	});

	it("never changes the rows itself: an edit with no new rows shows the old value", () => {
		mount({ onEdit: () => {} });
		press(cell("r2", "title"), "F2");
		type("Changed", "Enter");
		expect(cell("r2", "title").textContent).toBe("Beta");
	});

	it("cancels on Escape and takes an unchanged value as no edit", () => {
		const onEdit = vi.fn();
		mount({ onEdit });
		press(cell("r1", "title"), "F2");
		type("Nope", "Escape");
		expect(host.querySelector("input")).toBeNull();
		expect(document.activeElement).toBe(cell("r1", "title"));
		press(cell("r1", "title"), "Enter");
		type("Alpha", "Enter");
		expect(onEdit).not.toHaveBeenCalled();
	});

	it("parses numbers, rejecting junk, empty and the same number", () => {
		const onEdit = vi.fn();
		mount({ onEdit });
		press(cell("r1", "points"), "Enter");
		type("12abc", "Enter");
		press(cell("r1", "points"), "Enter");
		type("  ", "Enter");
		press(cell("r1", "points"), "Enter");
		type("3.0", "Enter");
		expect(onEdit).not.toHaveBeenCalled();
		press(cell("r1", "points"), "Enter");
		type("4.5", "Enter");
		expect(onEdit).toHaveBeenCalledWith(
			expect.objectContaining({ column: "points", value: 4.5, previous: 3 }),
		);
	});

	it("Tab commits and edits the next text or number cell, wrapping rows", () => {
		const onEdit = vi.fn();
		// Bool and select out, so the chain is title, points, title, ...
		mount({ onEdit, columns: COLUMNS.slice(0, 2) });
		press(cell("r1", "title"), "Enter");
		type("A2", "Tab");
		expect(onEdit).toHaveBeenLastCalledWith(expect.objectContaining({ key: "r1", value: "A2" }));
		expect(input().getAttribute("aria-label")).toBe("Edit points");
		expect(cell("r1", "points").contains(input())).toBe(true);
		type("3", "Tab");
		expect(cell("r2", "title").contains(input())).toBe(true);
		type("Beta", "Tab", { shiftKey: true });
		expect(cell("r1", "points").contains(input())).toBe(true);
		expect(onEdit).toHaveBeenCalledTimes(1);
		// At the last cell, Tab commits and stays.
		type("3", "Escape");
		press(cell("r3", "points"), "Enter");
		type("9", "Tab");
		expect(host.querySelector("input")).toBeNull();
		expect(document.activeElement).toBe(cell("r3", "points"));
		expect(onEdit).toHaveBeenLastCalledWith(expect.objectContaining({ key: "r3", value: 9 }));
	});

	it("flips a bool on Enter, Space and a checkbox click", () => {
		const onEdit = vi.fn();
		mount({ onEdit });
		press(cell("r1", "done"), "Enter");
		expect(onEdit).toHaveBeenLastCalledWith(
			expect.objectContaining({ key: "r1", column: "done", value: true, previous: false }),
		);
		press(cell("r2", "done"), " ");
		expect(onEdit).toHaveBeenLastCalledWith(expect.objectContaining({ key: "r2", value: false }));
		const box = cell("r3", "done").querySelector('[role="checkbox"]');
		expect(box?.hasAttribute("disabled")).toBe(false);
		if (box) click(box);
		expect(onEdit).toHaveBeenLastCalledWith(expect.objectContaining({ key: "r3", value: true }));
		expect(onEdit).toHaveBeenCalledTimes(3);
		expect(host.querySelector("input")).toBeNull();
	});

	it("opens a select in place and emits the pick", () => {
		const onEdit = vi.fn();
		mount({ onEdit });
		act(() => cell("r1", "state").focus());
		press(cell("r1", "state"), "Enter");
		const options = [...document.querySelectorAll('[role="option"]')];
		expect(options.map((o) => o.textContent)).toEqual(["todo", "doing", "done"]);
		const doing = options[1];
		if (doing) press(doing, "Enter");
		expect(onEdit).toHaveBeenCalledWith(
			expect.objectContaining({ key: "r1", column: "state", value: "doing", previous: "todo" }),
		);
		expect(document.querySelector('[role="listbox"]')).toBeNull();
	});

	it("reads, not edits, a column that says so, and activates there", () => {
		const onEdit = vi.fn();
		const onActivate = vi.fn();
		mount({
			onEdit,
			onActivate,
			columns: [{ key: "title", editable: false }, ...COLUMNS.slice(1)],
		});
		expect(cell("r1", "title").getAttribute("aria-readonly")).toBe("true");
		press(cell("r1", "title"), "Enter");
		expect(host.querySelector("input")).toBeNull();
		expect(onActivate).toHaveBeenCalledWith("r1", 0, expect.anything());
		act(() => {
			cell("r1", "title").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		});
		expect(host.querySelector("input")).toBeNull();
		act(() => {
			cell("r1", "points").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		});
		expect(input().value).toBe("3");
	});

	it("asks for no selection a click does not change", () => {
		const spy = vi.fn();
		act(() => root.render(<Selecting mode="multi" spy={spy} />));
		click(cell("r2", "title"));
		click(cell("r2", "title"));
		click(cell("r2", "points"));
		expect(spy).toHaveBeenCalledTimes(1);
		expect(spy).toHaveBeenLastCalledWith(["r2"]);
		click(cell("r3", "title"), { metaKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r2", "r3"]);
		expect(spy).toHaveBeenCalledTimes(2);
	});

	it("selects one row in single mode", () => {
		const spy = vi.fn();
		act(() => root.render(<Selecting mode="single" spy={spy} />));
		expect(host.querySelector("table")?.hasAttribute("aria-multiselectable")).toBe(false);
		expect(rowEl("r1").getAttribute("aria-selected")).toBe("false");
		click(cell("r2", "title"));
		expect(spy).toHaveBeenLastCalledWith(["r2"]);
		expect(rowEl("r2").getAttribute("aria-selected")).toBe("true");
		expect(rowEl("r2").getAttribute("data-state")).toBe("selected");
		click(cell("r3", "title"), { metaKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r3"]);
		press(cell("r1", "title"), " ");
		expect(spy).toHaveBeenLastCalledWith(["r1"]);
	});

	it("selects many with Cmd, Shift, Space, Shift+arrows and Cmd+A in multi mode", () => {
		const spy = vi.fn();
		act(() => root.render(<Selecting mode="multi" spy={spy} />));
		expect(host.querySelector("table")?.getAttribute("aria-multiselectable")).toBe("true");
		click(cell("r1", "title"));
		expect(spy).toHaveBeenLastCalledWith(["r1"]);
		click(cell("r3", "title"), { shiftKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r1", "r2", "r3"]);
		click(cell("r2", "title"), { metaKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r1", "r3"]);
		click(cell("r1", "title"));
		expect(spy).toHaveBeenLastCalledWith(["r1"]);
		press(cell("r1", "title"), "ArrowDown", { shiftKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r1", "r2"]);
		expect(document.activeElement).toBe(cell("r2", "title"));
		press(cell("r2", "title"), " ");
		expect(spy).toHaveBeenLastCalledWith(["r1"]);
		press(cell("r2", "title"), "a", { metaKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r1", "r2", "r3"]);
	});

	it("deletes the selection when the focused row is in it, else that row", () => {
		const onDelete = vi.fn();
		mount({ onDelete, selection: "multi", selected: ["r1", "r2"], onSelect: () => {} });
		press(cell("r2", "title"), "Delete");
		expect(onDelete).toHaveBeenLastCalledWith(["r1", "r2"]);
		press(cell("r3", "points"), "Backspace");
		expect(onDelete).toHaveBeenLastCalledWith(["r3"]);
	});

	it("does not delete while editing, nor without onDelete", () => {
		const onDelete = vi.fn();
		mount({ onEdit: () => {} });
		press(cell("r1", "title"), "Delete");
		act(() =>
			root.render(
				<DataTable
					aria-label="T"
					columns={COLUMNS}
					rows={ROWS}
					onEdit={() => {}}
					onDelete={onDelete}
				/>,
			),
		);
		press(cell("r1", "title"), "Enter");
		press(input(), "Delete");
		expect(onDelete).not.toHaveBeenCalled();
	});

	it("moves a row with Alt+arrows, not past the ends", () => {
		const onMove = vi.fn();
		mount({ onMove });
		press(cell("r2", "title"), "ArrowUp", { altKey: true });
		expect(onMove).toHaveBeenLastCalledWith("r2", 0);
		press(cell("r2", "title"), "ArrowDown", { altKey: true });
		expect(onMove).toHaveBeenLastCalledWith("r2", 2);
		press(cell("r1", "title"), "ArrowUp", { altKey: true });
		press(cell("r3", "title"), "ArrowDown", { altKey: true });
		expect(onMove).toHaveBeenCalledTimes(2);
		expect(rowEl("r1").draggable).toBe(true);
	});

	it("keeps the focus on a moved row once the host moves it", () => {
		function Host() {
			const [rows, setRows] = useState(ROWS);
			return (
				<DataTable
					aria-label="T"
					columns={COLUMNS}
					rows={rows}
					onMove={(key, index) =>
						setRows((prev) => {
							const rest = prev.filter((r) => r.key !== key);
							const row = prev.find((r) => r.key === key);
							if (row) rest.splice(index, 0, row);
							return rest;
						})
					}
				/>
			);
		}
		act(() => root.render(<Host />));
		act(() => cell("r1", "points").focus());
		press(cell("r1", "points"), "ArrowDown", { altKey: true });
		expect([...host.querySelectorAll("tbody tr")].map((r) => r.textContent?.slice(0, 4))).toEqual([
			"Beta",
			"Alph",
			"Gamm",
		]);
		expect(document.activeElement).toBe(cell("r1", "points"));
	});

	it("adds a row from the button at the end", () => {
		const onAdd = vi.fn();
		mount({ onAdd });
		const add = [...host.querySelectorAll("button")].find((b) => b.textContent === "Add row");
		if (add) click(add);
		expect(onAdd).toHaveBeenCalledWith(3);
	});

	it("builds the right-click menu from the features that are on", () => {
		const onAdd = vi.fn();
		const onDelete = vi.fn();
		mount({ onAdd, onDelete });
		act(() => {
			cell("r2", "title").dispatchEvent(
				new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 5, clientY: 5 }),
			);
		});
		const items = [...document.querySelectorAll('[role="menuitem"]')].map((m) => m.textContent);
		expect(items).toEqual(["Insert row above", "Insert row below", "Delete row"]);
		const below = [...document.querySelectorAll('[role="menuitem"]')][1];
		if (below) click(below);
		expect(onAdd).toHaveBeenCalledWith(2);
	});

	it("offers edit and move in the menu when they are on, and no menu with nothing on", () => {
		mount({ onEdit: () => {}, onMove: () => {} });
		act(() => {
			cell("r1", "title").dispatchEvent(
				new MouseEvent("contextmenu", { bubbles: true, cancelable: true }),
			);
		});
		const items = [...document.querySelectorAll('[role="menuitem"]')];
		expect(items.map((m) => m.textContent)).toEqual(["Edit cell", "Move up", "Move down"]);
		expect(items[1]?.hasAttribute("data-disabled")).toBe(true);
		act(() => root.unmount());
		root = createRoot(host);
		mount();
		const e = new MouseEvent("contextmenu", { bubbles: true, cancelable: true });
		act(() => {
			cell("r1", "title").dispatchEvent(e);
		});
		expect(document.querySelector('[role="menu"]')).toBeNull();
		// The browser keeps its own menu on a table that offers none.
		expect(e.defaultPrevented).toBe(false);
	});

	it("opens no menu on the empty state", () => {
		mount({ rows: [], onAdd: () => {}, onDelete: () => {} });
		const e = new MouseEvent("contextmenu", { bubbles: true, cancelable: true });
		const placeholder = host.querySelector('[data-slot="data-table-empty"]');
		act(() => {
			placeholder?.dispatchEvent(e);
		});
		expect(document.querySelector('[role="menu"]')).toBeNull();
	});

	it("counts the placeholder row in the grid's rows", () => {
		mount({ rows: [] });
		expect(host.querySelector("table")?.getAttribute("aria-rowcount")).toBe("2");
		const placeholder = host.querySelector('[data-slot="data-table-empty"]')?.closest("tr");
		expect(placeholder?.getAttribute("aria-rowindex")).toBe("2");
	});

	it("leaves the focus alone when rows that do not answer a refused delete arrive", () => {
		let setRows: (rows: DataTableRow[]) => void = () => {};
		function Host() {
			const [rows, set] = useState(ROWS);
			setRows = set;
			return <DataTable aria-label="T" columns={COLUMNS} rows={rows} onDelete={() => {}} />;
		}
		act(() => root.render(<Host />));
		act(() => cell("r2", "title").focus());
		press(cell("r2", "title"), "Delete");
		act(() => cell("r3", "title").focus());
		act(() => setRows([{ key: "r0", cells: ["Zero", 0, false, "todo"] }, ...ROWS]));
		expect(document.activeElement).toBe(cell("r3", "title"));
	});

	it("keeps a tab stop once the last row is deleted", () => {
		const one = [ROWS[0] as DataTableRow];
		function Host({ add }: { add: boolean }) {
			const [rows, set] = useState(one);
			return (
				<DataTable
					aria-label="T"
					columns={COLUMNS}
					rows={rows}
					onDelete={(keys) => set((prev) => prev.filter((r) => !keys.includes(r.key)))}
					onAdd={add ? () => {} : undefined}
				/>
			);
		}
		act(() => root.render(<Host add />));
		act(() => cell("r1", "title").focus());
		press(cell("r1", "title"), "Delete");
		expect(document.activeElement?.textContent).toBe("Add row");

		act(() => root.render(<Host key="b" add={false} />));
		act(() => cell("r1", "title").focus());
		press(cell("r1", "title"), "Delete");
		const placeholder = host.querySelector<HTMLElement>('[data-slot="data-table-empty"]');
		expect(placeholder?.tabIndex).toBe(0);
		expect(document.activeElement).toBe(placeholder);
	});

	it("sets the anchor on a Shift click when there was none", () => {
		const spy = vi.fn();
		act(() => root.render(<Selecting mode="multi" spy={spy} />));
		click(cell("r2", "title"), { shiftKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r2"]);
		click(cell("r3", "title"), { shiftKey: true });
		expect(spy).toHaveBeenLastCalledWith(["r2", "r3"]);
	});

	it("moves the Tab chain on out of an open select", () => {
		mount({ onEdit: () => {} });
		act(() => cell("r1", "state").focus());
		press(cell("r1", "state"), "Enter");
		const option = document.querySelector('[role="option"]');
		if (option) press(option, "Tab");
		expect(cell("r2", "title").contains(input())).toBe(true);
	});

	it("names each checkbox by its row, and lets other chords through", () => {
		mount();
		const box = cell("r3", "done").querySelector('[role="checkbox"]');
		expect(box?.getAttribute("aria-label")).toBe("done, Gamma");
		act(() => cell("r1", "title").focus());
		const e = new KeyboardEvent("keydown", {
			key: "ArrowRight",
			metaKey: true,
			bubbles: true,
			cancelable: true,
		});
		act(() => {
			cell("r1", "title").dispatchEvent(e);
		});
		expect(e.defaultPrevented).toBe(false);
		expect(document.activeElement).toBe(cell("r1", "title"));
	});
});
