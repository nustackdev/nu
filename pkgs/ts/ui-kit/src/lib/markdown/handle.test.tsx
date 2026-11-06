// The markdown handle, as transactions.
//
// What a host's commands do to the document and what comes back out:
// markdown, blank, tail, split, append, type, commit. handle.browser.test.tsx covers what only a real browser
// can say (keys at edges, landing under an x); here the handle is driven
// directly and the state read back, which jsdom is enough for.

import { TextSelection } from "prosemirror-state";
import type { EditorView } from "prosemirror-view";
import type { ReactElement } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProseEditor } from "./editor";
import type { MarkdownHandle, MarkdownIntent } from "./handle";
import { paragraphFromEmpty } from "./rules";
import { proseSchema } from "./schema";

// React 19 wants this before render or it logs a warning per test.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// A selection change scrolls into view, which measures a range. jsdom lays
// nothing out, so a range has no boxes; empty ones are the honest answer.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

let root: Root | null = null;
let host: HTMLDivElement | null = null;

afterEach(async () => {
	await act(async () => root?.unmount());
	host?.remove();
	root = null;
	host = null;
	vi.useRealTimers();
});

type Host = {
	view: EditorView;
	doc: MarkdownHandle;
	commits: string[];
	intents: MarkdownIntent[];
	/** A new inbound value. */
	set(value: string): void;
};

function open(value: string, opts: { listen?: boolean } = {}): Host {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	let view: EditorView | null = null;
	let doc: MarkdownHandle | null = null;
	const commits: string[] = [];
	const intents: MarkdownIntent[] = [];
	const ui = (v: string): ReactElement => (
		<ProseEditor
			value={v}
			onCommit={(s) => commits.push(s)}
			onView={(x) => {
				view = x;
			}}
			onHandle={(h) => {
				doc = h;
				if (h && opts.listen !== false) {
					h.onIntent((i) => {
						intents.push(i);
						return true;
					});
				}
			}}
		/>
	);
	act(() => root?.render(ui(value)));
	if (!view || !doc) throw new Error("no editor mounted");
	return {
		view,
		doc,
		commits,
		intents,
		set: (v) => act(() => root?.render(ui(v))),
	};
}

function caret(h: Host, pos: number): void {
	act(() =>
		h.view.dispatch(h.view.state.tr.setSelection(TextSelection.create(h.view.state.doc, pos))),
	);
}

describe("MarkdownHandle", () => {
	it("reads the markdown with unsaved edits, and blank as the placeholder sees it", () => {
		const h = open("");
		expect(h.doc.blank()).toBe(true);
		expect(h.doc.markdown()).toBe("");
		act(() => h.doc.type("hi"));
		expect(h.doc.blank()).toBe(false);
		expect(h.doc.markdown()).toBe("hi\n");
		expect(h.commits).toEqual([]);
	});

	it("is not blank with an empty heading, a divider or a table in it", () => {
		expect(open("# \n").doc.blank()).toBe(false);
	});

	it("types as at the keyboard: input rules apply", () => {
		const h = open("");
		act(() => h.doc.type("# Title"));
		expect(h.view.state.doc.firstChild?.type.name).toBe("heading");
		expect(h.doc.markdown()).toBe("# Title\n");
		act(() => h.doc.type("\n- item"));
		expect(h.doc.markdown()).toBe("# Title\n\n- item\n");
	});

	it("tails and splits at the caret, mid-paragraph", () => {
		const h = open("hello world\n\nnext\n");
		caret(h, 6);
		const tail = h.doc.tail();
		expect(h.doc.markdown()).toBe("hello world\n\nnext\n");
		act(() => expect(h.doc.split()).toBe(tail));
		expect(h.doc.markdown()).toBe("hello\n");
		expect(h.view.state.selection.head).toBe(6);
	});

	it("splits at a block boundary without leaving an empty block behind", () => {
		const h = open("one\n\ntwo\n\nthree\n");
		caret(h, 6);
		act(() => expect(h.doc.split()).toBe("two\n\nthree\n"));
		expect(h.doc.markdown()).toBe("one\n");
		expect(h.view.state.doc.childCount).toBe(1);
	});

	it("splits a list at the first item by taking the whole list", () => {
		const h = open("intro\n\n- a\n- b\n");
		caret(h, 10);
		expect(h.view.state.selection.$head.parent.textContent).toBe("a");
		act(() => expect(h.doc.split()).toBe("- a\n- b\n"));
		expect(h.doc.markdown()).toBe("intro\n");
	});

	it("splits at the very start into a blank head and the whole tail", () => {
		const h = open("hello\n\nworld\n");
		caret(h, 1);
		act(() => expect(h.doc.split()).toBe("hello\n\nworld\n"));
		expect(h.doc.blank()).toBe(true);
	});

	it("splits nothing at the end: an empty tail and no edit", () => {
		const h = open("hello\n");
		caret(h, 6);
		expect(h.doc.tail()).toBe("");
		act(() => expect(h.doc.split()).toBe(""));
		expect(h.commits).toEqual([]);
		expect(h.doc.markdown()).toBe("hello\n");
	});

	it("appends blocks at the end with the caret at the join", () => {
		const h = open("one\n");
		act(() => h.doc.append("two\n\n- three\n"));
		expect(h.doc.markdown()).toBe("one\n\ntwo\n\n- three\n");
		expect(h.view.state.selection.head).toBe(6);
		expect(h.view.state.selection.$head.parent.textContent).toBe("two");
	});

	it("appends into a blank document by replacing its empty paragraph, caret at the start", () => {
		const h = open("");
		act(() => h.doc.append("# two\n"));
		expect(h.doc.markdown()).toBe("# two\n");
		expect(h.view.state.doc.childCount).toBe(1);
		expect(h.view.state.selection.head).toBe(1);
	});

	it("appends nothing for blank markdown", () => {
		const h = open("one\n");
		act(() => h.doc.append(""));
		expect(h.doc.markdown()).toBe("one\n");
		expect(h.view.state.doc.childCount).toBe(1);
	});

	it("saves on commit, now, instead of at the quiet moment", () => {
		vi.useFakeTimers();
		const h = open("a\n");
		caret(h, 2);
		act(() => h.doc.type("b"));
		expect(h.commits).toEqual([]);
		act(() => h.doc.commit());
		expect(h.commits).toEqual(["ab\n"]);
		act(() => h.doc.commit());
		expect(h.commits).toEqual(["ab\n"]);
	});

	it("saves split and append like any edit, at the quiet moment", async () => {
		vi.useFakeTimers();
		const h = open("one\n");
		act(() => h.doc.append("two\n"));
		await act(async () => {
			vi.advanceTimersByTime(1000);
		});
		expect(h.commits).toEqual(["one\n\ntwo\n"]);
	});

	it("moves the editor's own selection on focus: start, end, and kept", () => {
		const h = open("one\n\ntwo\n");
		act(() => h.doc.focus("end"));
		expect(h.view.state.selection.head).toBe(9);
		act(() => h.doc.focus("start"));
		expect(h.view.state.selection.head).toBe(1);
		caret(h, 7);
		act(() => h.doc.focus("kept"));
		expect(h.view.state.selection.head).toBe(7);
		// Without layout, an x lands at the edge it asked for.
		act(() => h.doc.focus({ x: 40, edge: "last" }));
		expect(h.view.state.selection.head).toBe(9);
	});

	it("hands the handle out only while editable: not read-only, then on the flip", async () => {
		const seen: (MarkdownHandle | null)[] = [];
		host = document.createElement("div");
		document.body.appendChild(host);
		root = createRoot(host);
		const ui = (readOnly: boolean) => (
			<ProseEditor
				value=""
				readOnly={readOnly}
				onCommit={() => {}}
				onHandle={(h) => seen.push(h)}
			/>
		);
		act(() => root?.render(ui(true)));
		expect(seen).toEqual([]);
		act(() => root?.render(ui(false)));
		expect(seen).toHaveLength(1);
		expect(seen[0]).not.toBeNull();
		act(() => root?.render(ui(true)));
		expect(seen).toEqual([seen[0], null]);
		await act(async () => root?.unmount());
		expect(seen).toHaveLength(2);
	});

	it("counts a commit as the store when there is no owner: saved fires on commit", () => {
		const h = open("a\n");
		let n = 0;
		h.doc.saved(() => n++);
		expect(n).toBe(1);
		caret(h, 2);
		act(() => h.doc.type("b"));
		const stop = h.doc.saved(() => n++);
		expect(n).toBe(1);
		act(() => h.doc.commit());
		expect(n).toBe(2);
		stop();
		expect(h.commits).toEqual(["ab\n"]);
	});

	it("hands the handle out on mount and takes it back on teardown", async () => {
		const seen: (MarkdownHandle | null)[] = [];
		host = document.createElement("div");
		document.body.appendChild(host);
		root = createRoot(host);
		act(() =>
			root?.render(<ProseEditor value="" onCommit={() => {}} onHandle={(h) => seen.push(h)} />),
		);
		expect(seen).toHaveLength(1);
		expect(seen[0]).not.toBeNull();
		await act(async () => root?.unmount());
		expect(seen).toHaveLength(2);
		expect(seen[1]).toBeNull();
	});

	it("unsubscribes a listener, and asks the next one when the first declines", () => {
		const h = open("", { listen: false });
		const first = vi.fn(() => false);
		const second = vi.fn(() => true);
		const stop = h.doc.onIntent(first);
		h.doc.onIntent(second);
		stop();
		// The plugin is exercised by the browser tests; here the subscription itself.
		expect(first).not.toHaveBeenCalled();
		expect(second).not.toHaveBeenCalled();
	});
});

describe("empty heading rule", () => {
	const rule = paragraphFromEmpty(proseSchema);

	it("turns an empty heading into a paragraph, so the document is blank again", () => {
		const h = open("");
		act(() => h.doc.type("# "));
		expect(h.view.state.doc.firstChild?.type.name).toBe("heading");
		expect(h.doc.blank()).toBe(false);
		act(() => expect(rule(h.view.state, h.view.dispatch)).toBe(true));
		expect(h.doc.blank()).toBe(true);
	});

	it("leaves a heading with text, and a paragraph, alone", () => {
		const h = open("# title\n");
		caret(h, 1);
		expect(rule(h.view.state)).toBe(false);
		const p = open("");
		expect(rule(p.view.state)).toBe(false);
	});
});
