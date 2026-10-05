// The tree: the pure model (flatten, subtree, where a drop lands) and the
// component's behaviour (roving focus, fold keys, select vs activate, inline
// rename, drag and drop). The look is the story's job.

import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Tree, TreeItem, type TreeProps } from "./tree";
import { dropEdge, dropMove, flattenTree, subtreeOf, type TreeSource } from "./tree-model";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// src/
//   app.ts
//   lib/
//     a.ts
//     b.ts
// README.md
const KIDS: Record<string, string[]> = {
	src: ["app.ts", "lib"],
	lib: ["a.ts", "b.ts"],
};
const SOURCE: TreeSource = {
	roots: ["src", "README.md"],
	childrenOf: (key) => KIDS[key] ?? [],
};

describe("tree model", () => {
	it("flattens only what the fold state shows, with aria positions", () => {
		expect(flattenTree(SOURCE, new Set()).map((r) => r.key)).toEqual(["src", "README.md"]);
		const rows = flattenTree(SOURCE, new Set(["src", "lib"]));
		expect(rows.map((r) => [r.key, r.depth, r.parent, r.pos, r.size])).toEqual([
			["src", 0, null, 1, 2],
			["app.ts", 1, "src", 1, 2],
			["lib", 1, "src", 2, 2],
			["a.ts", 2, "lib", 1, 2],
			["b.ts", 2, "lib", 2, 2],
			["README.md", 0, null, 2, 2],
		]);
		expect(rows[0]?.hasChildren).toBe(true);
		expect(rows[1]?.hasChildren).toBe(false);
	});

	it("takes a key's whole subtree", () => {
		expect(subtreeOf(SOURCE, "src")).toEqual(["src", "app.ts", "lib", "a.ts", "b.ts"]);
		expect(subtreeOf(SOURCE, "README.md")).toEqual(["README.md"]);
	});

	it("reads the edge off the quarter of the row the pointer is in", () => {
		expect(dropEdge(100, 40, 105)).toBe("before");
		expect(dropEdge(100, 40, 120)).toBe("into");
		expect(dropEdge(100, 40, 135)).toBe("after");
	});

	it("places a drop before, after, into, under an open row and at the end", () => {
		const rows = flattenTree(SOURCE, new Set(["src", "lib"]));
		expect(dropMove(SOURCE, rows, "README.md", { key: "app.ts", edge: "before" })).toEqual({
			key: "README.md",
			parent: "src",
			index: 0,
		});
		expect(dropMove(SOURCE, rows, "README.md", { key: "a.ts", edge: "after" })).toEqual({
			key: "README.md",
			parent: "lib",
			index: 1,
		});
		expect(dropMove(SOURCE, rows, "README.md", { key: "lib", edge: "into" })).toEqual({
			key: "README.md",
			parent: "lib",
			index: 2,
		});
		// After an open row with children showing is its first child.
		expect(dropMove(SOURCE, rows, "README.md", { key: "lib", edge: "after" })).toEqual({
			key: "README.md",
			parent: "lib",
			index: 0,
		});
		expect(dropMove(SOURCE, rows, "a.ts", { key: null, edge: "after" })).toEqual({
			key: "a.ts",
			parent: null,
			index: 2,
		});
	});

	it("refuses a drop into its own subtree and one that moves nothing", () => {
		const rows = flattenTree(SOURCE, new Set(["src", "lib"]));
		expect(dropMove(SOURCE, rows, "src", { key: "a.ts", edge: "into" })).toBeNull();
		expect(dropMove(SOURCE, rows, "src", { key: "src", edge: "before" })).toBeNull();
		expect(dropMove(SOURCE, rows, "a.ts", { key: "b.ts", edge: "before" })).toBeNull();
		expect(dropMove(SOURCE, rows, "b.ts", { key: "a.ts", edge: "after" })).toBeNull();
	});
});

// --- The component -----------------------------------------------------------

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

type Spies = Partial<Pick<TreeProps, "onSelect" | "onActivate" | "onRename" | "onMove">>;

/** A tree that keeps its own fold state, the way an app would. */
function Harness({ spies, foldLeaves }: { spies: Spies; foldLeaves?: boolean }) {
	const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
	return (
		<Tree
			aria-label="Files"
			source={SOURCE}
			expanded={expanded}
			onToggle={(key, open) =>
				setExpanded((prev) => {
					const next = new Set(prev);
					if (open) next.add(key);
					else next.delete(key);
					return next;
				})
			}
			foldLeaves={foldLeaves}
			renderEmptyBranch={() => "Empty"}
			{...spies}
			renderItem={(item) => <TreeItem item={item} title={item.row.key} />}
		/>
	);
}

function mount(spies: Spies = {}, foldLeaves = false) {
	act(() => root.render(<Harness spies={spies} foldLeaves={foldLeaves} />));
}

function item(key: string): HTMLElement {
	const el = host.querySelector<HTMLElement>(`[role="treeitem"][data-key="${key}"]`);
	if (!el) throw new Error(`no row ${key}`);
	return el;
}

function visible(): string[] {
	return [...host.querySelectorAll('[role="treeitem"]')].map(
		(el) => el.getAttribute("data-key") ?? "",
	);
}

function press(el: HTMLElement, key: string) {
	act(() => {
		el.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }));
	});
}

describe("Tree", () => {
	it("is one tab stop with the tree's aria", () => {
		mount();
		expect(host.querySelector('[role="tree"]')?.getAttribute("aria-label")).toBe("Files");
		expect(item("src").tabIndex).toBe(0);
		expect(item("README.md").tabIndex).toBe(-1);
		expect(item("src").getAttribute("aria-expanded")).toBe("false");
		expect(item("README.md").hasAttribute("aria-expanded")).toBe(false);
		expect(item("src").getAttribute("aria-level")).toBe("1");
	});

	it("unfolds, steps in, climbs out and folds with the arrows", () => {
		mount();
		act(() => item("src").focus());
		press(item("src"), "ArrowRight");
		expect(visible()).toEqual(["src", "app.ts", "lib", "README.md"]);
		press(item("src"), "ArrowRight");
		expect(document.activeElement).toBe(item("app.ts"));
		press(item("app.ts"), "ArrowDown");
		expect(document.activeElement).toBe(item("lib"));
		expect(item("lib").tabIndex).toBe(0);
		press(item("lib"), "ArrowLeft");
		expect(document.activeElement).toBe(item("src"));
		press(item("src"), "ArrowLeft");
		expect(visible()).toEqual(["src", "README.md"]);
		press(item("src"), "End");
		expect(document.activeElement).toBe(item("README.md"));
	});

	it("does not unfold a leaf, unless the tree folds leaves", () => {
		mount();
		press(item("README.md"), "ArrowRight");
		expect(host.textContent).not.toContain("Empty");
		act(() => root.unmount());
		root = createRoot(host);
		mount({}, true);
		press(item("README.md"), "ArrowRight");
		expect(item("README.md").getAttribute("aria-expanded")).toBe("true");
		expect(host.textContent).toContain("Empty");
	});

	it("folds on a chevron click without selecting", () => {
		const onSelect = vi.fn();
		mount({ onSelect });
		const chevron = item("src").querySelector("button");
		act(() => chevron?.click());
		expect(visible()).toContain("app.ts");
		expect(onSelect).not.toHaveBeenCalled();
	});

	it("selects on click and Space, activates on Enter and double click", () => {
		const onSelect = vi.fn();
		const onActivate = vi.fn();
		mount({ onSelect, onActivate });
		act(() => item("README.md").click());
		expect(onSelect).toHaveBeenLastCalledWith("README.md");
		press(item("src"), " ");
		expect(onSelect).toHaveBeenLastCalledWith("src");
		press(item("src"), "Enter");
		expect(onActivate).toHaveBeenLastCalledWith("src", expect.anything());
		act(() => {
			item("README.md").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		});
		expect(onActivate).toHaveBeenLastCalledWith("README.md", expect.anything());
	});

	it("lets a claimed key through to the app first", () => {
		const onActivate = vi.fn();
		act(() =>
			root.render(
				<Tree
					aria-label="Files"
					source={SOURCE}
					expanded={new Set()}
					onToggle={() => {}}
					onActivate={onActivate}
					onItemKeyDown={(e) => {
						if (e.key === "Enter") e.preventDefault();
					}}
					renderItem={(i) => <TreeItem item={i} title={i.row.key} />}
				/>,
			),
		);
		press(item("src"), "Enter");
		expect(onActivate).not.toHaveBeenCalled();
	});

	it("renames in place on F2, committing only a real change", () => {
		const onRename = vi.fn();
		mount({ onRename });
		press(item("README.md"), "F2");
		const input = item("README.md").querySelector("input");
		expect(input?.value).toBe("README.md");
		expect(input?.getAttribute("aria-label")).toBe("Rename README.md");
		act(() => {
			if (input) input.value = "  NOTES.md ";
			input?.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
		});
		expect(onRename).toHaveBeenCalledWith("README.md", "NOTES.md");
		expect(item("README.md").querySelector("input")).toBeNull();
		expect(document.activeElement).toBe(item("README.md"));

		press(item("src"), "F2");
		act(() => {
			item("src")
				.querySelector("input")
				?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
		});
		expect(onRename).toHaveBeenCalledTimes(1);
	});

	it("takes no rename without onRename", () => {
		mount();
		press(item("src"), "F2");
		expect(item("src").querySelector("input")).toBeNull();
	});

	it("drags a row into another and reports the move", () => {
		const onMove = vi.fn();
		mount({ onMove });
		expect(item("README.md").draggable).toBe(true);
		const data = new Map<string, string>();
		const dataTransfer = {
			setData: (t: string, v: string) => data.set(t, v),
			getData: (t: string) => data.get(t) ?? "",
			effectAllowed: "",
			dropEffect: "",
		};
		const drag = (el: HTMLElement, type: string, clientY = 0) => {
			const e = new Event(type, { bubbles: true, cancelable: true });
			Object.assign(e, { dataTransfer, clientY });
			act(() => {
				el.dispatchEvent(e);
			});
		};
		// jsdom lays nothing out: every rect is 0 tall, so any pointer is "into".
		drag(item("README.md"), "dragstart");
		drag(item("src"), "dragover");
		drag(item("src"), "drop");
		expect(onMove).toHaveBeenCalledWith({ key: "README.md", parent: "src", index: 2 });

		// Its own subtree takes no drop.
		onMove.mockClear();
		drag(item("src"), "dragstart");
		drag(item("src"), "drop");
		expect(onMove).not.toHaveBeenCalled();
	});

	it("draws no drag without onMove", () => {
		mount();
		expect(item("src").draggable).toBe(false);
		expect(host.querySelector('[data-slot="tree-tail"]')).toBeNull();
	});
});
