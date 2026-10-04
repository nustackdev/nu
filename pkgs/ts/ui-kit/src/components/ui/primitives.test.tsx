// The primitives that carry behaviour beyond their classes: which parts an
// EmptyState draws, how a StatusDot names itself, that a ref reaches the
// element through Input and TextArea, and that an OverflowTooltip only opens
// over text that is actually cut off, without breaking the delay of the
// tooltips around it.

import { act, createRef } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EmptyState } from "./empty-state";
import { Input } from "./input";
import { OverflowTooltip } from "./overflow-tooltip";
import { StatusDot } from "./status-dot";
import { TextArea } from "./text-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

// React 19 wants this before render or it logs a warning per test.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures the tooltip through ResizeObserver, which jsdom lacks.
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

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

describe("EmptyState", () => {
	it("draws only the parts it is given", () => {
		mount(<EmptyState>Nothing here yet</EmptyState>);
		const el = host.querySelector("[data-slot=empty-state]");
		expect(el?.textContent).toBe("Nothing here yet");
		expect(el?.children).toHaveLength(1);
	});

	it("puts the description and the action under the line", () => {
		mount(
			<EmptyState
				icon={<svg />}
				description="Create one to start"
				action={<button type="button">New</button>}
			>
				No planes
			</EmptyState>,
		);
		const parts = Array.from(host.querySelector("[data-slot=empty-state]")?.children ?? []);
		expect(parts.map((p) => p.textContent)).toEqual([
			"",
			"No planes",
			"Create one to start",
			"New",
		]);
	});
});

describe("StatusDot", () => {
	it("is a named image with a label", () => {
		mount(<StatusDot tone="ok" label="Connected" />);
		const dot = host.querySelector("[data-slot=status-dot]");
		expect(dot?.getAttribute("role")).toBe("img");
		expect(dot?.getAttribute("aria-label")).toBe("Connected");
		expect(dot?.getAttribute("data-tone")).toBe("ok");
	});

	it("is decoration without one", () => {
		mount(<StatusDot pulse />);
		const dot = host.querySelector("[data-slot=status-dot]");
		expect(dot?.getAttribute("aria-hidden")).toBe("true");
		expect(dot?.getAttribute("role")).toBeNull();
		expect(dot?.className).toContain("animate-pulse");
	});
});

describe("ref forwarding", () => {
	it("reaches the input element", () => {
		const ref = createRef<HTMLInputElement>();
		mount(<Input ref={ref} ring="inset" />);
		expect(ref.current).toBeInstanceOf(HTMLInputElement);
		expect(ref.current?.className).toContain("focus-visible:ring-inset");
		expect(ref.current?.className).not.toContain("ring-offset-2");
	});

	it("reaches the textarea element", () => {
		const ref = createRef<HTMLTextAreaElement>();
		mount(<TextArea ref={ref} />);
		expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
	});
});

describe("OverflowTooltip", () => {
	function mountLabel(overflowing: boolean) {
		mount(
			<TooltipProvider>
				<OverflowTooltip label="A title too long for its row">
					<button type="button" data-testid="label">
						A title too long for its row
					</button>
				</OverflowTooltip>
			</TooltipProvider>,
		);
		const label = host.querySelector<HTMLElement>("[data-testid=label]");
		if (!label) throw new Error("no label");
		Object.defineProperty(label, "clientWidth", { value: 100, configurable: true });
		Object.defineProperty(label, "scrollWidth", {
			value: overflowing ? 240 : 100,
			configurable: true,
		});
		act(() => label.focus());
		return label;
	}

	it("opens over text the ellipsis cuts off", () => {
		mountLabel(true);
		expect(document.querySelector("[data-slot=tooltip-content]")).not.toBeNull();
	});

	it("stays shut over text that fits", () => {
		mountLabel(false);
		expect(document.querySelector("[data-slot=tooltip-content]")).toBeNull();
	});

	it("leaves the provider's delay alone when it stays shut", () => {
		vi.useFakeTimers();
		try {
			mount(
				<TooltipProvider>
					<OverflowTooltip label="Fits">
						<button type="button" data-testid="fits">
							Fits
						</button>
					</OverflowTooltip>
					<Tooltip>
						<TooltipTrigger asChild>
							<button type="button" data-testid="other">
								Other
							</button>
						</TooltipTrigger>
						<TooltipContent>Other tip</TooltipContent>
					</Tooltip>
				</TooltipProvider>,
			);
			const fits = host.querySelector<HTMLElement>("[data-testid=fits]");
			const other = host.querySelector<HTMLElement>("[data-testid=other]");
			if (!fits || !other) throw new Error("no triggers");
			const tip = () => document.querySelector("[data-slot=tooltip-content]");
			const move = (el: HTMLElement) =>
				act(() => {
					el.dispatchEvent(new MouseEvent("pointerover", { bubbles: true }));
					el.dispatchEvent(new MouseEvent("pointermove", { bubbles: true }));
				});
			const leave = (el: HTMLElement) =>
				act(() => {
					el.dispatchEvent(
						new MouseEvent("pointerout", { bubbles: true, relatedTarget: document.body }),
					);
				});
			const wait = (ms: number) => act(() => vi.advanceTimersByTime(ms));

			// Rest on the label that fits past the delay, leave, and wait out the
			// skip window.
			move(fits);
			wait(1000);
			expect(tip()).toBeNull();
			leave(fits);
			wait(1000);

			// The next tooltip still waits its delay.
			move(other);
			expect(tip()).toBeNull();
			wait(1000);
			expect(tip()?.textContent).toContain("Other tip");
		} finally {
			vi.useRealTimers();
		}
	});
});

describe("Tooltip", () => {
	// Three controls in a row, 24px apart, each with a hint below it far wider
	// than the control, as on a sidebar row. jsdom lays nothing out, so the
	// boxes are given.
	const X: Record<string, number> = { a: 0, b: 25, c: 50 };
	function boxOf(el: Element): DOMRect {
		const content = el.closest("[data-slot=tooltip-content]");
		if (content) {
			const x = X[content.getAttribute("data-k") ?? "a"];
			return new DOMRect(x - 53, 28, 130, 22);
		}
		const k = el.closest("[data-k]")?.getAttribute("data-k");
		return k ? new DOMRect(X[k], 0, 24, 24) : new DOMRect(0, 0, 0, 0);
	}

	function mountRow() {
		vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (
			this: Element,
		) {
			return boxOf(this);
		});
		mount(
			<TooltipProvider>
				{["a", "b", "c"].map((k) => (
					<Tooltip key={k}>
						<TooltipTrigger asChild>
							<button type="button" data-k={k}>
								{k}
							</button>
						</TooltipTrigger>
						<TooltipContent side="bottom" data-k={k}>
							{`${k} hint`}
						</TooltipContent>
					</Tooltip>
				))}
			</TooltipProvider>,
		);
		const el = (k: string) => host.querySelector(`button[data-k=${k}]`) as HTMLElement;
		const at = (type: string, target: Element, x: number, related?: Element, bubbles = true) =>
			target.dispatchEvent(
				new MouseEvent(type, { bubbles, clientX: x, clientY: 12, relatedTarget: related ?? null }),
			);
		// What a browser sends as the pointer crosses from `from` onto `to`.
		const cross = (from: Element | null, to: Element | null, x: number) =>
			act(() => {
				if (from) {
					at("pointerout", from, x, to ?? document.body);
					at("pointerleave", from, x, to ?? document.body, false);
				}
				if (to) {
					at("pointerover", to, x, from ?? document.body);
					at("pointerenter", to, x, from ?? document.body, false);
					at("pointermove", to, x);
				}
			});
		const shown = () =>
			[...document.querySelectorAll("[data-slot=tooltip-content]")].map((n) =>
				n.getAttribute("data-k"),
			);
		return { el, cross, shown };
	}

	it("hands over to the next control at once", () => {
		vi.useFakeTimers();
		try {
			const { el, cross, shown } = mountRow();
			cross(null, el("a"), 12);
			act(() => vi.advanceTimersByTime(1000));
			expect(shown()).toEqual(["a"]);
			// Straight onto the neighbour, inside the skip window.
			cross(el("a"), el("b"), 26);
			expect(shown()).toEqual(["b"]);
			cross(el("b"), el("c"), 51);
			expect(shown()).toEqual(["c"]);
		} finally {
			vi.useRealTimers();
			vi.restoreAllMocks();
		}
	});

	it("waits the full delay again once the skip window has passed", () => {
		vi.useFakeTimers();
		try {
			const { el, cross, shown } = mountRow();
			cross(null, el("a"), 12);
			act(() => vi.advanceTimersByTime(1000));
			cross(el("a"), null, 12);
			expect(shown()).toEqual([]);
			act(() => vi.advanceTimersByTime(1000));
			cross(null, el("b"), 37);
			expect(shown()).toEqual([]);
			act(() => vi.advanceTimersByTime(1000));
			expect(shown()).toEqual(["b"]);
		} finally {
			vi.useRealTimers();
			vi.restoreAllMocks();
		}
	});
});
