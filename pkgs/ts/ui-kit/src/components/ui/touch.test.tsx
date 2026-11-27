// Touch mode: that the signal is read from the device once and marks the
// document, that a TouchProvider forces it and puts the mark back, and that
// the reference overlay (Popover) renders a bottom sheet in touch mode and
// the anchored popover outside it, from the same parts.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TOUCH_ATTR, TOUCH_QUERY, TouchProvider } from "../../lib/touch";
import { Popover, PopoverArrow, PopoverContent, PopoverTrigger } from "./popover";

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
	document.body.innerHTML = "";
});

const html = () => document.documentElement;

describe("detection", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
		vi.resetModules();
		html().removeAttribute(TOUCH_ATTR);
	});

	const load = async (matches: boolean) => {
		const query = vi.fn((q: string) => ({ matches: matches && q === TOUCH_QUERY }));
		vi.stubGlobal("matchMedia", query);
		vi.resetModules();
		const mod = await import("../../lib/touch");
		return { mod, query };
	};

	it("reads a coarse, no-hover pointer as touch and marks the document", async () => {
		const { mod, query } = await load(true);
		expect(mod.touchDevice).toBe(true);
		expect(query).toHaveBeenCalledWith(TOUCH_QUERY);
		expect(html().hasAttribute(TOUCH_ATTR)).toBe(true);
	});

	it("leaves a fine pointer on desktop", async () => {
		const { mod } = await load(false);
		expect(mod.touchDevice).toBe(false);
		expect(html().hasAttribute(TOUCH_ATTR)).toBe(false);
	});
});

describe("TouchProvider", () => {
	it("marks the document while mounted and restores it after", () => {
		expect(html().hasAttribute(TOUCH_ATTR)).toBe(false);
		act(() => root.render(<TouchProvider value={true} />));
		expect(html().hasAttribute(TOUCH_ATTR)).toBe(true);
		act(() => root.render(<span />));
		expect(html().hasAttribute(TOUCH_ATTR)).toBe(false);
	});
});

describe("Popover", () => {
	// Radix's popper measures with ResizeObserver, which jsdom lacks.
	beforeEach(() => {
		vi.stubGlobal(
			"ResizeObserver",
			class {
				observe() {}
				unobserve() {}
				disconnect() {}
			},
		);
	});
	afterEach(() => vi.unstubAllGlobals());

	const popover = (
		<Popover defaultOpen>
			<PopoverTrigger>open</PopoverTrigger>
			<PopoverContent side="top" className="w-80 p-2">
				body
				<PopoverArrow />
			</PopoverContent>
		</Popover>
	);

	it("is anchored floating content on desktop", () => {
		act(() => root.render(popover));
		expect(document.querySelector('[data-slot="popover-content"]')).not.toBeNull();
		expect(document.querySelector('[data-slot="bottom-sheet-content"]')).toBeNull();
	});

	it("is a bottom sheet in touch mode, from the same parts", () => {
		act(() => root.render(<TouchProvider value={true}>{popover}</TouchProvider>));
		const sheet = document.querySelector('[data-slot="bottom-sheet-content"]');
		expect(sheet).not.toBeNull();
		expect(sheet?.getAttribute("role")).toBe("dialog");
		expect(sheet?.textContent).toContain("body");
		// The caller's classes style the body, its width yields to the sheet.
		const body = sheet?.querySelector('[data-slot="bottom-sheet-body"]');
		expect(body?.className).toContain("p-2");
		expect(body?.className).not.toContain("w-80");
		expect(document.querySelector('[data-slot="popover-content"]')).toBeNull();
	});
});
