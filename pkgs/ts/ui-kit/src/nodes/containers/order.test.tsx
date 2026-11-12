// The ordering ops over the real tree store on Row, Column and a flowing
// Grid: each keeps an order of keys and draws by it, the same ops a List
// takes (ui-core `order.ts`). A placed Grid keeps no order: it answers every
// op with an error and changes nothing.

import { ORDER_OPS, ORDER_PROP, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

function setup(type: string, props: Record<string, unknown> = {}) {
	act(() => {
		tree.getState().write([["c", type, props]]);
		for (const [seg, v] of [
			["0", "a"],
			["1", "b"],
			["2", "c"],
		]) {
			tree.getState().write([
				["c", type],
				[seg, "TextRef", { value: v }],
			]);
		}
		root.render(<NodeView path={["c"]} />);
	});
}

function send(op: string, payload: unknown, id?: string) {
	act(() => {
		tree.getState().dispatch({ op, ref: ["c"], payload, id });
	});
}

const drawn = () => [...host.querySelectorAll("[data-slot=text]")].map((el) => el.textContent);

describe.each(["Row", "Column", "Grid"])("%s order ops", (type) => {
	beforeEach(() => setup(type));

	it("moves one child and keeps the order", () => {
		send(ORDER_OPS.move, { key: "2", at: 0 });
		expect(drawn()).toEqual(["c", "a", "b"]);
		expect(tree.getState().getIn(["c"])?.props[ORDER_PROP]).toEqual(["2", "0", "1"]);
	});

	it("draws a child written into an inserted place there", () => {
		send(ORDER_OPS.insert, { key: "new", after: "0" });
		act(() => {
			tree.getState().write([
				["c", type],
				["new", "TextRef", { value: "n" }],
			]);
		});
		expect(drawn()).toEqual(["a", "n", "b", "c"]);
	});

	it("removes, truncates and keeps", () => {
		send(ORDER_OPS.remove, { key: "1" });
		expect(drawn()).toEqual(["a", "c"]);
		send(ORDER_OPS.truncate, { count: 1 });
		expect(drawn()).toEqual(["a"]);
		expect(tree.getState().getIn(["c", "2"])).toBeNull();
	});

	it("keeps the keys named, and puts named keys first", () => {
		send(ORDER_OPS.order, { keys: ["2", "1"] });
		expect(drawn()).toEqual(["c", "b", "a"]);
		send(ORDER_OPS.keep, { keys: ["0", "2"] });
		expect(drawn()).toEqual(["c", "a"]);
	});

	it("answers a payload it cannot apply with an error", () => {
		send(ORDER_OPS.move, { key: "nope" }, "3");
		expect(sent).toHaveLength(1);
		expect(sent[0]).toMatchObject({ op: "error", ref: ["c"], id: "3" });
		expect(drawn()).toEqual(["a", "b", "c"]);
	});
});

describe("placed Grid", () => {
	it("answers every order op with an error and changes nothing", () => {
		setup("Grid", { cols: "1fr 1fr" });
		const before = drawn();
		const ops: [string, unknown][] = [
			[ORDER_OPS.insert, { key: "x" }],
			[ORDER_OPS.move, { key: "0", at: 1 }],
			[ORDER_OPS.remove, { key: "0" }],
			[ORDER_OPS.truncate, { count: 1 }],
			[ORDER_OPS.keep, { keys: ["0"] }],
			[ORDER_OPS.order, { keys: ["2"] }],
		];
		for (const [op, payload] of ops) send(op, payload);
		expect(sent).toHaveLength(ops.length);
		for (const frame of sent) {
			expect(frame.op).toBe("error");
			expect((frame.payload as { code: string; message: string }).code).toBe("payload_invalid");
			expect((frame.payload as { message: string }).message).toContain("placed grid");
		}
		expect(tree.getState().getIn(["c"])?.props[ORDER_PROP]).toBeUndefined();
		expect(drawn()).toEqual(before);
		expect(tree.getState().getIn(["c", "0"])).not.toBeNull();
	});
});
