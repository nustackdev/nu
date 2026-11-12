// Keyed order: the pure op math, and the handlers over a real store.

import { describe, expect, it } from "vitest";
import {
	applyOrderOp,
	indexedOrder,
	keyedOrder,
	ORDER_OPS,
	ORDER_PROP,
	OrderError,
	orderHandlers,
	places,
} from "./order";
import { type Behaviour, createTreeStore, type TreeFrame } from "./tree";

const op = (name: string, payload: unknown, order: string[] | undefined, present: string[]) =>
	applyOrderOp(name, payload, order, present);

describe("default order", () => {
	it("sorts indices by number and keeps names where written", () => {
		expect(indexedOrder(["2", "a", "0", "b", "1"])).toEqual(["0", "a", "1", "b", "2"]);
	});

	it("is what draws until an order is kept", () => {
		expect(keyedOrder(undefined, ["10", "2"])).toEqual(["2", "10"]);
	});

	it("puts children with no place after the placed ones", () => {
		expect(keyedOrder(["b", "a"], ["a", "b", "3", "c", "1"])).toEqual(["b", "a", "1", "c", "3"]);
	});

	it("draws nothing for a place with no child", () => {
		expect(keyedOrder(["x", "a"], ["a"])).toEqual(["a"]);
		expect(places(["x", "a"], ["a"])).toEqual(["x", "a"]);
	});
});

describe("insert_item", () => {
	it("appends by default and writes the drawn order down first", () => {
		expect(op(ORDER_OPS.insert, { key: "n" }, undefined, ["1", "0"])).toEqual({
			order: ["0", "1", "n"],
			drop: [],
		});
	});

	it("places at a position, clamped", () => {
		expect(op(ORDER_OPS.insert, { key: "n", at: 1 }, ["a", "b"], [])?.order).toEqual([
			"a",
			"n",
			"b",
		]);
		expect(op(ORDER_OPS.insert, { key: "n", at: 99 }, ["a"], [])?.order).toEqual(["a", "n"]);
	});

	it("places before and after a key", () => {
		expect(op(ORDER_OPS.insert, { key: "n", before: "b" }, ["a", "b"], [])?.order).toEqual([
			"a",
			"n",
			"b",
		]);
		expect(op(ORDER_OPS.insert, { key: "n", after: "a" }, ["a", "b"], [])?.order).toEqual([
			"a",
			"n",
			"b",
		]);
	});

	it("moves a key already placed", () => {
		expect(op(ORDER_OPS.insert, { key: "b", at: 0 }, ["a", "b"], ["a", "b"])?.order).toEqual([
			"b",
			"a",
		]);
	});

	it("refuses an anchor with no place", () => {
		expect(() => op(ORDER_OPS.insert, { key: "n", before: "zz" }, ["a"], ["a"])).toThrow(
			OrderError,
		);
	});
});

describe("move_item", () => {
	it("moves one place, the rest keep theirs", () => {
		expect(op(ORDER_OPS.move, { key: "2", at: 0 }, undefined, ["0", "1", "2"])).toEqual({
			order: ["2", "0", "1"],
			drop: [],
		});
		expect(op(ORDER_OPS.move, { key: "0" }, undefined, ["0", "1", "2"])?.order).toEqual([
			"1",
			"2",
			"0",
		]);
	});

	it("refuses a key with no place", () => {
		expect(() => op(ORDER_OPS.move, { key: "q" }, undefined, ["a"])).toThrow(OrderError);
	});
});

describe("remove, truncate, keep", () => {
	it("removes one child and its place, a missing key is a no-op", () => {
		expect(op(ORDER_OPS.remove, { key: "b" }, ["a", "b", "c"], ["a", "b", "c"])).toEqual({
			order: ["a", "c"],
			drop: ["b"],
		});
		expect(op(ORDER_OPS.remove, { key: "q" }, ["a"], ["a"])).toEqual({ order: ["a"], drop: [] });
	});

	it("truncates to the first places", () => {
		expect(op(ORDER_OPS.truncate, { count: 2 }, undefined, ["2", "0", "1", "3"])).toEqual({
			order: ["0", "1"],
			drop: ["2", "3"],
		});
		expect(op(ORDER_OPS.truncate, { count: 0 }, ["a"], ["a"])).toEqual({ order: [], drop: ["a"] });
	});

	it("keeps the keys named, where they are", () => {
		expect(
			op(ORDER_OPS.keep, { keys: ["c", "a", "zz"] }, ["a", "b", "c"], ["a", "b", "c"]),
		).toEqual({
			order: ["a", "c"],
			drop: ["b"],
		});
	});

	it("refuses a bad payload", () => {
		expect(() => op(ORDER_OPS.truncate, { count: -1 }, [], [])).toThrow(OrderError);
		expect(() => op(ORDER_OPS.keep, { keys: "a" }, [], [])).toThrow(OrderError);
		expect(() => op(ORDER_OPS.remove, {}, [], [])).toThrow(OrderError);
	});
});

describe("order_items", () => {
	it("puts the named first, the rest keep theirs after", () => {
		expect(
			op(ORDER_OPS.order, { keys: ["c", "zz", "a"] }, undefined, ["a", "b", "c", "d"])?.order,
		).toEqual(["c", "a", "b", "d"]);
	});

	it("is not one of the ops for anything else", () => {
		expect(op("write", {}, undefined, [])).toBeNull();
	});
});

describe("handlers over a store", () => {
	const frame = (opName: string, payload: unknown, id?: string): TreeFrame => ({
		op: opName,
		ref: ["l"],
		payload,
		id,
	});

	function setup() {
		const disposed: string[] = [];
		const sent: TreeFrame[] = [];
		const behaviours: Record<string, Behaviour> = {
			L: { handlers: orderHandlers() },
			T: { dispose: ({ path }) => disposed.push(path.join("/")) },
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t], send: (f) => sent.push(f) });
		store.getState().write([["l", "L", {}]]);
		for (const k of ["0", "1", "2"])
			store.getState().write([
				["l", "L", {}],
				[k, "T", {}],
			]);
		const kids = () => [...(store.getState().getIn(["l"])?.children.keys() ?? [])];
		const order = () => store.getState().getIn(["l"])?.props[ORDER_PROP];
		return { store, disposed, sent, kids, order };
	}

	it("keeps the order on the node and rewrites no child", () => {
		const { store, kids, order } = setup();
		const child = store.getState().getIn(["l", "1"]);
		store.getState().dispatch(frame(ORDER_OPS.move, { key: "2", at: 0 }));
		expect(order()).toEqual(["2", "0", "1"]);
		expect(kids()).toEqual(["0", "1", "2"]);
		expect(store.getState().getIn(["l", "1"])).toBe(child);
	});

	it("drops children through the store, dispose included", () => {
		const { store, disposed, kids, order } = setup();
		store.getState().dispatch(frame(ORDER_OPS.truncate, { count: 1 }));
		expect(kids()).toEqual(["0"]);
		expect(order()).toEqual(["0"]);
		expect(disposed.sort()).toEqual(["l/1", "l/2"]);
	});

	it("draws a child written into an inserted place there", () => {
		const { store, order } = setup();
		store.getState().dispatch(frame(ORDER_OPS.insert, { key: "n", at: 0 }));
		store.getState().write([
			["l", "L", {}],
			["n", "T", {}],
		]);
		const node = store.getState().getIn(["l"]);
		const present = [...(node?.children.keys() ?? [])];
		expect(keyedOrder(order() as string[], present)).toEqual(["n", "0", "1", "2"]);
	});

	it("answers a payload it cannot apply with an error, changing nothing", () => {
		const { store, sent, order } = setup();
		store.getState().dispatch(frame(ORDER_OPS.move, { key: "q" }, "7"));
		expect(order()).toBeUndefined();
		expect(sent).toHaveLength(1);
		expect(sent[0]).toMatchObject({ op: "error", ref: ["l"], id: "7" });
		expect((sent[0].payload as { code: string }).code).toBe("payload_invalid");
	});

	it("turns an op down when the node refuses it, changing nothing", () => {
		const sent: TreeFrame[] = [];
		const behaviours: Record<string, Behaviour> = {
			G: {
				handlers: orderHandlers((props) =>
					props.cols ? "a placed grid keeps no order" : undefined,
				),
			},
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t], send: (f) => sent.push(f) });
		store.getState().write([["l", "G", { cols: "2fr 1fr" }]]);
		store.getState().dispatch(frame(ORDER_OPS.remove, { key: "0" }, "9"));
		expect(store.getState().getIn(["l"])?.props[ORDER_PROP]).toBeUndefined();
		expect(sent[0]).toMatchObject({ op: "error", ref: ["l"], id: "9" });
		expect((sent[0].payload as { message: string }).message).toContain("placed grid");
	});
});
