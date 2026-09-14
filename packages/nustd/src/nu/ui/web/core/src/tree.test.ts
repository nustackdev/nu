// The tree store, tested in isolation: no React, no socket, no server.
// Everything below is a plain frame in and a plain node out.

import { describe, expect, it, vi } from "vitest";
import {
	type Behaviour,
	type ChainStep,
	OPS,
	type TreeFrame,
	createTreeStore,
} from "./tree";

function step(segment: string, type: string | null = null, props?: Record<string, unknown>): ChainStep {
	return props ? [segment, type, props] : [segment, type];
}

function frame(op: string, ref: string[], payload?: unknown, chain?: ChainStep[]): TreeFrame {
	return { op, ref, payload, chain };
}

describe("write", () => {
	it("autovivifies every level in one go", () => {
		const store = createTreeStore();
		store.getState().write([step("page", "Page"), step("form", "Form"), step("inp", "InputRef")], {
			value: "hi",
		});

		const root = store.getState().root;
		expect(Object.keys(root.children)).toEqual(["page"]);
		expect(root.children.page.type).toBe("Page");
		expect(root.children.page.children.form.type).toBe("Form");
		const inp = store.getState().getIn(["page", "form", "inp"]);
		expect(inp).toEqual({ type: "InputRef", props: { value: "hi" }, children: {} });
	});

	it("leaves a level untyped when the chain does not name a type", () => {
		const store = createTreeStore();
		store.getState().write([step("a"), step("b", "TextRef")], { value: 1 });
		expect(store.getState().getIn(["a"])?.type).toBeNull();
		expect(store.getState().getIn(["b"])).toBeNull();
	});

	it("claims an untyped level when a later write names its type", () => {
		const store = createTreeStore();
		store.getState().write([step("a"), step("b", "TextRef")]);
		store.getState().write([step("a", "Column", { gap: 2 })]);
		expect(store.getState().getIn(["a"])?.type).toBe("Column");
		// The child that caused the autovivify is still there.
		expect(store.getState().getIn(["a", "b"])?.type).toBe("TextRef");
	});

	it("merges the payload into a level that already exists", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "InputRef", { label: "Name", value: "" })]);
		store.getState().write([step("a", "InputRef")], { value: "gor" });
		expect(store.getState().getIn(["a"])?.props).toEqual({ label: "Name", value: "gor" });
	});

	it("seeds chain props on creation only, never as an update", () => {
		const store = createTreeStore();
		store.getState().write([step("sec", "Card", { title: "One" }), step("t", "TextRef")]);
		// Same chain, same declared props, new child below it. The declared
		// title must not come back and overwrite a runtime one.
		store.getState().setProps(["sec"], { title: "Live" });
		store.getState().write([step("sec", "Card", { title: "One" }), step("u", "TextRef")]);
		expect(store.getState().getIn(["sec"])?.props).toEqual({ title: "Live" });
		expect(Object.keys(store.getState().getIn(["sec"])?.children ?? {})).toEqual(["t", "u"]);
	});

	it("keeps a prop set at runtime when a deep write rides through", () => {
		const store = createTreeStore();
		const chain = [
			step("page", "Page", { title: "Page" }),
			step("sec", "Section", { variant: "plain" }),
			step("t", "TextRef", { value: "" }),
		];
		store.getState().write(chain);
		store.getState().setProps(["page", "sec"], { variant: "auto-scroll" });
		store.getState().write(chain, { value: "tick" });
		expect(store.getState().getIn(["page", "sec"])?.props).toEqual({ variant: "auto-scroll" });
		expect(store.getState().getIn(["page", "sec", "t"])?.props.value).toBe("tick");
	});

	it("skips the walk when the leaf is already there", () => {
		const store = createTreeStore();
		store.getState().write([step("sec", "Card", { title: "One" }), step("t", "TextRef")]);
		store.getState().write([step("sec", "Card", { title: "Two" }), step("t", "TextRef")], {
			value: "x",
		});
		expect(store.getState().getIn(["sec"])?.props).toEqual({ title: "One" });
		expect(store.getState().getIn(["sec", "t"])?.props).toEqual({ value: "x" });
	});

	it("rebuilds a node whose type changed and disposes the old branch", () => {
		const gone: string[][] = [];
		const behaviours: Record<string, Behaviour> = {
			Card: { dispose: (ctx) => gone.push(ctx.path) },
			TextRef: { dispose: (ctx) => gone.push(ctx.path) },
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t] });
		store.getState().write([step("sec", "Card", { title: "One" }), step("t", "TextRef")]);
		store.getState().write([step("sec", "Modal", { open: true })]);

		expect(gone).toEqual([
			["sec", "t"],
			["sec"],
		]);
		expect(store.getState().getIn(["sec"])).toEqual({
			type: "Modal",
			props: { open: true },
			children: {},
		});
	});

	it("keeps a node whose write does not name a type", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "InputRef", { value: "x" })]);
		store.getState().write([step("a")], { value: "y" });
		expect(store.getState().getIn(["a"])).toEqual({
			type: "InputRef",
			props: { value: "y" },
			children: {},
		});
	});

	it("treats a segment with a dot as one segment", () => {
		const store = createTreeStore();
		store.getState().write([step("a.b", "Card"), step("c.d", "TextRef", { value: 1 })]);
		expect(store.getState().getIn(["a.b", "c.d"])?.props).toEqual({ value: 1 });
		expect(store.getState().getIn(["a", "b", "c", "d"])).toBeNull();
		expect(Object.keys(store.getState().root.children)).toEqual(["a.b"]);
	});

	it("writes into the root with an empty chain", () => {
		const store = createTreeStore();
		store.getState().write([], { title: "root" });
		expect(store.getState().root.props).toEqual({ title: "root" });
	});
});

describe("getIn", () => {
	it("returns null for a path that is not there", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "Card")]);
		expect(store.getState().getIn(["a", "nope"])).toBeNull();
		expect(store.getState().getIn(["nope"])).toBeNull();
	});

	it("returns the root for an empty path", () => {
		const store = createTreeStore();
		expect(store.getState().getIn([])).toBe(store.getState().root);
	});
});

describe("remove", () => {
	it("drops the subtree and disposes descendants first", () => {
		const gone: string[][] = [];
		const dispose = (ctx: { path: string[] }) => gone.push(ctx.path);
		const behaviours: Record<string, Behaviour> = {
			Card: { dispose },
			Column: { dispose },
			TextRef: { dispose },
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t] });
		store
			.getState()
			.write([step("sec", "Card"), step("col", "Column"), step("t", "TextRef", { value: 1 })]);
		store.getState().write([step("other", "TextRef")]);

		store.getState().remove(["sec"]);

		expect(gone).toEqual([
			["sec", "col", "t"],
			["sec", "col"],
			["sec"],
		]);
		expect(store.getState().getIn(["sec"])).toBeNull();
		expect(store.getState().getIn(["other"])?.type).toBe("TextRef");
	});

	it("hands dispose a live snapshot, not a dead draft", () => {
		const seen: unknown[] = [];
		const store = createTreeStore({
			resolve: () => ({ dispose: (ctx) => seen.push(ctx.node.props.value) }),
		});
		store.getState().write([step("a", "TextRef", { value: "keep" })]);
		store.getState().remove(["a"]);
		expect(seen).toEqual(["keep"]);
	});

	it("skips untyped nodes when disposing", () => {
		const dispose = vi.fn();
		const store = createTreeStore({ resolve: () => ({ dispose }) });
		store.getState().write([step("a"), step("b")]);
		store.getState().remove(["a"]);
		expect(dispose).not.toHaveBeenCalled();
	});

	it("is a no-op for a path that is not there", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "Card")]);
		store.getState().remove(["nope", "deeper"]);
		expect(store.getState().getIn(["a"])?.type).toBe("Card");
	});

	it("clears everything for an empty path", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "Card"), step("b", "TextRef")]);
		store.getState().remove([]);
		expect(store.getState().root).toEqual({ type: null, props: {}, children: {} });
	});
});

describe("dispatch", () => {
	it("creates the node on the first write it sees", () => {
		const store = createTreeStore();
		store
			.getState()
			.dispatch(
				frame(OPS.write, ["page", "inp"], "hello", [step("page", "Page"), step("inp", "InputRef")]),
			);
		expect(store.getState().getIn(["page", "inp"])).toEqual({
			type: "InputRef",
			props: { value: "hello" },
			children: {},
		});
	});

	it("merges an object payload as props", () => {
		const store = createTreeStore();
		store
			.getState()
			.dispatch(frame(OPS.write, ["a"], { label: "L", value: 2 }, [step("a", "InputRef")]));
		expect(store.getState().getIn(["a"])?.props).toEqual({ label: "L", value: 2 });
	});

	it("lands a list payload on value rather than spreading it", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.write, ["a"], [1, 2, 3], [step("a", "TableRef")]));
		expect(store.getState().getIn(["a"])?.props).toEqual({ value: [1, 2, 3] });
	});

	it("walks the ref untyped when a frame arrives with no chain", () => {
		const store = createTreeStore();
		store.getState().dispatch(frame(OPS.write, ["a", "b"], "x"));
		expect(store.getState().getIn(["a"])?.type).toBeNull();
		expect(store.getState().getIn(["a", "b"])).toEqual({
			type: null,
			props: { value: "x" },
			children: {},
		});
	});

	it("keeps a typed node's type when a chainless write lands on it", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "InputRef", { label: "L" })]);
		store.getState().dispatch(frame(OPS.write, ["a"], "typed"));
		expect(store.getState().getIn(["a"])).toEqual({
			type: "InputRef",
			props: { label: "L", value: "typed" },
			children: {},
		});
	});

	it("routes an op to the handler for the node's type", () => {
		const behaviours: Record<string, Behaviour> = {
			TableRef: {
				handlers: {
					append: (ctx, payload) =>
						ctx.update((props) => {
							props.rows = [...((props.rows as unknown[]) ?? []), payload];
						}),
				},
			},
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t] });
		store.getState().write([step("t", "TableRef", { rows: [] })]);
		store.getState().dispatch(frame("append", ["t"], { id: 1 }));
		store.getState().dispatch(frame("append", ["t"], { id: 2 }));
		expect(store.getState().getIn(["t"])?.props.rows).toEqual([{ id: 1 }, { id: 2 }]);
	});

	it("gives a type's own write handler the raw payload", () => {
		const behaviours: Record<string, Behaviour> = {
			InputRef: {
				handlers: {
					// A null write must not make the input uncontrolled.
					write: (ctx, payload) =>
						ctx.update((props) => {
							props.value = payload == null ? "" : String(payload);
						}),
				},
			},
		};
		const store = createTreeStore({ resolve: (t) => behaviours[t] });
		store.getState().dispatch(frame(OPS.write, ["i"], null, [step("i", "InputRef")]));
		expect(store.getState().getIn(["i"])?.props).toEqual({ value: "" });
	});

	it("removes on a remove frame", () => {
		const store = createTreeStore();
		store.getState().write([step("a", "Card"), step("b", "TextRef")]);
		store.getState().dispatch(frame(OPS.remove, ["a"]));
		expect(store.getState().getIn(["a"])).toBeNull();
	});

	it("answers a read with the node's value and the same id", () => {
		const sent: TreeFrame[] = [];
		const store = createTreeStore({ send: (f) => sent.push(f) });
		store.getState().write([step("a", "InputRef", { value: "gor" })]);
		store.getState().dispatch({ op: OPS.read, ref: ["a"], payload: null, id: "f1" });
		expect(sent).toEqual([{ op: OPS.read, ref: ["a"], payload: "gor", id: "f1" }]);
	});

	it("lets a type answer a read itself", () => {
		const sent: TreeFrame[] = [];
		const behaviours: Record<string, Behaviour> = {
			ProseRef: {
				handlers: {
					read: (ctx) => ctx.send(OPS.read, `md:${ctx.node.props.value}`, ctx.frame.id),
				},
			},
		};
		const store = createTreeStore({ send: (f) => sent.push(f), resolve: (t) => behaviours[t] });
		store.getState().write([step("p", "ProseRef", { value: "hi" })]);
		store.getState().dispatch({ op: OPS.read, ref: ["p"], payload: null, id: "f2" });
		expect(sent).toEqual([{ op: OPS.read, ref: ["p"], payload: "md:hi", id: "f2" }]);
	});

	it("reports an op on a node that is not there", () => {
		const errors: string[] = [];
		const store = createTreeStore({ onError: (m) => errors.push(m) });
		store.getState().dispatch(frame("append", ["nope"], 1));
		expect(errors).toHaveLength(1);
	});

	it("reports an op the node's type does not support", () => {
		const errors: string[] = [];
		const store = createTreeStore({ onError: (m) => errors.push(m) });
		store.getState().write([step("a", "TextRef")]);
		store.getState().dispatch(frame("append", ["a"], 1));
		expect(errors).toHaveLength(1);
	});
});

describe("send", () => {
	it("drops frames until a sender is set, then delivers", () => {
		const sent: TreeFrame[] = [];
		const store = createTreeStore();
		store.getState().send({ op: OPS.notify, ref: ["a"], payload: null });
		store.getState().setSender((f) => sent.push(f));
		store.getState().send({ op: OPS.notify, ref: ["a"], payload: null });
		expect(sent).toHaveLength(1);
	});
});

describe("subscription", () => {
	it("shares structure so an untouched branch keeps its identity", () => {
		const store = createTreeStore();
		store.getState().write([step("left", "Card"), step("t", "TextRef", { value: 1 })]);
		store.getState().write([step("right", "Card"), step("t", "TextRef", { value: 1 })]);
		const leftBefore = store.getState().getIn(["left"]);

		store.getState().write([step("right", "Card"), step("t", "TextRef")], { value: 2 });

		expect(store.getState().getIn(["left"])).toBe(leftBefore);
		expect(store.getState().getIn(["right"])).not.toBe(undefined);
		expect(store.getState().getIn(["right", "t"])?.props.value).toBe(2);
	});
});
