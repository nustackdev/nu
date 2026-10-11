// Display leaves over the real tree store: each node draws from its declared
// props alone (the boot chain, no write), then again after a partial write
// merges one or two keys into them.

import { OPS } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { isFill, NodeView, tree } from "../../tree";
import { initials } from "./avatar";
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

function mount(type: string, props: Record<string, unknown>) {
	act(() => {
		tree.getState().write([["d", type, props]]);
		root.render(<NodeView path={["d"]} />);
	});
}

function write(payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: ["d"], payload });
	});
}

const q = (sel: string) => host.querySelector(sel) as HTMLElement | null;

describe("AvatarRef", () => {
	it("draws initials from the name when there is no image", () => {
		mount("AvatarRef", { src: "", name: "Ada Lovelace", size: "md" });
		const avatar = q("[data-slot=avatar]");
		expect(avatar?.getAttribute("role")).toBe("img");
		expect(avatar?.getAttribute("aria-label")).toBe("Ada Lovelace");
		expect(avatar?.className).toContain("size-8");
		expect(q("[data-slot=avatar-fallback]")?.textContent).toBe("AL");
	});

	it("merges a size and a new name", () => {
		mount("AvatarRef", { src: "", name: "Ada Lovelace", size: "md" });
		write({ name: "Grace", size: "xl" });
		expect(q("[data-slot=avatar]")?.className).toContain("size-12");
		expect(q("[data-slot=avatar-fallback]")?.textContent).toBe("G");
	});

	it("is decorative with a person glyph when it has no name", () => {
		mount("AvatarRef", { src: "", name: "", size: "zigzag" });
		const avatar = q("[data-slot=avatar]");
		expect(avatar?.getAttribute("role")).toBeNull();
		expect(avatar?.getAttribute("aria-hidden")).toBe("true");
		expect(avatar?.className).toContain("size-8");
		expect(q("[data-slot=avatar-fallback] svg")).not.toBeNull();
	});

	it("takes initials from the first and last word", () => {
		expect(initials("Grace Brewster Murray Hopper")).toBe("GH");
		expect(initials("  nu  ")).toBe("n");
		expect(initials("")).toBe("");
	});
});

describe("BreadcrumbRef", () => {
	const trail = [
		{ label: "Home", href: "/" },
		{ label: "Docs", href: "https://example.org/docs" },
		{ label: "Plain", href: "" },
		{ label: "Settings", href: "/settings" },
	];

	it("draws the trail, the last crumb as the current page", () => {
		mount("BreadcrumbRef", { items: trail });
		const links = host.querySelectorAll("[data-slot=breadcrumb-link]");
		expect([...links].map((a) => a.textContent)).toEqual(["Home", "Docs"]);
		expect(links[0].getAttribute("href")).toBe("/");
		const page = q("[data-slot=breadcrumb-page]");
		expect(page?.textContent).toBe("Settings");
		expect(page?.getAttribute("aria-current")).toBe("page");
		expect(host.querySelectorAll("[data-slot=breadcrumb-separator]")).toHaveLength(3);
		expect(q("nav")?.getAttribute("aria-label")).toBe("Breadcrumb");
	});

	it("marks only the crumb on another host as external", () => {
		mount("BreadcrumbRef", { items: trail });
		const links = host.querySelectorAll("[data-slot=breadcrumb-link]");
		expect(links[0].querySelector("svg")).toBeNull();
		expect(links[1].querySelector("svg")).not.toBeNull();
	});

	it("replaces the trail on a write, strings read as crumbs", () => {
		mount("BreadcrumbRef", { items: trail });
		write({ items: ["Root", null, { label: "Leaf" }] });
		expect(host.querySelectorAll("[data-slot=breadcrumb-link]")).toHaveLength(0);
		expect(q("[data-slot=breadcrumb-page]")?.textContent).toBe("Leaf");
		expect(q("[data-slot=breadcrumb-item]")?.textContent).toBe("Root");
	});

	it("draws nothing for an empty trail", () => {
		mount("BreadcrumbRef", { items: [] });
		expect(q("nav")).toBeNull();
	});
});

describe("SkeletonRef", () => {
	it("fills a row as text or rect, keeps its size as a circle", () => {
		expect(isFill("SkeletonRef", { shape: "text" })).toBe(true);
		expect(isFill("SkeletonRef", { shape: "rect" })).toBe(true);
		expect(isFill("SkeletonRef", { shape: "circle" })).toBe(false);
	});

	it("stacks text lines, the last one shorter", () => {
		mount("SkeletonRef", { lines: 3, shape: "text", height: 0 });
		const bars = host.querySelectorAll("[data-slot=skeleton]");
		expect(bars).toHaveLength(3);
		expect(bars[2].className).toContain("w-3/5");
		expect(bars[0].getAttribute("aria-hidden")).toBe("true");
	});

	it("switches to a rect of the written height", () => {
		mount("SkeletonRef", { lines: 3, shape: "text", height: 0 });
		write({ shape: "rect" });
		expect(q("[data-slot=skeleton]")?.style.height).toBe("96px");
		write({ height: 140 });
		expect(host.querySelectorAll("[data-slot=skeleton]")).toHaveLength(1);
		expect(q("[data-slot=skeleton]")?.style.height).toBe("140px");
	});

	it("keeps a circle at its own size", () => {
		mount("SkeletonRef", { lines: 1, shape: "circle", height: 0 });
		expect(q("[data-slot=skeleton]")?.style.width).toBe("40px");
		write({ height: 64 });
		expect(q("[data-slot=skeleton]")?.style.width).toBe("64px");
	});
});

describe("SpinnerRef", () => {
	it("is a Loading status with no label", () => {
		mount("SpinnerRef", { size: "md", label: "" });
		const spinner = q("[data-slot=spinner]");
		expect(spinner?.getAttribute("role")).toBe("status");
		expect(spinner?.getAttribute("aria-label")).toBe("Loading");
		expect(q("[data-slot=text]")).toBeNull();
	});

	it("names itself and shows the label after a write", () => {
		mount("SpinnerRef", { size: "md", label: "" });
		write({ label: "Fetching rows", size: "lg" });
		const spinner = q("[data-slot=spinner]");
		expect(spinner?.getAttribute("aria-label")).toBe("Fetching rows");
		expect(spinner?.className).toContain("size-5");
		const text = q("[data-slot=text]");
		expect(text?.textContent).toBe("Fetching rows");
		expect(text?.getAttribute("aria-hidden")).toBe("true");
	});
});

describe("StatusPillRef", () => {
	it("draws the tone with its icon and the label", () => {
		mount("StatusPillRef", { tone: "ok", label: "Deployed" });
		const pill = q("[data-slot=status-pill]");
		expect(pill?.getAttribute("data-tone")).toBe("ok");
		expect(pill?.textContent).toBe("Deployed");
		expect(pill?.querySelector("svg")).not.toBeNull();
	});

	it("merges a tone and keeps the label", () => {
		mount("StatusPillRef", { tone: "ok", label: "Deployed" });
		write({ tone: "danger" });
		const pill = q("[data-slot=status-pill]");
		expect(pill?.getAttribute("data-tone")).toBe("danger");
		expect(pill?.textContent).toBe("Deployed");
	});

	it("reads an unknown tone as neutral", () => {
		mount("StatusPillRef", { tone: "zigzag", label: "?" });
		expect(q("[data-slot=status-pill]")?.getAttribute("data-tone")).toBe("neutral");
	});
});
