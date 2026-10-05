// TreeRef over the real tree store: what a write leaves on screen, and the
// notify each user intent sends out, its kind named in `event`.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

const NODES = [
	{ key: "src", parent: null, label: "src" },
	{ key: "app", parent: "src", label: "app.ts", badge: "M" },
	{ key: "lib", parent: "src", label: "lib" },
	{ key: "readme", parent: "", label: "README.md", icon: "📄" },
	{ key: "stray", parent: "gone", label: "stray" },
];

function mount(props: Record<string, unknown> = {}) {
	tree.getState().write([["t", "TreeRef", { label: "Files", nodes: NODES, ...props }]]);
	act(() => root.render(<NodeView path={["t"]} />));
}

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

function write(payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: ["t"], payload });
	});
}

const rows = () =>
	[...host.querySelectorAll('[role="treeitem"]')].map((el) => el.getAttribute("data-key"));

function row(key: string): HTMLElement {
	const el = host.querySelector<HTMLElement>(`[role="treeitem"][data-key="${key}"]`);
	if (!el) throw new Error(`no row ${key}`);
	return el;
}

function press(key: string, k: string) {
	act(() => {
		row(key).dispatchEvent(
			new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }),
		);
	});
}

/** Every notify sent so far: all on the tree's own path. */
function notifies(): unknown[] {
	return sent
		.filter((f) => f.op === OPS.notify)
		.map((f) => {
			expect(f.ref).toEqual(["t"]);
			return f.payload;
		});
}

describe("TreeRef", () => {
	it("draws the flat nodes as a tree, an orphan at the top", () => {
		mount();
		expect(host.querySelector('[role="tree"]')?.getAttribute("aria-label")).toBe("Files");
		expect(rows()).toEqual(["src", "readme", "stray"]);
		expect(row("readme").textContent).toContain("📄");
	});

	it("folds and unfolds, sending a toggle each way", () => {
		mount();
		press("src", "ArrowRight");
		expect(rows()).toEqual(["src", "app", "lib", "readme", "stray"]);
		expect(row("app").textContent).toContain("M");
		press("src", "ArrowLeft");
		expect(rows()).toEqual(["src", "readme", "stray"]);
		expect(notifies()).toEqual([
			{ event: "toggle", key: "src", open: true },
			{ event: "toggle", key: "src", open: false },
		]);
	});

	it("selects on click and opens on Enter", () => {
		mount();
		act(() => row("readme").click());
		expect(row("readme").getAttribute("aria-selected")).toBe("true");
		press("readme", "Enter");
		expect(notifies()).toEqual([
			{ event: "select", key: "readme" },
			{ event: "open", key: "readme" },
		]);
	});

	it("takes the server's nodes, selection and fold state as plain writes", () => {
		mount();
		write({ expanded: ["src"], selected: "app" });
		expect(rows()).toEqual(["src", "app", "lib", "readme", "stray"]);
		expect(row("app").getAttribute("aria-selected")).toBe("true");
		write({ nodes: [{ key: "only", label: "Only" }] });
		expect(rows()).toEqual(["only"]);
	});

	it("asks for a rename and leaves the label to the server", () => {
		mount({ editable: true });
		press("readme", "F2");
		const input = row("readme").querySelector("input");
		act(() => {
			if (input) input.value = "NOTES.md";
			input?.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
		});
		expect(notifies()).toEqual([{ event: "rename", key: "readme", title: "NOTES.md" }]);
		expect(row("readme").textContent).toContain("README.md");
	});

	it("takes no rename unless editable", () => {
		mount();
		press("readme", "F2");
		expect(row("readme").querySelector("input")).toBeNull();
	});

	it("drags only when draggable, a top-level parent as ''", () => {
		mount();
		expect(row("readme").draggable).toBe(false);
		act(() => root.unmount());
		tree.getState().remove([]);
		root = createRoot(host);
		mount({ draggable: true, expanded: ["src"] });
		const dataTransfer = { setData() {}, effectAllowed: "", dropEffect: "" };
		const drag = (key: string, type: string) => {
			const e = new Event(type, { bubbles: true, cancelable: true });
			Object.assign(e, { dataTransfer, clientY: 0 });
			act(() => {
				row(key).dispatchEvent(e);
			});
		};
		// jsdom lays nothing out, so every drop lands "into" the row under it.
		drag("app", "dragstart");
		drag("readme", "drop");
		drag("readme", "dragstart");
		act(() => {
			host
				.querySelector('[data-slot="tree-tail"]')
				?.dispatchEvent(
					Object.assign(new Event("drop", { bubbles: true, cancelable: true }), { dataTransfer }),
				);
		});
		expect(notifies()).toEqual([
			{ event: "move", key: "app", parent: "readme", index: 0 },
			{ event: "move", key: "readme", parent: "", index: 2 },
		]);
	});
});
