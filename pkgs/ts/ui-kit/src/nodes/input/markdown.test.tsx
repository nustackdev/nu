// MarkdownRef over the real tree store: what a save does on the wire, and
// what comes back.
//
// The frames are the real ones: a commit sets the value locally and sends a
// notify, Nu's read is a `read` frame answered through the node's handler,
// and a program's write (an echo of our own save, or somebody else's text)
// is a `write` frame. The rows are the interaction table's (task-162), M.
// live writes.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { DocumentHandle } from "../../lib/markdown/document";
import {
	documentPresent,
	documentUnder,
	NodeView,
	subscribeDocuments,
	subscribePresence,
	tree,
} from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// A selection change scrolls into view, which measures a range; jsdom lays
// nothing out, so a range has no boxes.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

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

afterEach(async () => {
	await act(async () => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

const PATH = ["n"];

function mount(value: string, editable = true): DocumentHandle {
	tree.getState().write([["n", "MarkdownRef", { value, editable }]]);
	act(() => root.render(<NodeView path={PATH} />));
	const doc = documentUnder(PATH);
	if (!doc) throw new Error("no document registered");
	return doc;
}

function dispatch(op: string, payload: unknown, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: PATH, payload, id }));
}

/** Type at the end and save now, the way a quiet moment would. */
function save(doc: DocumentHandle, text: string): void {
	act(() => {
		doc.focus("end");
		doc.type(text);
		doc.commit();
	});
}

const value = () => tree.getState().getIn(PATH)?.props.value;
const answered = (id: string) => sent.find((f) => f.op === OPS.read && f.id === id)?.payload;
const notifies = () => sent.filter((f) => f.op === OPS.notify).length;

describe("MarkdownRef saves", () => {
	it("sets the value locally and notifies, and answers the read with it", () => {
		const doc = mount("a\n");
		save(doc, "b");
		expect(value()).toBe("ab\n");
		expect(notifies()).toBe(1);
		dispatch(OPS.read, null, "r1");
		expect(answered("r1")).toBe("ab\n");
	});

	it("row 188: a stale echo of an earlier save leaves the value and the next read alone", () => {
		const doc = mount("a\n");
		save(doc, "b");
		dispatch(OPS.read, null, "r1");
		expect(answered("r1")).toBe("ab\n");
		save(doc, "c");
		// v1's echo lands after v2 is on the screen and before v2's read.
		dispatch(OPS.write, "ab\n");
		expect(value()).toBe("abc\n");
		expect(doc.markdown()).toBe("abc\n");
		dispatch(OPS.read, null, "r2");
		expect(answered("r2")).toBe("abc\n");
		// v2's own echo: nothing to do.
		dispatch(OPS.write, "abc\n");
		expect(value()).toBe("abc\n");
	});

	it("row 189: a write that is nobody's echo lands, after the echo and any time", () => {
		const doc = mount("a\n");
		save(doc, "b");
		dispatch(OPS.read, null, "r1");
		dispatch(OPS.write, "ab\n");
		dispatch(OPS.write, "theirs\n");
		expect(value()).toBe("theirs\n");
		expect(doc.markdown()).toBe("theirs\n");
	});

	it("answers the read for a save with that save, whatever landed meanwhile", () => {
		const doc = mount("a\n");
		save(doc, "b");
		// Another tab's text arrives between our notify and Nu's read for it.
		dispatch(OPS.write, "theirs\n");
		expect(value()).toBe("theirs\n");
		dispatch(OPS.read, null, "r1");
		expect(answered("r1")).toBe("ab\n");
		// Nu ordered theirs, then ours: ours comes back last and stays.
		dispatch(OPS.write, "ab\n");
		expect(value()).toBe("ab\n");
		expect(doc.markdown()).toBe("ab\n");
		// Once read back, a read answers the value as it stands.
		dispatch(OPS.write, "later\n");
		dispatch(OPS.read, null, "r2");
		expect(answered("r2")).toBe("later\n");
	});

	it("never holds a program's write back: a program that never writes the text back still writes", () => {
		const doc = mount("a\n");
		save(doc, "b");
		save(doc, "c");
		dispatch(OPS.write, "program\n");
		expect(value()).toBe("program\n");
		expect(doc.markdown()).toBe("program\n");
	});

	it("applies the rest of a map write while keeping the value from a stale echo", () => {
		const doc = mount("a\n");
		save(doc, "b");
		save(doc, "c");
		dispatch(OPS.write, { value: "ab\n", placeholder: "Write" });
		expect(value()).toBe("abc\n");
		expect(tree.getState().getIn(PATH)?.props.placeholder).toBe("Write");
		expect(doc.markdown()).toBe("abc\n");
	});

	it("lands nil as an empty source, as before", () => {
		mount("a\n");
		dispatch(OPS.write, null);
		expect(value()).toBe("");
	});

	it("forgets its saves with the node, so a rebuilt node takes any text", async () => {
		const doc = mount("a\n");
		save(doc, "b");
		save(doc, "c");
		await act(async () => root.unmount());
		tree.getState().remove(PATH);
		root = createRoot(host);
		mount("fresh\n");
		dispatch(OPS.write, "ab\n");
		expect(value()).toBe("ab\n");
	});
});

describe("MarkdownRef registration", () => {
	it("registers only while editable: a read-only document is not there to be asked", () => {
		tree.getState().write([["n", "MarkdownRef", { value: "a\n", editable: false }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(documentUnder(PATH)).toBeNull();
		dispatch(OPS.write, { editable: true });
		expect(documentUnder(PATH)).not.toBeNull();
		dispatch(OPS.write, { editable: false });
		expect(documentUnder(PATH)).toBeNull();
	});

	it("is present from the first frame, and takes commands from the second: nuverse's order", async () => {
		const presence: boolean[] = [];
		const stop = subscribePresence(PATH, (_path, p) => presence.push(p));
		// `body.set(...)`, then `body.set_editable(True)`: two frames, two renders.
		tree.getState().write([["n", "MarkdownRef", { value: "" }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(documentPresent(PATH)).toBe(true);
		expect(presence).toEqual([true]);
		expect(documentUnder(PATH)).toBeNull();
		dispatch(OPS.write, { editable: true });
		expect(documentUnder(PATH)).not.toBeNull();
		expect(documentPresent(PATH)).toBe(true);
		await act(async () => root.unmount());
		expect(documentPresent(PATH)).toBe(false);
		expect(presence).toEqual([true, false]);
		root = createRoot(host);
		stop();
	});

	it("announces the document to a waiting host only once editing is turned on, and it takes commands then", () => {
		const seen: (DocumentHandle | null)[] = [];
		const stop = subscribeDocuments(PATH, (_path, h) => seen.push(h));
		// The program's steps, in order: set the text, then open it for editing.
		tree.getState().write([["n", "MarkdownRef", { value: "" }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(seen).toEqual([]);
		dispatch(OPS.write, { editable: true });
		expect(seen).toHaveLength(1);
		const doc = seen[0];
		if (!doc) throw new Error("no document");
		act(() => {
			doc.focus("end");
			doc.type("typed");
		});
		expect(doc.markdown()).toBe("typed\n");
		stop();
	});
});

describe("MarkdownRef saved", () => {
	it("fires at once when nothing is unsaved or unread", () => {
		const doc = mount("a\n");
		let n = 0;
		doc.saved(() => n++);
		expect(n).toBe(1);
	});

	it("waits for the read that answers the latest save, then fires once", () => {
		const doc = mount("a\n");
		save(doc, "b");
		let n = 0;
		doc.saved(() => n++);
		expect(n).toBe(0);
		dispatch(OPS.read, null, "r1");
		expect(answered("r1")).toBe("ab\n");
		expect(n).toBe(1);
		dispatch(OPS.read, null, "r2");
		expect(n).toBe(1);
	});

	it("saves unsaved edits first: fires after the commit and its read", () => {
		const doc = mount("a\n");
		act(() => {
			doc.focus("end");
			doc.type("b");
		});
		let n = 0;
		doc.saved(() => n++);
		expect(n).toBe(0);
		act(() => doc.commit());
		expect(n).toBe(0);
		expect(value()).toBe("ab\n");
		dispatch(OPS.read, null, "r1");
		expect(n).toBe(1);
	});

	it("waits for the latest save when saves follow each other", () => {
		const doc = mount("a\n");
		save(doc, "b");
		let n = 0;
		doc.saved(() => n++);
		save(doc, "c");
		dispatch(OPS.read, null, "r1");
		expect(answered("r1")).toBe("abc\n");
		expect(n).toBe(1);
	});

	it("can be unsubscribed before the read", () => {
		const doc = mount("a\n");
		save(doc, "b");
		let n = 0;
		const stop = doc.saved(() => n++);
		stop();
		dispatch(OPS.read, null, "r1");
		expect(n).toBe(0);
	});
});
