// The editor, mounted.
//
// markdown.test.ts pins the format. This pins the other half: a real
// ProseMirror view over the schema renders markdown as a document, an edit
// comes back out as markdown through `onCommit`, and an inbound value is
// adopted only while the document is clean.
//
// Real key events are out of reach here (jsdom has no caret), so edits are
// applied as transactions, which is what a keystroke turns into one step
// later anyway.

import { language } from "@codemirror/language";
import { EditorView as CMView, runScopeHandlers } from "@codemirror/view";
import { GapCursor } from "prosemirror-gapcursor";
import { type Command, TextSelection } from "prosemirror-state";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { tableMenuText } from "../../components/ui/table-handles";
import { loadLanguage } from "../code/languages";
import { ProseEditor } from "./editor";
import { serializeMarkdown } from "./markdown";
import { leaveTable, tableCommands } from "./table";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Code fences are CodeMirror views, which measure text through ranges. jsdom
// lays nothing out, so a range has no boxes; empty ones are the honest answer.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

// A paste is driven through ProseMirror's own clipboard path, which builds a
// ClipboardEvent; jsdom has none, and a bare Event carries everything it reads.
(globalThis as { ClipboardEvent?: unknown }).ClipboardEvent ??= class extends Event {
	clipboardData = null;
};

let root: Root | null = null;
let host: HTMLDivElement | null = null;

function mount(ui: ReactElement): HTMLElement {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	act(() => root?.render(ui));
	return host;
}

function rerender(ui: ReactElement): void {
	act(() => root?.render(ui));
}

afterEach(async () => {
	// Async, so the node views' deferred unmounts land inside the act too.
	await act(async () => root?.unmount());
	host?.remove();
	root = null;
	host = null;
	vi.useRealTimers();
});

/** The contenteditable ProseMirror builds inside our host div. */
function editable(el: HTMLElement): HTMLElement {
	const node = el.querySelector(".nu-prose-editor");
	if (!node) throw new Error("no editor mounted");
	return node as HTMLElement;
}

/** Append text at the end of the document, the way typing there would. */
function type(view: EditorView, text: string): void {
	act(() => {
		const end = view.state.doc.content.size - 1;
		view.dispatch(
			view.state.tr.setSelection(TextSelection.near(view.state.doc.resolve(end))).insertText(text),
		);
	});
}

describe("ProseEditor", () => {
	it("renders markdown as a document, not as source", () => {
		const el = mount(<ProseEditor value={"# title\n\nbody **loud**\n"} onCommit={() => {}} />);
		const ed = editable(el);
		expect(ed.querySelector("h1")?.textContent).toBe("title");
		expect(ed.querySelector("strong")?.textContent).toBe("loud");
		// no markdown punctuation survived into the rendered text
		expect(ed.textContent).not.toContain("**");
		expect(ed.textContent).not.toContain("#");
	});

	it("hands the typed text back as markdown", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		mount(<ProseEditor value={"hello\n"} onCommit={onCommit} onView={(v) => (view = v)} />);

		type(view as unknown as EditorView, " world");

		// The autosave is a quiet moment, so nothing commits while you type.
		expect(onCommit).not.toHaveBeenCalled();
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(onCommit).toHaveBeenCalledWith("hello world\n");
	});

	it("keeps structure through a lap: a list edited comes back a list", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		mount(<ProseEditor value={"- a\n- b\n"} onCommit={onCommit} onView={(v) => (view = v)} />);

		type(view as unknown as EditorView, "!");

		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(onCommit).toHaveBeenCalledWith("- a\n- b!\n");
	});

	it("adopts an inbound value while the document is clean", () => {
		const el = mount(<ProseEditor value={"first\n"} onCommit={() => {}} />);
		rerender(<ProseEditor value={"## second\n"} onCommit={() => {}} />);
		expect(editable(el).querySelector("h2")?.textContent).toBe("second");
	});

	it("refuses an inbound value while there are uncommitted edits", () => {
		vi.useFakeTimers();
		let view: EditorView | null = null;
		const el = mount(
			<ProseEditor value={"mine\n"} onCommit={() => {}} onView={(v) => (view = v)} />,
		);
		type(view as unknown as EditorView, " typing");
		rerender(<ProseEditor value={"theirs\n"} onCommit={() => {}} />);
		expect(editable(el).textContent).toBe("mine typing");
	});

	it("shows the placeholder on an empty document and not otherwise", () => {
		const el = mount(<ProseEditor value="" placeholder="Write something" onCommit={() => {}} />);
		expect(editable(el).querySelector("[data-nu-placeholder]")).not.toBeNull();
		rerender(
			<ProseEditor value={"not empty\n"} placeholder="Write something" onCommit={() => {}} />,
		);
		expect(editable(el).querySelector("[data-nu-placeholder]")).toBeNull();
	});

	it("refuses edits when read only", () => {
		const el = mount(<ProseEditor value={"fixed\n"} readOnly onCommit={() => {}} />);
		expect(editable(el).getAttribute("contenteditable")).toBe("false");
	});
});

/** The CodeMirror view drawing the n-th code fence. */
function fence(el: HTMLElement, n = 0): CMView {
	const dom = el.querySelectorAll("[data-slot=code-fence] .cm-editor")[n];
	const cm = dom && CMView.findFromDOM(dom as HTMLElement);
	if (!cm) throw new Error("no fence mounted");
	return cm;
}

/** A key pressed inside a fence, through CodeMirror's own keymap dispatch. */
function press(cm: CMView, key: string, mods: KeyboardEventInit = {}): boolean {
	let handled = false;
	act(() => {
		handled = runScopeHandlers(cm, new KeyboardEvent("keydown", { key, ...mods }), "editor");
	});
	return handled;
}

const FENCED = "intro\n\n```python\nx = 1\n```\n";

describe("ProseEditor code fences", () => {
	it("draws a fence with the code engine, not as a <pre>", () => {
		const el = mount(<ProseEditor value={FENCED} readOnly onCommit={() => {}} />);
		const ed = editable(el);
		expect(ed.querySelector("pre")).toBeNull();
		expect(fence(el).state.doc.toString()).toBe("x = 1");
		expect(ed.querySelector("[data-slot=code-fence]")?.getAttribute("data-language")).toBe(
			"python",
		);
	});

	it("reads only while the document does: no editing, no picker, a copy button", () => {
		const el = mount(<ProseEditor value={FENCED} readOnly onCommit={() => {}} />);
		expect(el.querySelector(".cm-content")?.getAttribute("contenteditable")).not.toBe("true");
		expect(fence(el).state.readOnly).toBe(true);
		expect(el.querySelector("[aria-label='Code language']")).toBeNull();
		expect(el.querySelector("[aria-label='Copy code']")).not.toBeNull();
	});

	it("follows a read-only flip without a rebuild", () => {
		const el = mount(<ProseEditor value={FENCED} readOnly onCommit={() => {}} />);
		const cm = fence(el);
		rerender(<ProseEditor value={FENCED} onCommit={() => {}} />);
		expect(fence(el)).toBe(cm);
		expect(el.querySelector(".cm-content")?.getAttribute("contenteditable")).toBe("true");
		expect(el.querySelector("[aria-label='Code language']")).not.toBeNull();
		expect(el.querySelector("[aria-label='Copy code']")).toBeNull();
		rerender(<ProseEditor value={FENCED} readOnly onCommit={() => {}} />);
		expect(fence(el).state.readOnly).toBe(true);
	});

	it("hands an edit in the fence back as markdown on a quiet moment", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={FENCED} onCommit={onCommit} onView={(v) => (view = v)} />);
		const cm = fence(el);
		act(() => cm.dispatch({ changes: { from: cm.state.doc.length, insert: " + 1" } }));
		expect((view as unknown as EditorView).state.doc.child(1).textContent).toBe("x = 1 + 1");
		expect(onCommit).not.toHaveBeenCalled();
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(onCommit).toHaveBeenCalledWith("intro\n\n```python\nx = 1 + 1\n```\n");
	});

	it("commits when focus leaves the editor from inside a fence", () => {
		const onCommit = vi.fn();
		const el = mount(<ProseEditor value={FENCED} onCommit={onCommit} />);
		const cm = fence(el);
		act(() => cm.dispatch({ changes: { from: 0, insert: "y = 0\n" } }));
		act(() => {
			cm.contentDOM.dispatchEvent(
				new FocusEvent("focusout", { bubbles: true, relatedTarget: null }),
			);
		});
		expect(onCommit).toHaveBeenCalledWith("intro\n\n```python\ny = 0\nx = 1\n```\n");
	});

	it("adopts an inbound value into an open fence", () => {
		const el = mount(<ProseEditor value={FENCED} onCommit={() => {}} />);
		const cm = fence(el);
		rerender(<ProseEditor value={"intro\n\n```python\nx = 2\n```\n"} onCommit={() => {}} />);
		expect(fence(el).state.doc.toString()).toBe("x = 2");
		expect(fence(el)).toBe(cm);
	});

	it("loads the grammar the language attribute names, and swaps it when it changes", async () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={FENCED} onCommit={() => {}} onView={(v) => (view = v)} />);
		await act(async () => {
			await loadLanguage("python");
		});
		expect(fence(el).state.facet(language)?.name).toBe("python");

		const pm = view as unknown as EditorView;
		act(() => {
			const pos = 7; // after the intro paragraph
			const node = pm.state.doc.nodeAt(pos);
			pm.dispatch(pm.state.tr.setNodeMarkup(pos, undefined, { ...node?.attrs, language: "sql" }));
		});
		await act(async () => {
			await loadLanguage("sql");
		});
		const cm = fence(el);
		expect(cm.state.facet(language)?.name).toBe("sql");
		expect(el.querySelector("[data-slot=code-fence]")?.getAttribute("data-language")).toBe("sql");
		expect(el.querySelector("[aria-label='Code language']")?.textContent).toContain("sql");
	});

	it("routes undo inside a fence to the document's history", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={FENCED} onCommit={() => {}} onView={(v) => (view = v)} />);
		const cm = fence(el);
		act(() => cm.dispatch({ changes: { from: cm.state.doc.length, insert: "!" } }));
		expect(cm.state.doc.toString()).toBe("x = 1!");
		expect(press(cm, "z", { ctrlKey: true })).toBe(true);
		expect(cm.state.doc.toString()).toBe("x = 1");
		expect((view as unknown as EditorView).state.doc.child(1).textContent).toBe("x = 1");
	});

	it("leaves the fence into a new paragraph on mod-enter", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={FENCED} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		// The caret in the fence, as a click there would leave it.
		act(() => pm.dispatch(pm.state.tr.setSelection(TextSelection.create(pm.state.doc, 13))));
		expect(press(fence(el), "Enter", { ctrlKey: true })).toBe(true);
		expect(pm.state.doc.childCount).toBe(3);
		expect(pm.state.doc.child(2).type.name).toBe("paragraph");
		expect(pm.state.selection.$head.parent).toBe(pm.state.doc.child(2));
	});

	it("turns an empty fence back into a paragraph on backspace", async () => {
		let view: EditorView | null = null;
		const el = mount(
			<ProseEditor value={"intro\n\n```\n```\n"} onCommit={() => {}} onView={(v) => (view = v)} />,
		);
		const cm = fence(el);
		let handled = false;
		// Async: the fence's view is torn down, and its chrome unmounts a tick later.
		await act(async () => {
			handled = runScopeHandlers(cm, new KeyboardEvent("keydown", { key: "Backspace" }), "editor");
		});
		expect(handled).toBe(true);
		const pm = view as unknown as EditorView;
		expect(pm.state.doc.child(1).type.name).toBe("paragraph");
		expect(el.querySelector("[data-slot=code-fence]")).toBeNull();
	});
});

/** A key pressed in the document, through ProseMirror's own keymaps. */
function key(view: EditorView, k: string, mods: KeyboardEventInit = {}): boolean {
	let handled = false;
	act(() => {
		const e = new KeyboardEvent("keydown", { key: k, ...mods });
		handled = view.someProp("handleKeyDown", (f) => f(view, e)) ?? false;
	});
	return handled;
}

/** The caret at the end of the text of the n-th table cell (header cells first). */
function caretInCell(view: EditorView, n: number): void {
	let seen = 0;
	let at = -1;
	view.state.doc.descendants((node, pos) => {
		if (at >= 0) return false;
		if (node.type.spec.tableRole === "cell" || node.type.spec.tableRole === "header_cell") {
			if (seen++ === n) at = pos + node.nodeSize - 2;
			return false;
		}
		return true;
	});
	act(() => view.dispatch(view.state.tr.setSelection(TextSelection.create(view.state.doc, at))));
}

/** The text of the cell holding the caret. */
function caretCellText(view: EditorView): string {
	const $head = view.state.selection.$head;
	for (let d = $head.depth; d > 0; d--) {
		const role = $head.node(d).type.spec.tableRole;
		if (role === "cell" || role === "header_cell") return $head.node(d).textContent;
	}
	throw new Error("caret is not in a cell");
}

const TABLE = "| a | b |\n| --- | ---: |\n| 1 | 2 |\n";

/** Press a table handle, the way a pointer opens its menu. */
function openHandle(el: HTMLElement, which: "row" | "column"): void {
	const button = el.querySelector(`[data-table-handle=${which}] button`);
	if (!button) throw new Error(`no ${which} handle`);
	act(() => {
		button.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, button: 0 }));
	});
}

/** The open menu's items, radio items too, by their text. */
function menuTexts(): (string | null)[] {
	return [...document.querySelectorAll('[role="menu"] [role^="menuitem"]')].map(
		(m) => m.textContent,
	);
}

describe("ProseEditor tables", () => {
	it("draws a table: a header row of th, body rows of td, alignment on the cells", () => {
		const el = mount(<ProseEditor value={TABLE} readOnly onCommit={() => {}} />);
		const ed = editable(el);
		const ths = [...ed.querySelectorAll("th")].map((th) => th.textContent);
		const tds = [...ed.querySelectorAll("td")].map((td) => td.textContent);
		expect(ths).toEqual(["a", "b"]);
		expect(tds).toEqual(["1", "2"]);
		expect((ed.querySelectorAll("td")[1] as HTMLElement).style.textAlign).toBe("right");
		expect(ed.querySelector("[data-slot=prose-table] [data-table-scroll] table")).not.toBeNull();
	});

	it("has no handles when read only, and gains them on the flip", () => {
		const el = mount(<ProseEditor value={TABLE} readOnly onCommit={() => {}} />);
		expect(el.querySelector("[data-table-handle]")).toBeNull();
		expect(el.querySelector("[data-slot=prose-table]")?.hasAttribute("data-active")).toBe(false);
		rerender(<ProseEditor value={TABLE} onCommit={() => {}} />);
		// There for an editable table, out of sight until it is in use.
		const row = el.querySelector("[data-table-handle=row]");
		const column = el.querySelector("[data-table-handle=column]");
		expect(row?.querySelector("button")?.getAttribute("aria-label")).toBe(
			tableMenuText.rowHandle("1"),
		);
		expect(column?.querySelector("button")?.getAttribute("aria-label")).toBe(
			tableMenuText.columnHandle("a"),
		);
		expect(row?.className).toContain("invisible");
		expect(column?.className).toContain("invisible");
		rerender(<ProseEditor value={TABLE} readOnly onCommit={() => {}} />);
		expect(el.querySelector("[data-table-handle]")).toBeNull();
	});

	it("moves between cells on Tab and Shift-Tab", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0);
		expect(key(pm, "Tab")).toBe(true);
		expect(caretCellText(pm)).toBe("b");
		expect(key(pm, "Tab")).toBe(true);
		expect(caretCellText(pm)).toBe("1");
		expect(key(pm, "Tab", { shiftKey: true })).toBe(true);
		expect(caretCellText(pm)).toBe("b");
	});

	it("adds a row on Tab in the last cell and moves into it", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={onCommit} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 3);
		expect(key(pm, "Tab")).toBe(true);
		expect(pm.state.doc.firstChild?.childCount).toBe(3);
		act(() => pm.dispatch(pm.state.tr.insertText("x")));
		expect(caretCellText(pm)).toBe("x");
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		// The new row takes its column's alignment.
		expect(onCommit).toHaveBeenCalledWith("| a | b |\n| --- | ---: |\n| 1 | 2 |\n| x |  |\n");
	});

	it("goes down a cell on Enter, adding a row at the bottom", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 1);
		expect(key(pm, "Enter")).toBe(true);
		expect(caretCellText(pm)).toBe("2");
		expect(key(pm, "Enter")).toBe(true);
		expect(pm.state.doc.firstChild?.childCount).toBe(3);
		// Same column, new row.
		const $head = pm.state.selection.$head;
		expect($head.index($head.depth - 2)).toBe(1);
	});

	it("turns `| a | b |` then Enter into a table, the caret in the first body cell", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		mount(<ProseEditor value={"intro\n"} onCommit={onCommit} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		act(() => {
			const end = pm.state.doc.content.size;
			pm.dispatch(pm.state.tr.insert(end, pm.state.schema.nodes.paragraph.create()));
		});
		type(pm, "| a | **b** |");
		expect(key(pm, "Enter")).toBe(true);
		const table = pm.state.doc.child(1);
		expect(table.type.name).toBe("table");
		expect(table.childCount).toBe(2);
		expect(table.firstChild?.firstChild?.type.name).toBe("table_header");
		expect(caretCellText(pm)).toBe("");
		expect(pm.state.selection.$head.index(pm.state.selection.$head.depth - 2)).toBe(0);
		act(() => pm.dispatch(pm.state.tr.insertText("1")));
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		// The text `**b**` was typed literally, so it is written escaped.
		expect(onCommit).toHaveBeenCalledWith("intro\n\n| a | \\*\\*b** |\n| --- | --- |\n| 1 |  |\n");
	});

	it("turns ```python then Enter into an empty fence, the caret inside it", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		const el = mount(
			<ProseEditor value={"intro\n"} onCommit={onCommit} onView={(v) => (view = v)} />,
		);
		const pm = view as unknown as EditorView;
		act(() => {
			const end = pm.state.doc.content.size;
			pm.dispatch(pm.state.tr.insert(end, pm.state.schema.nodes.paragraph.create()));
		});
		type(pm, "```python");
		expect(key(pm, "Enter")).toBe(true);
		const block = pm.state.doc.child(1);
		expect(block.type.name).toBe("code_block");
		expect(block.attrs.language).toBe("python");
		expect(pm.state.selection.$head.parent.type.name).toBe("code_block");
		const cm = fence(el);
		act(() => cm.dispatch({ changes: { from: 0, insert: "x = 1" } }));
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(onCommit).toHaveBeenCalledWith("intro\n\n```python\nx = 1\n```\n");
	});

	it("opens a fence with no language on ``` then Enter, and leaves other lines alone", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={"intro\n"} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		type(pm, " ```");
		key(pm, "Enter");
		// Not the whole line: a paragraph ending in backticks is just text.
		expect(pm.state.doc.child(0).type.name).toBe("paragraph");
		act(() => {
			const end = pm.state.doc.content.size;
			pm.dispatch(pm.state.tr.insert(end, pm.state.schema.nodes.paragraph.create()));
		});
		type(pm, "```");
		key(pm, "Enter");
		const last = pm.state.doc.lastChild;
		expect(last?.type.name).toBe("code_block");
		expect(last?.attrs.language).toBe("");
	});

	it("leaves a pipe line alone where a table cannot go, or with nothing in it", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={"- x\n"} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		type(pm, " | a |");
		key(pm, "Enter");
		expect(pm.state.doc.firstChild?.type.name).toBe("bullet_list");
		expect(pm.state.doc.textContent).not.toContain("table");
		let none = false;
		pm.state.doc.descendants((n) => {
			if (n.type.name === "table") none = true;
		});
		expect(none).toBe(false);
	});

	it("adds and removes rows and columns through the menu's commands, and commits them", async () => {
		vi.useFakeTimers();
		const onCommit = vi.fn();
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={onCommit} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		const run = (c: Command) => act(() => void c(pm.state, pm.dispatch, pm));
		const md = () => serializeMarkdown(pm.state.doc);

		caretInCell(pm, 2); // `1`
		run(tableCommands.addRowAfter);
		expect(md()).toBe("| a | b |\n| --- | ---: |\n| 1 | 2 |\n|  |  |\n");
		run(tableCommands.addColumnAfter);
		expect(md()).toBe("| a |  | b |\n| --- | --- | ---: |\n| 1 |  | 2 |\n|  |  |  |\n");
		caretInCell(pm, 1); // the new column
		run(tableCommands.deleteColumn);
		caretInCell(pm, 0);
		run(tableCommands.addColumnBefore);
		expect(md()).toBe("|  | a | b |\n| --- | --- | ---: |\n|  | 1 | 2 |\n|  |  |  |\n");
		caretInCell(pm, 0); // the new column
		run(tableCommands.deleteColumn);
		caretInCell(pm, 4); // the empty row
		run(tableCommands.deleteRow);
		expect(md()).toBe(TABLE);

		// A row inserted above the header becomes the header.
		caretInCell(pm, 0);
		run(tableCommands.addRowBefore);
		const table = pm.state.doc.firstChild;
		expect(table?.child(0).firstChild?.type.name).toBe("table_header");
		expect(table?.child(1).firstChild?.type.name).toBe("table_cell");
		expect(md()).toBe("|  |  |\n| --- | ---: |\n| a | b |\n| 1 | 2 |\n");
		caretInCell(pm, 0); // the new header
		run(tableCommands.deleteRow);
		expect(pm.state.doc.firstChild?.child(0).firstChild?.type.name).toBe("table_header");

		caretInCell(pm, 0);
		run(tableCommands.alignColumn("center"));
		expect(md()).toBe("| a | b |\n| :---: | ---: |\n| 1 | 2 |\n");
		run(tableCommands.alignColumn("left"));
		expect(md()).toBe(TABLE);
		run(tableCommands.alignColumn("center"));

		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(onCommit).toHaveBeenLastCalledWith("| a | b |\n| :---: | ---: |\n| 1 | 2 |\n");

		// Async: the table's view is torn down, and its control unmounts a tick later.
		await act(async () => void tableCommands.deleteTable(pm.state, pm.dispatch));
		expect(pm.state.doc.firstChild?.type.name).toBe("paragraph");
	});

	it("takes the caret into the row or column an insert adds", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		const run = (c: Command) => act(() => void c(pm.state, pm.dispatch, pm));
		const at = () => {
			const $h = pm.state.selection.$head;
			return [$h.index($h.depth - 3), $h.index($h.depth - 2)];
		};
		caretInCell(pm, 3); // `2`: row 1, column 1
		run(tableCommands.addRowAfter);
		expect(at()).toEqual([2, 1]);
		run(tableCommands.addRowBefore);
		expect(at()).toEqual([2, 1]);
		run(tableCommands.addColumnAfter);
		expect(at()).toEqual([2, 2]);
		run(tableCommands.addColumnBefore);
		expect(at()).toEqual([2, 2]);
		expect(caretCellText(pm)).toBe("");
	});

	describe("pasting into a cell", () => {
		const paste = (how: (pm: EditorView) => void) => {
			let view: EditorView | null = null;
			mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
			const pm = view as unknown as EditorView;
			caretInCell(pm, 2); // `1`
			act(() => how(pm));
			return serializeMarkdown(pm.state.doc);
		};

		it("joins pasted lines into the cell, neighbours untouched", () => {
			expect(paste((pm) => pm.pasteText("l1\nl2\n\nl3"))).toBe(
				"| a | b |\n| --- | ---: |\n| 1l1 l2 l3 | 2 |\n",
			);
		});

		it("joins pasted paragraphs, keeping their marks", () => {
			expect(paste((pm) => pm.pasteHTML("<p>p1</p><p><strong>p2</strong></p>"))).toBe(
				"| a | b |\n| --- | ---: |\n| 1p1 **p2** | 2 |\n",
			);
		});

		it("joins a pasted list instead of splitting the table", () => {
			const md = paste((pm) => pm.pasteHTML("<ul><li>one</li><li>two</li></ul>"));
			expect(md).toBe("| a | b |\n| --- | ---: |\n| 1one two | 2 |\n");
		});

		it("still pastes cells as cells", () => {
			const md = paste((pm) => pm.pasteHTML("<table><tr><td>x</td><td>y</td></tr></table>"));
			expect(md).toBe("| a | b |\n| --- | ---: |\n| x | y |\n");
		});

		it("leaves a paste outside a table alone", () => {
			let view: EditorView | null = null;
			mount(<ProseEditor value={"intro\n"} onCommit={() => {}} onView={(v) => (view = v)} />);
			const pm = view as unknown as EditorView;
			act(() => {
				pm.dispatch(pm.state.tr.setSelection(TextSelection.create(pm.state.doc, 6)));
				pm.pasteHTML("<p>p1</p><p>p2</p>");
			});
			expect(pm.state.doc.childCount).toBe(2);
		});
	});

	it("deletes a selection on Enter in a cell, and stays", () => {
		let view: EditorView | null = null;
		mount(
			<ProseEditor
				value={"| abc |\n| --- |\n| x |\n"}
				onCommit={() => {}}
				onView={(v) => (view = v)}
			/>,
		);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0);
		const end = pm.state.selection.from;
		act(() =>
			pm.dispatch(pm.state.tr.setSelection(TextSelection.create(pm.state.doc, end - 2, end))),
		);
		expect(key(pm, "Enter")).toBe(true);
		expect(serializeMarkdown(pm.state.doc)).toBe("| a |\n| --- |\n| x |\n");
		expect(caretCellText(pm)).toBe("a");
	});

	it("leaves a table that ends the document on Mod-Enter, into a new paragraph", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0);
		expect(key(pm, "Enter", { ctrlKey: true }) || key(pm, "Enter", { metaKey: true })).toBe(true);
		expect(pm.state.doc.childCount).toBe(2);
		expect(pm.state.selection.$head.parent).toBe(pm.state.doc.child(1));
		act(() => pm.dispatch(pm.state.tr.insertText("after")));
		expect(serializeMarkdown(pm.state.doc)).toBe(`${TABLE}\nafter\n`);
	});

	it("arrows out of a table at the edge of the document into the gap there", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		// No view: jsdom cannot say whether the caret is on the cell's last line.
		const run = (c: Command) => {
			let done = false;
			act(() => {
				done = c(pm.state, pm.dispatch);
			});
			return done;
		};
		caretInCell(pm, 0);
		expect(run(leaveTable(1))).toBe(false); // a row below: the table's own business
		expect(run(leaveTable(-1))).toBe(true);
		expect(pm.state.selection).toBeInstanceOf(GapCursor);
		expect(pm.state.selection.from).toBe(0);
		caretInCell(pm, 3);
		expect(run(leaveTable(1))).toBe(true);
		expect(pm.state.selection).toBeInstanceOf(GapCursor);
		expect(pm.state.selection.from).toBe(pm.state.doc.content.size);
	});

	it("does not arrow into a gap when there is text past the table", () => {
		let view: EditorView | null = null;
		mount(
			<ProseEditor
				value={`intro\n\n${TABLE}\nafter\n`}
				onCommit={() => {}}
				onView={(v) => (view = v)}
			/>,
		);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0);
		expect(leaveTable(-1)(pm.state)).toBe(false);
		caretInCell(pm, 3);
		expect(leaveTable(1)(pm.state)).toBe(false);
	});

	it("keeps a pipe inside inline code in one header cell", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={""} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		const code = pm.state.schema.marks.code.create();
		act(() => {
			const s = pm.state.schema;
			pm.dispatch(
				pm.state.tr.insert(1, [s.text("| a | "), s.text("x|y", [code]), s.text(" | c |")]),
			);
		});
		expect(key(pm, "Enter")).toBe(true);
		expect(serializeMarkdown(pm.state.doc)).toBe(
			"| a | `x\\|y` | c |\n| --- | --- | --- |\n|  |  |  |\n",
		);
	});

	it("drops the handles, open menu or not, when the document turns read only", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		caretInCell(view as unknown as EditorView, 0);
		openHandle(el, "row");
		expect(document.querySelector('[role="menu"]')).not.toBeNull();
		rerender(<ProseEditor value={TABLE} readOnly onCommit={() => {}} />);
		expect(document.querySelector('[role="menu"]')).toBeNull();
		rerender(<ProseEditor value={TABLE} onCommit={() => {}} />);
		expect(el.querySelector("[data-table-handle=row]")?.className).toContain("invisible");
		expect(el.querySelector("[data-slot=prose-table]")?.hasAttribute("data-active")).toBe(false);
	});

	it("moves rows and columns, the caret along, the top row the header", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		const run = (c: Command) => act(() => void c(pm.state, pm.dispatch, pm));
		const md = () => serializeMarkdown(pm.state.doc);

		caretInCell(pm, 2); // `1`
		expect(tableCommands.moveRowDown(pm.state)).toBe(false);
		run(tableCommands.moveRowUp);
		expect(md()).toBe("| 1 | 2 |\n| --- | ---: |\n| a | b |\n");
		expect(caretCellText(pm)).toBe("1");
		const table = pm.state.doc.firstChild;
		expect(table?.child(0).firstChild?.type.name).toBe("table_header");
		expect(table?.child(1).firstChild?.type.name).toBe("table_cell");
		expect(tableCommands.moveRowUp(pm.state)).toBe(false);
		run(tableCommands.moveRowDown);
		expect(md()).toBe(TABLE);

		// A column takes its alignment along.
		caretInCell(pm, 0); // `a`
		expect(tableCommands.moveColumnLeft(pm.state)).toBe(false);
		run(tableCommands.moveColumnRight);
		expect(md()).toBe("| b | a |\n| ---: | --- |\n| 2 | 1 |\n");
		expect(caretCellText(pm)).toBe("a");
		run(tableCommands.moveColumnLeft);
		expect(md()).toBe(TABLE);
	});

	it("opens the row and column menus in the shared words, from a handle or a key", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		const t = tableMenuText;
		caretInCell(pm, 2);
		expect(key(pm, "F10", { shiftKey: true })).toBe(true);
		expect(menuTexts()).toEqual([
			t.insertRowAbove,
			t.insertRowBelow,
			t.moveRowUp,
			t.moveRowDown,
			t.deleteRow,
			t.deleteTable,
		]);
		expect(el.querySelector("[data-table-handle=row] button")?.getAttribute("aria-label")).toBe(
			t.rowHandle("2"),
		);
		// The bottom row moves no further down.
		const down = [...document.querySelectorAll('[role="menuitem"]')][3];
		expect(down?.hasAttribute("data-disabled")).toBe(true);
		act(() => {
			document.activeElement?.dispatchEvent(
				new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
			);
		});
		expect(document.querySelector('[role="menu"]')).toBeNull();

		expect(key(pm, "F10", { shiftKey: true, altKey: true })).toBe(true);
		expect(menuTexts()).toEqual([
			t.insertColumnLeft,
			t.insertColumnRight,
			t.moveColumnLeft,
			t.moveColumnRight,
			t.alignLeft,
			t.alignCenter,
			t.alignRight,
			t.deleteColumn,
			t.deleteTable,
		]);
		const right = [...document.querySelectorAll('[role="menuitem"]')][3];
		act(() => {
			right?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		});
		expect(serializeMarkdown(pm.state.doc)).toBe("| b | a |\n| ---: | --- |\n| 2 | 1 |\n");
	});

	it("closes a menu whose row goes away under it", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 2); // `1`, the last row
		openHandle(el, "row");
		expect(document.querySelector('[role="menu"]')).not.toBeNull();
		// As a replace from elsewhere would: the row is gone, the menu with it.
		act(() => void tableCommands.deleteRow(pm.state, pm.dispatch));
		expect(document.querySelector('[role="menu"]')).toBeNull();
	});

	it("puts the caret in the row a handle's menu is opened on", () => {
		let view: EditorView | null = null;
		const el = mount(<ProseEditor value={TABLE} onCommit={() => {}} onView={(v) => (view = v)} />);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0); // `a`
		const cell = el.querySelectorAll("td")[1] as HTMLElement; // `2`
		act(() => {
			cell.dispatchEvent(new PointerEvent("pointerover", { bubbles: true }));
		});
		openHandle(el, "row");
		expect(caretCellText(pm)).toBe("2");
		const up = [...document.querySelectorAll('[role="menuitem"]')][2];
		act(() => {
			up?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		});
		expect(serializeMarkdown(pm.state.doc)).toBe("| 1 | 2 |\n| --- | ---: |\n| a | b |\n");
	});

	it("will not delete the last column or the header-only table's last row", () => {
		let view: EditorView | null = null;
		mount(
			<ProseEditor value={"| a |\n| --- |\n"} onCommit={() => {}} onView={(v) => (view = v)} />,
		);
		const pm = view as unknown as EditorView;
		caretInCell(pm, 0);
		expect(tableCommands.deleteColumn(pm.state)).toBe(false);
		expect(tableCommands.deleteRow(pm.state)).toBe(false);
	});
});
