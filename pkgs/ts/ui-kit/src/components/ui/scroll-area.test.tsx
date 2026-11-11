// ScrollArea: that it renders its children inside the viewport, that
// `viewportRef` reaches the element that scrolls, and that `orientation`
// decides which bars exist and which axes scroll.

import { act, createRef } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { ScrollArea } from "./scroll-area";

// React 19 wants this before render or it logs a warning per test.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures the viewport and its content through ResizeObserver, which
// jsdom lacks.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
};

let host: HTMLDivElement;
let root: Root;

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

const q = (slot: string) => host.querySelectorAll(`[data-slot=${slot}]`);

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

describe("ScrollArea", () => {
	it("renders the root and puts the children in the viewport", () => {
		mount(
			<ScrollArea className="h-40">
				<p>first</p>
				<p>second</p>
			</ScrollArea>,
		);
		const rootEl = q("scroll-area")[0] as HTMLElement;
		expect(rootEl).toBeTruthy();
		expect(rootEl.className).toContain("h-40");
		const viewport = q("scroll-area-viewport")[0] as HTMLElement;
		expect(viewport.textContent).toBe("firstsecond");
		expect(viewport.querySelectorAll("p")).toHaveLength(2);
	});

	it("hands the viewport to viewportRef, scrollable from outside", () => {
		const ref = createRef<HTMLDivElement>();
		mount(
			<ScrollArea orientation="both" viewportRef={ref}>
				<div style={{ width: 2000, height: 2000 }} />
			</ScrollArea>,
		);
		expect(ref.current).toBe(q("scroll-area-viewport")[0]);
		expect(ref.current?.hasAttribute("data-radix-scroll-area-viewport")).toBe(true);
		const viewport = ref.current as HTMLDivElement;
		viewport.scrollTop = 120;
		viewport.scrollLeft = 80;
		expect(viewport.scrollTop).toBe(120);
		expect(viewport.scrollLeft).toBe(80);
	});

	it("draws one vertical bar by default and scrolls only down", () => {
		mount(
			<ScrollArea>
				<p>rows</p>
			</ScrollArea>,
		);
		const bars = [...q("scroll-area-scrollbar")];
		expect(bars.map((b) => b.getAttribute("data-orientation"))).toEqual(["vertical"]);
		const viewport = q("scroll-area-viewport")[0] as HTMLElement;
		expect(viewport.style.overflowY).toBe("scroll");
		expect(viewport.style.overflowX).toBe("hidden");
		expect(q("scroll-area")[0].getAttribute("data-orientation")).toBe("vertical");
	});

	it("draws one horizontal bar and scrolls only sideways", () => {
		mount(
			<ScrollArea orientation="horizontal">
				<p>cards</p>
			</ScrollArea>,
		);
		const bars = [...q("scroll-area-scrollbar")];
		expect(bars.map((b) => b.getAttribute("data-orientation"))).toEqual(["horizontal"]);
		const viewport = q("scroll-area-viewport")[0] as HTMLElement;
		expect(viewport.style.overflowX).toBe("scroll");
		expect(viewport.style.overflowY).toBe("hidden");
	});

	it("draws both bars for both", () => {
		mount(
			<ScrollArea orientation="both">
				<p>grid</p>
			</ScrollArea>,
		);
		const bars = [...q("scroll-area-scrollbar")];
		expect(bars.map((b) => b.getAttribute("data-orientation")).sort()).toEqual([
			"horizontal",
			"vertical",
		]);
		const viewport = q("scroll-area-viewport")[0] as HTMLElement;
		expect(viewport.style.overflowX).toBe("scroll");
		expect(viewport.style.overflowY).toBe("scroll");
	});

	it("keeps the bars mounted but hidden until something scrolls", () => {
		mount(
			<ScrollArea orientation="both">
				<p>idle</p>
			</ScrollArea>,
		);
		for (const bar of q("scroll-area-scrollbar")) {
			expect(bar.getAttribute("data-state")).toBe("hidden");
		}
	});
});
