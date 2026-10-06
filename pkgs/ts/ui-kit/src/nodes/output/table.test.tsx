// TableRef on the kit DataTable: the old wire (string columns, list rows, the
// sort and row notifies, the write / append / read handlers) unchanged, and
// the new one (dict columns and rows, row keys, select, edit, add, delete,
// move), each intent one notify naming its kind in `event`.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cellKey } from "../../components/ui/data-table-model";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

function mount(props: Record<string, unknown>) {
	tree.getState().write([["t", "TableRef", props]]);
	act(() => root.render(<NodeView path={["t"]} />));
}

function dispatch(op: string, payload: unknown, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: ["t"], payload, id }));
}

const props = () => tree.getState().getIn(["t"])?.props ?? {};
const notifies = () => sent.filter((f) => f.op === OPS.notify).map((f) => f.payload);

function cell(row: string, col: string): HTMLElement {
	const el = host.querySelector<HTMLElement>(`[data-key='${cellKey(row, col)}']`);
	if (!el) throw new Error(`no cell ${row}/${col}`);
	return el;
}

const texts = (sel: string) => [...host.querySelectorAll(sel)].map((e) => e.textContent);

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

function dblclick(el: Element) {
	act(() => {
		el.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
	});
}

function typeInto(value: string, key: string) {
	const el = host.querySelector<HTMLInputElement>("input");
	if (!el) throw new Error("no editor");
	act(() => {
		el.value = value;
	});
	press(el, key);
}

describe("TableRef, the old wire", () => {
	beforeEach(() =>
		mount({ columns: ["title", "year"], rows: [["Arrival", 2016]], clickable_rows: true }),
	);

	it("names a header click a sort", () => {
		act(() => host.querySelector<HTMLElement>("th")?.click());
		expect(notifies()).toEqual([{ event: "sort", sort_column: "title", sort_direction: "asc" }]);
	});

	it("names a row click a row, with the row's key", () => {
		act(() => host.querySelector<HTMLElement>("tbody td")?.click());
		expect(notifies()).toEqual([{ event: "row", row_index: 0, key: "0" }]);
	});

	it("draws string columns, list rows, stripes and a pointer on clickable rows", () => {
		expect(texts("th")).toEqual(["title", "year"]);
		expect(texts("tbody td")).toEqual(["Arrival", "2016"]);
		expect(host.querySelector("table")?.getAttribute("aria-label")).toBe("Table");
		expect(host.querySelector("[data-slot=data-table]")?.className).toContain("cursor-pointer");
		// Read-only: no edits, no menu, no add.
		expect(cell("0", "title").getAttribute("aria-readonly")).toBe("true");
		expect(host.textContent).not.toContain("Add row");
	});

	it("shows the server's sort and asks for the other direction", () => {
		dispatch(OPS.write, { sort_column: "year", sort_direction: "asc" });
		const year = host.querySelectorAll("th")[1];
		expect(year?.getAttribute("aria-sort")).toBe("ascending");
		act(() => year?.click());
		expect(notifies()).toEqual([{ event: "sort", sort_column: "year", sort_direction: "desc" }]);
	});

	it("caps write and append at max_rows, oldest first out", () => {
		dispatch(OPS.write, {
			max_rows: 2,
			rows: [
				["a", 1],
				["b", 2],
				["c", 3],
			],
		});
		expect(props().rows).toEqual([
			["b", 2],
			["c", 3],
		]);
		dispatch("append", ["d", 4]);
		expect(props().rows).toEqual([
			["c", 3],
			["d", 4],
		]);
		expect(texts("tbody td")).toEqual(["c", "3", "d", "4"]);
	});

	it("answers a read with columns and rows as sent", () => {
		dispatch(OPS.read, null, "r1");
		const read = sent.find((f) => f.op === OPS.read);
		expect(read?.payload).toEqual({ columns: ["title", "year"], rows: [["Arrival", 2016]] });
		expect(read?.id).toBe("r1");
	});
});

describe("TableRef, plain", () => {
	it("says no rows when there is nothing at all", () => {
		mount({});
		expect(host.textContent).toBe("no rows");
	});

	it("emits no row without clickable_rows", () => {
		mount({ columns: ["title"], rows: [["Arrival"]] });
		click(cell("0", "title"));
		expect(notifies()).toEqual([]);
	});

	it("names positional columns when none are sent", () => {
		mount({ rows: [["a", 1]] });
		expect(texts("th")).toEqual(["col_0", "col_1"]);
	});
});

const COLUMNS = [
	{ key: "id", label: "ID" },
	{ key: "title", label: "Title" },
	{ key: "year", label: "Year", kind: "number" },
	{ key: "seen", label: "Seen", kind: "bool" },
	{ key: "genre", label: "Genre", kind: "select", options: ["drama", "scifi"] },
	{ key: "note", editable: false },
];

const ROWS = [
	{ id: "m1", title: "Arrival", year: 2016, seen: true, genre: "scifi", note: "x" },
	{ id: "m2", title: "Perfect Days", year: 2023, seen: false, genre: "drama", note: "y" },
];

describe("TableRef, the new wire", () => {
	it("draws dict columns, dict rows and list rows, keyed by row_key", () => {
		mount({
			columns: ["id", { key: "title", label: "Title" }],
			rows: [{ id: "m1", title: "Arrival" }, ["m2", "Dune"]],
			row_key: "id",
			label: "Movies",
		});
		expect(texts("th")).toEqual(["id", "Title"]);
		expect(cell("m1", "title").textContent).toBe("Arrival");
		expect(cell("m2", "title").textContent).toBe("Dune");
		expect(host.querySelector("table")?.getAttribute("aria-label")).toBe("Movies");
	});

	it("falls back to the index and tells duplicate keys apart", () => {
		mount({
			columns: ["id", "title"],
			rows: [
				{ id: "", title: "no key" },
				{ id: "a", title: "first a" },
				{ id: "a", title: "second a" },
				{ title: "missing" },
			],
			row_key: "id",
			clickable_rows: true,
		});
		expect(cell("0", "title").textContent).toBe("no key");
		expect(cell("a", "title").textContent).toBe("first a");
		expect(cell("a~2", "title").textContent).toBe("second a");
		expect(cell("3", "title").textContent).toBe("missing");
		click(cell("a~2", "title"));
		expect(notifies()).toEqual([{ event: "row", row_index: 2, key: "a~2" }]);
	});

	it("keeps the selection in its props and notifies it", () => {
		mount({ columns: COLUMNS, rows: ROWS, row_key: "id", selection: "multi" });
		click(cell("m1", "title"));
		click(cell("m2", "title"), { metaKey: true });
		expect(notifies()).toEqual([
			{ event: "select", keys: ["m1"], row_indexes: [0] },
			{ event: "select", keys: ["m1", "m2"], row_indexes: [0, 1] },
		]);
		expect(props().selected).toEqual(["m1", "m2"]);
		expect(cell("m2", "title").closest("tr")?.getAttribute("aria-selected")).toBe("true");
	});

	it("shows a selection the server writes", () => {
		mount({ columns: COLUMNS, rows: ROWS, row_key: "id", selection: "single" });
		dispatch(OPS.write, { selected: ["m2"] });
		expect(cell("m2", "title").closest("tr")?.getAttribute("aria-selected")).toBe("true");
		expect(cell("m1", "title").closest("tr")?.getAttribute("aria-selected")).toBe("false");
	});

	it("drops keys of rows that are gone from the selection", () => {
		mount({ columns: COLUMNS, rows: ROWS, row_key: "id", selection: "multi" });
		dispatch(OPS.write, { selected: ["m2"] });
		// Another tab deleted m2: the server ships the rows without it.
		dispatch(OPS.write, { rows: [ROWS[0]] });
		expect(props().selected).toEqual([]);
		click(cell("m1", "title"), { metaKey: true });
		expect(notifies()).toEqual([{ event: "select", keys: ["m1"], row_indexes: [0] }]);
		expect(props().selected).toEqual(["m1"]);
	});

	it("names rows by position without row_key", () => {
		mount({
			columns: ["title"],
			rows: [["a"], ["b"], ["c"]],
			selection: "multi",
			deletable: true,
			draggable: true,
		});
		click(cell("1", "title"));
		click(cell("2", "title"), { shiftKey: true });
		press(cell("2", "title"), "Delete");
		press(cell("0", "title"), "ArrowDown", { altKey: true });
		expect(notifies()).toEqual([
			{ event: "select", keys: ["1"], row_indexes: [1] },
			{ event: "select", keys: ["1", "2"], row_indexes: [1, 2] },
			{ event: "delete", keys: ["1", "2"], row_indexes: [1, 2] },
			{ event: "move", key: "0", index: 1, row_index: 0 },
		]);
	});

	it("asks for edits typed by kind and never edits a row itself", () => {
		mount({ columns: COLUMNS, rows: ROWS, row_key: "id", editable: true });
		dblclick(cell("m1", "title"));
		typeInto("Arrival (2016)", "Enter");
		dblclick(cell("m2", "year"));
		typeInto("2024", "Enter");
		press(cell("m1", "seen"), " ");
		expect(notifies()).toEqual([
			{
				event: "edit",
				key: "m1",
				row_index: 0,
				column: "title",
				value: "Arrival (2016)",
				previous: "Arrival",
			},
			{ event: "edit", key: "m2", row_index: 1, column: "year", value: 2024, previous: 2023 },
			{ event: "edit", key: "m1", row_index: 0, column: "seen", value: false, previous: true },
		]);
		// The request changed nothing here: the server answers with rows.
		expect(cell("m1", "title").textContent).toBe("Arrival");
		expect(props().rows).toEqual(ROWS);
	});

	it("never edits the row_key column or one that says editable false", () => {
		mount({ columns: COLUMNS, rows: ROWS, row_key: "id", editable: true });
		expect(cell("m1", "id").getAttribute("aria-readonly")).toBe("true");
		expect(cell("m1", "note").getAttribute("aria-readonly")).toBe("true");
		expect(cell("m1", "title").hasAttribute("aria-readonly")).toBe(false);
		dblclick(cell("m1", "id"));
		expect(host.querySelector("input")).toBeNull();
	});

	it("asks to add, delete and move rows", () => {
		mount({
			columns: COLUMNS,
			rows: ROWS,
			row_key: "id",
			addable: true,
			deletable: true,
			draggable: true,
		});
		const add = [...host.querySelectorAll("button")].find((b) => b.textContent === "Add row");
		act(() => add?.click());
		press(cell("m1", "title"), "Delete");
		press(cell("m1", "title"), "ArrowDown", { altKey: true });
		expect(notifies()).toEqual([
			{ event: "add", index: 2 },
			{ event: "delete", keys: ["m1"], row_indexes: [0] },
			{ event: "move", key: "m1", index: 1, row_index: 0 },
		]);
		expect(props().rows).toEqual(ROWS);
	});

	it("answers a read with dict columns as sent", () => {
		mount({ columns: ["id", { key: "title", kind: "text" }], rows: [{ id: "a", title: "A" }] });
		dispatch(OPS.read, null, "r2");
		expect(sent.find((f) => f.op === OPS.read)?.payload).toEqual({
			columns: ["id", { key: "title", kind: "text" }],
			rows: [{ id: "a", title: "A" }],
		});
	});

	it("appends a dict row under the cap", () => {
		mount({ columns: ["id"], rows: [{ id: "a" }], max_rows: 1 });
		dispatch("append", { id: "b" });
		expect(props().rows).toEqual([{ id: "b" }]);
	});
});
