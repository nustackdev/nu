// TableRef on the kit DataTable: the old wire (string columns, list rows, the
// sort and row notifies, the write / append / read handlers) unchanged, and
// the new one (dict columns and rows, row keys, select, edit, add, delete,
// move), each intent one notify naming its kind in `event`, and the patch
// handler's row-level ops (set_row, insert_row, remove_rows, set_order).

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

describe("TableRef, row-level patches", () => {
	const DICTS = [
		{ id: "a", title: "A" },
		{ id: "b", title: "B" },
		{ id: "c", title: "C" },
	];
	const LISTS = [
		["a", "A"],
		["b", "B"],
		["c", "C"],
	];
	const patch = (p: unknown) => dispatch("patch", p);
	const ids = () =>
		(props().rows as unknown[]).map((r) => (Array.isArray(r) ? r[0] : (r as { id: string }).id));

	it("replaces a dict row in place by row_key, and draws it", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id" });
		patch({ op: "set_row", key: "b", row: { id: "b", title: "Bee" } });
		expect(props().rows).toEqual([DICTS[0], { id: "b", title: "Bee" }, DICTS[2]]);
		expect(cell("b", "title").textContent).toBe("Bee");
	});

	it("replaces a list row in place by the row_key column's position", () => {
		mount({ columns: ["title", "id"], rows: LISTS.map(([i, t]) => [t, i]), row_key: "id" });
		patch({ op: "set_row", key: "c", row: ["See", "c"] });
		expect(props().rows).toEqual([
			["A", "a"],
			["B", "b"],
			["See", "c"],
		]);
	});

	it("keys by position without row_key", () => {
		mount({ columns: ["id", "title"], rows: LISTS });
		patch({ op: "set_row", key: "0", row: ["z", "Z"] });
		patch({ op: "remove_rows", keys: ["2"] });
		expect(props().rows).toEqual([
			["z", "Z"],
			["b", "B"],
		]);
		patch({ op: "set_order", keys: ["1"] });
		expect(ids()).toEqual(["b", "z"]);
		patch({ op: "set_row", key: 1, row: ["y", "Y"] });
		expect(ids()).toEqual(["b", "y"]);
	});

	it("upserts: a key not shown appends, under the cap", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id", max_rows: 3 });
		patch({ op: "set_row", key: "d", row: { id: "d", title: "D" } });
		expect(ids()).toEqual(["b", "c", "d"]);
		expect(cell("d", "title").textContent).toBe("D");
	});

	it("touches the first row with a key", () => {
		mount({ columns: ["id", "title"], rows: [...DICTS, { id: "a", title: "A2" }], row_key: "id" });
		patch({ op: "set_row", key: "a", row: { id: "a", title: "first" } });
		patch({ op: "set_row", key: "a~2", row: { id: "a", title: "second" } });
		expect((props().rows as { title: string }[]).map((r) => r.title)).toEqual([
			"first",
			"B",
			"C",
			"second",
		]);
	});

	it("inserts at an index, clamped, list and dict rows alike", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id" });
		patch({ op: "insert_row", index: 1, row: { id: "x", title: "X" } });
		patch({ op: "insert_row", index: 99, row: ["y", "Y"] });
		patch({ op: "insert_row", index: -5, row: { id: "w", title: "W" } });
		expect(ids()).toEqual(["w", "a", "x", "b", "c", "y"]);
		expect(cell("y", "title").textContent).toBe("Y");
	});

	it("caps an insert at max_rows, oldest first out", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id", max_rows: 3 });
		patch({ op: "insert_row", index: 1, row: { id: "x", title: "X" } });
		expect(ids()).toEqual(["x", "b", "c"]);
	});

	it("removes rows by key, skipping keys not shown", () => {
		mount({ columns: ["id", "title"], rows: LISTS, row_key: "id" });
		patch({ op: "remove_rows", keys: ["a", "nope", "c"] });
		expect(props().rows).toEqual([["b", "B"]]);
	});

	it("orders named rows first, the rest after, unknown keys skipped", () => {
		mount({
			columns: ["id", "title"],
			rows: [...DICTS, { id: "d", title: "D" }],
			row_key: "id",
		});
		patch({ op: "set_order", keys: ["c", "nope", "a", "c"] });
		expect(ids()).toEqual(["c", "a", "b", "d"]);
		expect(texts("tbody tr td:nth-child(1)")).toEqual(["c", "a", "b", "d"]);
		patch({ op: "set_order", keys: ["d", "c", "b", "a"] });
		expect(ids()).toEqual(["d", "c", "b", "a"]);
	});

	it("keeps the selection on rows still shown and drops removed ones", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id", selection: "multi" });
		dispatch(OPS.write, { selected: ["a", "c"] });
		patch({ op: "set_order", keys: ["c"] });
		expect(props().selected).toEqual(["a", "c"]);
		patch({ op: "remove_rows", keys: ["a"] });
		expect(props().selected).toEqual(["c"]);
		expect(cell("c", "title").closest("tr")?.getAttribute("aria-selected")).toBe("true");
		expect(notifies()).toEqual([]);
	});

	it("ignores malformed and unknown patches", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id" });
		for (const p of [
			null,
			"set_row",
			["set_row"],
			{},
			{ op: "nope", keys: ["a"] },
			{ op: "set_row", key: "a" },
			{ op: "set_row", key: "a", row: "A" },
			{ op: "set_row", key: null, row: { id: "a" } },
			{ op: "set_row", key: { k: 1 }, row: { id: "a" } },
			{ op: "insert_row", row: { id: "x" } },
			{ op: "insert_row", index: "1", row: { id: "x" } },
			{ op: "insert_row", index: Number.NaN, row: { id: "x" } },
			{ op: "insert_row", index: 0, row: 7 },
			{ op: "remove_rows", keys: "a" },
			{ op: "remove_rows" },
			{ op: "set_order", keys: "c" },
		]) {
			patch(p);
		}
		expect(props().rows).toEqual(DICTS);
		expect(texts("tbody tr td:nth-child(2)")).toEqual(["A", "B", "C"]);
	});

	it("leaves write, append and read as they were", () => {
		mount({ columns: ["id", "title"], rows: DICTS, row_key: "id" });
		patch({ op: "set_order", keys: ["b"] });
		dispatch("append", { id: "d", title: "D" });
		dispatch(OPS.read, null, "r3");
		expect(sent.find((f) => f.op === OPS.read)?.payload).toEqual({
			columns: ["id", "title"],
			rows: [DICTS[1], DICTS[0], DICTS[2], { id: "d", title: "D" }],
		});
	});
});
