// IconRef and PageLinkRef over the real tree store: a glyph by name on the
// size and tone ladders, inline in a Line, and a page link that is a real
// anchor with an icon or an emoji for its mark.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

type Step = [string, string, Record<string, unknown>?];

function draw(...chain: Step[]) {
	act(() => {
		tree
			.getState()
			.write(chain.map(([seg, type, props]) => (props ? [seg, type, props] : [seg, type])));
		root.render(<NodeView path={[chain[0][0]]} />);
	});
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
	vi.restoreAllMocks();
});

describe("IconRef", () => {
	it("draws the named glyph on the size and tone ladders, decorative by default", () => {
		draw(["i", "IconRef", { name: "rocket", size: "lg", tone: "accent" }]);
		const svg = q("[data-slot=icon]");
		expect(svg?.tagName.toLowerCase()).toBe("svg");
		expect(svg?.getAttribute("class")).toContain("size-5");
		expect(svg?.getAttribute("class")).toContain("text-accent-text");
		expect(svg?.getAttribute("aria-hidden")).toBe("true");
	});

	it("takes a label as its accessible name, and frames in a tinted square", () => {
		draw(["i", "IconRef", { name: "circle-check", tone: "ok", framed: true, label: "Done" }]);
		expect(q("[data-slot=icon-frame]")?.className).toContain("bg-status-ok-wash");
		expect(q("[data-slot=icon]")?.getAttribute("aria-label")).toBe("Done");
	});

	it("sits on the baseline at text size in a Line", () => {
		draw(["l", "Line"], ["i", "IconRef", { name: "check", size: "xl" }]);
		expect(q("[data-slot=icon]")?.getAttribute("class")).toContain("size-[1em]");
	});

	it("draws nothing for an unknown name, and warns", () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
		draw(["i", "IconRef", { name: "no-such-glyph" }]);
		expect(host.innerHTML).toBe("");
		expect(warn).toHaveBeenCalledOnce();
	});
});

describe("PageLinkRef", () => {
	it("is a real link with an icon mark, title, description and meta", () => {
		draw([
			"p",
			"PageLinkRef",
			{ href: "/notes", title: "Notes", icon: "book-open", description: "All of them", meta: "2d" },
		]);
		const a = q("[data-slot=page-link]");
		expect(a?.tagName).toBe("A");
		expect(a?.getAttribute("href")).toBe("/notes");
		expect(a?.dataset.variant).toBe("row");
		expect(q("[data-slot=page-link-mark] svg")).not.toBeNull();
		expect(q("[data-slot=page-link-title]")?.textContent).toBe("Notes");
		expect(q("[data-slot=page-link-description]")?.textContent).toBe("All of them");
		expect(q("[data-slot=page-link-meta]")?.textContent).toBe("2d");
	});

	it("draws an emoji mark as text, without warning, and a tile when asked", () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
		draw(["p", "PageLinkRef", { href: "/r", title: "Roadmap", icon: "🗺️", variant: "tile" }]);
		expect(q("[data-slot=page-link-mark]")?.textContent).toBe("🗺️");
		expect(q("[data-slot=page-link]")?.dataset.variant).toBe("tile");
		expect(warn).not.toHaveBeenCalled();
	});

	it("has no mark with no icon, shows its href with no title, and opens _blank safely", () => {
		draw(["p", "PageLinkRef", { href: "https://example.com", target: "_blank" }]);
		expect(q("[data-slot=page-link-mark]")).toBeNull();
		expect(q("[data-slot=page-link-title]")?.textContent).toBe("https://example.com");
		expect(q("[data-slot=page-link]")?.getAttribute("rel")).toBe("noopener noreferrer");
	});
	it("frames a glyph once, the Icon frame being the mark's square", () => {
		draw(["p", "PageLinkRef", { href: "/n", title: "Notes", icon: "book-open" }]);
		const mark = q("[data-slot=page-link-mark]");
		expect(mark?.querySelectorAll("[data-slot=icon-frame]")).toHaveLength(1);
		expect(mark?.className).not.toContain("bg-bg-sunken");
		expect(q("[data-slot=page-link]")?.className).toContain("cursor-default");
		expect(q("[data-slot=page-link]")?.className).toContain("focus-ring");
	});

	it("hides a text mark from screen readers, the title naming the link", () => {
		draw(["p", "PageLinkRef", { href: "/r", title: "Roadmap", icon: "🗺️" }]);
		expect(q("[data-slot=page-link-mark]")?.getAttribute("aria-hidden")).toBe("true");
	});

	it("draws a tile at level 0: the default line at rest", () => {
		draw(["p", "PageLinkRef", { href: "/r", title: "Roadmap", variant: "tile" }]);
		const cls = q("[data-slot=page-link]")?.className ?? "";
		expect(cls).toContain("border-border-default");
		expect(cls).toContain("hover:border-border-strong");
		expect(cls).not.toContain("hover:bg-bg-hover");
	});

	it("draws inline as a mention: mark and title only, unframed, its own width", () => {
		draw([
			"p",
			"PageLinkRef",
			{
				href: "/r",
				title: "Roadmap",
				icon: "🗺️",
				description: "dropped",
				meta: "dropped",
				variant: "inline",
			},
		]);
		const a = q("[data-slot=page-link]");
		expect(a?.dataset.variant).toBe("inline");
		expect(a?.textContent).toBe("🗺️Roadmap");
		expect(q("[data-slot=page-link-mark]")?.getAttribute("aria-hidden")).toBe("true");
		expect(q("[data-slot=page-link-title]")?.className).toContain("decoration-border-subtle");
		expect(q("[data-slot=page-link-description]")).toBeNull();
		expect(q("[data-slot=page-link-meta]")).toBeNull();
		// Content in a block flow: a cell keeps it at its own width.
		draw(["c", "Column"], ["p", "PageLinkRef", { href: "/r", title: "R", variant: "inline" }]);
		expect(q("[data-slot=block-cell] [data-slot=page-link]")).not.toBeNull();
	});

	it("runs with the text in a Line, a glyph at text size", () => {
		draw(
			["l", "Line"],
			["p", "PageLinkRef", { href: "/n", title: "Notes", icon: "book-open", variant: "inline" }],
		);
		expect(q("[data-slot=page-link]")?.className).toContain("inline");
		expect(q("[data-slot=icon-frame]")).toBeNull();
		expect(q("[data-slot=icon]")?.getAttribute("class")).toContain("size-[1em]");
	});
});
