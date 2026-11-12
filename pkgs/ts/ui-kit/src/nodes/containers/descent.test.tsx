// Descent on the browser side: positions draw in number order in every body
// container, children no tab / section names say so, a Field's second child
// says so, and a level with no type (a bare child) claims nothing.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

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

function text(parent: string, type: string, seg: string, value: string) {
	tree.getState().write([
		[parent, type],
		[seg, "TextRef", { value }],
	]);
}

describe("positions draw in number order", () => {
	for (const type of ["Row", "Column", "Grid", "Box", "Container", "Form", "Fieldset"]) {
		it(type, () => {
			act(() => {
				text("c", type, "2", "two");
				text("c", type, "k", "name");
				text("c", type, "0", "zero");
				text("c", type, "1", "one");
			});
			act(() => root.render(<NodeView path={["c"]} />));
			const order = ["zero", "name", "one", "two"];
			const got = host.textContent ?? "";
			const at = order.map((w) => got.indexOf(w));
			expect(at.every((i) => i >= 0)).toBe(true);
			expect([...at].sort((a, b) => a - b)).toEqual(at);
		});
	}
});

describe("children a container cannot draw", () => {
	it("Tabs names a child no tab has", () => {
		act(() => {
			tree.getState().write([["t", "Tabs", { tabs: [{ id: "a", label: "A" }] }]]);
			text("t", "Tabs", "a", "ay");
			text("t", "Tabs", "zz", "lost");
		});
		act(() => root.render(<NodeView path={["t"]} />));
		expect(host.textContent).toContain('"zz" not drawn, no tab has that id');
		expect(host.textContent).not.toContain("lost");
	});

	it("Accordion names a child no section has", () => {
		act(() => {
			tree.getState().write([["a", "Accordion", { sections: [{ id: "s", label: "S" }] }]]);
			text("a", "Accordion", "s", "body");
			text("a", "Accordion", "q", "lost");
		});
		act(() => root.render(<NodeView path={["a"]} />));
		expect(host.textContent).toContain('"q" not drawn, no section has that id');
	});

	it("Field names a second control", () => {
		act(() => {
			text("f", "Field", "control", "one");
			text("f", "Field", "extra", "two");
		});
		act(() => root.render(<NodeView path={["f"]} />));
		expect(host.textContent).toContain("one");
		expect(host.textContent).toContain('"extra" not drawn, a Field holds one control');
	});
});

describe("a bare level", () => {
	it("hides what is there without claiming a kind", () => {
		act(() => text("r", "Row", "0", "zero"));
		const ok = tree.getState().write([
			["r", "Row"],
			["0", null],
		]);
		expect(ok).toBe(true);
		expect(tree.getState().getIn(["r", "0"])?.type).toBe("TextRef");
	});
});
