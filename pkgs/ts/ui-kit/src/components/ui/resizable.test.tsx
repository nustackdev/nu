// Split panels: the defaults they share, the bounds a key or a drag cannot
// cross, the fold of a collapsible panel, the double-click reset, the layout
// that a storage key carries across a remount, sizes that follow their panels
// through a reorder, a px sidebar that holds its width while the group
// resizes, and the scrolling desk whose panels outgrow the group.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "./resizable";

// React 19 wants this before render or it logs a warning per test.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	window.localStorage.clear();
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

const panels = () => Array.from(host.querySelectorAll<HTMLElement>("[data-slot=resizable-panel]"));
const handle = (i = 0) => host.querySelectorAll<HTMLElement>("[data-slot=resizable-handle]")[i];
const grow = (el: HTMLElement) => Number.parseFloat(el.style.flexGrow);

function press(el: HTMLElement, key: string) {
	act(() => {
		el.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
	});
}

/** Give every panel a measured width, the way a laid out page would. */
function layOut(width: number) {
	for (const el of panels()) {
		el.getBoundingClientRect = () => {
			const w = (grow(el) / 100) * width;
			return {
				width: w,
				height: 100,
				x: 0,
				y: 0,
				top: 0,
				left: 0,
				right: w,
				bottom: 100,
			} as DOMRect;
		};
	}
}

function Split({ storageKey }: { storageKey?: string }) {
	return (
		<ResizablePanelGroup storageKey={storageKey}>
			<ResizablePanel defaultSize={30} minSize={20} maxSize={60} collapsible>
				a
			</ResizablePanel>
			<ResizableHandle />
			<ResizablePanel>b</ResizablePanel>
		</ResizablePanelGroup>
	);
}

describe("Resizable", () => {
	it("shares what the given defaults leave equally", () => {
		mount(
			<ResizablePanelGroup>
				<ResizablePanel defaultSize={40}>a</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel>b</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel>c</ResizablePanel>
			</ResizablePanelGroup>,
		);
		expect(panels().map(grow)).toEqual([40, 30, 30]);
	});

	it("is a focusable separator that reports the panel before it", () => {
		mount(<Split />);
		const h = handle();
		expect(h.getAttribute("role")).toBe("separator");
		expect(h.getAttribute("aria-orientation")).toBe("vertical");
		expect(h.tabIndex).toBe(0);
		expect(h.getAttribute("aria-valuenow")).toBe("30");
		expect(h.getAttribute("aria-valuemax")).toBe("60");
		expect(h.getAttribute("aria-controls")).toBe(panels()[0].id);
	});

	it("steps with the arrows and stops at the bounds", () => {
		mount(<Split />);
		const h = handle();
		press(h, "ArrowRight");
		expect(h.getAttribute("aria-valuenow")).toBe("35");
		press(h, "End");
		expect(panels().map(grow)).toEqual([60, 40]);
		press(h, "ArrowRight");
		expect(grow(panels()[0])).toBe(60);
		// An arrow never folds: it stops at the minimum.
		for (let i = 0; i < 10; i++) press(h, "ArrowLeft");
		expect(grow(panels()[0])).toBe(20);
	});

	it("folds a collapsible panel with Enter and brings it back", () => {
		mount(<Split />);
		const h = handle();
		press(h, "Enter");
		expect(grow(panels()[0])).toBe(0);
		expect(panels()[0].dataset.state).toBe("collapsed");
		press(h, "Enter");
		expect(grow(panels()[0])).toBe(30);
		expect(panels()[0].dataset.state).toBe("expanded");
	});

	it("drags a border and resets on double-click", () => {
		mount(<Split />);
		layOut(1000);
		const h = handle();
		act(() => {
			h.dispatchEvent(new MouseEvent("pointerdown", { bubbles: true, button: 0, clientX: 300 }));
		});
		act(() => {
			window.dispatchEvent(new MouseEvent("pointermove", { clientX: 400 }));
		});
		expect(grow(panels()[0])).toBeCloseTo(40);
		expect(h.hasAttribute("data-dragging")).toBe(true);
		act(() => {
			window.dispatchEvent(new MouseEvent("pointerup", { clientX: 400 }));
		});
		expect(h.hasAttribute("data-dragging")).toBe(false);
		act(() => {
			h.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		});
		expect(panels().map(grow)).toEqual([30, 70]);
	});

	it("keeps the layout under its storage key", () => {
		mount(<Split storageKey="t.split" />);
		press(handle(), "ArrowRight");
		act(() => root.unmount());
		root = createRoot(host);
		mount(<Split storageKey="t.split" />);
		expect(panels().map(grow)).toEqual([35, 65]);
	});

	it("keeps each panel's size through a reorder, and resets when one goes", () => {
		const Three = ({ order }: { order: string[] }) => (
			<ResizablePanelGroup>
				{order.flatMap((id, i) => [
					i > 0 ? <ResizableHandle key={`h-${id}`} /> : null,
					<ResizablePanel key={id} id={id}>
						{id}
					</ResizablePanel>,
				])}
			</ResizablePanelGroup>
		);
		mount(<Three order={["a", "b", "c"]} />);
		press(handle(0), "ArrowRight");
		const sized = panels().map(grow);
		mount(<Three order={["c", "a", "b"]} />);
		expect(panels().map((el) => el.id)).toEqual(["c", "a", "b"]);
		expect(panels().map(grow)).toEqual([sized[2], sized[0], sized[1]]);
		mount(<Three order={["a", "b"]} />);
		expect(panels().map(grow)).toEqual([50, 50]);
	});

	it("ignores a stored layout that no longer fits", () => {
		window.localStorage.setItem("t.split", "[10, 20, 70]");
		mount(<Split storageKey="t.split" />);
		expect(panels().map(grow)).toEqual([30, 70]);
	});

	describe("overflow scroll", () => {
		function Desk() {
			return (
				<ResizablePanelGroup overflow="scroll">
					<ResizablePanel minSize="400px">a</ResizablePanel>
					<ResizableHandle />
					<ResizablePanel minSize="400px">b</ResizablePanel>
				</ResizablePanelGroup>
			);
		}

		/** The group shows `width` px; each panel is its share of it. */
		function layOutDesk(width: number) {
			const group = host.querySelector<HTMLElement>("[data-slot=resizable-panel-group]");
			if (group) Object.defineProperty(group, "clientWidth", { value: width, configurable: true });
			layOut(width);
		}

		it("scrolls along its axis and never shrinks a panel", () => {
			mount(<Desk />);
			const group = host.querySelector<HTMLElement>("[data-slot=resizable-panel-group]");
			expect(group?.className).toContain("overflow-x-auto");
			expect(panels()[0].style.flexShrink).toBe("0");
			expect(panels()[0].style.minWidth).toBe("400px");
		});

		it("grows the content when a drag passes the neighbour's minimum", () => {
			mount(<Desk />);
			layOutDesk(1000);
			const h = handle();
			act(() => {
				h.dispatchEvent(new MouseEvent("pointerdown", { bubbles: true, button: 0, clientX: 500 }));
			});
			act(() => {
				window.dispatchEvent(new MouseEvent("pointermove", { clientX: 800 }));
			});
			act(() => {
				window.dispatchEvent(new MouseEvent("pointerup", { clientX: 800 }));
			});
			// a took all 300px it asked for; b stopped at its 400px floor.
			expect(grow(panels()[0])).toBeCloseTo(80);
			expect(grow(panels()[1])).toBeCloseTo(40);
		});

		it("has no ceiling without a maxSize, so End does nothing", () => {
			mount(<Desk />);
			const h = handle();
			expect(h.hasAttribute("aria-valuemax")).toBe(false);
			press(h, "End");
			expect(panels().map(grow)).toEqual([50, 50]);
			press(h, "ArrowRight");
			expect(panels().map(grow)).toEqual([55, 45]);
		});
	});

	describe("px sizes", () => {
		// A group `width` px long that a ResizeObserver reports on demand.
		let width = 1000;
		let resized: (() => void) | null = null;
		const rect = HTMLElement.prototype.getBoundingClientRect;
		const observer = globalThis.ResizeObserver;

		beforeEach(() => {
			width = 1000;
			HTMLElement.prototype.getBoundingClientRect = function (this: HTMLElement) {
				if (this.dataset.slot !== "resizable-panel") return rect.call(this);
				const w = (grow(this) / 100) * width;
				return {
					width: w,
					height: 100,
					x: 0,
					y: 0,
					top: 0,
					left: 0,
					right: w,
					bottom: 100,
				} as DOMRect;
			};
			globalThis.ResizeObserver = class {
				constructor(cb: ResizeObserverCallback) {
					resized = () => cb([], this as unknown as ResizeObserver);
				}
				observe() {}
				unobserve() {}
				disconnect() {}
			} as unknown as typeof ResizeObserver;
		});

		afterEach(() => {
			HTMLElement.prototype.getBoundingClientRect = rect;
			globalThis.ResizeObserver = observer;
			resized = null;
		});

		function resize(to: number) {
			width = to;
			act(() => resized?.());
		}

		function Sidebar({ storageKey }: { storageKey?: string }) {
			return (
				<ResizablePanelGroup storageKey={storageKey}>
					<ResizablePanel id="side" defaultSize="250px" minSize="200px" maxSize="500px" collapsible>
						side
					</ResizablePanel>
					<ResizableHandle />
					<ResizablePanel id="main">main</ResizablePanel>
				</ResizablePanelGroup>
			);
		}

		it("resolves a px default and holds it while the group resizes", () => {
			mount(<Sidebar />);
			expect(grow(panels()[0])).toBeCloseTo(25);
			resize(2000);
			expect(grow(panels()[0])).toBeCloseTo(12.5);
			// A step is 5% of 2000px: the sidebar is 350px now, and stays so.
			press(handle(), "ArrowRight");
			resize(1000);
			expect(grow(panels()[0])).toBeCloseTo(35);
			expect(grow(panels()[1])).toBeCloseTo(65);
		});

		it("keeps the fold and the width to unfold to across a remount", () => {
			mount(<Sidebar storageKey="t.side" />);
			press(handle(), "ArrowRight");
			press(handle(), "Enter");
			expect(panels()[0].dataset.state).toBe("collapsed");
			expect(panels()[0].hasAttribute("inert")).toBe(true);
			act(() => root.unmount());
			root = createRoot(host);
			width = 2000;
			mount(<Sidebar storageKey="t.side" />);
			expect(grow(panels()[0])).toBe(0);
			expect(panels()[0].hasAttribute("inert")).toBe(true);
			// Folded at 300px of 1000, it opens to 300px of 2000.
			press(handle(), "Enter");
			expect(panels()[0].hasAttribute("inert")).toBe(false);
			expect(grow(panels()[0])).toBeCloseTo(15);
		});
	});
});
