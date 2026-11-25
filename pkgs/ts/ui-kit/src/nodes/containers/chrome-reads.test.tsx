// Chrome reads and change events: Tabs, Modal, Sheet, Popover, Collapsible,
// Accordion. A read frame answers the state the person changes (the tab on
// show, open or not, the open sections), and each user move emits `change`
// carrying that same value.

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

function put(seg: string, type: string, props: Record<string, unknown>) {
	act(() => tree.getState().write([[seg, type, props]]));
}

/** A server write onto a node that already exists. */
function write(seg: string, payload: Record<string, unknown>) {
	act(() => tree.getState().dispatch({ op: OPS.write, ref: [seg], payload }));
}

function draw(seg: string) {
	act(() => root.render(<NodeView path={[seg]} />));
}

/** The main read of the node at `seg`, as the store answers a read frame. */
function read(seg: string): unknown {
	const before = sent.length;
	act(() => tree.getState().dispatch({ op: OPS.read, ref: [seg], payload: null, id: "r" }));
	const answer = sent.slice(before).find((f) => f.op === OPS.read);
	expect(answer).toBeDefined();
	return answer?.payload;
}

const notifies = () => sent.filter((f) => f.op === OPS.notify).map((f) => f.payload);

const TABS = [
	{ id: "a", label: "A" },
	{ id: "b", label: "B" },
];

describe("Tabs", () => {
	it("reads the pinned tab, else the first, else null", () => {
		put("t", "Tabs", { tabs: TABS, active: "b" });
		expect(read("t")).toBe("b");
		write("t", { active: "gone" });
		expect(read("t")).toBe("a");
		act(() => tree.getState().remove([]));
		put("t", "Tabs", { tabs: [] });
		expect(read("t")).toBeNull();
	});

	it("reads what set_active pinned", () => {
		put("t", "Tabs", { tabs: TABS });
		act(() => tree.getState().dispatch({ op: "set_active", ref: ["t"], payload: "b" }));
		expect(read("t")).toBe("b");
	});

	it("emits change with the clicked tab id, which a read then answers", () => {
		put("t", "Tabs", { tabs: TABS });
		draw("t");
		const second = host.querySelectorAll("[role=tab]")[1] as HTMLElement;
		act(() => {
			second.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, button: 0 }));
		});
		expect(notifies()).toEqual([{ event: "change", value: "b" }]);
		expect(read("t")).toBe("b");
	});
});

describe("open state", () => {
	for (const type of ["Modal", "Sheet", "Popover", "Collapsible"]) {
		it(`${type} reads whether it is open`, () => {
			put("o", type, { open: true });
			expect(read("o")).toBe(true);
			write("o", { open: false });
			expect(read("o")).toBe(false);
			act(() => tree.getState().remove([]));
			put("o", type, {});
			expect(read("o")).toBe(false);
		});
	}

	it("Modal emits change to false on a dismiss, and reads closed after", () => {
		put("m", "Modal", { open: true, title: "Sure?" });
		draw("m");
		act(() => {
			document.activeElement?.dispatchEvent(
				new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
			);
		});
		expect(notifies()).toEqual([{ event: "change", value: false }]);
		expect(read("m")).toBe(false);
	});
});

describe("Accordion", () => {
	const sections = [
		{ id: "one", label: "First" },
		{ id: "two", label: "Second" },
	];

	it("reads the open ids, clamped to one when not multi", () => {
		put("a", "Accordion", { sections, open: ["one", "two"] });
		expect(read("a")).toEqual(["one", "two"]);
		write("a", { multi: false });
		expect(read("a")).toEqual(["one"]);
		act(() => tree.getState().remove([]));
		put("a", "Accordion", { sections });
		expect(read("a")).toEqual([]);
	});

	it("emits change with the open ids after a toggle", () => {
		put("a", "Accordion", { sections, open: ["one"] });
		draw("a");
		const second = host.querySelectorAll("[data-slot=accordion-trigger]")[1] as HTMLElement;
		act(() => second.click());
		expect(notifies()).toEqual([{ event: "change", value: ["one", "two"] }]);
		expect(read("a")).toEqual(["one", "two"]);
	});
});
