// Chrome containers over the real tree store: Card's surface, its named
// slots (media, action, footer) and its whole-card link, Box's pad and
// grounds, Tabs' strip variant.

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

	it("still reads the old footer prop and set_footer op as the caption", () => {
		tree.getState().write([["c", "Card", { footer: "old" }]]);
		draw("c");
		expect(slot("card-footer")?.textContent).toBe("old");
		act(() => tree.getState().dispatch({ op: "set_footer", ref: ["c"], payload: "older" }));
		expect(slot("card-footer")?.textContent).toBe("older");
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

describe("Box", () => {
	it("draws padding none with no pad", () => {
		tree.getState().write([["b", "Box", { padding: "none" }]]);
		draw("b");
		expect(cls(slot("panel"))).toContain("[--panel-pad:0px]");
		expect(cls(slot("panel"))).not.toContain("[--panel-pad:0.5rem]");
	});

	it("pads sm as sm", () => {
		tree.getState().write([["b", "Box", { padding: "sm" }]]);
		draw("b");
		expect(cls(slot("panel"))).toContain("[--panel-pad:0.5rem]");
	});

	it("gives each ground its own fill", () => {
		const fills: Record<string, string> = {
			muted: "bg-bg-hover",
			sunken: "bg-bg-sunken",
			accent: "bg-accent-2-wash",
			brand: "bg-accent-soft",
		};
		for (const [ground, fill] of Object.entries(fills)) {
			tree.getState().write([[ground, "Box", { background: ground }]]);
			draw(ground);
			expect(cls(slot("panel"))).toContain(fill);
		}
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
