// NavRef over the real tree store: a write moves the page through the active
// navigator, plain history by default or whatever a host installed, and only
// moves the server did not ask for come back as a notify.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, setNavigator, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	window.history.replaceState({}, "", "/start");
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
	setNavigator(null);
});

function mount() {
	act(() => {
		tree.getState().write([["nav", "NavRef", {}]]);
		root.render(<NodeView path={["nav"]} />);
	});
}

function write(payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: ["nav"], payload });
	});
}

const value = () => tree.getState().getIn(["nav"])?.props.value;
const notifies = () => sent.filter((f) => f.op === OPS.notify).map((f) => f.payload);

describe("NavRef", () => {
	it("pushes and replaces on plain history", () => {
		mount();
		write("/feed");
		expect(window.location.pathname).toBe("/feed");
		expect(value()).toBe("/feed");
		const depth = window.history.length;
		write({ action: "replace", uri: "/other" });
		expect(window.location.pathname).toBe("/other");
		expect(window.history.length).toBe(depth);
		expect(notifies()).toEqual([]);
	});

	it("notifies a move it did not make", () => {
		mount();
		act(() => {
			window.history.pushState({}, "", "/elsewhere");
			window.dispatchEvent(new PopStateEvent("popstate"));
		});
		expect(value()).toBe("/elsewhere");
		expect(notifies()).toEqual(["/elsewhere"]);
	});

	it("moves through a host navigator", () => {
		const pushed: string[] = [];
		const listeners = new Set<() => void>();
		let at = "/a";
		setNavigator({
			push: (uri) => {
				pushed.push(uri);
				at = `/routed${uri}`;
				for (const fn of listeners) fn();
			},
			current: () => at,
			subscribe: (fn) => {
				listeners.add(fn);
				return () => listeners.delete(fn);
			},
		});
		mount();
		expect(value()).toBe("/a");
		write("/b");
		expect(pushed).toEqual(["/b"]);
		// The host decided where it landed, and the write was not echoed.
		expect(value()).toBe("/routed/b");
		expect(notifies()).toEqual([]);
		// A move of the host's own is.
		act(() => {
			at = "/c";
			for (const fn of listeners) fn();
		});
		expect(notifies()).toEqual(["/c"]);
		// A report that leaves the uri where it was is no move.
		act(() => {
			for (const fn of listeners) fn();
		});
		expect(notifies()).toEqual(["/c"]);
	});

	it("reads the live uri", () => {
		mount();
		window.history.replaceState({}, "", "/live?x=1");
		act(() => {
			tree.getState().dispatch({ op: OPS.read, ref: ["nav"], payload: null, id: "r1" });
		});
		const read = sent.find((f) => f.op === OPS.read);
		expect(read?.payload).toBe("/live?x=1");
		expect(read?.id).toBe("r1");
	});
});
