// A node sends only what the server watches.
//
// The setup file counts every event as watched for the rest of the kit's
// tests; here that is off, and the server's `watch` / `unwatch` frames go
// through the store as they do over the wire.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { emit } from "./emit";
import { EVENTS } from "./events";
import { NodeView } from "./NodeView";
import { flushOutbox, unbatch } from "./outbox";
import { tree } from "./store";
import { ANY, isWatched } from "./watch";
import "../nodes";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let sent: TreeFrame[] = [];

const notifies = () => unbatch(sent).filter((f) => f.op === OPS.notify);

function server(op: string, ref: string[], event: string) {
	act(() => tree.getState().dispatch({ op, ref, payload: { event } }));
}

beforeEach(() => {
	sent = [];
	tree.getState().setWatchAll(false);
	tree.getState().setSender((f) => sent.push(f));
});

afterEach(() => {
	flushOutbox();
	tree.getState().setSender(null);
	tree.getState().remove([]);
	tree.getState().unwatchAll();
});

describe("emit", () => {
	it("sends nothing for an event nobody watches", () => {
		emit(["w", "s"], EVENTS.change, { value: 1 });
		flushOutbox();
		expect(sent).toEqual([]);
	});

	it("sends the watched event and only that one", () => {
		server(OPS.watch, ["w", "s"], EVENTS.change);
		emit(["w", "s"], EVENTS.input, { value: 1 });
		emit(["w", "s"], EVENTS.change, { value: 1 });
		emit(["w", "t"], EVENTS.change, { value: 1 });
		flushOutbox();
		expect(notifies()).toEqual([
			{ op: OPS.notify, ref: ["w", "s"], payload: { event: "change", value: 1 } },
		]);
	});

	it("sends every event under a * watch", () => {
		server(OPS.watch, ["w", "t"], ANY);
		emit(["w", "t"], EVENTS.select, { value: "a" });
		emit(["w", "t"], "toggle");
		flushOutbox();
		expect(notifies().map((f) => (f.payload as { event: string }).event)).toEqual([
			"select",
			"toggle",
		]);
	});

	it("stops after unwatch", () => {
		server(OPS.watch, ["w", "s"], EVENTS.change);
		server(OPS.unwatch, ["w", "s"], EVENTS.change);
		emit(["w", "s"], EVENTS.change, { value: 1 });
		flushOutbox();
		expect(sent).toEqual([]);
		expect(isWatched(["w", "s"], EVENTS.change)).toBe(false);
	});
});

describe("a drawn node", () => {
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
	});

	function mountButton() {
		act(() => {
			tree.getState().write([["b", "ButtonRef", { label: "Go" }]]);
			root.render(<NodeView path={["b"]} />);
		});
	}

	const click = () => act(() => host.querySelector<HTMLButtonElement>("button")?.click());

	it("sends no click nobody watches", () => {
		mountButton();
		click();
		flushOutbox();
		expect(sent).toEqual([]);
	});

	it("sends the click once watched, even when the watch came first", () => {
		server(OPS.watch, ["b"], EVENTS.click);
		mountButton();
		click();
		flushOutbox();
		expect(notifies()).toEqual([{ op: OPS.notify, ref: ["b"], payload: { event: "click" } }]);
	});

	it("keeps the watch across a remove and a redraw", () => {
		server(OPS.watch, ["b"], EVENTS.click);
		mountButton();
		act(() => tree.getState().dispatch({ op: OPS.remove, ref: ["b"], payload: null }));
		mountButton();
		click();
		flushOutbox();
		expect(notifies()).toHaveLength(1);
	});
});
