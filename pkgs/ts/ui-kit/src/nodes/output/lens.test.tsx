// LensRef over the real tree store: a move goes out as a `change` carrying the
// cursor, and the cursor read back is the last move or the last write.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
// jsdom has no layout; the columns keep the cursor row in view.
Element.prototype.scrollIntoView ??= () => {};

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

const ROOT_COLUMN = {
	kind: "shape",
	total: 2,
	entries: [
		{ key: "counts", kind: "mapping", preview: "", navigable: true },
		{ key: "title", kind: "leaf", preview: "a zoo", navigable: false, vtype: "str" },
	],
};

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

function mount() {
	act(() => {
		tree.getState().write([["lens", "LensRef", {}]]);
		root.render(<NodeView path={["lens"]} />);
	});
}

function setColumns(cursor: string[], columns: unknown[]) {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: ["lens"], payload: { cursor, columns } });
	});
}

function read(id: string) {
	act(() => {
		tree.getState().dispatch({ op: OPS.read, ref: ["lens"], payload: null, id });
	});
	return sent.find((f) => f.op === OPS.read && f.id === id)?.payload;
}

describe("LensRef", () => {
	it("reads [] before anything moved it", () => {
		mount();
		expect(read("r0")).toEqual([]);
	});

	it("reads the cursor a write shipped, and keeps the columns", () => {
		mount();
		setColumns(["counts"], [ROOT_COLUMN]);
		const props = tree.getState().getIn(["lens"])?.props;
		expect(props?.cursor).toEqual(["counts"]);
		expect(props?.columns).toEqual([ROOT_COLUMN]);
		expect(read("r1")).toEqual(["counts"]);
	});

	it("sends a move as a change carrying the cursor, and reads it back", () => {
		mount();
		setColumns([], [ROOT_COLUMN]);
		const row = host.querySelector<HTMLElement>('[role="treeitem"]');
		expect(row?.textContent).toContain("counts");
		act(() => row?.click());
		const notify = sent.find((f) => f.op === OPS.notify);
		expect(notify?.ref).toEqual(["lens"]);
		expect(notify?.payload).toEqual({ event: "change", value: ["counts"] });
		// The read follows the move before the server answers it.
		expect(read("r2")).toEqual(["counts"]);
		// The drawn cursor waits for the cascade: the trail never runs ahead.
		expect(tree.getState().getIn(["lens"])?.props.cursor).toEqual([]);
		// The server's next write is where the lens is now.
		setColumns(["title"], [ROOT_COLUMN]);
		expect(read("r3")).toEqual(["title"]);
	});
});
