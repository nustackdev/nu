// Sizing over the real tree store: height and scroll on Column, Row, Grid and
// Box, a child's grow and basis kept by its Row or Column, a placed grid that
// stacks under its width, the Modal's size and scrolling body, and a
// disclosure that clips only while its height moves.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	CollapsibleContent,
	Collapsible as CollapsibleRoot,
} from "../../components/ui/collapsible";
import { NodeView, tree } from "../../tree";
import "..";
import { rowFlex } from "./row";
import { cssLength, readWeights, sizing } from "./sizing";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix Presence escapes the animation name on animationend; jsdom has no CSS.escape.
const css = globalThis as unknown as { CSS?: { escape?: (s: string) => string } };
css.CSS ??= {};
css.CSS.escape ??= (s: string) => s;

let host: HTMLDivElement;
let root: Root;

function write(...chain: [string, string, Record<string, unknown>?][]) {
	act(() => {
		tree
			.getState()
			.write(chain.map(([seg, type, props]) => (props ? [seg, type, props] : [seg, type])));
	});
}

function show(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

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

describe("sizing props", () => {
	it("reads lengths as px or a CSS length, nothing else", () => {
		expect(cssLength(240)).toBe("240px");
		expect(cssLength("60vh")).toBe("60vh");
		expect(cssLength("12")).toBe("12px");
		expect(cssLength("100%")).toBe("100%");
		expect(cssLength("calc(1px)")).toBeUndefined();
		expect(cssLength(-1)).toBeUndefined();
		expect(cssLength(null)).toBeUndefined();
	});

	it("maps scroll to an overflow class and leaves an unsized container alone", () => {
		expect(sizing(null, null, "none")).toEqual({ className: undefined, style: undefined });
		expect(sizing(320, "50vh", "y")).toEqual({
			className: "min-h-0 overflow-y-auto",
			style: { height: "320px", maxHeight: "50vh" },
		});
		expect(sizing(null, null, "both").className).toContain("overflow-auto");
		expect(sizing(null, null, "sideways").className).toBeUndefined();
	});

	it("reads per child weights, dropping what is not a number >= 0", () => {
		expect(readWeights({ a: 2, b: "x", c: -1, d: 0 })).toEqual({ a: 2, d: 0 });
		expect(readWeights([1])).toEqual({});
	});

	it("sizes and scrolls a Column", () => {
		write(["c", "Column", { height: 200, scroll: "y" }]);
		show(["c"]);
		const el = host.firstElementChild as HTMLElement;
		expect(el.style.height).toBe("200px");
		expect(el.className).toContain("overflow-y-auto");
	});

	it("puts a Box's height on the panel and the scroll on its body", () => {
		write(["b", "Box", { title: "T", max_height: "40vh", scroll: "y" }], ["t", "TextRef"]);
		show(["b"]);
		const panel = host.firstElementChild as HTMLElement;
		expect(panel.style.maxHeight).toBe("40vh");
		const body = host.querySelector(".overflow-y-auto");
		expect(body).not.toBeNull();
		expect(body?.className).toContain("flex-1");
	});
});

describe("Row grow and basis", () => {
	it("keeps the kind's flex unless the row sizes the child", () => {
		expect(rowFlex("fill", 240, undefined, undefined)).toBe("1 1 240px");
		expect(rowFlex("content", 240, undefined, undefined)).toBe("0 1 auto");
		expect(rowFlex("fill", 240, 2, undefined)).toBe("2 1 240px");
		expect(rowFlex("content", 240, 1, undefined)).toBe("1 1 auto");
		expect(rowFlex("fill", 240, undefined, 280)).toBe("0 1 280px");
		expect(rowFlex("grow", 240, 3, undefined)).toBe("3 1 0px");
	});

	it("reads grow and basis by segment", () => {
		write(["r", "Row", { grow: { main: 2 }, basis: { side: 280 } }], ["side", "Card"]);
		write(["r", "Row"], ["main", "Card"]);
		write(["r", "Row"], ["plain", "Card"]);
		show(["r"]);
		const flex = [...host.querySelectorAll<HTMLElement>("[data-slot=row-cell]")].map(
			(c) => c.style.flex,
		);
		expect(flex).toEqual(["0 1 280px", "2 1 240px", "1 1 240px"]);
	});
});

describe("Column grow", () => {
	it("gives a grown child a flex cell and leaves the others in theirs", () => {
		write(["c", "Column", { height: 400, grow: { list: 1 } }], ["head", "TextRef"]);
		write(["c", "Column"], ["list", "Card"]);
		show(["c"]);
		const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=column-cell]")];
		expect(cells).toHaveLength(1);
		expect(cells[0].style.flex).toBe("1 1 0px");
	});
});

describe("Grid stack_below", () => {
	it("stacks a board to one column under its width, in reading order", () => {
		const callbacks: (() => void)[] = [];
		const saved = globalThis.ResizeObserver;
		globalThis.ResizeObserver = class {
			constructor(cb: () => void) {
				callbacks.push(cb);
			}
			observe() {}
			unobserve() {}
			disconnect() {}
		} as unknown as typeof ResizeObserver;
		const width = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth");
		let w = 300;
		Object.defineProperty(HTMLElement.prototype, "clientWidth", {
			configurable: true,
			get: () => w,
		});
		try {
			write(["g", "Grid", { cols: "2fr 1fr", stack_below: 640, spans: { "0,0": { cols: 2 } } }]);
			write(["g", "Grid"], ["1,0", "TextRef"]);
			write(["g", "Grid"], ["0,0", "TextRef"]);
			show(["g"]);
			const grid = host.querySelector("[data-slot=grid]") as HTMLElement;
			expect(grid.dataset.mode).toBe("stacked");
			expect(grid.style.gridTemplateColumns).toBe("minmax(0, 1fr)");
			const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=grid-cell]")];
			expect(cells.map((c) => c.dataset.cell)).toEqual(["0,0", "1,0"]);
			expect(cells[0].style.gridColumn).toBe("");

			w = 900;
			act(() => {
				for (const cb of callbacks) cb();
			});
			expect(grid.dataset.mode).toBe("placed");
			expect(cells[0].style.gridColumn).toBe("1 / span 2");
		} finally {
			globalThis.ResizeObserver = saved;
			if (width) Object.defineProperty(HTMLElement.prototype, "clientWidth", width);
		}
	});
});

describe("Modal", () => {
	it("takes a size, caps at the window and scrolls its body", () => {
		write(["m", "Modal", { open: true, title: "Edit", size: "xl" }], ["t", "TextRef"]);
		show(["m"]);
		const content = document.querySelector("[data-slot=dialog-content]") as HTMLElement;
		expect(content.className).toContain("max-w-4xl");
		expect(content.className).toContain("max-h-[calc(100dvh-2rem)]");
		expect(content.className).toContain("flex-col");
		const body = document.querySelector("[data-slot=modal-body]") as HTMLElement;
		expect(body.className).toContain("overflow-y-auto");
		expect(body.className).toContain("min-h-0");
	});
});

describe("disclosure clip", () => {
	it("clips only while its own height animation runs", () => {
		act(() =>
			root.render(
				<CollapsibleRoot open>
					<CollapsibleContent>
						<span data-inner>x</span>
					</CollapsibleContent>
				</CollapsibleRoot>,
			),
		);
		const content = host.querySelector("[data-slot=collapsible-content]") as HTMLElement;
		expect(content.className).not.toMatch(/(^| )overflow-hidden/);
		expect(content.className).toContain("data-[moving]:overflow-hidden");
		expect(content.hasAttribute("data-moving")).toBe(false);

		const inner = host.querySelector("[data-inner]") as HTMLElement;
		act(() => {
			inner.dispatchEvent(new Event("animationstart", { bubbles: true }));
		});
		expect(content.hasAttribute("data-moving")).toBe(false);

		act(() => {
			content.dispatchEvent(new Event("animationstart", { bubbles: true }));
		});
		expect(content.hasAttribute("data-moving")).toBe(true);
		act(() => {
			content.dispatchEvent(new Event("animationend", { bubbles: true }));
		});
		expect(content.hasAttribute("data-moving")).toBe(false);
	});
});
