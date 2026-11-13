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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MarkdownHandle } from "../../lib/markdown/handle";
import { NodeView, tree } from "../../tree";
import "..";
import { type MarkdownEntry, markdownAt, registerMarkdown, subscribeMarkdown } from "./markdown";

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

function mount(value: string, editable = true): MarkdownHandle {
	tree.getState().write([["n", "MarkdownRef", { value, readonly: !editable }]]);
	act(() => root.render(<NodeView path={PATH} />));
	const doc = markdownAt(PATH)?.handle;
	if (!doc) throw new Error("no editable markdown editor registered");
	return doc;
}

function dispatch(op: string, payload: unknown, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: PATH, payload, id }));
}

/** Type at the end and save now, the way a quiet moment would. */
function save(doc: MarkdownHandle, text: string): void {
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
	it("hands its handle only while editable: a read-only editor is there, and takes no commands", () => {
		tree.getState().write([["n", "MarkdownRef", { value: "a\n", readonly: true }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(markdownAt(PATH)).toEqual({ handle: null });
		dispatch(OPS.write, { readonly: false });
		expect(markdownAt(PATH)?.handle).not.toBeNull();
		dispatch(OPS.write, { readonly: true });
		expect(markdownAt(PATH)).toEqual({ handle: null });
	});

	it("is there from the first frame, and takes commands from the second: nuverse's order", async () => {
		const seen: ("read-only" | "editable" | "left")[] = [];
		const stop = subscribeMarkdown(PATH, (_path, e) =>
			seen.push(e === null ? "left" : e.handle ? "editable" : "read-only"),
		);
		// `body.set(...)`, then `body.set_readonly(False)`: two frames, two renders.
		tree.getState().write([["n", "MarkdownRef", { value: "" }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(markdownAt(PATH)).toEqual({ handle: null });
		expect(seen).toEqual(["read-only"]);
		dispatch(OPS.write, { readonly: false });
		expect(markdownAt(PATH)?.handle).not.toBeNull();
		await act(async () => root.unmount());
		expect(markdownAt(PATH)).toBeNull();
		expect(seen).toEqual(["read-only", "editable", "read-only", "left"]);
		root = createRoot(host);
		stop();
	});

	it("announces the handle to a waiting host only once editing is turned on, and it takes commands then", () => {
		const seen: MarkdownHandle[] = [];
		const stop = subscribeMarkdown(PATH, (_path, e) => {
			if (e?.handle) seen.push(e.handle);
		});
		// The program's steps, in order: set the text, then open it for editing.
		tree.getState().write([["n", "MarkdownRef", { value: "" }]]);
		act(() => root.render(<NodeView path={PATH} />));
		expect(seen).toEqual([]);
		dispatch(OPS.write, { readonly: false });
		expect(seen).toHaveLength(1);
		const doc = seen[0];
		if (!doc) throw new Error("no handle");
		act(() => {
			doc.focus("end");
			doc.type("typed");
		});
		expect(doc.markdown()).toBe("typed\n");
		stop();
	});
});

/** A handle that is only an identity; the table never calls into it. */
function fakeHandle(name: string): MarkdownHandle {
	return { name } as unknown as MarkdownHandle;
}

describe("markdown editors by path", () => {
	it("finds the editor at a path, or under it, and nothing elsewhere", () => {
		const a = fakeHandle("a");
		const reg = registerMarkdown(["cells", "1", "ui", "text"]);
		reg.editable(a);
		expect(markdownAt(["cells", "1", "ui", "text"])).toEqual({ handle: a });
		expect(markdownAt(["cells", "1", "ui"])).toEqual({ handle: a });
		expect(markdownAt(["cells", "1"])).toEqual({ handle: a });
		expect(markdownAt(["cells", "2"])).toBeNull();
		expect(markdownAt(["cells", "1", "ui", "text", "deeper"])).toBeNull();
		reg.leave();
		expect(markdownAt(["cells", "1"])).toBeNull();
	});

	it("does not confuse a path with one that only starts the same way", () => {
		const reg = registerMarkdown(["cells", "10"]);
		expect(markdownAt(["cells", "1"])).toBeNull();
		reg.leave();
	});

	it("tells a read-only editor from an editable one and from none", () => {
		const reg = registerMarkdown(["cells", "1", "ui", "text"]);
		expect(markdownAt(["cells", "1"])).toEqual({ handle: null });
		expect(markdownAt(["cells", "2"])).toBeNull();
		const a = fakeHandle("a");
		reg.editable(a);
		expect(markdownAt(["cells", "1"])).toEqual({ handle: a });
		reg.editable(null);
		expect(markdownAt(["cells", "1"])).toEqual({ handle: null });
		reg.leave();
		expect(markdownAt(["cells", "1"])).toBeNull();
	});

	it("prefers an editor that takes commands over a read-only one under the same path", () => {
		const ro = registerMarkdown(["c", "a"]);
		const rw = registerMarkdown(["c", "b"]);
		const b = fakeHandle("b");
		rw.editable(b);
		expect(markdownAt(["c"])).toEqual({ handle: b });
		rw.leave();
		ro.leave();
	});

	it("tells a subscriber under a path when an editor appears, changes and leaves, and nobody else", () => {
		const here = vi.fn();
		const elsewhere = vi.fn();
		const everywhere = vi.fn();
		const stop = [
			subscribeMarkdown(["cells", "1"], here),
			subscribeMarkdown(["cells", "2"], elsewhere),
			subscribeMarkdown(null, everywhere),
		];
		const a = fakeHandle("a");
		const reg = registerMarkdown(["cells", "1", "ui"]);
		expect(here).toHaveBeenLastCalledWith(["cells", "1", "ui"], { handle: null });
		reg.editable(a);
		expect(here).toHaveBeenLastCalledWith(["cells", "1", "ui"], { handle: a });
		expect(everywhere).toHaveBeenLastCalledWith(["cells", "1", "ui"], { handle: a });
		expect(elsewhere).not.toHaveBeenCalled();
		reg.leave();
		expect(here).toHaveBeenLastCalledWith(["cells", "1", "ui"], null);
		expect(everywhere).toHaveBeenLastCalledWith(["cells", "1", "ui"], null);
		expect(here).toHaveBeenCalledTimes(3);
		for (const s of stop) s();
		registerMarkdown(["cells", "1", "ui"]).leave();
		expect(here).toHaveBeenCalledTimes(3);
	});

	it("announces synchronously, inside the call, so a parked request is consumed with no timing", () => {
		const seen: (MarkdownEntry | null)[] = [];
		const stop = subscribeMarkdown(["c"], (_path, e) => seen.push(e));
		const a = fakeHandle("a");
		const reg = registerMarkdown(["c", "doc"]);
		expect(seen).toEqual([{ handle: null }]);
		reg.editable(a);
		expect(seen).toEqual([{ handle: null }, { handle: a }]);
		reg.leave();
		expect(seen).toEqual([{ handle: null }, { handle: a }, null]);
		stop();
	});

	it("lets a remount replace the editor without the old leave removing the new one", () => {
		const first = registerMarkdown(["c"]);
		first.editable(fakeHandle("first"));
		const second = registerMarkdown(["c"]);
		const b = fakeHandle("second");
		second.editable(b);
		expect(markdownAt(["c"])).toEqual({ handle: b });
		first.editable(null);
		first.leave();
		expect(markdownAt(["c"])).toEqual({ handle: b });
		second.leave();
		expect(markdownAt(["c"])).toBeNull();
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

// `lost`: the text a host waited on will never be stored, so whatever it
// held back (a cut, a withdrawn cell) must be let go the other way.
describe("MarkdownRef saved, lost", () => {
	/** The node goes from the tree, as a server-driven remove drops it. */
	const drop = () => act(() => tree.getState().remove(PATH));

	it("fires lost, never fn, when the node is disposed before Nu's read comes back", () => {
		const doc = mount("a\n");
		save(doc, "b");
		const fn = vi.fn();
		const lost = vi.fn();
		doc.saved(fn, lost);
		drop();
		expect(lost).toHaveBeenCalledOnce();
		expect(fn).not.toHaveBeenCalled();
		// A read for the gone node finds nobody waiting.
		dispatch(OPS.read, null, "r1");
		expect(fn).not.toHaveBeenCalled();
		expect(lost).toHaveBeenCalledOnce();
	});

	it("fires lost when the editor tears down with the edits still unsaved", () => {
		const doc = mount("a\n");
		act(() => {
			doc.focus("end");
			doc.type("b");
		});
		const fn = vi.fn();
		const lost = vi.fn();
		doc.saved(fn, lost);
		drop();
		expect(lost).toHaveBeenCalledOnce();
		expect(fn).not.toHaveBeenCalled();
		expect(notifies()).toBe(0);
	});

	it("never fires lost once the read has come back, nor once unsubscribed", () => {
		const doc = mount("a\n");
		save(doc, "b");
		const fn = vi.fn();
		const lost = vi.fn();
		doc.saved(fn, lost);
		dispatch(OPS.read, null, "r1");
		expect(fn).toHaveBeenCalledOnce();
		save(doc, "c");
		const later = vi.fn();
		doc.saved(vi.fn(), later)();
		drop();
		expect(lost).not.toHaveBeenCalled();
		expect(later).not.toHaveBeenCalled();
	});
});
