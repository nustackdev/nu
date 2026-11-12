// Chrome containers over the real tree store: Card's surface, its named
// slots (media, action, footer) and its whole-card link, its variants and
// size preset, Tabs' strip variant.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

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
	tree.getState().remove([]);
});

function child(
	parent: [string, string, Record<string, unknown>],
	seg: string,
	type: string,
	props = {},
) {
	tree.getState().write([parent, [seg, type, props]]);
}

function draw(seg: string) {
	act(() => root.render(<NodeView path={[seg]} />));
}

const slot = (name: string, from: ParentNode = host) =>
	from.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

describe("Card", () => {
	it("takes the primitive's variant and size", () => {
		tree.getState().write([["c", "Card", { title: "T", variant: "elevated", size: "lg" }]]);
		draw("c");
		const card = slot("card");
		expect(cls(card)).toContain("shadow-raised");
		expect(card?.getAttribute("data-size")).toBe("lg");
	});

	it("draws media, actions and footer in their places, the rest as body", () => {
		const card: [string, string, Record<string, unknown>] = ["c", "Card", { title: "Pro" }];
		child(card, "price", "TextRef", { value: "$9" });
		child(card, "footer", "ButtonRef", { label: "Choose" });
		child(card, "actions", "BadgeRef", { label: "Popular" });
		child(card, "media", "ImageRef", { src: "/a.png", alt: "" });
		draw("c");
		const el = slot("card");
		const parts = [...(el?.children ?? [])].map((el) => el.getAttribute("data-slot"));
		expect(parts).toEqual(["card-media", "card-header", "card-content", "card-footer"]);
		expect(slot("image", slot("card-media") as HTMLElement)).not.toBeNull();
		expect(slot("badge", slot("card-action") as HTMLElement)?.textContent).toBe("Popular");
		expect(slot("card-content")?.textContent).toBe("$9");
		const footer = slot("card-footer");
		expect(slot("button", footer as HTMLElement)?.textContent).toBe("Choose");
		// Pinned to the bottom, so stretched cards line their footers up.
		expect(cls(footer)).toContain("mt-auto");
		expect(cls(slot("card-content"))).toContain("flex-1");
		expect(cls(el)).toContain("overflow-hidden");
	});

	it("draws the caption, under a footer child when there is one", () => {
		tree.getState().write([["c", "Card", { caption: "updated 2m ago" }]]);
		draw("c");
		expect(cls(slot("card-footer"))).toContain("border-t");
		expect(slot("card-footer")?.textContent).toBe("updated 2m ago");
		act(() => child(["c", "Card", {}], "footer", "ButtonRef", { label: "Go" }));
		const footer = slot("card-footer");
		expect(footer?.textContent).toBe("Goupdated 2m ago");
		expect(cls(footer)).not.toContain("border-t");
	});

	it("draws a header for actions alone", () => {
		const card: [string, string, Record<string, unknown>] = ["c", "Card", {}];
		child(card, "actions", "ButtonRef", { label: "", icon: "x" });
		draw("c");
		expect(slot("card-action")).not.toBeNull();
	});

	it("is one interactive link with an href", () => {
		tree
			.getState()
			.write([["c", "Card", { title: "Docs", href: "https://example.com", target: "_blank" }]]);
		draw("c");
		const card = slot("card");
		expect(card?.tagName).toBe("A");
		expect(card?.getAttribute("href")).toBe("https://example.com");
		expect(card?.getAttribute("rel")).toBe("noopener noreferrer");
		expect(cls(card)).toContain("hover:border-border-strong");
	});
});

describe("Card surfaces", () => {
	it("gives each variant its own surface", () => {
		const looks: Record<string, string> = {
			sunken: "bg-bg-sunken",
			elevated: "shadow-raised",
			outline: "bg-transparent",
			plain: "border-transparent",
			accent: "bg-accent-2-wash",
			brand: "bg-accent-soft",
		};
		for (const [variant, look] of Object.entries(looks)) {
			tree.getState().write([[variant, "Card", { variant }]]);
			draw(variant);
			expect(cls(slot("card"))).toContain(look);
		}
	});

	it("takes the size preset for its pad", () => {
		tree.getState().write([["c", "Card", { size: "sm" }]]);
		draw("c");
		expect(cls(slot("card"))).toContain("[--card-pad:0.75rem]");
	});
});

describe("Tabs", () => {
	const tabs = [
		{ id: "a", label: "A" },
		{ id: "b", label: "B" },
	];

	it("draws a line strip by default", () => {
		tree.getState().write([["t", "Tabs", { tabs }]]);
		draw("t");
		expect(slot("tabs-list")?.getAttribute("data-variant")).toBe("line");
	});

	it("takes pill and segmented, reading anything else as line", () => {
		tree.getState().write([["t", "Tabs", { tabs, variant: "segmented" }]]);
		draw("t");
		expect(slot("tabs-list")?.getAttribute("data-variant")).toBe("segmented");
		expect(cls(slot("tabs-list"))).toContain("self-start");
		act(() => tree.getState().dispatch({ op: "write", ref: ["t"], payload: { variant: "zig" } }));
		expect(slot("tabs-list")?.getAttribute("data-variant")).toBe("line");
	});
});
