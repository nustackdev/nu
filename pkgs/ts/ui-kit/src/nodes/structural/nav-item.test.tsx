// NavItemRef over the real tree store: a real link, active when pinned, and
// following the tab when not, through pushState and back.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { matchesPath, NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

function write(props: Record<string, unknown>) {
	act(() =>
		tree.getState().write([
			["n", "NavList"],
			["i", "NavItemRef", props],
		]),
	);
}

const link = () => host.querySelector<HTMLAnchorElement>("[data-slot=nav-link]");

beforeEach(() => {
	window.history.replaceState({}, "", "/");
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	window.history.replaceState({}, "", "/");
});

describe("NavItemRef", () => {
	it("is a real link with its icon, label and meta", () => {
		write({ label: "Docs", href: "/docs", icon: "book-open", meta: "12" });
		act(() => root.render(<NodeView path={["n"]} />));
		expect(link()?.tagName).toBe("A");
		expect(link()?.getAttribute("href")).toBe("/docs");
		expect(link()?.querySelector("svg")).not.toBeNull();
		expect(link()?.textContent).toBe("Docs12");
	});

	it("follows the tab when active is unset", () => {
		write({ label: "Docs", href: "/docs", active: null });
		act(() => root.render(<NodeView path={["n"]} />));
		expect(link()?.getAttribute("aria-current")).toBeNull();
		act(() => {
			window.history.pushState({}, "", "/docs/intro");
			// pushState fires nothing; the next tree change re-reads the tab.
			tree.getState().write([["other", "TextRef"]], { value: "x" });
		});
		expect(link()?.getAttribute("aria-current")).toBe("page");
		act(() => {
			window.history.pushState({}, "", "/");
			window.dispatchEvent(new PopStateEvent("popstate"));
		});
		expect(link()?.getAttribute("aria-current")).toBeNull();
	});

	it("is pinned by active true or false", () => {
		window.history.replaceState({}, "", "/docs");
		write({ label: "Docs", href: "/docs", active: false });
		act(() => root.render(<NodeView path={["n"]} />));
		expect(link()?.getAttribute("aria-current")).toBeNull();
		act(() =>
			tree.getState().dispatch({ op: "write", ref: ["n", "i"], payload: { active: true } }),
		);
		window.history.replaceState({}, "", "/elsewhere");
		expect(link()?.getAttribute("aria-current")).toBe("page");
	});
});

describe("matchesPath", () => {
	it("matches the path, the paths under it, and only itself for / or exact", () => {
		expect(matchesPath("/docs", "/docs", false)).toBe(true);
		expect(matchesPath("/docs/", "/docs", false)).toBe(true);
		expect(matchesPath("/docs", "/docs/intro", false)).toBe(true);
		expect(matchesPath("/docs", "/docsy", false)).toBe(false);
		expect(matchesPath("/docs", "/docs/intro", true)).toBe(false);
		expect(matchesPath("/", "/docs", false)).toBe(false);
		expect(matchesPath("/", "/", false)).toBe(true);
		expect(matchesPath("/docs?tab=2#x", "/docs", true)).toBe(true);
		expect(matchesPath("https://elsewhere.example/docs", "/docs", false)).toBe(false);
		expect(matchesPath("", "/", false)).toBe(false);
	});
});
