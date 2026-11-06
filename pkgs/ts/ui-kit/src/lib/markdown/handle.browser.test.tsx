// The markdown handle, under real keys.
//
// One test per row of the interaction table (task-162) whose test column is
// `kit-browser`, named by row number so the mapping can be checked. Each row
// is a caret somewhere, a key, and what the editor did with it: kept it (a
// list splits, a table moves a cell, the caret moves a line) or reported an
// intent to the host. The host here records every intent and answers true,
// so a reported key is consumed; where the row says the key is the kit's
// own, no intent may appear and the document shows the kit's result.
//
// Keys go through `userEvent`, which Playwright delivers to Firefox as
// input, so the browser decides what an arrow on a wrapped line means.
// ProseMirror reads the result from the DOM on its own schedule, hence
// `expect.poll` after every key.

import { EditorView as CMView } from "@codemirror/view";
import { userEvent } from "@vitest/browser/context";
import { GapCursor } from "prosemirror-gapcursor";
import { NodeSelection, TextSelection } from "prosemirror-state";
import { CellSelection } from "prosemirror-tables";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";
import { ProseEditor } from "./editor";
import type { Cut, MarkdownHandle, MarkdownIntent } from "./handle";
import { MOD_ENTER } from "./keys.testing";
import "../../index.css";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let host: HTMLDivElement | null = null;

afterEach(async () => {
	await act(async () => root?.unmount());
	host?.remove();
	root = null;
	host = null;
});

type Host = {
	el: HTMLElement;
	view: EditorView;
	doc: MarkdownHandle;
	intents: MarkdownIntent[];
	commits: string[];
	/** Every key the editor saw (modifiers left out) and whether it consumed it. */
	keys: { key: string; consumed: boolean }[];
	/** A new inbound value. */
	set(value: string): void;
};

/** Mount with a host that records every intent and answers true. */
function open(value: string, opts: { width?: number; hint?: string } = {}): Host {
	host = document.createElement("div");
	host.style.width = `${opts.width ?? 400}px`;
	host.style.font = "16px/1.5 Inter, sans-serif";
	document.body.appendChild(host);
	root = createRoot(host);
	let view: EditorView | null = null;
	let doc: MarkdownHandle | null = null;
	const intents: MarkdownIntent[] = [];
	const commits: string[] = [];
	const keys: { key: string; consumed: boolean }[] = [];
	const ui = (v: string): ReactElement => (
		<ProseEditor
			value={v}
			placeholder={opts.hint}
			onCommit={(s) => commits.push(s)}
			onView={(x) => {
				view = x;
			}}
			onHandle={(h) => {
				doc = h;
				h?.onIntent((i) => {
					intents.push(i);
					return true;
				});
			}}
		/>
	);
	act(() => root?.render(ui(value)));
	if (!view || !doc) throw new Error("no editor mounted");
	// After ProseMirror's own listener, so `defaultPrevented` says whether it consumed the key.
	(view as EditorView).dom.addEventListener("keydown", (e) => {
		if (!["Shift", "Control", "Meta", "Alt"].includes(e.key)) {
			keys.push({ key: e.key, consumed: e.defaultPrevented });
		}
	});
	return {
		el: host,
		view,
		doc,
		intents,
		commits,
		keys,
		set: (v) => act(() => root?.render(ui(v))),
	};
}

/** The caret at a document position, focused: what a click there leaves. */
function caret(h: Host, pos: number): void {
	act(() => {
		h.view.dispatch(h.view.state.tr.setSelection(TextSelection.create(h.view.state.doc, pos)));
		h.view.focus();
	});
}

/** A text selection from `from` to `to` (head at `to`), focused. */
function select(h: Host, from: number, to: number): void {
	act(() => {
		h.view.dispatch(h.view.state.tr.setSelection(TextSelection.create(h.view.state.doc, from, to)));
		h.view.focus();
	});
}

/** The fence's CodeMirror view. */
function fence(h: Host): CMView {
	const dom = h.el.querySelector("[data-slot=code-fence] .cm-editor");
	const cm = dom && CMView.findFromDOM(dom as HTMLElement);
	if (!cm) throw new Error("no fence mounted");
	return cm;
}

const press = (keys: string) => userEvent.keyboard(keys);
const UP = "{ArrowUp}";
const DOWN = "{ArrowDown}";
const LEFT = "{ArrowLeft}";
const RIGHT = "{ArrowRight}";
const SHIFT_UP = "{Shift>}{ArrowUp}{/Shift}";
const SHIFT_DOWN = "{Shift>}{ArrowDown}{/Shift}";

/**
 * The key was the browser's own: the editor saw it, consumed nothing and
 * reported nothing. What the browser then does with its caret is its own;
 * under CPU starvation headless Firefox sometimes skips a caret move for a
 * key it received (the key arrives, the selection stays), so that is not
 * what these rows assert.
 */
async function browsersOwn(h: Host, ...keys: string[]): Promise<void> {
	await expect.poll(() => h.keys.length).toBe(keys.length);
	expect(h.keys).toEqual(keys.map((key) => ({ key, consumed: false })));
	expect(h.intents).toEqual([]);
}

async function reported(h: Host, expected: Partial<MarkdownIntent>): Promise<MarkdownIntent> {
	await expect.poll(() => h.intents.length).toBe(1);
	const intent = h.intents[0];
	expect(intent).toMatchObject(expected);
	return intent;
}

/** A leave carries the caret's screen x. */
function expectX(intent: MarkdownIntent, near: number): void {
	if (intent.kind !== "leave") throw new Error("not a leave");
	expect(Math.abs(intent.x - near)).toBeLessThan(2);
}

const head = (h: Host) => h.view.state.selection.head;
const text = (h: Host) => h.view.state.doc.textContent;

const long = "the quick brown fox jumps over the lazy dog and keeps running far past the fence";
const TABLE = "| a | b |\n|---|---|\n| c | d |\n";

describe("A. input line", () => {
	it("row 22: type_applies_input_rules", async () => {
		const h = open("");
		act(() => {
			h.doc.focus("end");
			h.doc.type("# hello");
		});
		expect(h.view.state.doc.firstChild?.type.name).toBe("heading");
		expect(h.doc.markdown()).toBe("# hello\n");
		expect(h.intents).toEqual([]);
	});
});

describe("C. blank prose cell", () => {
	it("row 41: erase_back_on_blank", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
		expect(h.doc.blank()).toBe(true);
	});

	it("row 47: slash_reported_only_when_blank", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press("/");
		await reported(h, { kind: "slash" });
		// Taken by the host: the slash never landed.
		expect(h.doc.blank()).toBe(true);
		expect(text(h)).toBe("");
	});

	it("row 48: slash_not_reported_with_text", async () => {
		const h = open("text\n");
		act(() => h.doc.focus("end"));
		await press("/");
		await expect.poll(() => text(h)).toBe("text/");
		expect(h.intents).toEqual([]);
	});

	it("row 52: break_reported_outside_table_fence", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
		expect(h.doc.blank()).toBe(true);
	});

	it("row 58: enter_on_blank_is_kits", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(h.doc.blank()).toBe(false);
		expect(h.intents).toEqual([]);
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(1);
		expect(h.doc.blank()).toBe(true);
		expect(h.intents).toEqual([]);
	});

	it("row 59: placeholder_on_blank", async () => {
		const h = open("", { hint: "Write here" });
		const hinted = () =>
			h.el.querySelector("[data-nu-placeholder]")?.getAttribute("data-nu-placeholder");
		expect(hinted()).toBe("Write here");
		act(() => h.doc.focus("start"));
		await press("x");
		await expect.poll(() => text(h)).toBe("x");
		expect(hinted()).toBeUndefined();
	});

	it("row 60: backspace_empty_heading", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press("# ");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("heading");
		expect(h.doc.blank()).toBe(false);
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("paragraph");
		expect(h.doc.blank()).toBe(true);
		expect(h.intents).toEqual([]);
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
	});

	it("row 61: slash_empty_heading", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		await press("# ");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("heading");
		await press("/");
		await expect.poll(() => text(h)).toBe("/");
		expect(h.view.state.doc.firstChild?.type.name).toBe("heading");
		expect(h.intents).toEqual([]);
	});

	it("row 62: backspace_empty_item_lifts", async () => {
		// A variant's prefill: an empty to-do item.
		const h = open("- [ ] \n");
		expect(h.view.state.doc.firstChild?.type.name).toBe("task_list");
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("paragraph");
		expect(h.doc.blank()).toBe(true);
		expect(h.intents).toEqual([]);
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
	});
});

describe("D. arrows, plain and wrapped", () => {
	it("row 64 (and 38): leave_up_first_line", async () => {
		const h = open("hello\n");
		caret(h, 3);
		const x = h.view.coordsAtPos(3).left;
		await press(UP);
		expectX(await reported(h, { kind: "leave", dir: "up", extend: false }), x);
		expect(head(h)).toBe(3);
	});

	it("row 67: leave_down_last_line", async () => {
		const h = open("hello\n");
		caret(h, 3);
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down", extend: false });
	});

	it("row 75: no_leave_off_edge", async () => {
		const h = open("hello world\n");
		caret(h, 3);
		await press(LEFT);
		await press(RIGHT);
		await browsersOwn(h, "ArrowLeft", "ArrowRight");
	});

	it("row 76: wrapped_inner_up", async () => {
		const h = open(`${long}\n`, { width: 160 });
		caret(h, h.view.state.doc.content.size - 1);
		expect(h.view.endOfTextblock("up")).toBe(false);
		await press(UP);
		await browsersOwn(h, "ArrowUp");
	});

	it("row 77: wrapped_first_line_leaves", async () => {
		const h = open(`${long}\n`, { width: 160 });
		caret(h, 3);
		await press(UP);
		await reported(h, { kind: "leave", dir: "up" });
	});

	it("row 78: wrapped_last_line_leaves", async () => {
		const h = open(`${long}\n`, { width: 160 });
		const last = h.view.state.doc.content.size - 1;
		caret(h, last - 2);
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down" });
	});

	it("row 79: wrapped_inner_down", async () => {
		const h = open(`${long}\n`, { width: 160 });
		caret(h, 3);
		expect(h.view.endOfTextblock("down")).toBe(false);
		await press(DOWN);
		await browsersOwn(h, "ArrowDown");
	});

	it("row 80: inner_block_up", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 7);
		await press(UP);
		await browsersOwn(h, "ArrowUp");
	});

	it("row 81: inner_block_down", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 2);
		await press(DOWN);
		await browsersOwn(h, "ArrowDown");
	});

	it("row 82: leave_needs_collapsed_caret", async () => {
		const h = open("hello\n");
		select(h, 1, 4);
		await press(UP);
		await browsersOwn(h, "ArrowUp");
		caret(h, 3);
		await press(UP);
		await reported(h, { kind: "leave", dir: "up", extend: false });
	});

	it("row 83: leave_only_at_true_edge", async () => {
		const h = open("---\n\nhello\n");
		caret(h, 2);
		// Up selects the divider, up again reaches the gap before it: both the
		// kit's. Only from the gap, with nothing beyond, is it a leave.
		await press(UP);
		await expect.poll(() => h.view.state.selection instanceof NodeSelection).toBe(true);
		await press(UP);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(h.intents).toEqual([]);
		await press(UP);
		await reported(h, { kind: "leave", dir: "up" });
	});

	it("row 84: focus_x_wrapped", async () => {
		const h = open(`${long}\n`, { width: 160 });
		const last = h.view.state.doc.content.size - 1;
		const top = (pos: number) => h.view.coordsAtPos(pos).top;
		// Under the x of the 6th character, on the last line and on the first.
		const x = h.view.coordsAtPos(6).left;
		act(() => h.doc.focus({ x, edge: "last" }));
		expect(top(head(h))).toBe(top(last));
		expect(Math.abs(h.view.coordsAtPos(head(h)).left - x)).toBeLessThan(8);
		act(() => h.doc.focus({ x, edge: "first" }));
		expect(top(head(h))).toBe(top(1));
		expect(head(h)).toBe(6);
		expect(h.view.hasFocus()).toBe(true);
	});

	it("row 85: focus_x_table", async () => {
		const h = open(TABLE);
		const cell = (pos: number) => h.view.state.doc.resolve(pos).parent.textContent;
		// The x of the second column: where "b" is drawn.
		let bPos = 0;
		h.view.state.doc.descendants((n, pos) => {
			if (n.isText && n.text === "b") bPos = pos;
		});
		const x = h.view.coordsAtPos(bPos).left + 2;
		act(() => h.doc.focus({ x, edge: "first" }));
		expect(cell(head(h))).toBe("b");
		act(() => h.doc.focus({ x, edge: "last" }));
		expect(cell(head(h))).toBe("d");
	});

	it("row 86: focus_x_fence", async () => {
		const h = open("```\nabcdef\nghijkl\n```\n");
		const cm = fence(h);
		// Just inside the 4th column of the code, measured on its last line.
		const x = (cm.coordsAtPos(7 + 3)?.left ?? 0) + 1;
		act(() => h.doc.focus({ x, edge: "last" }));
		expect(h.view.state.selection.$head.parent.type.name).toBe("code_block");
		await expect.poll(() => cm.hasFocus).toBe(true);
		// Into the block, past the first line and its newline, three columns in.
		expect(cm.state.selection.main.head).toBe(7 + 3);
		act(() => h.doc.focus({ x, edge: "first" }));
		await expect.poll(() => cm.state.selection.main.head).toBe(3);
	});

	it("row 87: focus_x_past_end", async () => {
		const h = open("hi\n");
		act(() => h.doc.focus({ x: 100000, edge: "first" }));
		expect(head(h)).toBe(3);
		act(() => h.doc.focus({ x: -100000, edge: "last" }));
		expect(head(h)).toBe(1);
	});

	it("row 91: enter_never_reported", async () => {
		const h = open("hello\n");
		act(() => h.doc.focus("end"));
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(h.intents).toEqual([]);
	});
});

describe("E. Shift+arrows", () => {
	it("row 92: leave_extend_reports_head", async () => {
		const h = open("hello\n");
		caret(h, 3);
		await press(SHIFT_UP);
		await reported(h, { kind: "leave", dir: "up", extend: true });
	});

	it("row 98: wrapped_extend_inner", async () => {
		const h = open(`${long}\n`, { width: 160 });
		caret(h, h.view.state.doc.content.size - 1);
		expect(h.view.endOfTextblock("up")).toBe(false);
		await press(SHIFT_UP);
		await browsersOwn(h, "ArrowUp");
	});

	it("row 103: table_edge_shift_reports", async () => {
		const h = open(TABLE);
		// The second cell of the first row: the row is the edge, not the cell.
		let bPos = 0;
		h.view.state.doc.descendants((n, pos) => {
			if (n.isText && n.text === "b") bPos = pos;
		});
		caret(h, bPos);
		await press(SHIFT_UP);
		await reported(h, { kind: "leave", dir: "up", extend: true });
	});

	it("row 104: table_shift_inner", async () => {
		const h = open(TABLE);
		let cPos = 0;
		h.view.state.doc.descendants((n, pos) => {
			if (n.isText && n.text === "c") cPos = pos;
		});
		caret(h, cPos);
		await press(SHIFT_UP);
		await expect.poll(() => h.view.state.selection instanceof CellSelection).toBe(true);
		expect(h.intents).toEqual([]);
	});

	it("row 105: fence_edge_shift", async () => {
		const h = open("```\nabc\ndef\n```\n");
		act(() => h.doc.focus("start"));
		const cm = fence(h);
		await expect.poll(() => cm.hasFocus).toBe(true);
		await press(SHIFT_UP);
		await reported(h, { kind: "leave", dir: "up", extend: true });
		h.intents.length = 0;
		act(() => h.doc.focus("end"));
		await expect.poll(() => cm.state.selection.main.head).toBe(7);
		await press(SHIFT_DOWN);
		await reported(h, { kind: "leave", dir: "down", extend: true });
	});

	it("row 106: gap_edge_shift_reports", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press(UP);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(h.intents).toEqual([]);
		await press(SHIFT_UP);
		await reported(h, { kind: "leave", dir: "up", extend: true });
	});

	it("row 107: list_edge_shift_reports", async () => {
		const h = open("- a\n- b\n");
		act(() => h.doc.focus("start"));
		await press(SHIFT_UP);
		await reported(h, { kind: "leave", dir: "up", extend: true });
		h.intents.length = 0;
		const q = open("> quote\n");
		act(() => q.doc.focus("end"));
		await press(SHIFT_DOWN);
		await reported(q, { kind: "leave", dir: "down", extend: true });
	});
});

describe("F. lists", () => {
	it("row 108: list_enter_kits", async () => {
		const h = open("- a\n");
		act(() => h.doc.focus("end"));
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.firstChild?.childCount).toBe(2);
		expect(h.intents).toEqual([]);
	});

	it("row 109: list_enter_empty_lifts", async () => {
		const h = open("- a\n");
		act(() => h.doc.focus("end"));
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.firstChild?.childCount).toBe(2);
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(h.view.state.doc.lastChild?.type.name).toBe("paragraph");
		expect(h.view.state.doc.firstChild?.childCount).toBe(1);
		expect(h.intents).toEqual([]);
	});

	it("row 110: list_backspace_joins", async () => {
		const h = open("- a\n- b\n");
		caret(h, 8);
		expect(h.view.state.selection.$head.parent.textContent).toBe("b");
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.firstChild?.childCount).toBe(1);
		expect(text(h)).toBe("ab");
		expect(h.intents).toEqual([]);
	});

	it("row 111: list_backspace_first_lifts", async () => {
		const h = open("- a\n");
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("paragraph");
		expect(h.doc.markdown()).toBe("a\n");
		expect(h.intents).toEqual([]);
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
	});

	it("row 113: list_first_item_leaves", async () => {
		const h = open("- a\n- b\n");
		act(() => h.doc.focus("start"));
		await press(UP);
		await reported(h, { kind: "leave", dir: "up" });
	});

	it("row 114: list_last_item_leaves", async () => {
		const h = open("- a\n- b\n");
		act(() => h.doc.focus("end"));
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down" });
	});

	it("row 115: list_inner_arrows", async () => {
		const h = open("- a\n- b\n");
		act(() => h.doc.focus("end"));
		await press(UP);
		await browsersOwn(h, "ArrowUp");
		act(() => h.doc.focus("start"));
		await press(DOWN);
		await expect.poll(() => h.keys.length).toBe(2);
		expect(h.keys[1]).toEqual({ key: "ArrowDown", consumed: false });
		expect(h.intents).toEqual([]);
	});

	it("row 116: split_tail_in_list", async () => {
		const h = open("- ab\n- c\n");
		caret(h, 4);
		expect(h.view.state.doc.textBetween(1, 4)).toBe("a");
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "mid" });
		expect(h.doc.tail()).toBe("- b\n- c\n");
		let tail = "";
		act(() => {
			tail = h.doc.split();
		});
		expect(tail).toBe("- b\n- c\n");
		expect(h.doc.markdown()).toBe("- a\n");
	});

	it("row 116b: split_at_item_end_takes_no_empty_item", async () => {
		const h = open("- a\n- b\n- c\n");
		caret(h, 9);
		expect(h.view.state.doc.textBetween(8, 9)).toBe("b");
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "mid" });
		expect(h.doc.tail()).toBe("- c\n");
		let tail = "";
		act(() => {
			tail = h.doc.split();
		});
		expect(tail).toBe("- c\n");
		expect(h.doc.markdown()).toBe("- a\n- b\n");
	});

	it("row 116c: split_at_heading_end_takes_no_empty_heading", async () => {
		const h = open("# Title\n\nbody\n");
		caret(h, 6);
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "mid" });
		expect(h.doc.tail().trim()).toBe("body");
	});

	it("row 117: list_break_at_end", async () => {
		const h = open("- a\n- b\n");
		act(() => h.doc.focus("end"));
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
	});
});

describe("G. tables and the gap cursor", () => {
	it("row 121: table_mod_enter_not_reported", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press(MOD_ENTER);
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(h.view.state.doc.lastChild?.type.name).toBe("paragraph");
		expect(h.view.state.selection.$head.parent).toBe(h.view.state.doc.lastChild);
		expect(h.intents).toEqual([]);
	});

	it("row 123: gap_up_reports", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press(UP);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(h.intents).toEqual([]);
		await press(UP);
		await reported(h, { kind: "leave", dir: "up", extend: false });
	});

	it("row 125: table_left_to_gap", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press(LEFT);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(head(h)).toBe(0);
		expect(h.intents).toEqual([]);
	});

	it("row 126: gap_left_reports", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press(LEFT);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		await press(LEFT);
		await reported(h, { kind: "leave", dir: "left", extend: false });
	});

	it("row 128: gap_down_reports", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("end"));
		await press(DOWN);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(h.intents).toEqual([]);
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down", extend: false });
	});

	it("row 129: table_right_to_gap", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("end"));
		await press(RIGHT);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		expect(head(h)).toBe(h.view.state.doc.content.size);
		expect(h.intents).toEqual([]);
	});

	it("row 130: gap_right_reports", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("end"));
		await press(RIGHT);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		await press(RIGHT);
		await reported(h, { kind: "leave", dir: "right", extend: false });
	});

	it("row 133: gap_break_at_end", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("end"));
		await press(DOWN);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
	});

	it("row 135: gap_erase_back", async () => {
		const h = open(TABLE);
		const before = h.doc.markdown();
		act(() => h.doc.focus("start"));
		await press(UP);
		await expect.poll(() => h.view.state.selection instanceof GapCursor).toBe(true);
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
		expect(h.doc.markdown()).toBe(before);
	});

	it("row 136: table_cell_backspace_not_reported", async () => {
		const h = open(TABLE);
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await press("x");
		await expect.poll(() => text(h)).toContain("xa");
		expect(h.intents).toEqual([]);
	});
});

describe("H. code fences", () => {
	it("row 138: fence_mod_enter_not_reported", async () => {
		const h = open("```\nabc\n```\n");
		act(() => h.doc.focus("end"));
		await expect.poll(() => fence(h).hasFocus).toBe(true);
		await press(MOD_ENTER);
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(h.view.state.doc.lastChild?.type.name).toBe("paragraph");
		expect(h.intents).toEqual([]);
	});

	it("row 140: fence_backspace_start_silent", async () => {
		const h = open("```\nabc\n```\n");
		act(() => h.doc.focus("start"));
		await expect.poll(() => fence(h).hasFocus).toBe(true);
		await press("{Backspace}");
		await press("x");
		await expect.poll(() => fence(h).state.doc.toString()).toBe("xabc");
		expect(h.intents).toEqual([]);
	});

	it("row 142: fence_start_up_reports", async () => {
		const h = open("```\nabc\ndef\n```\n\nafter\n");
		act(() => h.doc.focus("start"));
		const cm = fence(h);
		await expect.poll(() => cm.hasFocus).toBe(true);
		act(() => cm.dispatch({ selection: { anchor: 2 } }));
		const x = cm.coordsAtPos(2)?.left ?? 0;
		await press(UP);
		expectX(await reported(h, { kind: "leave", dir: "up", extend: false }), x);
	});

	it("row 143: fence_start_left_reports", async () => {
		const h = open("```\nabc\n```\n\nafter\n");
		act(() => h.doc.focus("start"));
		await expect.poll(() => fence(h).hasFocus).toBe(true);
		await press(LEFT);
		await reported(h, { kind: "leave", dir: "left", extend: false });
	});

	it("row 144: fence_end_down_reports", async () => {
		const h = open("before\n\n```\nabc\ndef\n```\n");
		act(() => h.doc.focus("end"));
		const cm = fence(h);
		await expect.poll(() => cm.hasFocus).toBe(true);
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down", extend: false });
	});

	it("row 145: fence_end_right_reports", async () => {
		const h = open("before\n\n```\nabc\n```\n");
		act(() => h.doc.focus("end"));
		await expect.poll(() => fence(h).hasFocus).toBe(true);
		await press(RIGHT);
		await reported(h, { kind: "leave", dir: "right", extend: false });
	});
});

describe("I. blockquote", () => {
	it("row 148: quote_up_reports", async () => {
		const h = open("> q\n\nafter\n");
		act(() => h.doc.focus("start"));
		await press(UP);
		await reported(h, { kind: "leave", dir: "up" });
	});

	it("row 149: quote_down_reports", async () => {
		const h = open("before\n\n> q\n");
		act(() => h.doc.focus("end"));
		await press(DOWN);
		await reported(h, { kind: "leave", dir: "down" });
	});

	it("row 151: quote_backspace_lifts", async () => {
		const h = open("> q\n");
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.firstChild?.type.name).toBe("paragraph");
		expect(h.doc.markdown()).toBe("q\n");
		expect(h.intents).toEqual([]);
	});

	it("row 153: quote_break_at_end", async () => {
		const h = open("> q\n");
		act(() => h.doc.focus("end"));
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
	});
});

describe("J. merge", () => {
	it("row 154: erase_back_at_doc_start", async () => {
		const h = open("hello\n");
		act(() => h.doc.focus("start"));
		await press("{Backspace}");
		await reported(h, { kind: "erase", dir: "back" });
		expect(h.doc.markdown()).toBe("hello\n");
	});

	it("row 154: append_caret_at_join", async () => {
		const h = open("one\n");
		act(() => h.doc.append("two\n"));
		expect(h.doc.markdown()).toBe("one\n\ntwo\n");
		act(() => h.doc.focus("kept"));
		expect(h.view.hasFocus()).toBe(true);
		expect(head(h)).toBe(6);
		expect(h.view.state.selection.$head.parent.textContent).toBe("two");
		// The way back: Backspace there joins the paragraphs, the kit's own.
		await press("{Backspace}");
		await expect.poll(() => text(h)).toBe("onetwo");
		expect(h.view.state.doc.childCount).toBe(1);
		expect(h.intents).toEqual([]);
	});

	it("row 155: append_into_blank", async () => {
		const h = open("");
		act(() => h.doc.append("two\n"));
		expect(h.doc.markdown()).toBe("two\n");
		expect(h.view.state.doc.childCount).toBe(1);
		expect(head(h)).toBe(1);
	});

	it("row 160: backspace_inner_join_kits", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 6);
		await press("{Backspace}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(1);
		expect(text(h)).toBe("onetwo");
		expect(h.intents).toEqual([]);
	});

	it("row 161: backspace_selection_kits", async () => {
		const h = open("hello\n");
		select(h, 1, 4);
		await press("{Backspace}");
		await expect.poll(() => text(h)).toBe("lo");
		expect(h.intents).toEqual([]);
	});
});

describe("K. split", () => {
	it("row 164: split_keeps_head_returns_tail", async () => {
		const h = open("hello world\n");
		caret(h, 6);
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "mid" });
		const tail = h.doc.tail();
		expect(tail.trim()).toBe("world");
		let cut = "";
		act(() => {
			cut = h.doc.split();
		});
		expect(cut).toBe(tail);
		expect(h.doc.markdown()).toBe("hello\n");
	});

	// The held cut: what split's sugar does once the new cell holds the tail.
	// It shows at once, and this document saves nothing until the host says
	// how the move ended, so the store keeps the tail here meanwhile.
	it("row 164b: cut_shows_at_once_commits_nothing", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 6);
		let cut: Cut | null = null;
		act(() => {
			cut = h.doc.cut();
		});
		expect((cut as Cut | null)?.tail).toBe("two\n");
		expect(h.doc.markdown()).toBe("one\n");
		// Held: neither a commit, nor a blur, nor an edit sends anything.
		act(() => h.doc.commit());
		act(() => h.view.dom.blur());
		act(() => {
			h.doc.focus("end");
			h.doc.type("!");
		});
		act(() => h.doc.commit());
		expect(h.commits).toEqual([]);
		expect(h.doc.markdown()).toBe("one!\n");
	});

	it("row 164c: cut_keep_commits", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 6);
		let cut: Cut | null = null;
		act(() => {
			cut = h.doc.cut();
		});
		act(() => {
			h.doc.focus("end");
			h.doc.type("!");
		});
		expect(h.commits).toEqual([]);
		act(() => (cut as Cut | null)?.keep());
		// Out at once, with the edits since.
		expect(h.commits).toEqual(["one!\n"]);
		// Released: saves are the editor's own again, and a second end does nothing.
		act(() => (cut as Cut | null)?.undo());
		expect(h.doc.markdown()).toBe("one!\n");
		act(() => {
			h.doc.type("?");
			h.doc.commit();
		});
		expect(h.commits).toEqual(["one!\n", "one!?\n"]);
	});

	it("row 164d: cut_undo_restores_exactly", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 6);
		const before = h.view.state.doc;
		let cut: Cut | null = null;
		act(() => {
			cut = h.doc.cut();
		});
		expect(h.doc.markdown()).toBe("one\n");
		act(() => (cut as Cut | null)?.undo());
		expect(h.view.state.doc.eq(before)).toBe(true);
		expect(h.doc.markdown()).toBe("one\n\ntwo\n");
		// What the store has already: nothing goes out.
		expect(h.commits).toEqual([]);
		act(() => (cut as Cut | null)?.keep());
		expect(h.commits).toEqual([]);
	});

	it("row 164e: cut_undo_after_edit_appends_tail", async () => {
		const h = open("one\n\ntwo\n");
		caret(h, 6);
		let cut: Cut | null = null;
		act(() => {
			cut = h.doc.cut();
		});
		act(() => h.doc.focus("end"));
		await press("!");
		await expect.poll(() => text(h)).toBe("one!");
		act(() => (cut as Cut | null)?.undo());
		// Not where it was, but kept: on the end, at a paragraph break, saved at once.
		expect(h.doc.markdown()).toBe("one!\n\ntwo\n");
		expect(h.commits).toEqual(["one!\n\ntwo\n"]);
	});

	it("row 168: break_at_end_flag", async () => {
		const h = open("hello\n");
		act(() => h.doc.focus("end"));
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
	});

	it("row 169: break_trailing_empty_is_end", async () => {
		const h = open("hello\n");
		act(() => h.doc.focus("end"));
		await press("{Enter}{Enter}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(3);
		caret(h, 6);
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
	});

	it("row 170: break_with_selection", async () => {
		const h = open("hello world\n");
		select(h, 7, 12);
		await press(MOD_ENTER);
		await reported(h, { kind: "break", at: "end" });
		expect(text(h)).toBe("hello ");
		expect(h.view.state.selection.empty).toBe(true);
	});
});

describe("N. hints drawn through the editor", () => {
	const hinted = (h: Host) =>
		[...h.el.querySelectorAll("[data-nu-placeholder]")].map((n) =>
			n.getAttribute("data-nu-placeholder"),
		);

	it("draws a host hint on a blank document in place of the placeholder, and clears it", async () => {
		const h = open("", { hint: "Nu's placeholder" });
		expect(hinted(h)).toEqual(["Nu's placeholder"]);
		act(() => h.doc.hint("Write, or press / for cells"));
		expect(hinted(h)).toEqual(["Write, or press / for cells"]);
		act(() => h.doc.focus("start"));
		await press("x");
		await expect.poll(() => text(h)).toBe("x");
		expect(hinted(h)).toEqual([]);
		await press("{Backspace}");
		await expect.poll(() => h.doc.blank()).toBe(true);
		expect(hinted(h)).toEqual(["Write, or press / for cells"]);
		act(() => h.doc.hint(null));
		expect(hinted(h)).toEqual(["Nu's placeholder"]);
		expect(h.doc.markdown()).toBe("");
	});

	it("draws a tail hint on an empty last line only, and clears it", async () => {
		const h = open("hello\n");
		act(() => h.doc.hint("Cmd+Enter for a new cell", "tail"));
		expect(hinted(h)).toEqual([]);
		act(() => h.doc.focus("end"));
		await press("{Enter}");
		await expect.poll(() => h.view.state.doc.childCount).toBe(2);
		expect(hinted(h)).toEqual(["Cmd+Enter for a new cell"]);
		expect(h.el.querySelector("p:last-child")?.getAttribute("data-nu-placeholder")).toBe(
			"Cmd+Enter for a new cell",
		);
		await press("y");
		await expect.poll(() => text(h)).toBe("helloy");
		expect(hinted(h)).toEqual([]);
		await press("{Backspace}");
		await expect.poll(() => text(h)).toBe("hello");
		expect(hinted(h)).toEqual(["Cmd+Enter for a new cell"]);
		act(() => h.doc.hint(null, "tail"));
		expect(hinted(h)).toEqual([]);
	});

	it("leaves a blank document to the placeholder, never the tail hint", () => {
		const h = open("", { hint: "Nu's" });
		act(() => h.doc.hint("Cmd+Enter for a new cell", "tail"));
		expect(hinted(h)).toEqual(["Nu's"]);
	});
});

// Rows 188 and 189 (the echo guard) live in ../../nodes/input/markdown.test.tsx:
// the guard is MarkdownRef's, where the saves go out and the frames come in.
describe("M. live writes", () => {
	it("row 186: inbound_lands_when_clean", async () => {
		const h = open("");
		act(() => h.doc.focus("start"));
		h.set("written\n");
		expect(h.doc.markdown()).toBe("written\n");
		expect(h.doc.blank()).toBe(false);
		await press("{Backspace}");
		await expect.poll(() => text(h)).toBe("writte");
		expect(h.intents).toEqual([]);
	});

	it("row 187: inbound_held_while_dirty", async () => {
		const h = open("a\n");
		act(() => h.doc.focus("end"));
		await press("b");
		await expect.poll(() => text(h)).toBe("ab");
		h.set("theirs\n");
		expect(text(h)).toBe("ab");
	});

	it("row 191: type_after_prefill", async () => {
		const h = open("# \n");
		expect(h.view.state.doc.firstChild?.type.name).toBe("heading");
		act(() => {
			h.doc.focus("end");
			h.doc.type("hello");
		});
		expect(h.doc.markdown()).toBe("# hello\n");
		expect(h.view.hasFocus()).toBe(true);
	});
});
