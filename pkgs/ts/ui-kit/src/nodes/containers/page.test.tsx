// Page parts over the real tree store: a PageSection's header and body, the
// two NavList variants, a Column capped at a page width, and a Spacer that
// pushes the rest of a Row to its end.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, register, tree, useFlow } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

// A leaf that prints the flow its parent hands it.
function FlowProbe() {
	return <span data-probe>{useFlow()}</span>;
}
register("PageTestProbe", { component: FlowProbe });

type Step = [string, string, Record<string, unknown>?];

function write(...chain: Step[]) {
	act(() => {
		tree
			.getState()
			.write(chain.map(([seg, type, props]) => (props ? [seg, type, props] : [seg, type])));
	});
}

function draw(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

const q = (sel: string) => host.querySelector<HTMLElement>(sel);

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

describe("PageSection", () => {
	it("draws the title, description and the actions child in the header", () => {
		const sec: Step = ["s", "PageSection", { title: "Usage", description: "Last 30 days" }];
		write(sec, ["actions", "Row"], ["export", "ButtonRef", { label: "Export" }]);
		write(sec, ["body", "TextRef", { value: "rows" }]);
		draw(["s"]);
		const header = q("[data-slot=section-header]");
		expect(header?.querySelector("h2")?.textContent).toBe("Usage");
		expect(header?.textContent).toContain("Last 30 days");
		expect(q("[data-slot=section-actions]")?.textContent).toBe("Export");
		const body = q("[data-slot=section-body]");
		expect(body?.textContent).toBe("rows");
		expect(body?.textContent).not.toContain("Export");
	});

	it("hands the body a block flow and the actions a row flow", () => {
		write(["s", "PageSection", { title: "T" }], ["actions", "PageTestProbe"]);
		write(["s", "PageSection"], ["b", "PageTestProbe"]);
		draw(["s"]);
		expect(q("[data-slot=section-actions] [data-probe]")?.textContent).toBe("row");
		expect(q("[data-slot=section-body] [data-probe]")?.textContent).toBe("block");
	});

	it("draws no header with nothing to put in it, and maps size and bordered", () => {
		write(["s", "PageSection", { size: "lg", bordered: true, gap: 2 }], ["b", "TextRef"]);
		draw(["s"]);
		expect(q("[data-slot=section-header]")).toBeNull();
		const section = q("[data-slot=section]");
		expect(section?.className).toContain("gap-8");
		expect(section?.className).toContain("border-t");
		expect(q("[data-slot=section-body]")?.className).toContain("gap-2");
	});
});

describe("NavList", () => {
	it("stacks items under a group label, as full width rows", () => {
		write(
			["n", "NavList", { label: "Workspace" }],
			["a", "NavItemRef", { label: "A", href: "/a" }],
		);
		draw(["n"]);
		const nav = q("[data-slot=nav-list]");
		expect(nav?.tagName).toBe("NAV");
		// The drawn label names the landmark, by reference rather than twice.
		const labelId = nav?.getAttribute("aria-labelledby") ?? "";
		expect(nav?.getAttribute("aria-label")).toBeNull();
		expect(document.getElementById(labelId)?.textContent).toBe("Workspace");
		expect(nav?.className).toContain("flex-col");
		expect(nav?.textContent).toContain("Workspace");
		expect(q("[data-slot=nav-link]")?.className).toContain("w-full");
	});

	it("puts items on one scrolling line when horizontal, the label only naming it", () => {
		write(
			["n", "NavList", { variant: "horizontal", label: "Main" }],
			["a", "NavItemRef", { label: "A", href: "/a" }],
		);
		draw(["n"]);
		const nav = q("[data-slot=nav-list]");
		expect(nav?.className).toContain("flex-row");
		expect(nav?.className).toContain("overflow-x-auto");
		expect(nav?.textContent).toBe("A");
		expect(q("[data-slot=nav-link]")?.className).not.toContain("w-full");
	});
});

describe("Column page width", () => {
	it("caps and centers at a named width", () => {
		write(["c", "Column", { max_width: "main" }], ["t", "TextRef", { value: "x" }]);
		draw(["c"]);
		const col = q("[data-max-width]");
		expect(col?.dataset.maxWidth).toBe("main");
		expect(col?.className).toContain("max-w-main");
		expect(col?.className).toContain("mx-auto");
		expect(col?.className).toContain("w-full");
	});

	it("caps without centering, and caps nothing at full", () => {
		write(["c", "Column", { max_width: "prose", center: false }], ["t", "TextRef"]);
		draw(["c"]);
		expect(q("[data-max-width]")?.className).not.toContain("mx-auto");
		act(() =>
			tree.getState().dispatch({ op: "write", ref: ["c"], payload: { max_width: "full" } }),
		);
		expect(q("[data-max-width]")).toBeNull();
	});

	it("justifies evenly", () => {
		write(["c", "Column", { justify: "evenly" }], ["t", "TextRef"]);
		draw(["c"]);
		expect(host.firstElementChild?.className).toContain("justify-evenly");
	});
});

describe("SpacerRef", () => {
	it("grows from nothing in a Row, so what follows sits at the end", () => {
		write(["r", "Row"], ["title", "TextRef", { value: "Title" }]);
		write(["r", "Row"], ["gap", "SpacerRef"]);
		write(["r", "Row"], ["go", "ButtonRef", { label: "Go" }]);
		draw(["r"]);
		const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=row-cell]")];
		expect(cells.map((c) => c.style.flex)).toEqual(["0 1 auto", "1 1 0px", "0 1 auto"]);
		expect(cells[1].querySelector("[data-slot=spacer]")).not.toBeNull();
	});

	it("draws bare in a Column and nothing in a Line", () => {
		write(["c", "Column"], ["gap", "SpacerRef"]);
		write(["l", "Line"], ["gap", "SpacerRef"]);
		draw(["c"]);
		expect(q("[data-slot=spacer]")?.parentElement?.dataset.slot).toBeUndefined();
		draw(["l"]);
		expect(q("[data-slot=spacer]")).toBeNull();
	});
});
