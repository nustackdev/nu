// The watch table: what the server listens to, per path. Plain frames in,
// `isWatched` out; no React, no socket.

import { describe, expect, it, vi } from "vitest";
import { createTreeStore, OPS, type TreeFrame } from "./tree";

function frame(op: string, ref: string[], payload?: unknown): TreeFrame {
	return { op, ref, payload };
}

describe("watch", () => {
	it("watches nothing until the server asks", () => {
		const store = createTreeStore();
		expect(store.getState().isWatched(["s"], "change")).toBe(false);
	});

	it("watches one event on one path", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["p", "s"], { event: "change" }));
		expect(store.getState().isWatched(["p", "s"], "change")).toBe(true);
		expect(store.getState().isWatched(["p", "s"], "input")).toBe(false);
		expect(store.getState().isWatched(["p"], "change")).toBe(false);
		expect(store.getState().isWatched(["p", "t"], "change")).toBe(false);
	});

	it("takes * as every event", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["t"], { event: "*" }));
		expect(store.getState().isWatched(["t"], "select")).toBe(true);
		expect(store.getState().isWatched(["t"], "toggle")).toBe(true);
	});

	it("unwatch stops that event only", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["s"], { event: "change" }));
		store.getState().dispatch(frame(OPS.watch, ["s"], { event: "input" }));
		store.getState().dispatch(frame(OPS.unwatch, ["s"], { event: "change" }));
		expect(store.getState().isWatched(["s"], "change")).toBe(false);
		expect(store.getState().isWatched(["s"], "input")).toBe(true);
		store.getState().dispatch(frame(OPS.unwatch, ["s"], { event: "input" }));
		expect(store.getState().isWatched(["s"], "input")).toBe(false);
	});

	it("lands before the node is drawn and creates nothing", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["page", "s"], { event: "change" }));
		expect(store.getState().getIn(["page"])).toBeNull();
		store.getState().write([
			["page", "Page"],
			["s", "Slider"],
		]);
		expect(store.getState().isWatched(["page", "s"], "change")).toBe(true);
	});

	it("survives a remove and a clear of the node", () => {
		const store = createTreeStore();
		store.getState().write([["s", "Slider"]]);
		store.getState().dispatch(frame(OPS.watch, ["s"], { event: "change" }));
		store.getState().dispatch(frame(OPS.remove, ["s"]));
		expect(store.getState().isWatched(["s"], "change")).toBe(true);
		store.getState().dispatch(frame(OPS.remove, []));
		expect(store.getState().isWatched(["s"], "change")).toBe(true);
	});

	it("keeps segments apart that a joined key would merge", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["a.b"], { event: "change" }));
		expect(store.getState().isWatched(["a", "b"], "change")).toBe(false);
	});

	it("unwatchAll forgets every watch", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.watch, ["s"], { event: "*" }));
		store.getState().unwatchAll();
		expect(store.getState().isWatched(["s"], "change")).toBe(false);
	});

	it("setWatchAll counts every event as watched", () => {
		const store = createTreeStore();
		store.getState().setWatchAll(true);
		expect(store.getState().isWatched(["any"], "input")).toBe(true);
		store.getState().setWatchAll(false);
		expect(store.getState().isWatched(["any"], "input")).toBe(false);
	});

	it("reports a watch that names no event, and sends nothing", () => {
		const onError = vi.fn();
		const send = vi.fn();
		const store = createTreeStore({ onError, send });
		store.getState().dispatch(frame(OPS.watch, ["s"], null));
		expect(onError).toHaveBeenCalledOnce();
		expect(send).not.toHaveBeenCalled();
		expect(store.getState().isWatched(["s"], "change")).toBe(false);
	});
});
