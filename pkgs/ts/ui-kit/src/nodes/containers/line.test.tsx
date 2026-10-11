// Line over the real tree store: children run inline in insertion order, and
// the content leaves draw as runs of the sentence inside it and as blocks
// outside it.

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

function draw(rootSegment: string, chains: [string, string, Record<string, unknown>?][][]) {
	act(() => {
		for (const chain of chains) tree.getState().write(chain);
		root.render(<NodeView path={[rootSegment]} />);
	});
}

const line = () => host.querySelector("[data-slot=line]") as HTMLElement;

describe("Line", () => {
	it("draws a TextRef as a span inside a Line and as a p in a Column", () => {
		draw("page", [
			[
				["page", "Column"],
				["l", "Line"],
				["t", "TextRef", { value: "inline run" }],
			],
			[
				["page", "Column"],
				["c", "TextRef", { value: "block text" }],
			],
		]);
		const [inLine, inColumn] = [...host.querySelectorAll("[data-slot=text]")];
		expect(inLine.tagName).toBe("SPAN");
		expect(inLine.textContent).toBe("inline run");
		expect(inLine.className).not.toContain("py-1");
		expect(line().contains(inLine)).toBe(true);
		expect(inColumn.tagName).toBe("P");
		expect(inColumn.className).toContain("py-1");
	});

	it("puts a Badge on the text's baseline inside a Line only", () => {
		draw("page", [
			[
				["page", "Column"],
				["l", "Line"],
				["b", "BadgeRef", { label: "0.6" }],
			],
			[
				["page", "Column"],
				["c", "BadgeRef", { label: "0.6" }],
			],
		]);
		const [inLine, inColumn] = [...host.querySelectorAll("[data-slot=badge]")];
		expect(inLine.className).toContain("align-baseline");
		expect(inLine.className).toContain("inline-flex");
		expect(inColumn.className).not.toContain("align-baseline");
	});

	it("draws a LinkRef as an inline anchor inside a Line", () => {
		draw("l", [
			[
				["l", "Line"],
				["a", "LinkRef", { href: "/docs", label: "Docs" }],
			],
		]);
		const a = host.querySelector("[data-slot=link]") as HTMLElement;
		expect(a.className.split(" ")).toContain("inline");
		expect(a.className).not.toContain("inline-flex");
	});

	it("keeps its children in insertion order, a word space before each", () => {
		draw("l", [
			[
				["l", "Line"],
				["lead", "TextRef", { value: "Built with" }],
			],
			[
				["l", "Line"],
				["nu", "LinkRef", { href: "https://nustack.dev", label: "Nu" }],
			],
			[
				["l", "Line"],
				["v", "BadgeRef", { label: "0.6" }],
			],
			[
				["l", "Line"],
				["k", "KbdRef", { label: "K" }],
			],
			[
				["l", "Line"],
				["dot", "StatusDotRef", { tone: "ok", label: "live" }],
			],
		]);
		const slots = [...line().querySelectorAll("[data-slot]")]
			.filter((el) => el.parentElement === line())
			.map((el) => el.getAttribute("data-slot"));
		expect(slots).toEqual(["text", "link", "badge", "kbd", "status-dot"]);
		expect(line().textContent).toBe(" Built with Nu 0.6 K ");
	});

	it("puts no space before a text run that opens with punctuation", () => {
		draw("l", [
			[
				["l", "Line"],
				["a", "TextRef", { value: "press" }],
			],
			[
				["l", "Line"],
				["k", "KbdRef", { label: "Esc" }],
			],
			[
				["l", "Line"],
				["b", "TextRef", { value: ", then go." }],
			],
		]);
		expect(line().textContent).toBe(" press Esc, then go.");
	});

	it("reads align and wrap off its props", () => {
		draw("l", [[["l", "Line", { align: "center", wrap: false }]]]);
		expect(line().className).toContain("text-center");
		expect(line().className).toContain("whitespace-nowrap");
		expect(line().getAttribute("data-wrap")).toBe("false");
	});

	it("wraps by default and falls back to start on an unknown align", () => {
		draw("l", [[["l", "Line", { align: "sideways" }]]]);
		expect(line().className).toContain("text-start");
		expect(line().getAttribute("data-wrap")).toBe("true");
	});
});
