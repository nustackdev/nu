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
import { TextSelection } from "prosemirror-state";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadLanguage } from "../code/languages";
import { ProseEditor } from "./editor";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Code fences are CodeMirror views, which measure text through ranges. jsdom
// lays nothing out, so a range has no boxes; empty ones are the honest answer.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

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
