// Page parts over the real tree store: a PageSection's header and body, the
// two NavList variants, a Column capped at a page width, the Container page
// frame, and a Spacer that pushes the rest of a Row to its end.

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

	it("draws no header with nothing to put in it, and maps size and the body gap", () => {
		write(["s", "PageSection", { size: "lg", gap: 2 }], ["b", "TextRef"]);
		draw(["s"]);
		expect(q("[data-slot=section-header]")).toBeNull();
		const section = q("[data-slot=section]");
		expect(section?.className).toContain("gap-8");
		expect(section?.className).not.toContain("border-t");
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
	const col = () => host.firstElementChild as HTMLElement;

	it("caps at a named width and leaves placing to its parent", () => {
		write(["c", "Column", { max_width: "main" }], ["t", "TextRef", { value: "x" }]);
		draw(["c"]);
		expect(col().style.maxWidth).toBe("75rem");
		expect(col().className).toContain("w-full");
		expect(col().className).not.toContain("mx-auto");
	});

	it("caps at any length", () => {
		write(["c", "Column", { max_width: 640 }], ["t", "TextRef"]);
		draw(["c"]);
		expect(col().style.maxWidth).toBe("640px");
	});

	it("caps nothing when no max_width is set", () => {
		write(["c", "Column"], ["t", "TextRef"]);
		draw(["c"]);
		expect(col().style.maxWidth).toBe("");
		expect(col().className).not.toContain("w-full");
	});

	it("justifies between", () => {
		write(["c", "Column", { justify: "between" }], ["t", "TextRef"]);
		draw(["c"]);
		expect(col().className).toContain("justify-between");
	});
});

describe("Container", () => {
	it("frames at main by default: full width to the cap, centred, gutter, gap", () => {
		write(["p", "Container", {}], ["a", "PageTestProbe"]);
		write(["p", "Container", {}], ["b", "TextRef", { value: "b" }]);
		draw(["p"]);
		const frame = q("[data-slot=container]");
		expect(frame?.dataset.maxWidth).toBe("main");
		const cls = frame?.className ?? "";
		for (const c of ["w-full", "mx-auto", "max-w-main", "flex-col", "gap-6"]) {
			expect(cls).toContain(c);
		}
		// The gutter follows the window, nothing else does.
		for (const c of ["px-4", "md:px-8", "lg:px-12"]) expect(cls).toContain(c);
		expect(cls).not.toMatch(/(sm|md|lg|xl):max-w/);
		// Children stack as blocks, in the order they landed.
		expect(q("[data-probe]")?.textContent).toBe("block");
		expect(frame?.textContent).toBe("blockb");
	});

	it("takes every page width, and any length, as its max_width", () => {
		const want: Record<string, string> = {
			form: "30rem",
			prose: "40rem",
			panel: "60rem",
			dashboard: "87.5rem",
			full: "100%",
			"72rem": "72rem",
		};
		write(["p", "Container"]);
		draw(["p"]);
		for (const [width, css] of Object.entries(want)) {
			act(() =>
				tree.getState().dispatch({ op: "write", ref: ["p"], payload: { max_width: width } }),
			);
			expect(q("[data-slot=container]")?.style.maxWidth).toBe(css);
		}
	});

	it("drops the gutter edge to edge, and takes its gap", () => {
		write(["p", "Container", { padding: 0, gap: 2 }], ["t", "TextRef"]);
		draw(["p"]);
		const cls = q("[data-slot=container]")?.className ?? "";
		expect(cls).not.toContain("px-4");
		expect(cls).toContain("gap-2");
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
