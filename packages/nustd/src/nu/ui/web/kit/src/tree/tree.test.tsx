// The React bindings over the tree store.
//
// What is worth pinning here is not that a value shows up on screen, it is
// who re-renders when it does. A node's props change must not wake its
// siblings, and a node appearing somewhere else in the tree must not wake an
// unrelated parent. Both fall out of immer's structural sharing plus a
// shallow compare on the child list, so both are easy to lose by accident.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { OPS, type Path } from "@nustackdev/ui-core";
import { NodeChildren, NodeView } from "./NodeView";
import { useChildren, useProps, useStringProp } from "./hooks";
import { registry, register } from "./registry";
import { tree } from "./store";

// React 19 wants this before render or it logs a warning per test.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
const registered: string[] = [];

function add(type: string, entry: Parameters<typeof register>[1]) {
	register(type, entry);
	registered.push(type);
}

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	for (const type of registered.splice(0)) delete registry[type];
});

// Counts renders per path so a test can assert who woke up.
const renders: Record<string, number> = {};
function bump(path: Path) {
	const key = path.join("/");
	renders[key] = (renders[key] ?? 0) + 1;
}

function Leaf({ path }: { path: Path }) {
	bump(path);
	const value = useStringProp(path, "value");
	return <span data-testid={path.join("/")}>{value}</span>;
}

function Box({ path }: { path: Path }) {
	bump(path);
	const children = useChildren(path);
	return (
		<div data-testid={path.join("/")} data-children={children.join(",")}>
			<NodeChildren path={path} />
		</div>
	);
}

function text(testid: string): string | null {
	return host.querySelector(`[data-testid="${testid}"]`)?.textContent ?? null;
}

describe("useNode", () => {
	beforeEach(() => {
		for (const k in renders) delete renders[k];
		add("Leaf", { component: Leaf });
		add("Box", { component: Box });
	});

	it("re-renders on the node's own change", () => {
		tree.getState().write([["a", "Leaf", { value: "one" }]]);
		mount(<NodeView path={["a"]} />);
		expect(text("a")).toBe("one");

		act(() => {
			tree.getState().setProps(["a"], { value: "two" });
		});
		expect(text("a")).toBe("two");
	});

	it("does not re-render a node when a sibling changes", () => {
		tree.getState().write([["box", "Box"], ["a", "Leaf", { value: "a" }]]);
		tree.getState().write([["box", "Box"], ["b", "Leaf", { value: "b" }]]);
		mount(<NodeView path={["box"]} />);
		const before = renders["box/a"];

		act(() => {
			tree.getState().setProps(["box", "b"], { value: "b2" });
		});

		expect(text("box/b")).toBe("b2");
		expect(renders["box/a"]).toBe(before);
	});

	it("does not re-render a parent when a child's props change", () => {
		tree.getState().write([["box", "Box"], ["a", "Leaf", { value: "a" }]]);
		mount(<NodeView path={["box"]} />);
		const before = renders.box;

		act(() => {
			tree.getState().setProps(["box", "a"], { value: "a2" });
		});

		expect(text("box/a")).toBe("a2");
		expect(renders.box).toBe(before);
	});
});

describe("useChildren", () => {
	beforeEach(() => {
		for (const k in renders) delete renders[k];
		add("Leaf", { component: Leaf });
		add("Box", { component: Box });
	});

	it("picks up a child that autovivifies later", () => {
		tree.getState().write([["box", "Box"]]);
		mount(<NodeView path={["box"]} />);
		expect(text("box")).toBe("");

		act(() => {
			tree.getState().write([["box", "Box"], ["late", "Leaf", { value: "hi" }]]);
		});
		expect(text("box/late")).toBe("hi");
	});

	it("keeps insertion order", () => {
		mount(<NodeView path={["box"]} />);
		act(() => {
			for (const seg of ["z", "m", "a"]) {
				tree.getState().write([["box", "Box"], [seg, "Leaf", { value: seg }]]);
			}
		});
		expect(host.querySelector('[data-testid="box"]')?.getAttribute("data-children")).toBe("z,m,a");
	});

	it("does not re-render a parent when a node appears elsewhere", () => {
		tree.getState().write([["box", "Box"], ["a", "Leaf", { value: "a" }]]);
		tree.getState().write([["other", "Box"]]);
		mount(<NodeView path={["box"]} />);
		const before = renders.box;

		act(() => {
			tree.getState().write([["other", "Box"], ["new", "Leaf", { value: "n" }]]);
		});

		expect(renders.box).toBe(before);
	});

	it("re-renders the parent when its own child list changes", () => {
		tree.getState().write([["box", "Box"], ["a", "Leaf", { value: "a" }]]);
		mount(<NodeView path={["box"]} />);
		const before = renders.box;

		act(() => {
			tree.getState().write([["box", "Box"], ["b", "Leaf", { value: "b" }]]);
		});

		expect(renders.box).toBe(before + 1);
		expect(text("box/b")).toBe("b");
	});
});

describe("NodeView", () => {
	beforeEach(() => {
		for (const k in renders) delete renders[k];
		add("Leaf", { component: Leaf });
		add("Box", { component: Box });
	});

	it("recurses to any depth", () => {
		tree.getState().write([
			["a", "Box"],
			["b", "Box"],
			["c", "Leaf", { value: "deep" }],
		]);
		mount(<NodeView path={["a"]} />);
		expect(text("a/b/c")).toBe("deep");
	});

	it("renders the children of an untyped node", () => {
		// `mid` only exists because something below it was written.
		tree.getState().write([["top", "Box"], ["mid"], ["leaf", "Leaf", { value: "through" }]]);
		mount(<NodeView path={["top"]} />);
		expect(text("top/mid/leaf")).toBe("through");
	});

	it("says so when a type has no component", () => {
		tree.getState().write([["a", "NobodyRegisteredThis"]]);
		mount(<NodeView path={["a"]} />);
		expect(host.textContent).toContain("no component for NobodyRegisteredThis");
	});

	it("drops a subtree the server removed", () => {
		tree.getState().write([["box", "Box"], ["a", "Leaf", { value: "a" }]]);
		mount(<NodeView path={["box"]} />);
		expect(text("box/a")).toBe("a");

		act(() => {
			tree.getState().dispatch({ op: OPS.remove, ref: ["box", "a"], payload: null });
		});
		expect(text("box/a")).toBeNull();
	});
});

describe("registry", () => {
	it("routes an inbound frame to the type's handler and the view follows", () => {
		add("Counter", {
			component: ({ path }) => <span data-testid="c">{useProps(path).hits as number}</span>,
			handlers: {
				bump: (ctx) =>
					ctx.update((props) => {
						props.hits = ((props.hits as number) ?? 0) + 1;
					}),
			},
		});
		tree.getState().write([["c", "Counter", { hits: 0 }]]);
		mount(<NodeView path={["c"]} />);
		expect(text("c")).toBe("0");

		act(() => {
			tree.getState().dispatch({ op: "bump", ref: ["c"], payload: null });
		});
		expect(text("c")).toBe("1");
	});

	it("autovivifies a component from a write to a path nobody mounted", () => {
		add("Leaf", { component: Leaf });
		add("Box", { component: Box });
		mount(<NodeView path={["box"]} />);

		act(() => {
			tree.getState().dispatch({
				op: OPS.write,
				ref: ["box", "fresh"],
				payload: "appeared",
				chain: [
					["box", "Box", {}],
					["fresh", "Leaf", {}],
				],
			});
		});

		expect(text("box/fresh")).toBe("appeared");
	});

	it("runs dispose when the server removes the node", () => {
		const gone: string[] = [];
		add("Held", {
			component: Leaf,
			dispose: (ctx) => gone.push(ctx.path.join("/")),
		});
		tree.getState().write([["h", "Held", { value: "x" }]]);
		mount(<NodeView path={["h"]} />);

		act(() => {
			tree.getState().dispatch({ op: OPS.remove, ref: ["h"], payload: null });
		});
		expect(gone).toEqual(["h"]);
	});
});
