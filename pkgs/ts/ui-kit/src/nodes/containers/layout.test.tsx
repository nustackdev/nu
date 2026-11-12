// Layout over the real tree store: the four layers every container reads
// (`layout.tsx`), the per child maps, `set_child`, and how each container
// draws them: a stack's cells, a row's flex and stacking, a surface's pad, an
// overlay's width, a placed grid that stacks under its width, and a
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
import {
	cssLength,
	flowClass,
	readChildMaps,
	readLayout,
	readSpan,
	sizeStyle,
	stickyStyle,
} from "./layout";
import { FILL_BASIS, rowFlex } from "./row";

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

function dispatch(ref: string[], op: string, payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op, ref, payload });
	});
}

function show(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

const props = (path: string[]) => tree.getState().getIn(path)?.props ?? {};

/** Stub ResizeObserver and clientWidth; `set` changes the width and fires the observers. */
function stubWidth(initial: number) {
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
	const descriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth");
	let w = initial;
	Object.defineProperty(HTMLElement.prototype, "clientWidth", {
		configurable: true,
		get: () => w,
	});
	return {
		set(next: number) {
			w = next;
			act(() => {
				for (const cb of callbacks) cb();
			});
		},
		restore() {
			globalThis.ResizeObserver = saved;
			if (descriptor) Object.defineProperty(HTMLElement.prototype, "clientWidth", descriptor);
		},
	};
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

describe("lengths", () => {
	it("reads px, digits, CSS lengths and page widths, nothing else", () => {
		expect(cssLength(240)).toBe("240px");
		expect(cssLength("12")).toBe("12px");
		expect(cssLength("60vh")).toBe("60vh");
		expect(cssLength("100%")).toBe("100%");
		expect(cssLength("prose")).toBe("40rem");
		expect(cssLength("form")).toBe("30rem");
		expect(cssLength("panel")).toBe("60rem");
		expect(cssLength("main")).toBe("75rem");
		expect(cssLength("dashboard")).toBe("87.5rem");
		expect(cssLength("full")).toBe("100%");
		expect(cssLength("calc(1px)")).toBeUndefined();
		expect(cssLength("wide")).toBeUndefined();
		expect(cssLength(-1)).toBeUndefined();
		expect(cssLength(null)).toBeUndefined();
	});

	it("puts the size props in a style, none when nothing is set", () => {
		expect(sizeStyle({})).toBeUndefined();
		expect(sizeStyle({ width: 320, max_width: "prose", min_height: "10vh", junk: 3 })).toEqual({
			width: "320px",
			maxWidth: "40rem",
			minHeight: "10vh",
		});
	});
});

describe("readLayout", () => {
	const defaults = { gap: 4, padding: 0, justify: "start", align: "stretch" };

	it("takes the container's own look for what is unset, null included", () => {
		const l = readLayout({ gap: null, padding: null, justify: null }, defaults);
		expect(l).toMatchObject({
			gap: 4,
			padding: 0,
			padSet: false,
			justify: "start",
			align: "stretch",
			divided: false,
			size: undefined,
			scroll: undefined,
		});
	});

	it("reads what is set, a step off the scale as unset", () => {
		const l = readLayout(
			{ gap: 2, padding: 6, justify: "between", align: "end", divided: true, scroll: "y" },
			defaults,
		);
		expect(l).toMatchObject({ gap: 2, padding: 6, padSet: true, justify: "between", align: "end" });
		expect(l.divided).toBe(true);
		expect(l.scroll).toBe("min-h-0 overflow-y-auto");
		expect(readLayout({ gap: 17, padding: 1.5 }, defaults)).toMatchObject({
			gap: 4,
			padding: 0,
			padSet: false,
		});
	});

	it("draws the hairline and the scroll along the axis", () => {
		const l = readLayout({ divided: true, scroll: "x" }, defaults);
		const column = flowClass(l, "column");
		expect(column).toContain("divide-y");
		expect(column).toContain("gap-4");
		expect(column).toContain("p-0");
		expect(column).toContain("overflow-x-auto");
		expect(flowClass(l, "row")).toContain("divide-x");
		expect(
			flowClass(readLayout({ padding: 3 }, defaults), "column", { padding: false }),
		).not.toContain("p-3");
	});
});

describe("per child maps", () => {
	it("reads each map, dropping what does not read", () => {
		const maps = readChildMaps({
			grow: { a: 2, b: "x", c: -1, d: 0 },
			basis: { a: 280, b: "20rem", c: "junk" },
			span: { "0,0": { cols: 2 }, "1,1": { cols: 1, rows: 1 } },
			align_self: { a: "end", b: 3 },
			sticky: { head: "top" },
		});
		expect(maps.grow).toEqual({ a: 2, d: 0 });
		expect(maps.basis).toEqual({ a: "280px", b: "20rem" });
		expect(maps.span).toEqual({ "0,0": { cols: 2, rows: 1 } });
		expect(maps.alignSelf).toEqual({ a: "end" });
		expect(maps.sticky).toEqual({ head: "top" });
		expect(readChildMaps({ grow: [1] }).grow).toEqual({});
	});

	it("reads a span of whole tracks, 1 by 1 as none", () => {
		expect(readSpan({ cols: 2, rows: 3 })).toEqual({ cols: 2, rows: 3 });
		expect(readSpan({ rows: 2 })).toEqual({ cols: 1, rows: 2 });
		expect(readSpan({ cols: 1 })).toBeUndefined();
		expect(readSpan({ cols: 0 })).toBeUndefined();
		expect(readSpan(2)).toBeUndefined();
	});

	it("sticks a child to the edge it names, and nothing else", () => {
		expect(stickyStyle("top")).toEqual({ position: "sticky", top: 0, zIndex: 1 });
		expect(stickyStyle("left")).toEqual({ position: "sticky", left: 0, zIndex: 1 });
		expect(stickyStyle("middle")).toBeUndefined();
		expect(stickyStyle(undefined)).toBeUndefined();
	});

	it("merges set_child into the maps, null and a 1 by 1 span drop the entry", () => {
		write(["c", "Column", { grow: { a: 1 }, sticky: { a: "top" } }]);
		dispatch(["c"], "set_child", { key: "b", grow: 2, basis: 120 });
		expect(props(["c"]).grow).toEqual({ a: 1, b: 2 });
		expect(props(["c"]).basis).toEqual({ b: 120 });
		dispatch(["c"], "set_child", { key: "a", grow: null });
		expect(props(["c"]).grow).toEqual({ b: 2 });
		expect(props(["c"]).sticky).toEqual({ a: "top" });
		write(["g", "Grid", { span: { x: { cols: 2, rows: 1 } } }]);
		dispatch(["g"], "set_child", { key: "y", span: { cols: 1, rows: 3 } });
		expect(props(["g"]).span).toEqual({ x: { cols: 2, rows: 1 }, y: { cols: 1, rows: 3 } });
		dispatch(["g"], "set_child", { key: "x", span: { cols: 1, rows: 1 } });
		expect(props(["g"]).span).toEqual({ y: { cols: 1, rows: 3 } });
	});
});

describe("Column", () => {
	it("sizes and scrolls", () => {
		write(["c", "Column", { height: 200, scroll: "y" }]);
		show(["c"]);
		const el = host.firstElementChild as HTMLElement;
		expect(el.style.height).toBe("200px");
		expect(el.className).toContain("overflow-y-auto");
	});

	it("grows a child by a true ratio from 0, or from its basis", () => {
		write(["c", "Column", { height: 400, grow: { list: 1 }, basis: { foot: 64 } }]);
		write(["c", "Column"], ["head", "TextRef"]);
		write(["c", "Column"], ["list", "Card"]);
		write(["c", "Column"], ["foot", "Card"]);
		show(["c"]);
		const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=stack-cell]")];
		expect(cells.map((c) => c.style.flex)).toEqual(["1 1 0px", "0 1 64px"]);
	});

	it("aligns one child and pins a sticky one", () => {
		write(["c", "Column", { align_self: { a: "end" }, sticky: { h: "top" } }], ["h", "TextRef"]);
		write(["c", "Column"], ["a", "Card"]);
		show(["c"]);
		const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=stack-cell]")];
		expect(cells).toHaveLength(2);
		expect(cells[0].style.position).toBe("sticky");
		expect(cells[0].style.top).toBe("0px");
		expect(cells[1].className).toContain("self-end");
	});

	it("wraps every child in a cell when divided, the hairline between them", () => {
		write(["c", "Column", { divided: true, gap: 3 }], ["a", "TextRef"]);
		write(["c", "Column"], ["b", "TextRef"]);
		show(["c"]);
		const el = host.firstElementChild as HTMLElement;
		expect(el.className).toContain("divide-y");
		expect(el.style.getPropertyValue("--flow-gap")).toBe("calc(var(--spacing) * 3)");
		expect(host.querySelectorAll("[data-slot=stack-cell]")).toHaveLength(2);
	});

	it("draws plain children in the stack's own cell", () => {
		write(["c", "Column"], ["a", "TextRef"]);
		show(["c"]);
		expect(host.querySelector("[data-slot=stack-cell]")).toBeNull();
	});
});

describe("Row", () => {
	it("keeps the kind's flex unless the row sizes the child", () => {
		expect(rowFlex("fill", undefined, undefined)).toBe(`1 1 ${FILL_BASIS}px`);
		expect(rowFlex("content", undefined, undefined)).toBe("0 1 auto");
		expect(rowFlex("grow", undefined, undefined)).toBe("1 1 0px");
		expect(rowFlex("fill", 2, undefined)).toBe("2 1 0px");
		expect(rowFlex("content", 1, undefined)).toBe("1 1 0px");
		expect(rowFlex("fill", undefined, "280px")).toBe("0 1 280px");
		expect(rowFlex("grow", 3, "10rem")).toBe("3 1 10rem");
	});

	it("reads grow and basis by segment, a grown child from 0", () => {
		write(["r", "Row", { grow: { main: 2 }, basis: { side: 280 } }], ["side", "Card"]);
		write(["r", "Row"], ["main", "Card"]);
		write(["r", "Row"], ["plain", "Card"]);
		show(["r"]);
		const flex = [...host.querySelectorAll<HTMLElement>("[data-slot=row-cell]")].map(
			(c) => c.style.flex,
		);
		expect(flex).toEqual(["0 1 280px", "2 1 0px", "1 1 240px"]);
	});

	it("keeps 240px under a grown fill child in a wrapping row, so it still wraps", () => {
		write(["r", "Row", { wrap: true, grow: { a: 1, b: 2 } }], ["a", "Card"]);
		write(["r", "Row"], ["b", "Card"]);
		show(["r"]);
		const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=row-cell]")];
		expect(cells.map((c) => c.style.minWidth)).toEqual(["240px", "240px"]);
		expect((host.firstElementChild as HTMLElement).className).toContain("flex-wrap");
	});

	it("aligns one child", () => {
		write(["r", "Row", { align_self: { a: "end" } }], ["a", "TextRef"]);
		show(["r"]);
		expect(host.querySelector("[data-slot=row-cell]")?.className).toContain("self-end");
	});

	it("stacks to a column under stack_below", () => {
		const width = stubWidth(400);
		try {
			write(["r", "Row", { stack_below: 640, grow: { a: 1 } }], ["a", "Card"]);
			write(["r", "Row"], ["b", "Card"]);
			show(["r"]);
			const el = host.firstElementChild as HTMLElement;
			expect(el.dataset.stacked).toBe("");
			expect(el.className).toContain("flex-col");
			const cell = host.querySelector<HTMLElement>("[data-slot=row-cell]");
			expect(cell?.style.flex).toBe("0 0 auto");
			width.set(900);
			expect(el.dataset.stacked).toBeUndefined();
			expect(el.className).toContain("flex-row");
			expect(cell?.style.flex).toBe("1 1 0px");
		} finally {
			width.restore();
		}
	});
});

describe("surfaces", () => {
	it("pads a Card from its size unless padding is set, and gaps the body 3", () => {
		write(["c", "Card", { title: "T" }], ["t", "TextRef"]);
		show(["c"]);
		const card = host.querySelector<HTMLElement>("[data-slot=card]");
		expect(card?.style.getPropertyValue("--card-pad")).toBe("");
		const body = host.querySelector<HTMLElement>("[data-slot=card-content]");
		expect(body?.className).toContain("gap-3");
		dispatch(["c"], "write", { padding: 2, gap: 1 });
		expect(card?.style.getPropertyValue("--card-pad")).toBe("calc(var(--spacing) * 2)");
		expect(body?.className).toContain("gap-1");
	});

	it("puts a Card's height on the card and the scroll on its body", () => {
		write(["c", "Card", { title: "T", max_height: "40vh", scroll: "y" }], ["t", "TextRef"]);
		show(["c"]);
		const card = host.querySelector<HTMLElement>("[data-slot=card]");
		expect(card?.style.maxHeight).toBe("40vh");
		const body = host.querySelector<HTMLElement>("[data-slot=card-content]");
		expect(body?.className).toContain("overflow-y-auto");
		expect(body?.className).toContain("flex-1");
	});

	it("draws the plain, accent and brand surfaces", () => {
		for (const variant of ["plain", "accent", "brand"]) {
			write([variant, "Card", { variant, title: variant }]);
			show([variant]);
			const card = host.querySelector<HTMLElement>("[data-slot=card]");
			expect(card?.className).toContain(
				{ plain: "border-transparent", accent: "bg-accent-2-wash", brand: "bg-accent-soft" }[
					variant
				] as string,
			);
		}
	});

	it("takes a Modal's width as a cap, caps at the window and scrolls its body", () => {
		write(["m", "Modal", { open: true, title: "Edit", width: 672, padding: 4 }], ["t", "TextRef"]);
		show(["m"]);
		const content = document.querySelector("[data-slot=dialog-content]") as HTMLElement;
		expect(content.style.maxWidth).toBe("672px");
		expect(content.style.width).toBe("");
		expect(content.style.padding).toBe("calc(var(--spacing) * 4)");
		expect(content.className).toContain("max-h-[calc(100dvh-2rem)]");
		const body = document.querySelector("[data-slot=modal-body]") as HTMLElement;
		expect(body.className).toContain("overflow-y-auto");
		expect(body.className).toContain("gap-4");
	});

	it("gives a Sheet its width", () => {
		write(["s", "Sheet", { open: true, title: "Inspector", width: "prose" }], ["t", "TextRef"]);
		show(["s"]);
		const content = document.querySelector("[data-node=sheet]") as HTMLElement;
		expect(content.style.width).toBe("40rem");
	});

	it("leaves the hairline between sections to the stack that holds them", () => {
		write(["c", "Column", { divided: true }], ["a", "PageSection", { title: "A", gap: 2 }]);
		write(["c", "Column"], ["b", "PageSection", { title: "B" }]);
		write(["c", "Column"], ["a", "PageSection"], ["t", "TextRef"]);
		show(["c"]);
		expect((host.firstElementChild as HTMLElement).className).toContain("divide-y");
		expect(host.querySelectorAll("[data-slot=stack-cell]")).toHaveLength(2);
		const body = host.querySelector<HTMLElement>("[data-slot=section-body]");
		expect(body?.className).toContain("gap-2");
	});
});

describe("Container", () => {
	it("caps at max_width as a style, main unless set", () => {
		write(["p", "Container", { max_width: "dashboard" }]);
		show(["p"]);
		const el = host.querySelector<HTMLElement>("[data-slot=container]");
		expect(el?.style.maxWidth).toBe("87.5rem");
		write(["q", "Container"]);
		show(["q"]);
		expect(host.querySelector("[data-slot=container]")?.className).toContain("max-w-main");
	});

	it("drops the gutter when padding is set", () => {
		write(["p", "Container", { padding: 0, gap: 2 }]);
		show(["p"]);
		const el = host.querySelector<HTMLElement>("[data-slot=container]");
		expect(el?.className).not.toContain("md:px-8");
		expect(el?.className).toContain("p-0");
		expect(el?.className).toContain("gap-2");
	});
});

describe("holders and the rest", () => {
	it("spaces a Fieldset and a Field", () => {
		write(["f", "Fieldset", { legend: "L", padding: 2, gap: 6 }], ["t", "TextRef"]);
		show(["f"]);
		const fieldset = host.querySelector("fieldset") as HTMLElement;
		expect(fieldset.className).toContain("p-2");
		expect(fieldset.querySelector(".gap-6")).not.toBeNull();
		write(["d", "Field", { label: "Name" }], ["control", "TextRef"]);
		show(["d"]);
		expect((host.firstElementChild as HTMLElement).className).toContain("gap-1");
		dispatch(["d"], "write", { gap: 3, width: 200 });
		expect((host.firstElementChild as HTMLElement).className).toContain("gap-3");
		expect((host.firstElementChild as HTMLElement).style.width).toBe("200px");
	});

	it("gaps a Collapsible's body", () => {
		write(["c", "Collapsible", { title: "More", open: true, gap: 5 }], ["t", "TextRef"]);
		show(["c"]);
		expect(host.querySelector(".gap-5")).not.toBeNull();
	});

	it("spaces a NavList and a List", () => {
		write(["n", "NavList", { gap: 2, padding: 1 }], ["a", "NavItemRef", { label: "A" }]);
		show(["n"]);
		const nav = host.querySelector("nav") as HTMLElement;
		expect(nav.className).toContain("gap-2");
		expect(nav.className).toContain("p-1");
		write(["l", "List", { items: ["a", "b"] }]);
		show(["l"]);
		const plain = host.firstElementChild as HTMLElement;
		expect(plain.className).toContain("py-1");
		dispatch(["l"], "write", { gap: 2, padding: 3, divided: true });
		const list = host.firstElementChild as HTMLElement;
		expect(list.className).toContain("p-3");
		expect(list.className).toContain("divide-y");
		expect(list.style.getPropertyValue("--list-gap")).toBe("calc(var(--spacing) * 2)");
	});

	it("puts the size props on Tabs and an Accordion", () => {
		write(["t", "Tabs", { tabs: [{ id: "a", label: "A" }], width: 300 }]);
		show(["t"]);
		expect((host.firstElementChild as HTMLElement).style.width).toBe("300px");
		write(["a", "Accordion", { sections: [{ id: "x", label: "X" }], max_height: 120 }]);
		show(["a"]);
		expect((host.firstElementChild as HTMLElement).style.maxHeight).toBe("120px");
	});

	it("scrolls Tabs, an Accordion and a Field", () => {
		write(["ts", "Tabs", { tabs: [{ id: "a", label: "A" }], scroll: "y" }]);
		show(["ts"]);
		expect(host.firstElementChild?.className).toContain("overflow-y-auto");
		write(["ac", "Accordion", { sections: [{ id: "x", label: "X" }], scroll: "y" }]);
		show(["ac"]);
		expect(host.firstElementChild?.className).toContain("overflow-y-auto");
		write(["fd", "Field", { label: "L", scroll: "x" }]);
		show(["fd"]);
		expect(host.firstElementChild?.className).toContain("overflow-x-auto");
	});

	it("merges a set_layout write into an Accordion beside its own keys", () => {
		write(["am", "Accordion", { sections: [{ id: "x", label: "X" }], open: ["x"] }]);
		dispatch(["am"], "write", { max_height: 80, scroll: "y" });
		expect(props(["am"])).toMatchObject({ max_height: 80, scroll: "y", open: ["x"] });
		dispatch(["am"], "write", { open: [] });
		expect(props(["am"])).toMatchObject({ max_height: 80, open: [] });
	});
});

describe("Grid stack_below", () => {
	it("stacks a board to one column under its width, in reading order", () => {
		const width = stubWidth(300);
		try {
			write(["g", "Grid", { cols: "2fr 1fr", stack_below: 640, span: { "0,0": { cols: 2 } } }]);
			write(["g", "Grid"], ["1,0", "TextRef"]);
			write(["g", "Grid"], ["0,0", "TextRef"]);
			show(["g"]);
			const grid = host.querySelector("[data-slot=grid]") as HTMLElement;
			expect(grid.dataset.mode).toBe("stacked");
			expect(grid.style.gridTemplateColumns).toBe("minmax(0, 1fr)");
			const cells = [...host.querySelectorAll<HTMLElement>("[data-slot=grid-cell]")];
			expect(cells.map((c) => c.dataset.cell)).toEqual(["0,0", "1,0"]);
			expect(cells[0].style.gridColumn).toBe("");
			width.set(900);
			expect(grid.dataset.mode).toBe("placed");
			expect(cells[0].style.gridColumn).toBe("1 / span 2");
		} finally {
			width.restore();
		}
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
