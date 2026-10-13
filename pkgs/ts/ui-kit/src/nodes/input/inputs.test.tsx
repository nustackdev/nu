// Input nodes over the real tree store: ButtonRef's icon and tooltip,
// ToggleRef's press, write and read, SelectRef's searchable picker, and
// SketchRef's board: drawn, undone, cleared, written and read.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, registry, tree } from "../../tree";
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
	vi.restoreAllMocks();
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(op: string, payload: unknown, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: ["n"], payload, id }));
}

const props = () => tree.getState().getIn(["n"])?.props ?? {};
const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);
// A tooltip's trigger takes over the button's data-slot, so an icon button
// under one is found by its square size class instead.
const iconButton = () => host.querySelector<HTMLElement>("button.size-8");

describe("ButtonRef", () => {
	it("draws an icon-only button as an IconButton named by its tooltip", () => {
		mount("ButtonRef", { label: "", icon: "refresh-cw", tooltip: "Reload", variant: "ghost" });
		const btn = iconButton();
		expect(btn).not.toBeNull();
		expect(btn?.getAttribute("data-slot")).toBe("tooltip-trigger");
		expect(btn?.getAttribute("aria-label")).toBe("Reload");
		expect(btn?.querySelector("svg")).not.toBeNull();
		expect(btn?.textContent).toBe("");
		expect(slot("button")).toBeNull();
	});

	it("falls back to the icon name for the accessible name", () => {
		mount("ButtonRef", { label: "", icon: "trash-2" });
		expect(slot("icon-button")?.getAttribute("aria-label")).toBe("trash-2");
	});

	it("draws the icon before the label", () => {
		mount("ButtonRef", { label: "Add", icon: "plus" });
		const btn = slot("button");
		expect(btn?.firstElementChild?.tagName.toLowerCase()).toBe("svg");
		expect(btn?.textContent).toBe("Add");
	});

	it("falls back to the label on an unknown icon, warning once", () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
		mount("ButtonRef", { label: "Go", icon: "no-such-glyph" });
		expect(slot("icon-button")).toBeNull();
		expect(slot("button")?.textContent).toBe("Go");
		expect(slot("button")?.querySelector("svg")).toBeNull();
		dispatch(OPS.write, { label: "Go again" });
		expect(warn).toHaveBeenCalledTimes(1);
		expect(String(warn.mock.calls[0][0])).toContain("no-such-glyph");
	});

	it("notifies on click and picks up an icon from a later write", () => {
		mount("ButtonRef", { label: "Run" });
		act(() => slot("button")?.click());
		expect(sent.map((f) => f.op)).toEqual([OPS.notify]);
		dispatch(OPS.write, { label: "", icon: "play", tooltip: "Run" });
		expect(iconButton()?.getAttribute("aria-label")).toBe("Run");
	});
});

describe("ToggleRef", () => {
	it("flips pressed and notifies on press", () => {
		mount("ToggleRef", { label: "", icon: "bold", pressed: false });
		const t = slot("toggle");
		expect(t?.getAttribute("aria-label")).toBe("bold");
		expect(t?.getAttribute("aria-pressed")).toBe("false");
		act(() => t?.click());
		expect(props().pressed).toBe(true);
		expect(slot("toggle")?.getAttribute("aria-pressed")).toBe("true");
		expect(sent.map((f) => f.op)).toEqual([OPS.notify]);
	});

	it("lands a bare write on pressed and merges a map", () => {
		mount("ToggleRef", { label: "Wrap", icon: "", pressed: false });
		dispatch(OPS.write, true);
		expect(props().pressed).toBe(true);
		dispatch(OPS.write, { label: "Pin", icon: "pin" });
		expect(props()).toMatchObject({ label: "Pin", icon: "pin", pressed: true });
		expect(slot("toggle")?.querySelector("svg")).not.toBeNull();
		dispatch(OPS.write, null);
		expect(props().pressed).toBe(false);
	});

	it("answers a read with the pressed state", () => {
		mount("ToggleRef", { label: "Pin", pressed: true });
		dispatch(OPS.read, null, "r1");
		expect(sent).toEqual([expect.objectContaining({ op: OPS.read, payload: true, id: "r1" })]);
	});
});

describe("SelectRef", () => {
	const options = [
		{ value: "nu", label: "Nu" },
		{ value: "nulog", label: "nulog" },
	];

	it("renders the Combobox trigger when searchable", () => {
		mount("SelectRef", { options, selected: "nu", searchable: true });
		const trigger = slot("combobox-trigger");
		expect(trigger).not.toBeNull();
		expect(trigger?.getAttribute("role")).toBe("combobox");
		expect(trigger?.textContent).toBe("Nu");
		expect(slot("select-trigger")).toBeNull();
	});

	it("shows the placeholder, muted, with nothing picked", () => {
		mount("SelectRef", { options, selected: "", placeholder: "Pick one", searchable: true });
		const trigger = slot("combobox-trigger");
		expect(trigger?.textContent).toBe("Pick one");
		expect(trigger?.hasAttribute("data-placeholder")).toBe(true);
	});

	it("keeps the plain Select by default", () => {
		mount("SelectRef", { options, selected: "nu" });
		expect(slot("select-trigger")).not.toBeNull();
		expect(slot("combobox-trigger")).toBeNull();
	});

	it("keeps the read contract when searchable", () => {
		mount("SelectRef", { options, selected: "", searchable: true });
		dispatch(OPS.write, "nulog");
		expect(slot("combobox-trigger")?.textContent).toBe("nulog");
		dispatch(OPS.read, null, "r2");
		expect(sent).toEqual([expect.objectContaining({ op: OPS.read, payload: "nulog", id: "r2" })]);
	});

	it("fills a Row's free width", () => {
		expect(registry.SelectRef.fill).toBe(true);
	});
});

describe("SketchRef", () => {
	const elements = [
		{
			type: "path",
			points: [
				[0.1, 0.2],
				[0.3, 0.4],
			],
			stroke: "ink",
			width: 0.012,
		},
		{ type: "rect", x: 0.1, y: 0.1, w: 0.3, h: 0.2, stroke: "red", fill: "red-soft", width: 0.006 },
	];
	const surface = () => slot("sketch-board-surface");
	const drawn = () => host.querySelectorAll("[data-slot=sketch-board-elements] > *").length;
	const button = (name: string) =>
		host.querySelector<HTMLButtonElement>(`button[aria-label="${name}"]`);
	const toolbar = () => slot("sketch-board-toolbar");

	// jsdom lays nothing out: give the board a 200px box at the origin.
	function sized() {
		const el = surface();
		if (!el) throw new Error("no board");
		el.getBoundingClientRect = () => new DOMRect(0, 0, 200, 200);
		el.setPointerCapture = () => {};
		return el;
	}

	function fire(
		el: HTMLElement,
		type: string,
		x: number,
		y: number,
		extra: Record<string, unknown> = {},
	) {
		const e = new MouseEvent(type, {
			bubbles: true,
			cancelable: true,
			clientX: x,
			clientY: y,
			button: 0,
			shiftKey: Boolean(extra.shiftKey),
		});
		Object.defineProperty(e, "pointerId", { value: extra.pointerId ?? 1 });
		Object.defineProperty(e, "pointerType", { value: extra.pointerType ?? "mouse" });
		Object.defineProperty(e, "pressure", { value: extra.pressure ?? 0.5 });
		el.dispatchEvent(e);
	}
	const pointer = (el: HTMLElement, type: string, x: number, y: number, extra = {}) =>
		act(() => fire(el, type, x, y, extra));
	const key = (k: string, mods: KeyboardEventInit = {}) =>
		act(() => {
			slot("sketch-board")?.dispatchEvent(
				new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true, ...mods }),
			);
		});
	const value = () => props().value as Record<string, unknown>[];

	it("draws the elements it is given, with defaults filled in", () => {
		mount("SketchRef", { width: 200, value: elements });
		expect(drawn()).toBe(2);
		expect(surface()?.getAttribute("aria-label")).toBe("Sketch board, 2 elements");
	});

	it("notifies once per pen stroke, on pointer up, not on moves", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = sized();
		pointer(el, "pointerdown", 20, 40);
		pointer(el, "pointermove", 60, 80);
		pointer(el, "pointermove", 100, 120);
		pointer(el, "pointermove", 400, -10);
		expect(sent).toEqual([]);
		expect(slot("sketch-board-draft")).not.toBeNull();
		pointer(el, "pointerup", 400, -10);
		expect(sent.map((f) => f.op)).toEqual([OPS.notify]);
		expect(value()).toEqual([
			{
				type: "path",
				points: [
					[0.1, 0.2],
					[0.3, 0.4],
					[0.5, 0.6],
					[1, 0],
				],
				stroke: "ink",
				width: 0.012,
			},
		]);
	});

	it("keeps pen pressure on the points", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = sized();
		pointer(el, "pointerdown", 20, 20, { pointerType: "pen", pressure: 0.25 });
		pointer(el, "pointerup", 80, 80, { pointerType: "pen", pressure: 0.75 });
		expect((value()[0].points as number[][]).map((p) => p[2])).toEqual([0.25, 0.75]);
	});

	it("draws shapes from the defaults, and the tool keys switch tools", () => {
		mount("SketchRef", {
			width: 200,
			value: [],
			defaults: { tool: "rect", stroke: "blue", fill: "blue-soft", size: 0.024 },
		});
		const el = sized();
		pointer(el, "pointerdown", 140, 120);
		pointer(el, "pointermove", 40, 20);
		pointer(el, "pointerup", 40, 20);
		expect(value()[0]).toEqual({
			type: "rect",
			x: 0.2,
			y: 0.1,
			w: 0.5,
			h: 0.5,
			stroke: "blue",
			fill: "blue-soft",
			width: 0.024,
		});
		key("a");
		pointer(el, "pointerdown", 20, 180);
		pointer(el, "pointerup", 180, 20);
		expect(value()[1]).toMatchObject({
			type: "arrow",
			points: [
				[0.1, 0.9],
				[0.9, 0.1],
			],
		});
		key("o");
		pointer(el, "pointerdown", 20, 20);
		pointer(el, "pointermove", 100, 60, { shiftKey: true });
		pointer(el, "pointerup", 100, 60, { shiftKey: true });
		expect(value()[2]).toMatchObject({ type: "ellipse", w: 0.4, h: 0.4 });
		expect(drawn()).toBe(3);
	});

	it("drops a shape that never left its first point", () => {
		mount("SketchRef", { width: 200, value: [], defaults: { tool: "line" } });
		const el = sized();
		pointer(el, "pointerdown", 50, 50);
		pointer(el, "pointerup", 50, 50);
		expect(value()).toEqual([]);
		expect(sent).toEqual([]);
	});

	it("ignores a tool key for a tool the board does not have", () => {
		mount("SketchRef", { width: 200, value: [], tools: ["pen"] });
		const el = sized();
		key("r");
		pointer(el, "pointerdown", 20, 20);
		pointer(el, "pointerup", 60, 60);
		expect(value()[0].type).toBe("path");
	});

	it("keeps both of two strokes that end before a render", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = sized();
		act(() => {
			fire(el, "pointerdown", 20, 20);
			fire(el, "pointerup", 60, 60);
			fire(el, "pointerdown", 100, 100);
			fire(el, "pointerup", 140, 140);
		});
		expect(value().length).toBe(2);
		expect(sent.map((f) => f.op)).toEqual([OPS.notify, OPS.notify]);
	});

	it("undoes, redoes and clears, one notify each", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = sized();
		pointer(el, "pointerdown", 20, 20);
		pointer(el, "pointerup", 60, 60);
		pointer(el, "pointerdown", 100, 100);
		pointer(el, "pointerup", 140, 140);
		expect(button("Undo")?.disabled).toBe(false);
		expect(button("Redo")?.disabled).toBe(true);
		act(() => button("Undo")?.click());
		expect(value().length).toBe(1);
		key("z", { shiftKey: true, metaKey: true });
		expect(value().length).toBe(2);
		act(() => button("Clear")?.click());
		expect(value()).toEqual([]);
		key("z", { ctrlKey: true });
		expect(value().length).toBe(2);
		expect(sent.map((f) => f.op)).toEqual(Array(6).fill(OPS.notify));
	});

	it("starts the history over on a server write", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = sized();
		pointer(el, "pointerdown", 20, 20);
		pointer(el, "pointerup", 60, 60);
		dispatch(OPS.write, elements);
		expect(button("Undo")?.disabled).toBe(true);
		expect(drawn()).toBe(2);
	});

	it("shows only the configured controls, and none at all when empty", () => {
		mount("SketchRef", { width: 200, value: elements, tools: ["pen"], controls: ["clear"] });
		expect(toolbar()?.querySelectorAll("button").length).toBe(1);
		expect(button("Clear")).not.toBeNull();
		expect(button("Pen")).toBeNull();
		dispatch(OPS.write, { controls: [] });
		expect(toolbar()).toBeNull();
	});

	it("puts the four shapes in one menu next to the pen", () => {
		mount("SketchRef", { width: 480, value: [] });
		expect(button("Pen")?.getAttribute("aria-pressed")).toBe("true");
		expect(button("Shapes")).not.toBeNull();
		expect(button("Rectangle")).toBeNull();
		expect(button("Stroke color")).not.toBeNull();
		expect(button("Fill color")).not.toBeNull();
		expect(button("Stroke size")).not.toBeNull();
	});

	it("takes no input and shows no toolbar when readonly", () => {
		mount("SketchRef", { width: 200, value: elements, readonly: true });
		const el = sized();
		pointer(el, "pointerdown", 20, 20);
		pointer(el, "pointerup", 40, 40);
		expect(toolbar()).toBeNull();
		expect(sent).toEqual([]);
		expect(value().length).toBe(2);
	});

	it("lands a list write on the elements, nil clears, a map merges config", () => {
		mount("SketchRef", { width: 200, value: [], defaults: { stroke: "green", size: 0.05 } });
		dispatch(OPS.write, [
			{
				type: "line",
				points: [
					[0, 0],
					[2, 1],
				],
			},
			{ type: "blob" },
			"junk",
		]);
		expect(value()).toEqual([
			{
				type: "line",
				points: [
					[0, 0],
					[1, 1],
				],
				stroke: "green",
				width: 0.05,
			},
		]);
		expect(drawn()).toBe(1);
		dispatch(OPS.write, { label: "Board", readonly: true });
		expect(props()).toMatchObject({ label: "Board", readonly: true });
		expect(value().length).toBe(1);
		dispatch(OPS.write, { value: [[[0.5, 0.5]]] });
		expect(value()).toEqual([{ type: "path", points: [[0.5, 0.5]], stroke: "green", width: 0.05 }]);
		dispatch(OPS.write, null);
		expect(value()).toEqual([]);
		expect(drawn()).toBe(0);
	});

	it("answers a read with the elements", () => {
		mount("SketchRef", { width: 200, value: elements });
		dispatch(OPS.read, null, "r3");
		expect(sent).toEqual([expect.objectContaining({ op: OPS.read, payload: elements, id: "r3" })]);
	});
});
