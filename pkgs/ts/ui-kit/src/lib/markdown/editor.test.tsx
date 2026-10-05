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

import { TextSelection } from "prosemirror-state";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProseEditor } from "./editor";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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

afterEach(() => {
	act(() => root?.unmount());
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
