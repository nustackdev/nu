// RangeSliderRef and ColorPickerRef over the real tree store: a committed
// move sends one named change, writes are coerced to the value's shape, a
// read and a Form see the value, a reset puts the seed back, and the
// ColorPicker's hex field submits on Enter.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures its controls; jsdom has no ResizeObserver.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;

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

type Level = [string, string | null, Record<string, unknown>?];

function put(...chain: Level[]) {
	tree.getState().write(chain.map(([seg, type, props]) => [seg, type, props ?? {}]));
}

function draw(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

function dispatch(path: string[], op: string, payload: unknown = null, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: path, payload, id }));
}

const notifies = () =>
	sent.filter((f) => f.op === OPS.notify).map((f) => ({ ref: f.ref, payload: f.payload }));
const propsAt = (path: string[]) => tree.getState().getIn(path)?.props ?? {};

function key(el: Element, k: string, init: KeyboardEventInit = {}) {
	act(() => {
		el.dispatchEvent(
			new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true, ...init }),
		);
	});
}

function type(el: HTMLInputElement, text: string) {
	const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
	act(() => {
		setter?.call(el, text);
		el.dispatchEvent(new Event("input", { bubbles: true }));
	});
}

const change = { event: "change" };
const submit = { event: "submit" };

describe("RangeSliderRef", () => {
	it("names each thumb and the group", () => {
		put(["n", "RangeSliderRef", { value: [20, 60], label: "Price" }]);
		draw(["n"]);
		const thumbs = host.querySelectorAll("[role=slider]");
		expect(thumbs).toHaveLength(2);
		expect(thumbs[0].getAttribute("aria-label")).toBe("Minimum");
		expect(thumbs[1].getAttribute("aria-label")).toBe("Maximum");
		expect(thumbs[0].getAttribute("aria-valuenow")).toBe("20");
		expect(thumbs[1].getAttribute("aria-valuenow")).toBe("60");
		const group = host.querySelector("[role=group]") as HTMLElement;
		const label = document.getElementById(group.getAttribute("aria-labelledby") ?? "");
		expect(label?.textContent).toBe("Price");
	});

	it("takes its own thumb names", () => {
		put(["n", "RangeSliderRef", { value: [1, 2], thumb_labels: ["From", "To"] }]);
		draw(["n"]);
		const thumbs = host.querySelectorAll("[role=slider]");
		expect(thumbs[0].getAttribute("aria-label")).toBe("From");
		expect(thumbs[1].getAttribute("aria-label")).toBe("To");
	});

	it("commits an arrow key as one named change", () => {
		put(["n", "RangeSliderRef", { value: [20, 60] }]);
		draw(["n"]);
		const high = host.querySelectorAll("[role=slider]")[1] as HTMLElement;
		act(() => high.focus());
		key(high, "ArrowRight");
		expect(propsAt(["n"]).value).toEqual([20, 61]);
		expect(notifies()).toEqual([{ ref: ["n"], payload: change }]);
	});

	it("coerces writes to an ordered pair inside the bounds", () => {
		put(["n", "RangeSliderRef", { value: [20, 60], min: 0, max: 100 }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, [80, 10]);
		expect(propsAt(["n"]).value).toEqual([10, 80]);
		dispatch(["n"], OPS.write, [-5, 500]);
		expect(propsAt(["n"]).value).toEqual([0, 100]);
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toEqual([0, 100]);
		dispatch(["n"], OPS.write, { value: [3, 4], label: "Span" });
		expect(propsAt(["n"])).toMatchObject({ value: [3, 4], label: "Span" });
		expect(notifies()).toEqual([]);
	});

	it("formats the readout and the marks", () => {
		put([
			"n",
			"RangeSliderRef",
			{
				value: [0.25, 0.75],
				min: 0,
				max: 1,
				step: 0.05,
				format: "{}x",
				marks: [0, { value: 1, label: "all" }],
			},
		]);
		draw(["n"]);
		expect(host.querySelector("[data-slot=range-slider-value]")?.textContent).toBe("0.25x - 0.75x");
		expect(host.querySelector("[data-slot=range-slider-marks]")?.textContent).toBe("0.00xall");
	});

	it("answers a read, resets to its seed, and lands in a Form", () => {
		put(["f", "Form", {}], ["span", "RangeSliderRef", { value: [20, 60] }]);
		draw(["f"]);
		dispatch(["f", "span"], OPS.write, [30, 40]);
		dispatch(["f", "span"], OPS.read, null, "r");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: [30, 40], id: "r" });
		dispatch(["f"], OPS.read, null, "v");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: { span: [30, 40] }, id: "v" });
		dispatch(["f", "span"], "reset");
		expect(propsAt(["f", "span"]).value).toEqual([20, 60]);
	});

	it("takes disabled and readonly as a still control, and the Field's aria", () => {
		put(
			["f", "Field", { label: "Span", help: "Inclusive", error: "Too wide" }],
			["control", "RangeSliderRef", { value: [1, 9], readonly: true }],
		);
		draw(["f"]);
		const thumbs = host.querySelectorAll("[role=slider]");
		expect(thumbs[0].getAttribute("aria-invalid")).toBe("true");
		expect(thumbs[0].getAttribute("aria-describedby")).toContain("-help");
		expect(thumbs[0].hasAttribute("data-disabled")).toBe(true);
		const group = host.querySelector("[role=group]") as HTMLElement;
		const label = document.getElementById(group.getAttribute("aria-labelledby") ?? "");
		expect(label?.textContent).toContain("Span");
	});
});

describe("ColorPickerRef", () => {
	const trigger = () => host.querySelector("[data-slot=color-picker-trigger]") as HTMLButtonElement;
	const open = () => act(() => trigger().click());
	const hexField = () => document.querySelector("[data-slot=color-picker-hex]") as HTMLInputElement;

	it("shows the hex on a labelled trigger", () => {
		put(["n", "ColorPickerRef", { value: "#8946DB", label: "Accent" }]);
		draw(["n"]);
		expect(trigger().textContent).toBe("#8946db");
		const names = (trigger().getAttribute("aria-labelledby") ?? "").split(" ");
		expect(document.getElementById(names[0])?.textContent).toBe("Accent");
	});

	it("sends a change then a submit on Enter in the hex field", () => {
		put(["n", "ColorPickerRef", { value: "#000000" }]);
		draw(["n"]);
		open();
		type(hexField(), "#4269d0");
		expect(propsAt(["n"]).value).toBe("#4269d0");
		expect(notifies()).toEqual([]);
		key(hexField(), "Enter");
		expect(notifies()).toEqual([
			{ ref: ["n"], payload: change },
			{ ref: ["n"], payload: submit },
		]);
	});

	it("widens a short hex on Enter, and holds a bad one back", () => {
		put(["n", "ColorPickerRef", { value: "#000000" }]);
		draw(["n"]);
		open();
		type(hexField(), "#zzz");
		key(hexField(), "Enter");
		expect(notifies()).toEqual([]);
		expect(hexField().getAttribute("aria-invalid")).toBe("true");
		type(hexField(), "#abc");
		key(hexField(), "Enter");
		expect(propsAt(["n"]).value).toBe("#aabbcc");
		expect(notifies()).toEqual([
			{ ref: ["n"], payload: change },
			{ ref: ["n"], payload: submit },
		]);
	});

	it("commits a key on the area and on the hue as one change each", () => {
		put(["n", "ColorPickerRef", { value: "#ff0000" }]);
		draw(["n"]);
		open();
		const area = document.querySelector('[aria-label="Saturation and brightness"]') as HTMLElement;
		act(() => area.focus());
		key(area, "ArrowDown", { shiftKey: true });
		expect(propsAt(["n"]).value).toBe("#e60000");
		expect(notifies()).toEqual([{ ref: ["n"], payload: change }]);
		const hue = document.querySelector('[role=slider][aria-label="Hue"]') as HTMLElement;
		act(() => hue.focus());
		key(hue, "ArrowRight");
		expect(propsAt(["n"]).value).toBe("#e60400");
		expect(notifies()).toHaveLength(2);
	});

	it("submits on Enter on the closed trigger", () => {
		put(["n", "ColorPickerRef", { value: "#000000" }]);
		draw(["n"]);
		key(trigger(), "Enter");
		expect(notifies()).toEqual([{ ref: ["n"], payload: submit }]);
	});

	it("lands a swatch with one change, the palette from the kit tokens", () => {
		put(["n", "ColorPickerRef", { value: "#000000", swatches: "palette" }]);
		draw(["n"]);
		open();
		const swatches = document.querySelectorAll("[data-slot=color-picker-swatches] button");
		expect(swatches).toHaveLength(10);
		const first = swatches[0] as HTMLButtonElement;
		act(() => first.click());
		expect(propsAt(["n"]).value).toBe(first.getAttribute("aria-label"));
		expect(notifies()).toEqual([{ ref: ["n"], payload: change }]);
		expect(first.getAttribute("aria-pressed")).toBe("true");
	});

	it("takes a list of swatches", () => {
		put(["n", "ColorPickerRef", { value: "#000000", swatches: ["#FFF", "#123456", "nope"] }]);
		draw(["n"]);
		open();
		const labels = Array.from(
			document.querySelectorAll("[data-slot=color-picker-swatches] button"),
		).map((b) => b.getAttribute("aria-label"));
		expect(labels).toEqual(["#ffffff", "#123456"]);
	});

	it("keeps the color on a bad write, merges a map, answers a read, resets", () => {
		put(["f", "Form", {}], ["ink", "ColorPickerRef", { value: "#111111" }]);
		draw(["f"]);
		dispatch(["f", "ink"], OPS.write, "#ABC");
		expect(propsAt(["f", "ink"]).value).toBe("#aabbcc");
		dispatch(["f", "ink"], OPS.write, "red");
		expect(propsAt(["f", "ink"]).value).toBe("#aabbcc");
		dispatch(["f", "ink"], OPS.write, null);
		expect(propsAt(["f", "ink"]).value).toBe("#aabbcc");
		dispatch(["f", "ink"], OPS.write, { value: 7, label: "Ink" });
		expect(propsAt(["f", "ink"])).toMatchObject({ value: "#aabbcc", label: "Ink" });
		dispatch(["f"], OPS.read, null, "v");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: { ink: "#aabbcc" }, id: "v" });
		dispatch(["f", "ink"], "reset");
		expect(propsAt(["f", "ink"]).value).toBe("#111111");
		expect(notifies()).toEqual([]);
	});

	it("is a disabled trigger when disabled or readonly", () => {
		put(["n", "ColorPickerRef", { value: "#000000", readonly: true }]);
		draw(["n"]);
		expect(trigger().disabled).toBe(true);
	});
});
