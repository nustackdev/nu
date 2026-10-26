// The shell renders the program's tree and decides nothing: a compact header,
// then the root's children bare, in the order they landed, with headless
// nodes taking no space, and every plain click on a same-origin link a
// History push.

import { History, tree } from "@nustackdev/ui-kit";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { Shell } from "./App";

beforeEach(() => {
	window.history.replaceState(null, "", "/");
});

afterEach(() => {
	act(() => tree.getState().remove([]));
});

describe("Shell", () => {
	it("draws a page outline until something lands", () => {
		const { container } = render(<Shell status="connecting" />);
		expect(screen.getByRole("status")).toHaveTextContent("Booting");
		expect(container.querySelectorAll("[data-slot=skeleton]").length).toBeGreaterThan(0);
		expect(screen.getByText("connecting")).toBeInTheDocument();
	});

	it("renders the root's children in the order they landed", () => {
		render(<Shell status="connected" />);
		act(() => {
			tree.getState().write([["second", "TextRef", {}]], { value: "Second" });
			tree.getState().write([["first", "TextRef", {}]], { value: "First" });
		});
		expect(screen.queryByRole("status")).toBeNull();
		const second = screen.getByText("Second");
		const first = screen.getByText("First");
		expect(second.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("keeps a compact header on the sidebar ground", () => {
		const { container } = render(<Shell status="connected" />);
		const header = container.querySelector("[data-slot=nudle-header]");
		expect(header?.textContent).toContain("nudle");
		expect(header?.textContent).toContain("connected");
		for (const c of ["bg-[var(--ground-deep)]", "border-b", "border-[var(--line-subtle)]"]) {
			expect(header?.className).toContain(c);
		}
	});

	it("draws the root bare, and headless nodes take no space", () => {
		const { container } = render(<Shell status="connected" />);
		act(() => {
			tree.getState().write([["title", "TitleRef", {}]]);
			tree.getState().write([["history", "HistoryRef", {}]]);
			tree.getState().write([["page", "Container", {}], ["t", "TextRef", {}]], { value: "Hi" });
		});
		const main = container.querySelector("[data-slot=nudle-main]");
		expect(main?.className ?? "").toBe("py-6");
		// The title and the history draw nothing, not even a wrapper: the
		// container is the main area's only element.
		expect(main?.children).toHaveLength(1);
		expect(main?.firstElementChild?.getAttribute("data-slot")).toBe("container");
		expect(screen.getByText("Hi")).toBeInTheDocument();
	});

	it("routes a plain click on an in-app link through History", () => {
		render(<Shell status="connected" />);
		act(() => {
			tree.getState().write([["docs", "LinkRef", { href: "/docs", label: "Docs" }]]);
		});
		fireEvent.click(screen.getByText("Docs"));
		expect(History.current().path).toBe("/docs");
	});
});
