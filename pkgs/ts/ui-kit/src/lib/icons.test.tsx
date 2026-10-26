// Icons by name: every lucide name draws, an unknown one is null at once, and
// a glyph holds its size empty until its drawing lands.

import dynamicIconImports from "lucide-react/dynamicIconImports";
import { act, createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ICON_NAMES, iconFor, isIconName } from "./icons";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.append(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

describe("icons", () => {
	it("knows every lucide name, older ones included, and nothing else", () => {
		expect(ICON_NAMES.length).toBeGreaterThan(1500);
		for (const name of ["palette", "briefcase", "house", "home", "text-wrap"]) {
			expect(isIconName(name)).toBe(true);
		}
		for (const name of ["", "🚀", "Palette", "no-such-glyph"]) expect(isIconName(name)).toBe(false);
	});

	it("answers null for an unknown name, warning once", () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
		expect(iconFor("")).toBeNull();
		expect(iconFor("no-such-glyph")).toBeNull();
		expect(iconFor("no-such-glyph")).toBeNull();
		expect(warn).toHaveBeenCalledTimes(1);
		warn.mockRestore();
	});

	it("hands out one component per name", () => {
		expect(iconFor("palette")).toBe(iconFor("palette"));
	});

	it("draws an empty svg of its size, then the glyph", async () => {
		const Palette = iconFor("palette");
		if (!Palette) throw new Error("palette is a lucide name");
		act(() => root.render(createElement(Palette, { className: "size-4" })));
		const svg = host.querySelector("svg");
		expect(svg?.getAttribute("class")).toContain("size-4");
		expect(svg?.childElementCount).toBe(0);
		// The same module the glyph asked for: once it is in, so is the drawing.
		await act(() => dynamicIconImports.palette());
		expect(host.querySelector("svg path")).not.toBeNull();
		expect(host.querySelector("svg")?.getAttribute("class")).toContain("lucide-palette");
	});
});
