// Tabs and Accordion over the real tree store: a body is the child whose
// segment is its tab or section id, whatever order the bodies were written.

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

function body(seg: string, type: string, id: string, text: string) {
	tree.getState().write([[seg, type], [id, "TextRef", { value: text }]]);
}

describe("Tabs", () => {
	const panels = () =>
		[...host.querySelectorAll("[role=tabpanel]")].map((p) => [
			p.getAttribute("hidden") === null,
			p.textContent,
		]);

	it("pairs each tab with the child at its id, not at its index", () => {
		const tabs = [
			{ id: "a", label: "A" },
			{ id: "b", label: "B" },
		];
		act(() => {
			tree.getState().write([["t", "Tabs", { tabs, active: "a" }]]);
			body("t", "Tabs", "b", "bee");
			body("t", "Tabs", "a", "ay");
		});
		act(() => root.render(<NodeView path={["t"]} />));
		expect(panels()).toEqual([
			[true, "ay"],
			[false, "bee"],
		]);
	});

	it("moves the bodies with a reordered tab list and leaves a missing body empty", () => {
		act(() => {
			tree.getState().write([
				[
					"t",
					"Tabs",
					{
						tabs: [
							{ id: "b", label: "B" },
							{ id: "a", label: "A" },
							{ id: "c", label: "C" },
						],
						active: "a",
					},
				],
			]);
			body("t", "Tabs", "a", "ay");
			body("t", "Tabs", "b", "bee");
		});
		act(() => root.render(<NodeView path={["t"]} />));
		expect(panels()).toEqual([
			[false, "bee"],
			[true, "ay"],
			[false, ""],
		]);
	});
});

describe("Accordion", () => {
	it("pairs each section with the child at its id", () => {
		const sections = [
			{ id: "one", label: "One" },
			{ id: "two", label: "Two" },
		];
		act(() => {
			tree.getState().write([["acc", "Accordion", { sections, open: ["one", "two"] }]]);
			body("acc", "Accordion", "two", "second");
			body("acc", "Accordion", "one", "first");
		});
		act(() => root.render(<NodeView path={["acc"]} />));
		const regions = [...host.querySelectorAll("[role=region]")].map((r) => r.textContent);
		expect(regions).toEqual(["first", "second"]);
	});
});
