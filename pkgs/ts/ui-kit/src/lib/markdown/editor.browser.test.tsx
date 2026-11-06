// The editor, laid out.
//
// editor.test.tsx pins what a transaction does to the document; jsdom has no
// layout, so it cannot say where a line wraps or where the caret sits on
// screen. This runs in a real Firefox and pins the harness itself: a long
// paragraph in a narrow column wraps into several visual lines, ProseMirror's
// layout queries see them, and a real keypress moves the caret by what the
// browser drew, not by what the document says.
//
// Keys go through `userEvent`, which Playwright delivers as input to the
// browser, so the browser decides what line end means. ProseMirror picks the
// result up from the DOM on its own schedule, hence `expect.poll` rather than
// reading the state on the next line.

import { userEvent } from "@vitest/browser/context";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";
import { ProseEditor } from "./editor";
// The editor's own rules (pre-wrap, break-word) are what ProseMirror maps the
// DOM through; the fonts come along, so line breaks land the same every run.
import "../../index.css";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let host: HTMLDivElement | null = null;

/** Mount into a column narrow enough that a sentence has to wrap. */
function mount(ui: ReactElement): HTMLElement {
	host = document.createElement("div");
	host.style.width = "160px";
	host.style.font = "16px/1.5 Inter, sans-serif";
	document.body.appendChild(host);
	root = createRoot(host);
	act(() => root?.render(ui));
	return host;
}

afterEach(async () => {
	await act(async () => root?.unmount());
	host?.remove();
	root = null;
	host = null;
});

function editable(el: HTMLElement): HTMLElement {
	const node = el.querySelector(".nu-prose-editor");
	if (!node) throw new Error("no editor mounted");
	return node as HTMLElement;
}

const long = "the quick brown fox jumps over the lazy dog and keeps running far past the fence";

describe("ProseEditor in a real browser", () => {
	it("sees a wrapped paragraph as several visual lines", () => {
		let view: EditorView | null = null;
		mount(<ProseEditor value={`${long}\n`} onCommit={() => {}} onView={(v) => (view = v)} />);
		const v = view as unknown as EditorView;
		const first = 1;
		const last = v.state.doc.content.size - 1;

		// One textblock, drawn on more than one line.
		expect(v.state.doc.childCount).toBe(1);
		expect(v.coordsAtPos(last).top).toBeGreaterThan(v.coordsAtPos(first).top);
	});

	it("moves the caret by the drawn line under a real keypress", async () => {
		let view: EditorView | null = null;
		const el = mount(
			<ProseEditor value={`${long}\n`} onCommit={() => {}} onView={(v) => (view = v)} />,
		);
		const v = view as unknown as EditorView;
		const last = v.state.doc.content.size - 1;
		const lineTop = (pos: number) => v.coordsAtPos(pos).top;

		// A real click in the top left corner puts the caret at the start.
		await userEvent.click(editable(el), { position: { x: 1, y: 4 } });
		await expect.poll(() => v.state.selection.head).toBe(1);

		// First visual line: up leaves the block, down does not, because the
		// block goes on below. Only a laid-out view can tell those apart.
		expect(v.endOfTextblock("up")).toBe(true);
		expect(v.endOfTextblock("down")).toBe(false);

		// The end of the first visual line, not of the paragraph: a real click
		// at its right edge, which only a laid-out view can resolve. (A native
		// line-end key is the browser's own move, and headless Firefox under
		// load sometimes skips one; see ./handle.browser.test.tsx.)
		const box = editable(el).getBoundingClientRect();
		await userEvent.click(editable(el), { position: { x: box.width - 2, y: 4 } });
		await expect.poll(() => v.state.selection.head).toBeGreaterThan(1);
		const head = v.state.selection.head;
		expect(head).toBeLessThan(last);
		expect(lineTop(head - 1)).toBe(lineTop(1));

		// And typing there lands at the wrap, mid paragraph.
		await userEvent.keyboard("!");
		await expect.poll(() => v.state.doc.textContent.includes("!")).toBe(true);
		expect(v.state.doc.textContent.endsWith("!")).toBe(false);
		expect(v.state.doc.textContent.indexOf("!")).toBe(head - 1);
	});
});
