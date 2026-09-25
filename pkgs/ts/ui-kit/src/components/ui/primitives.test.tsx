// The primitives that carry behaviour beyond their classes: which parts an
// EmptyState draws, how a StatusDot names itself, that a ref reaches the
// element through Input and TextArea, and that an OverflowTooltip only opens
// over text that is actually cut off.

import { act, createRef } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { EmptyState } from "./empty-state";
import { Input } from "./input";
import { OverflowTooltip } from "./overflow-tooltip";
import { StatusDot } from "./status-dot";
import { TextArea } from "./text-area";
import { TooltipProvider } from "./tooltip";

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
});
