// Content nodes over the real tree store: TextRef and HeadingRef type,
// LinkRef looks, ImageRef corners and ratio, EmptyStateRef's icon and way
// out, BadgeRef's brand tones and sizes, DividerRef's label align.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";
import { normAspect } from "./image";
import { clampLines } from "./text";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(op: string, payload: unknown) {
	act(() => tree.getState().dispatch({ op, ref: ["n"], payload }));
}

const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

describe("TextRef", () => {
	it("draws the defaults when no style prop is set", () => {
		mount("TextRef", { value: "hi" });
		const p = slot("text");
		expect(p?.tagName).toBe("P");
		expect(cls(p)).toEqual(expect.arrayContaining(["text-base", "text-text-primary"]));
	});

	it("takes tone, size, weight, mono and align", () => {
		mount("TextRef", {
			value: "v0.6",
			tone: "muted",
			size: "sm",
			weight: "semibold",
			mono: true,
			align: "center",
		});
		expect(cls(slot("text"))).toEqual(
			expect.arrayContaining([
				"text-text-muted",
				"text-sm",
				"font-semibold",
				"font-mono",
				"text-center",
				"w-full",
			]),
		);
	});

	it("reads an unknown tone as primary and right as end", () => {
		mount("TextRef", { value: "x", tone: "loud", align: "right" });
		expect(cls(slot("text"))).toEqual(expect.arrayContaining(["text-text-primary", "text-end"]));
	});

	it("keeps a bare write on the value and the style it had", () => {
		mount("TextRef", { value: "a", tone: "accent" });
		dispatch(OPS.write, "b");
		expect(slot("text")?.textContent).toBe("b");
		expect(cls(slot("text"))).toContain("text-accent-text");
		dispatch(OPS.write, { tone: "danger" });
		expect(cls(slot("text"))).toContain("text-status-danger");
	});

	it("clamps to one line with an ellipsis, or to n lines", () => {
		mount("TextRef", { value: "long", lines: 1 });
		expect(cls(slot("text"))).toEqual(
			expect.arrayContaining(["text-ellipsis", "whitespace-nowrap"]),
		);
		expect(cls(slot("text"))).not.toContain("whitespace-pre-wrap");
		expect(clampLines(3).style?.WebkitLineClamp).toBe(3);
		expect(clampLines(0)).toEqual({});
	});

	it("is a bare run in a Line, carrying only what it sets", () => {
		tree.getState().write([
			["n", "Line", {}],
			["t", "TextRef", { value: "run", tone: "muted" }],
		]);
		tree.getState().write([
			["n", "Line", {}],
			["u", "TextRef", { value: "plain" }],
		]);
		act(() => root.render(<NodeView path={["n"]} />));
		const [muted, plain] = host.querySelectorAll<HTMLElement>("span[data-slot=text]");
		expect(muted.className).toBe("text-text-muted");
		expect(plain.className).toBe("");
	});
});

describe("HeadingRef", () => {
	it("takes the level's size by default and display apart from the tag", () => {
		mount("HeadingRef", { label: "Plans", level: 2 });
		expect(cls(slot("heading"))).toContain("text-2xl");
		dispatch(OPS.write, { size: "display", level: 1 });
		const h = slot("heading");
		expect(h?.tagName).toBe("H1");
		expect(cls(h)).toEqual(expect.arrayContaining(["text-display", "font-bold"]));
	});

	it("keeps the display size under a tone", () => {
		mount("HeadingRef", { label: "Hero", size: "display", tone: "secondary" });
		expect(cls(slot("heading"))).toEqual(
			expect.arrayContaining(["text-display", "text-text-secondary"]),
		);
	});

	it("reads muted as primary: muted ink is for labels and hints", () => {
		mount("HeadingRef", { label: "Quiet", tone: "muted" });
		expect(cls(slot("heading"))).not.toContain("text-text-muted");
	});

	it("groups an eyebrow and a subtitle with the heading, sharing its align", () => {
		mount("HeadingRef", {
			label: "Pricing",
			eyebrow: "Plans",
			subtitle: "Pick one",
			align: "center",
		});
		const group = slot("heading-group");
		expect(group?.tagName).toBe("HGROUP");
		expect(cls(group)).toContain("text-center");
		expect(slot("heading-eyebrow")?.textContent).toBe("Plans");
		expect(slot("heading-subtitle")?.textContent).toBe("Pick one");
	});

	it("reads left as start and keeps the string shorthand", () => {
		mount("HeadingRef", { label: "a", align: "left" });
		expect(cls(slot("heading"))).toContain("text-start");
		dispatch(OPS.write, "b");
		expect(slot("heading")?.textContent).toBe("b");
	});
});

describe("LinkRef", () => {
	it("is a text link with the hand cursor by default", () => {
		mount("LinkRef", { href: "/docs", label: "Docs" });
		const a = slot("link");
		expect(a?.getAttribute("data-variant")).toBe("text");
		expect(cls(a)).toEqual(expect.arrayContaining(["text-accent-2", "cursor-pointer"]));
	});

	it("draws a muted link in the secondary ink", () => {
		mount("LinkRef", { href: "/a", label: "a", variant: "muted" });
		expect(cls(slot("link"))).toContain("text-text-secondary");
	});

	it("draws a button look as an anchor with the button's classes and size", () => {
		mount("LinkRef", { href: "/start", label: "Start", variant: "button", size: "lg" });
		const a = slot("link");
		expect(a?.tagName).toBe("A");
		expect(a?.getAttribute("href")).toBe("/start");
		expect(cls(a)).toEqual(expect.arrayContaining(["bg-accent", "h-10", "cursor-default"]));
		dispatch(OPS.write, { variant: "outline" });
		expect(cls(slot("link"))).toContain("border-border-default");
	});

	it("draws a leading icon and a trailing arrow in place of the external glyph", () => {
		mount("LinkRef", {
			href: "https://example.com",
			label: "Out",
			icon: "sparkles",
			arrow: true,
			target: "_blank",
		});
		const svgs = [...(slot("link")?.querySelectorAll("svg") ?? [])];
		expect(svgs.map((s) => s.classList.contains("lucide-arrow-right"))).toEqual([false, true]);
		expect(slot("link")?.querySelector(".lucide-external-link")).toBeNull();
	});
});

describe("ImageRef", () => {
	it("maps the old rounded bool when radius is unset", () => {
		mount("ImageRef", { src: "/a.png", rounded: true });
		expect(cls(slot("image"))).toContain("rounded-md");
		dispatch(OPS.write, { radius: "full" });
		expect(cls(slot("image"))).toContain("rounded-full");
	});

	it("holds an aspect ratio and takes the full width for it", () => {
		mount("ImageRef", { src: "/a.png", aspect: "16:9", fit: "scale-down" });
		const img = slot("image");
		expect(img?.style.aspectRatio).toBe("16 / 9");
		expect(img?.style.width).toBe("100%");
		expect(cls(img)).toContain("object-scale-down");
	});

	it("reads the aspect spellings", () => {
		expect(normAspect("4/3")).toBe("4 / 3");
		expect(normAspect("1.5")).toBe("1.5");
		expect(normAspect("")).toBeUndefined();
		expect(normAspect("wide")).toBeUndefined();
		expect(normAspect("1/0")).toBeUndefined();
	});
});

describe("EmptyStateRef", () => {
	it("draws the icon and a way out that notifies", () => {
		mount("EmptyStateRef", { label: "No planes", icon: "folder", action: "New plane" });
		const empty = slot("empty-state");
		expect(empty?.querySelector("svg")).not.toBeNull();
		const btn = slot("button");
		expect(btn?.tagName).toBe("BUTTON");
		expect(btn?.textContent).toBe("New plane");
		act(() => btn?.click());
		expect(sent.map((f) => [f.op, f.ref])).toEqual([[OPS.notify, ["n"]]]);
	});

	it("makes the way out a link with an href", () => {
		mount("EmptyStateRef", { label: "None", action: "Docs", action_href: "/docs" });
		const a = slot("button");
		expect(a?.tagName).toBe("A");
		expect(a?.getAttribute("href")).toBe("/docs");
	});

	it("draws no button without an action", () => {
		mount("EmptyStateRef", { label: "None" });
		expect(slot("button")).toBeNull();
	});
});

describe("BadgeRef", () => {
	it("draws the brand and secondary chips and a size", () => {
		mount("BadgeRef", { label: "New", variant: "brand", size: "lg" });
		expect(cls(slot("badge"))).toEqual(expect.arrayContaining(["bg-accent-soft", "text-sm"]));
		dispatch(OPS.write, { variant: "secondary" });
		expect(cls(slot("badge"))).toContain("bg-accent-2-wash");
	});
});

describe("DividerRef", () => {
	it("pulls the label to the start edge", () => {
		mount("DividerRef", { label: "Older", align: "start" });
		const [lead, tail] = slot("separator-labeled")?.querySelectorAll("[aria-hidden]") ?? [];
		expect(cls(lead)).toContain("w-4");
		expect(cls(tail)).toContain("flex-1");
	});

	it("reads right as end and centers by default", () => {
		mount("DividerRef", { label: "x", align: "right" });
		const [lead, tail] = slot("separator-labeled")?.querySelectorAll("[aria-hidden]") ?? [];
		expect(cls(lead)).toContain("flex-1");
		expect(cls(tail)).toContain("w-4");
	});
});
