// HistoryRef over the real tree store: a write moves the page through
// History, and every move but the ones this ref's own writes caused comes
// back as a notify.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { History, NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	window.history.replaceState(null, "", "/start");
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

function mount(type = "HistoryRef", segment = "nav") {
	act(() => {
		tree.getState().write([[segment, type, {}]]);
		root.render(<NodeView path={[segment]} />);
	});
}

function write(payload: unknown, segment = "nav") {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: [segment], payload });
	});
}

/** A popstate, the way the browser lands a traversal: the address has already moved. */
function pop(url: string, state: unknown = null) {
	act(() => {
		window.history.replaceState(state, "", url);
		window.dispatchEvent(new PopStateEvent("popstate", { state }));
	});
}

/** Run `go` and wait for the popstate it causes, all inside act. */
async function traversal(go: () => void): Promise<void> {
	await act(async () => {
		const landed = new Promise((resolve) => {
			window.addEventListener("popstate", resolve, { once: true });
		});
		go();
		await landed;
	});
}

const dispatch = (payload: unknown) =>
	tree.getState().dispatch({ op: OPS.write, ref: ["nav"], payload });

const value = () => tree.getState().getIn(["nav"])?.props.value;
const notifies = () => sent.filter((f) => f.op === OPS.notify).map((f) => f.payload);

describe("HistoryRef", () => {
	it("pushes and replaces, with state", () => {
		mount();
		write("/feed");
		expect(window.location.pathname).toBe("/feed");
		expect(value()).toBe("/feed");
		const depth = window.history.length;
		write({ action: "replace", uri: "/other?x=1", state: { panes: [1] } });
		expect(History.current().url).toBe("/other?x=1");
		expect(History.current().state).toEqual({ panes: [1] });
		expect(window.history.length).toBe(depth);
		write({ action: "push", uri: "/third", state: { a: 1 } });
		expect(window.history.length).toBe(depth + 1);
		expect(History.current().state).toEqual({ a: 1 });
		// None of those were echoed: the server asked for each.
		expect(notifies()).toEqual([]);
	});

	it("still draws under the old NavRef name", () => {
		mount("NavRef");
		write("/old");
		expect(window.location.pathname).toBe("/old");
		expect(notifies()).toEqual([]);
	});

	it("reports a move it did not make", () => {
		mount();
		pop("/elsewhere");
		expect(value()).toBe("/elsewhere");
		act(() => {
			History.push("/routed");
		});
		expect(notifies()).toEqual(["/elsewhere", "/routed"]);
	});

	it("does not echo its own back and forward, but does the user's", async () => {
		mount();
		write("/a");
		await traversal(() => dispatch({ action: "back" }));
		expect(window.location.pathname).toBe("/start");
		expect(value()).toBe("/start");
		await traversal(() => dispatch({ action: "forward" }));
		expect(value()).toBe("/a");
		expect(notifies()).toEqual([]);
		// The user's back button: the same traversal, nobody's write.
		await traversal(() => window.history.back());
		expect(notifies()).toEqual(["/start"]);
	});

	it("reports another HistoryRef's moves", () => {
		mount();
		act(() => tree.getState().write([["other", "HistoryRef", {}]]));
		write("/from-other", "other");
		expect(notifies()).toEqual(["/from-other"]);
		expect(sent.find((f) => f.op === OPS.notify)?.ref).toEqual(["nav"]);
	});

	it("merges the query with a replace, keeping path, hash and state", () => {
		mount();
		write({ action: "replace", uri: "/list?q=old&page=2#top", state: { k: 1 } });
		const depth = window.history.length;
		write({ action: "set_query", query: { q: "new term", page: null, sort: true } });
		expect(History.current().url).toBe("/list?q=new+term&sort=true#top");
		expect(History.current().query).toEqual({ q: "new term", sort: "true" });
		expect(History.current().state).toEqual({ k: 1 });
		expect(window.history.length).toBe(depth);
		expect(notifies()).toEqual([]);
	});

	it("skips a push to the entry it is on", () => {
		mount();
		write("/same");
		const depth = window.history.length;
		write("/same");
		expect(window.history.length).toBe(depth);
		write({ action: "push", uri: "/same", state: { x: 1 } });
		expect(window.history.length).toBe(depth + 1);
	});

	it("reads the live entry", () => {
		mount();
		window.history.replaceState({ s: 1 }, "", "/live?x=1&y=a+b#h");
		act(() => {
			tree.getState().dispatch({ op: OPS.read, ref: ["nav"], payload: null, id: "r1" });
		});
		const read = sent.find((f) => f.op === OPS.read);
		expect(read?.payload).toEqual({
			uri: "/live?x=1&y=a+b#h",
			path: "/live",
			query: { x: "1", y: "a b" },
			hash: "#h",
			state: { s: 1 },
		});
		expect(read?.id).toBe("r1");
	});
});
