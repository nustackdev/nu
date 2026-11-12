// ListRef over the real tree store: what each wire op leaves on screen, and
// child nodes drawn as items after the strings.

import { OPS, ORDER_OPS } from "@nustackdev/ui-core";
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
	tree.getState().write([["l", "List", { items: [], variant: "bullet", start: 1 }]]);
	act(() => root.render(<NodeView path={["l"]} />));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

function send(op: string, payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op, ref: ["l"], payload });
	});
}

const items = () => [...host.querySelectorAll("li")].map((li) => li.textContent);
const list = () => host.querySelector("[data-slot=list]") as HTMLElement;

describe("List", () => {
	it("replaces the items with a written list, stringified", () => {
		send(OPS.write, ["a", 2, null, "c"]);
		expect(items()).toEqual(["a", "2", "c"]);
		expect(list().tagName).toBe("UL");
	});

	it("merges a written map", () => {
		send(OPS.write, { items: ["one", "two"], variant: "number", start: 3 });
		expect(items()).toEqual(["one", "two"]);
		expect(list().tagName).toBe("OL");
		expect(list().getAttribute("start")).toBe("3");

		send(OPS.write, { variant: "bullet" });
		expect(items()).toEqual(["one", "two"]);
		expect(list().tagName).toBe("UL");
	});

	it("appends one item", () => {
		send(OPS.write, ["a"]);
		send("append", "b");
		expect(items()).toEqual(["a", "b"]);
	});

	it("clears on nil", () => {
		send(OPS.write, ["a"]);
		send(OPS.write, null);
		expect(items()).toEqual([]);
	});

	it("falls back to bullets on an unknown variant", () => {
		send(OPS.write, { items: ["a"], variant: "zigzag" });
		expect(list().tagName).toBe("UL");
	});

	it("draws each child node as one more item, after the strings", () => {
		send(OPS.write, ["a", "b"]);
		act(() => {
			tree.getState().write([
				["l", "List"],
				["badge", "BadgeRef", { label: "live" }],
			]);
			tree.getState().write([
				["l", "List"],
				["note", "TextRef", { value: "plain node" }],
			]);
		});
		expect(items()).toEqual(["a", "b", "live", "plain node"]);
		const last = host.querySelectorAll("li")[2];
		expect(last.getAttribute("data-slot")).toBe("list-item");
		expect(last.querySelector("[data-slot=badge]")).not.toBeNull();
	});

	it("keeps child items when the strings are replaced or cleared", () => {
		act(() => {
			tree.getState().write([
				["l", "List"],
				["note", "TextRef", { value: "kept" }],
			]);
		});
		send(OPS.write, ["x"]);
		expect(items()).toEqual(["x", "kept"]);
		send(OPS.write, null);
		expect(items()).toEqual(["kept"]);
	});

	it("draws indexed children in index order, whatever order they were written", () => {
		act(() => {
			for (const [i, v] of [
				["2", "third"],
				["0", "first"],
				["1", "second"],
			]) {
				tree.getState().write([
					["l", "List"],
					[i, "TextRef", { value: v }],
				]);
			}
		});
		expect(items()).toEqual(["first", "second", "third"]);
	});

	it("keeps named children in place among indexed ones", () => {
		act(() => {
			for (const [seg, v] of [
				["1", "b"],
				["head", "named"],
				["0", "a"],
			]) {
				tree.getState().write([
					["l", "List"],
					[seg, "TextRef", { value: v }],
				]);
			}
		});
		expect(items()).toEqual(["a", "named", "b"]);
	});
});

describe("List order ops", () => {
	function children(...entries: [string, string][]) {
		act(() => {
			for (const [seg, v] of entries) {
				tree.getState().write([
					["l", "List"],
					[seg, "TextRef", { value: v }],
				]);
			}
		});
	}

	beforeEach(() => children(["0", "a"], ["1", "b"], ["2", "c"]));

	it("moves one child, the strings stay first", () => {
		send(OPS.write, ["s"]);
		send(ORDER_OPS.move, { key: "2", at: 0 });
		expect(items()).toEqual(["s", "c", "a", "b"]);
	});

	it("draws a child written into an inserted place there", () => {
		send(ORDER_OPS.insert, { key: "new", before: "1" });
		expect(items()).toEqual(["a", "b", "c"]);
		children(["new", "n"]);
		expect(items()).toEqual(["a", "n", "b", "c"]);
	});

	it("draws a child nothing placed after the placed ones", () => {
		send(ORDER_OPS.move, { key: "0" });
		children(["late", "z"]);
		expect(items()).toEqual(["b", "c", "a", "z"]);
	});

	it("removes, truncates and keeps", () => {
		children(["3", "d"]);
		send(ORDER_OPS.remove, { key: "1" });
		expect(items()).toEqual(["a", "c", "d"]);
		send(ORDER_OPS.truncate, { count: 2 });
		expect(items()).toEqual(["a", "c"]);
		expect(tree.getState().getIn(["l", "3"])).toBeNull();
		send(ORDER_OPS.keep, { keys: ["2"] });
		expect(items()).toEqual(["c"]);
	});

	it("puts the keys named first", () => {
		send(ORDER_OPS.order, { keys: ["2", "1"] });
		expect(items()).toEqual(["c", "b", "a"]);
	});
});
