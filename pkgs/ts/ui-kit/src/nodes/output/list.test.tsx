// ListRef over the real tree store: what each wire op leaves on screen.

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
	tree.getState().write([["l", "ListRef", { items: [], variant: "bullet", start: 1 }]]);
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

describe("ListRef", () => {
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
});
