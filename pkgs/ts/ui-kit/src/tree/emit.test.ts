// The notify seam and the per-field reads.
//
// `emit` is what every node sends through, so what it puts on the wire is
// the contract the Python side filters on: one notify, the node's ref, and a
// payload that names its event. Reads answer from the registry entry, the
// main one from `props.value` when the type declares none.

import { OP_ERROR, OPS, type TreeFrame } from "@nustackdev/ui-core";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { EVENTS, emit } from "./emit";
import { mainRead, readOf, register, registry } from "./registry";
import { tree } from "./store";

let sent: TreeFrame[] = [];
const registered: string[] = [];

function add(type: string, entry: Parameters<typeof register>[1]) {
	register(type, entry);
	registered.push(type);
}

beforeEach(() => {
	sent = [];
	tree.getState().setSender((f) => sent.push(f));
});

afterEach(() => {
	tree.getState().setSender(null);
	tree.getState().remove(["e"]);
	for (const t of registered.splice(0)) delete registry[t];
});

describe("emit", () => {
	it("sends one notify that names its event", () => {
		emit(["e", "b"], EVENTS.click);
		expect(sent).toEqual([{ op: OPS.notify, ref: ["e", "b"], payload: { event: "click" } }]);
	});

	it("carries the extra fields next to the event", () => {
		emit(["e", "s"], EVENTS.change, { value: 5 });
		expect(sent).toEqual([
			{ op: OPS.notify, ref: ["e", "s"], payload: { event: "change", value: 5 } },
		]);
	});

	it("never lets a field rename the event", () => {
		emit(["e", "s"], EVENTS.input, { event: "change", value: 1 });
		expect((sent[0].payload as { event: string }).event).toBe("input");
	});
});

describe("reads", () => {
	it("answers the main read from props.value when the type declares none", () => {
		add("EmitPlainRef", {});
		expect(mainRead("EmitPlainRef", { value: 3 })).toBe(3);
		expect(mainRead("EmitPlainRef", {})).toBeNull();
		expect(mainRead(null, { value: "x" })).toBe("x");
	});

	it("answers each field through the entry's reads", () => {
		add("EmitTreeRef", {
			reads: { "": (p) => p.selected ?? null, expanded: (p) => p.expanded ?? [] },
		});
		expect(mainRead("EmitTreeRef", { selected: "a" })).toBe("a");
		expect(readOf("EmitTreeRef", { expanded: ["x"] }, "expanded")).toEqual({ value: ["x"] });
		expect(readOf("EmitTreeRef", {}, "nope")).toBeUndefined();
	});

	it("answers a read frame for a field through the store", () => {
		add("EmitTabsRef", { reads: { "": (p) => p.active ?? null } });
		tree.getState().write([["e"], ["t", "EmitTabsRef", { active: "two" }]]);
		tree.getState().dispatch({ op: OPS.read, ref: ["e", "t"], payload: null, id: "r1" });
		tree
			.getState()
			.dispatch({ op: OPS.read, ref: ["e", "t"], payload: { field: "nope" }, id: "r2" });
		expect(sent[0]).toEqual({ op: OPS.read, ref: ["e", "t"], payload: "two", id: "r1" });
		expect(sent[1]).toMatchObject({ op: OP_ERROR, ref: ["e", "t"], id: "r2" });
	});
});
