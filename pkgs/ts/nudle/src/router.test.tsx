// The page router: exact pathname match on each page's route, the query
// free, the first page at a bare "/" nobody claims, not-found for the rest.
// Driven by History, with no HistoryRef node in the tree at all.

import { History, tree } from "@nustackdev/ui-kit";
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NOT_FOUND, pageFor, useActivePage } from "./router";

const PAGES = [
	{ segment: "feed", path: "/feed" },
	{ segment: "settings", path: "/settings/" },
];

describe("pageFor", () => {
	it("matches the pathname exactly, trailing slash aside", () => {
		expect(pageFor(PAGES, "/feed")).toBe("feed");
		expect(pageFor(PAGES, "/settings")).toBe("settings");
		expect(pageFor(PAGES, "/feed/")).toBe("feed");
		expect(pageFor(PAGES, "/feed/more")).toBe(NOT_FOUND);
	});

	it("shows the first page at a bare / no page claims", () => {
		expect(pageFor(PAGES, "/")).toBe("feed");
		expect(pageFor([{ segment: "home", path: "/" }, ...PAGES], "/")).toBe("home");
		expect(pageFor(PAGES, "/nope")).toBe(NOT_FOUND);
	});

	it("has nothing to say with no pages", () => {
		expect(pageFor([], "/anything")).toBeNull();
	});
});

function Active() {
	const page = useActivePage();
	return <span data-testid="page">{page === NOT_FOUND ? "not-found" : String(page)}</span>;
}

describe("useActivePage", () => {
	beforeEach(() => {
		window.history.replaceState(null, "", "/");
		act(() => tree.getState().write([["home", "Page", { route: "/", label: "Home" }]]));
		act(() => tree.getState().write([["feed", "Page", { route: "/feed", label: "Feed" }]]));
	});

	afterEach(() => {
		act(() => tree.getState().remove([]));
	});

	it("follows History, query ignored, with no HistoryRef in the tree", () => {
		render(<Active />);
		const page = () => screen.getByTestId("page").textContent;
		expect(page()).toBe("home");
		act(() => {
			History.push("/feed?x=1");
		});
		expect(page()).toBe("feed");
		act(() => {
			History.push("/missing");
		});
		expect(page()).toBe("not-found");
	});
});
