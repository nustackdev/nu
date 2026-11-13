// The choice inputs over the real tree store: SegmentedControlRef,
// CheckboxGroupRef, MultiSelectRef and AutocompleteRef. Each sends a named
// change when its value moves, takes a bare, map and nil write, answers a
// read, resets to its seed and lands in a Form's values. Autocomplete picks
// a highlighted suggestion on Enter and submits the typed text otherwise.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures its controls and cmdk scrolls its rows; jsdom has neither.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;
Element.prototype.scrollIntoView ??= () => {};

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
const CHANGE = { ref: ["n"], payload: { event: "change" } };
const SUBMIT = { ref: ["n"], payload: { event: "submit" } };

function type(el: HTMLInputElement, text: string) {
	const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
	act(() => {
		setter?.call(el, text);
		el.dispatchEvent(new Event("input", { bubbles: true }));
	});
}

function key(el: Element, k: string, init: KeyboardEventInit = {}) {
	act(() => {
		el.dispatchEvent(
			new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true, ...init }),
		);
	});
}

function blur(el: HTMLElement) {
	act(() => {
		el.dispatchEvent(new FocusEvent("focusout", { bubbles: true }));
	});
}

function read(path: string[]): unknown {
	dispatch(path, OPS.read, null, "r");
	const last = sent.at(-1);
	expect(last).toMatchObject({ op: OPS.read, id: "r" });
	return last?.payload;
}

const click = (el: Element | null | undefined) => act(() => (el as HTMLElement).click());

describe("SegmentedControlRef", () => {
	const options = ["Day", "Week", "Month"];

	it("is a radiogroup that picks on click, with a named change", () => {
		put(["n", "SegmentedControlRef", { options, value: "Day", label: "Range" }]);
		draw(["n"]);
		const group = host.querySelector('[role="radiogroup"]');
		const label = host.querySelector("span[id]");
		expect(group?.getAttribute("aria-labelledby")).toBe(label?.id);
		const radios = host.querySelectorAll('[role="radio"]');
		expect(radios).toHaveLength(3);
		expect(radios[0].getAttribute("aria-checked")).toBe("true");
		click(radios[2]);
		expect(propsAt(["n"]).value).toBe("Month");
		expect(notifies()).toEqual([CHANGE]);
		expect(read(["n"])).toBe("Month");
	});

	it("takes bare, map and nil writes, and resets to its seed", () => {
		put(["n", "SegmentedControlRef", { options, value: "Day" }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, "Week");
		expect(propsAt(["n"]).value).toBe("Week");
		dispatch(["n"], OPS.write, { options: ["Hour", "Day"] });
		expect(host.querySelectorAll('[role="radio"]')).toHaveLength(2);
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toBe("");
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toBe("Day");
		expect(notifies()).toEqual([]);
	});

	it("moves the pick with the arrow keys", async () => {
		put(["n", "SegmentedControlRef", { options, value: "Day" }]);
		draw(["n"]);
		const radios = host.querySelectorAll<HTMLButtonElement>('[role="radio"]');
		act(() => radios[0].focus());
		key(radios[0], "ArrowRight");
		// Radix roving focus moves on the next tick.
		await act(() => new Promise((done) => setTimeout(done, 0)));
		expect(document.activeElement).toBe(radios[1]);
		expect(propsAt(["n"]).value).toBe("Week");
		expect(notifies()).toEqual([CHANGE]);
	});

	it("takes no pick when readonly", () => {
		put(["n", "SegmentedControlRef", { options, value: "Day", readonly: true }]);
		draw(["n"]);
		click(host.querySelectorAll('[role="radio"]')[1]);
		expect(propsAt(["n"]).value).toBe("Day");
		expect(notifies()).toEqual([]);
	});
});

describe("CheckboxGroupRef", () => {
	const options = ["drama", "comedy", "sci-fi"];

	it("ticks and unticks in option order, one change each", () => {
		put(["n", "CheckboxGroupRef", { options, value: ["sci-fi"], label: "Genres" }]);
		draw(["n"]);
		const group = host.querySelector("fieldset");
		const label = host.querySelector("span[id]");
		expect(group?.getAttribute("aria-labelledby")).toBe(label?.id);
		const boxes = host.querySelectorAll('[role="checkbox"]');
		click(boxes[0]);
		expect(propsAt(["n"]).value).toEqual(["drama", "sci-fi"]);
		click(boxes[2]);
		expect(propsAt(["n"]).value).toEqual(["drama"]);
		expect(notifies()).toEqual([CHANGE, CHANGE]);
		expect(read(["n"])).toEqual(["drama"]);
	});

	it("takes list, lone string, map and nil writes, and resets to its seed", () => {
		put(["n", "CheckboxGroupRef", { options, value: ["drama"] }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, ["comedy", 3]);
		expect(propsAt(["n"]).value).toEqual(["comedy", "3"]);
		dispatch(["n"], OPS.write, "sci-fi");
		expect(propsAt(["n"]).value).toEqual(["sci-fi"]);
		dispatch(["n"], OPS.write, { value: null, orientation: "horizontal" });
		expect(propsAt(["n"]).value).toEqual([]);
		expect(propsAt(["n"]).orientation).toBe("horizontal");
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toEqual([]);
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toEqual(["drama"]);
	});

	it("takes no tick when readonly", () => {
		put(["n", "CheckboxGroupRef", { options, value: [], readonly: true }]);
		draw(["n"]);
		click(host.querySelector('[role="checkbox"]'));
		expect(propsAt(["n"]).value).toEqual([]);
		expect(notifies()).toEqual([]);
	});

	it("is named by a Field around it", () => {
		put(
			["f", "Field", { label: "Genres", error: "Pick one" }],
			["control", "CheckboxGroupRef", { options, value: [] }],
		);
		draw(["f"]);
		const group = host.querySelector("fieldset");
		expect(group?.getAttribute("aria-labelledby")).toBe(host.querySelector("label")?.id);
		expect(group?.getAttribute("aria-describedby")).toBe(`${group?.id}-error`);
		expect(host.querySelector('[role="checkbox"]')?.getAttribute("aria-invalid")).toBe("true");
	});
});

describe("MultiSelectRef", () => {
	const options = [
		{ value: "nu", label: "Nu" },
		{ value: "nustd", label: "Nustd" },
		{ value: "nudle", label: "Nudle" },
	];
	const trigger = () => host.querySelector<HTMLButtonElement>('[role="combobox"]');
	const item = (value: string) =>
		document.querySelector(`[data-slot="multi-select-item"][data-value="${value}"]`);

	it("shows the picks on the trigger, labelled by its own label", () => {
		put(["n", "MultiSelectRef", { options, value: ["nu", "nudle"], label: "Packages" }]);
		draw(["n"]);
		const chips = host.querySelectorAll('[data-slot="multi-select-chip"]');
		expect(Array.from(chips, (c) => c.textContent)).toEqual(["Nu", "Nudle"]);
		expect(host.querySelector("label")?.getAttribute("for")).toBe(trigger()?.id);
	});

	it("toggles picks in the open list, which stays open, one change each", () => {
		put(["n", "MultiSelectRef", { options, value: ["nudle"] }]);
		draw(["n"]);
		click(trigger());
		expect(item("nu")?.getAttribute("aria-checked")).toBe("false");
		click(item("nu"));
		expect(propsAt(["n"]).value).toEqual(["nu", "nudle"]);
		expect(item("nu")?.getAttribute("aria-checked")).toBe("true");
		click(item("nudle"));
		expect(propsAt(["n"]).value).toEqual(["nu"]);
		expect(notifies()).toEqual([CHANGE, CHANGE]);
		expect(read(["n"])).toEqual(["nu"]);
	});

	it("takes no pick when readonly", () => {
		put(["n", "MultiSelectRef", { options, value: [], readonly: true }]);
		draw(["n"]);
		click(trigger());
		click(item("nu"));
		expect(propsAt(["n"]).value).toEqual([]);
		expect(notifies()).toEqual([]);
	});

	it("takes writes and resets to its seed", () => {
		put(["n", "MultiSelectRef", { options, value: ["nu"] }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, ["nustd", "nudle"]);
		expect(propsAt(["n"]).value).toEqual(["nustd", "nudle"]);
		dispatch(["n"], OPS.write, { placeholder: "Pick" });
		expect(propsAt(["n"]).value).toEqual(["nustd", "nudle"]);
		dispatch(["n"], OPS.write, null);
		expect(trigger()?.textContent).toBe("Pick");
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toEqual(["nu"]);
	});
});

describe("AutocompleteRef", () => {
	const options = ["Amsterdam", "Athens", "Berlin"];
	const field = () => host.querySelector("input") as HTMLInputElement;

	it("commits free text on blur, one change, never per keystroke", () => {
		put(["n", "AutocompleteRef", { options, value: "" }]);
		draw(["n"]);
		type(field(), "Ath");
		type(field(), "Atlantis");
		expect(notifies()).toEqual([]);
		blur(field());
		expect(notifies()).toEqual([CHANGE]);
		expect(read(["n"])).toBe("Atlantis");
	});

	it("submits the typed text on Enter with nothing highlighted", () => {
		put(["n", "AutocompleteRef", { options, value: "" }]);
		draw(["n"]);
		type(field(), "At");
		expect(field().getAttribute("aria-expanded")).toBe("true");
		key(field(), "Enter");
		expect(propsAt(["n"]).value).toBe("At");
		expect(notifies()).toEqual([CHANGE, SUBMIT]);
	});

	it("picks a highlighted suggestion on Enter, with a change and no submit", () => {
		put(["n", "AutocompleteRef", { options, value: "" }]);
		draw(["n"]);
		type(field(), "a");
		key(field(), "ArrowDown");
		key(field(), "ArrowDown");
		const active = field().getAttribute("aria-activedescendant");
		expect(document.getElementById(active ?? "")?.textContent).toBe("Athens");
		key(field(), "Enter");
		expect(propsAt(["n"]).value).toBe("Athens");
		expect(notifies()).toEqual([CHANGE]);
		expect(field().getAttribute("aria-expanded")).toBe("false");
		blur(field());
		expect(notifies()).toEqual([CHANGE]);
	});

	it("picks a suggestion on click", () => {
		put(["n", "AutocompleteRef", { options, value: "" }]);
		draw(["n"]);
		type(field(), "ber");
		const rows = document.querySelectorAll('[role="option"]');
		expect(Array.from(rows, (r) => r.textContent)).toEqual(["Berlin"]);
		click(rows[0]);
		expect(propsAt(["n"]).value).toBe("Berlin");
		expect(notifies()).toEqual([CHANGE]);
	});

	it("closes on Escape and ignores Enter while composing", () => {
		put(["n", "AutocompleteRef", { options, value: "" }]);
		draw(["n"]);
		type(field(), "a");
		key(field(), "Escape");
		expect(field().getAttribute("aria-expanded")).toBe("false");
		key(field(), "Enter", { isComposing: true });
		expect(notifies()).toEqual([]);
	});

	it("takes writes, replaces suggestions, and resets to its seed", () => {
		put(["n", "AutocompleteRef", { options, value: "Berlin" }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, "Lisbon");
		expect(field().value).toBe("Lisbon");
		dispatch(["n"], OPS.write, { options: ["Lisbon", "Porto"] });
		type(field(), "o");
		expect(document.querySelectorAll('[role="option"]')).toHaveLength(2);
		dispatch(["n"], OPS.write, null);
		expect(field().value).toBe("");
		dispatch(["n"], "reset");
		expect(field().value).toBe("Berlin");
	});
});

describe("choice inputs in a Form", () => {
	it("land in the form's values, and a reset puts every seed back", () => {
		put(["f", "Form", {}], ["range", "SegmentedControlRef", { options: ["a", "b"], value: "a" }]);
		put(["f", "Form", {}], ["tags", "CheckboxGroupRef", { options: ["x", "y"], value: ["x"] }]);
		put(["f", "Form", {}], ["pkgs", "MultiSelectRef", { options: ["nu"], value: [] }]);
		put(["f", "Form", {}], ["city", "AutocompleteRef", { options: [], value: "" }]);
		draw(["f"]);
		dispatch(["f", "pkgs"], OPS.write, ["nu"]);
		dispatch(["f", "city"], OPS.write, "Yerevan");
		expect(read(["f"])).toEqual({
			range: "a",
			tags: ["x"],
			pkgs: ["nu"],
			city: "Yerevan",
		});
		dispatch(["f"], "reset");
		expect(read(["f"])).toEqual({ range: "a", tags: ["x"], pkgs: [], city: "" });
	});

	it("submits the form on Enter in an Autocomplete", () => {
		put(["f", "Form", {}], ["city", "AutocompleteRef", { options: ["Berlin"], value: "" }]);
		draw(["f"]);
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "Rome");
		key(input, "Enter");
		const form = notifies().filter((n) => n.ref.length === 1);
		expect(form).toEqual([
			{ ref: ["f"], payload: { event: "submit", values: { city: "Rome" }, button: null } },
		]);
	});
});
