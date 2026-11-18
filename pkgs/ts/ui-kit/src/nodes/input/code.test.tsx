// CodeRef in diff mode over the real tree store: what the view draws for an
// old and a new text, that it folds and stays read-only, and that a write to
// either side redraws the diff in the same view.

import { OPS } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// CodeMirror measures ranges; jsdom lays nothing out, so a range has no boxes.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	tree.getState().setSender(() => {});
});

afterEach(async () => {
	await act(async () => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

const PATH = ["c"];

function mount(props: Record<string, unknown>) {
	tree.getState().write([["c", "CodeRef", props]]);
	act(() => root.render(<NodeView path={PATH} />));
}

function write(payload: unknown) {
	act(() => tree.getState().dispatch({ op: OPS.write, ref: PATH, payload }));
}

const all = (sel: string) => Array.from(host.querySelectorAll<HTMLElement>(sel));
const added = () => all(".cm-changedLine").map((el) => el.textContent);
const removed = () => all(".cm-deletedChunk .cm-deletedLine").map((el) => el.textContent);
const folds = () => all(".cm-collapsedLines");
const content = () => host.querySelector<HTMLElement>(".cm-content");

const lines = (n: number, tag = "line") =>
	Array.from({ length: n }, (_, i) => `${tag} ${i + 1}`).join("\n");

describe("CodeRef diff", () => {
	it("draws added and removed lines against the original", () => {
		mount({ value: "a\nB\nc\n", original: "a\nb\nc\n", language: "" });
		expect(host.querySelector("[data-slot=code-block]")?.hasAttribute("data-diff")).toBe(true);
		expect(added()).toEqual(["B"]);
		expect(removed()).toEqual(["b"]);
	});

	it("keeps highlighting on both sides once the language lands", async () => {
		mount({ value: "x = 2\n", original: "x = 1\n", language: "python" });
		await act(async () => {
			await new Promise((resolve) => setTimeout(resolve, 200));
		});
		const tokens = (el: Element | undefined) =>
			Array.from(el?.querySelectorAll("span[class]") ?? []).filter((span) =>
				Array.from(span.classList).some((c) => !c.startsWith("cm-")),
			).length;
		expect(tokens(all(".cm-changedLine")[0])).toBeGreaterThan(0);
		expect(tokens(all(".cm-deletedLine")[0])).toBeGreaterThan(0);
	});

	it("draws no diff without an original, and every line added against an empty one", () => {
		mount({ value: "a\nb\n" });
		expect(host.querySelector(".cm-merge-b")).toBeNull();
		expect(host.querySelector("[data-slot=code-block]")?.hasAttribute("data-diff")).toBe(false);
		write({ original: "" });
		expect(added()).toEqual(["a", "b"]);
		expect(removed()).toEqual([]);
	});

	it("folds long unchanged runs", () => {
		const before = lines(30);
		const after = before.replace("line 15", "line fifteen");
		mount({ value: after, original: before });
		expect(added()).toEqual(["line fifteen"]);
		// Lines 1-11 and 19-30 sit more than three lines from the change.
		expect(folds().map((el) => el.textContent)).toEqual([
			"11 unchanged lines",
			"12 unchanged lines",
		]);
	});

	it("is read-only even when told it may be edited, and editable again once the diff is off", () => {
		mount({ value: "b", original: "a", readonly: false });
		expect(content()?.getAttribute("contenteditable")).toBe("false");
		expect(host.querySelector("[data-slot=code-block]")?.hasAttribute("data-editable")).toBe(false);
		write({ original: null });
		expect(host.querySelector(".cm-merge-b")).toBeNull();
		expect(content()?.getAttribute("contenteditable")).toBe("true");
	});

	it("redraws when either side moves, folds included", () => {
		mount({ value: "a\nb\n", original: "a\nb\n" });
		expect(added()).toEqual([]);
		write("a\nb\nc\n");
		expect(added()).toEqual(["c"]);
		write({ original: "x\nb\n" });
		expect(added()).toEqual(["a", "c"]);
		expect(removed()).toEqual(["x"]);

		const before = lines(30);
		write({ value: before.replace("line 2", "line two"), original: before });
		expect(added()).toEqual(["line two"]);
		expect(removed()).toEqual(["line 2"]);
		expect(folds().map((el) => el.textContent)).toEqual(["25 unchanged lines"]);
	});
});
