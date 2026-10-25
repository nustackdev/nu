// hide / display over the real tree store and the kit's containers: a
// hidden node draws nothing, takes no cell in its parent, and comes back in
// its place with the state it had.

import { type ChainStep, OPS } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

function write(...chain: ChainStep[]) {
	act(() => tree.getState().write(chain));
}

function op(name: string, chain: ChainStep[]) {
	act(() =>
		tree.getState().dispatch({ op: name, ref: chain.map((s) => s[0]), payload: null, chain }),
	);
}

function draw(seg: string) {
	act(() => root.render(<NodeView path={[seg]} />));
}

const all = (sel: string) => host.querySelectorAll(sel);

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

describe("hide / display", () => {
	it("draws nothing for a hidden node, and draws it again with its state on display", () => {
		write(["t", "TextRef", { value: "kept" }]);
		draw("t");
		op(OPS.hide, [["t", "TextRef"]]);
		expect(host.innerHTML).toBe("");
		write(["t", "TextRef"]);
		act(() => tree.getState().setProps(["t"], { value: "changed while hidden" }));
		op(OPS.display, [["t", "TextRef"]]);
		expect(host.textContent).toBe("changed while hidden");
	});

	it("leaves no cell in a Row, a Grid or a Column", () => {
		const cells = { Row: "row-cell", Grid: "grid-cell", Column: "block-cell" } as const;
		for (const [type, cell] of Object.entries(cells)) {
			act(() => tree.getState().remove([]));
			write(["c", type], ["a", "BadgeRef", { label: "A" }]);
			write(["c", type], ["b", "BadgeRef", { label: "B" }]);
			draw("c");
			expect(all(`[data-slot=${cell}]`)).toHaveLength(2);
			op(OPS.hide, [
				["c", type],
				["a", "BadgeRef"],
			]);
			expect(all(`[data-slot=${cell}]`)).toHaveLength(1);
			expect(host.textContent).toBe("B");
			op(OPS.display, [
				["c", type],
				["a", "BadgeRef"],
			]);
			// Back in its place, not at the end.
			expect(host.textContent).toBe("AB");
		}
	});

	it("hides a whole branch, children and all", () => {
		write(["c", "Column"], ["r", "Row"], ["t", "TextRef", { value: "deep" }]);
		draw("c");
		op(OPS.hide, [
			["c", "Column"],
			["r", "Row"],
		]);
		expect(host.textContent).toBe("");
		expect(tree.getState().getIn(["c", "r", "t"])?.props.value).toBe("deep");
	});

	it("drops a card's named slot and its wrapper", () => {
		write(["k", "Card", { title: "T" }], ["media", "TextRef", { value: "pic" }]);
		write(["k", "Card"], ["footer", "TextRef", { value: "foot" }]);
		write(["k", "Card"], ["body", "TextRef", { value: "body" }]);
		draw("k");
		expect(all("[data-slot=card-media]")).toHaveLength(1);
		op(OPS.hide, [
			["k", "Card"],
			["media", "TextRef"],
		]);
		op(OPS.hide, [
			["k", "Card"],
			["footer", "TextRef"],
		]);
		expect(all("[data-slot=card-media]")).toHaveLength(0);
		expect(all("[data-slot=card-footer]")).toHaveLength(0);
		expect(host.textContent).toContain("body");
	});

	it("hides a node that arrives hidden, before any write", () => {
		write(["c", "Column"]);
		draw("c");
		op(OPS.hide, [
			["c", "Column"],
			["late", "TextRef", { value: "not yet" }],
		]);
		expect(host.textContent).toBe("");
		op(OPS.display, [
			["c", "Column"],
			["late", "TextRef"],
		]);
		expect(host.textContent).toBe("not yet");
	});
});
