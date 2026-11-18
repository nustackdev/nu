// Quote over the real tree store: the header child in its own box above
// the body, the string title as its shorthand, the body as a stack.

import { OPS } from "@nustackdev/ui-core";
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

type Level = [string, string, Record<string, unknown>?];

function write(...chain: Level[]) {
	act(() => tree.getState().write(chain.map(([s, t, p]) => [s, t, p ?? {}])));
}

function draw() {
	act(() => root.render(<NodeView path={["q"]} />));
}

const slot = (name: string, from: ParentNode = host) =>
	from.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

describe("Quote", () => {
	it("draws the accent rule and quiets the primary ink", () => {
		write(["q", "Quote", {}], ["t", "TextRef", { value: "quoted" }]);
		draw();
		const quote = slot("quote");
		expect(cls(quote)).toEqual(expect.arrayContaining(["border-l-2", "border-accent-line"]));
		expect(cls(quote)).toContain("[--text-primary:var(--text-secondary)]");
		expect(slot("quote-content")?.textContent).toBe("quoted");
	});

	it("draws no header with neither a title nor a header child", () => {
		write(["q", "Quote", {}], ["t", "TextRef", { value: "body" }]);
		draw();
		expect(slot("quote-header")).toBeNull();
	});

	it("draws the title as the header line, retitled by a write", () => {
		write(["q", "Quote", { title: "Note" }], ["t", "TextRef", { value: "body" }]);
		draw();
		expect(slot("quote-header")?.textContent).toBe("Note");
		act(() =>
			tree.getState().dispatch({ op: OPS.write, ref: ["q"], payload: { title: "Source" } }),
		);
		expect(slot("quote-header")?.textContent).toBe("Source");
	});

	it("draws the header child above the body, in place of the title", () => {
		write(["q", "Quote", { title: "Note" }], ["t", "TextRef", { value: "body" }]);
		write(
			["q", "Quote"],
			["header", "Row", { gap: 2 }],
			["label", "TextRef", { value: "Working" }],
		);
		draw();
		const quote = slot("quote") as HTMLElement;
		const parts = [...quote.children].map((el) => el.getAttribute("data-slot"));
		expect(parts).toEqual(["quote-header", "quote-content"]);
		const header = slot("quote-header");
		expect(header?.textContent).toBe("Working");
		expect(slot("quote-content")?.textContent).toBe("body");
	});

	it("gives the header the full width and lets its child shrink", () => {
		write(["q", "Quote"], ["header", "Row"], ["label", "TextRef", { value: "a long line" }]);
		draw();
		expect(cls(slot("quote-header"))).toEqual(expect.arrayContaining(["w-full", "min-w-0"]));
	});

	it("stacks the body with the column layers", () => {
		write(["q", "Quote", { gap: 5, divided: true }], ["a", "TextRef", { value: "a" }]);
		write(["q", "Quote"], ["b", "TextRef", { value: "b" }]);
		draw();
		const body = slot("quote-content");
		expect(cls(body)).toContain("gap-5");
		expect(cls(body)).not.toContain("gap-2");
		expect(cls(body)).toContain("divide-y");
		expect(body?.textContent).toBe("ab");
	});

	it("puts the size on the quote and scrolls the body", () => {
		write(["q", "Quote", { max_height: 120, scroll: "y" }], ["a", "TextRef", { value: "a" }]);
		draw();
		expect(slot("quote")?.style.maxHeight).toBe("120px");
		expect(cls(slot("quote-content"))).toEqual(
			expect.arrayContaining(["overflow-y-auto", "flex-1"]),
		);
	});
});
