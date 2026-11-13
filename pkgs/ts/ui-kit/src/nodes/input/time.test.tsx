// The date and time inputs over the real tree store: TimePickerRef,
// DateTimePickerRef and DateRangePickerRef. Typing is a local edit and blur
// commits; Enter commits then submits; the clear button sends its change at
// once; writes take the bare value, a map of chrome, or nil; reset puts the
// seed back; a Form gathers each value.

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

// An input's submit also carries the value it sent (forms.test.tsx checks it);
// these tests are about which events go out, so it is left off here.
const bare = (payload: unknown) => {
	if (!payload || typeof payload !== "object" || !("value" in payload)) return payload;
	const { value: _sent, ...rest } = payload as Record<string, unknown>;
	return rest;
};
const notifies = () =>
	sent.filter((f) => f.op === OPS.notify).map((f) => ({ ref: f.ref, payload: bare(f.payload) }));
const propsAt = (path: string[]) => tree.getState().getIn(path)?.props ?? {};

function type(el: HTMLInputElement, text: string) {
	const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
	act(() => {
		setter?.call(el, text);
		el.dispatchEvent(new Event("input", { bubbles: true }));
	});
}

function key(el: Element, k: string) {
	act(() => {
		el.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
	});
}

function blur(el: HTMLElement) {
	act(() => {
		el.dispatchEvent(new FocusEvent("focusout", { bubbles: true }));
	});
}

function click(el: Element | null) {
	act(() => (el as HTMLElement).click());
}

const CHANGE = { ref: ["n"], payload: { event: "change" } };
const SUBMIT = { ref: ["n"], payload: { event: "submit" } };

const timeField = () => host.querySelector('input[type="time"]') as HTMLInputElement;
const trigger = () => host.querySelector('[data-slot="date-picker-trigger"]') as HTMLButtonElement;

describe("TimePickerRef", () => {
	it("edits while typing, commits on blur, and submits on Enter", () => {
		put(["n", "TimePickerRef", { value: "" }]);
		draw(["n"]);
		const input = timeField();
		type(input, "09:30");
		expect(propsAt(["n"]).value).toBe("09:30");
		expect(notifies()).toEqual([]);
		blur(input);
		expect(notifies()).toEqual([CHANGE]);
		type(input, "10:00");
		key(input, "Enter");
		expect(notifies()).toEqual([CHANGE, CHANGE, SUBMIT]);
	});

	it("clears with the clear button and sends the change at once", () => {
		put(["n", "TimePickerRef", { value: "18:45" }]);
		draw(["n"]);
		click(host.querySelector('button[aria-label="Clear time"]'));
		expect(propsAt(["n"]).value).toBeNull();
		expect(notifies()).toEqual([CHANGE]);
		expect(host.querySelector('button[aria-label="Clear time"]')).toBeNull();
	});

	it("takes min, max, step and the common props onto the field", () => {
		put([
			"n",
			"TimePickerRef",
			{ value: "", label: "Starts", min: "08:00", max: "18:00", step: 1, required: true },
		]);
		draw(["n"]);
		const input = timeField();
		expect(input.min).toBe("08:00");
		expect(input.max).toBe("18:00");
		expect(input.step).toBe("1");
		expect(input.required).toBe(true);
		expect(host.querySelector(`label[for="${input.id}"]`)?.textContent).toContain("Starts");
	});

	it("writes bare, as a map and as nil, and resets to its seed", () => {
		put(["n", "TimePickerRef", { value: "07:00" }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, "12:15");
		expect(timeField().value).toBe("12:15");
		dispatch(["n"], OPS.write, { label: "At" });
		expect(propsAt(["n"]).value).toBe("12:15");
		expect(propsAt(["n"]).label).toBe("At");
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toBeNull();
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toBe("07:00");
		dispatch(["n"], OPS.read, null, "r");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, id: "r", payload: "07:00" });
	});
});

describe("DateTimePickerRef", () => {
	it("moves the time locally, commits on blur, and submits on Enter", () => {
		put(["n", "DateTimePickerRef", { value: "2016-11-11T19:30" }]);
		draw(["n"]);
		expect(trigger().textContent).toContain("2016");
		const input = timeField();
		expect(input.value).toBe("19:30");
		type(input, "20:05");
		expect(propsAt(["n"]).value).toBe("2016-11-11T20:05");
		expect(notifies()).toEqual([]);
		blur(input);
		expect(notifies()).toEqual([CHANGE]);
		key(input, "Enter");
		expect(notifies()).toEqual([CHANGE, SUBMIT]);
		key(trigger(), "Enter");
		expect(notifies()).toEqual([CHANGE, SUBMIT, SUBMIT]);
	});

	it("keeps a time typed before any date in the field, off the value", () => {
		put(["n", "DateTimePickerRef", { value: "" }]);
		draw(["n"]);
		const input = timeField();
		type(input, "08:00");
		expect(input.value).toBe("08:00");
		expect(propsAt(["n"]).value).toBe("");
	});

	it("clears both parts with the clear button", () => {
		put(["n", "DateTimePickerRef", { value: "2016-11-11T19:30" }]);
		draw(["n"]);
		click(host.querySelector('button[aria-label="Clear date and time"]'));
		expect(propsAt(["n"]).value).toBeNull();
		expect(timeField().value).toBe("");
		expect(notifies()).toEqual([CHANGE]);
	});

	it("labels both parts and writes, resets like any input", () => {
		put(["n", "DateTimePickerRef", { value: "2020-01-02T03:04", label: "Starts" }]);
		draw(["n"]);
		const labelId = host.querySelector("label")?.id as string;
		expect(trigger().getAttribute("aria-labelledby")).toContain(labelId);
		expect(timeField().getAttribute("aria-labelledby")).toContain(labelId);
		dispatch(["n"], OPS.write, "2021-05-06T07:08");
		expect(timeField().value).toBe("07:08");
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toBeNull();
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toBe("2020-01-02T03:04");
	});
});

describe("DateRangePickerRef", () => {
	const RANGE = { start: "2016-11-11", end: "2016-11-13" };

	it("writes a bare range, a wrapped one, chrome, and nil", () => {
		put(["n", "DateRangePickerRef", { value: { start: "", end: "" } }]);
		draw(["n"]);
		expect(trigger().getAttribute("data-empty")).toBe("true");
		dispatch(["n"], OPS.write, RANGE);
		expect(propsAt(["n"]).value).toEqual(RANGE);
		expect(propsAt(["n"]).start).toBeUndefined();
		expect(trigger().textContent).toContain(" - ");
		dispatch(["n"], OPS.write, { value: { start: "2020-01-01", end: null } });
		expect(propsAt(["n"]).value).toEqual({ start: "2020-01-01", end: "" });
		dispatch(["n"], OPS.write, { label: "Stay" });
		expect(propsAt(["n"]).label).toBe("Stay");
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toEqual({ start: "", end: "" });
	});

	it("clears with the clear button or Backspace on the trigger", () => {
		put(["n", "DateRangePickerRef", { value: RANGE }]);
		draw(["n"]);
		click(host.querySelector('button[aria-label="Clear range"]'));
		expect(propsAt(["n"]).value).toEqual({ start: "", end: "" });
		expect(notifies()).toEqual([CHANGE]);
		dispatch(["n"], OPS.write, RANGE);
		key(trigger(), "Backspace");
		expect(propsAt(["n"]).value).toEqual({ start: "", end: "" });
		expect(notifies()).toEqual([CHANGE, CHANGE]);
	});

	it("edits on calendar picks and commits once when the calendar closes", () => {
		put(["n", "DateRangePickerRef", { value: RANGE }]);
		draw(["n"]);
		const days = () =>
			Array.from(document.body.querySelectorAll<HTMLButtonElement>("[data-day] button"));
		const day = (iso: string) =>
			document.body.querySelector<HTMLButtonElement>(`[data-day="${iso}"] button`);
		click(trigger());
		expect(days().length).toBeGreaterThan(0);
		click(day("2016-11-20"));
		expect(notifies()).toEqual([]);
		key(
			document.body.querySelector('[data-slot="date-range-picker-content"]') as Element,
			"Escape",
		);
		expect(propsAt(["n"]).value).toMatchObject({ start: "2016-11-11", end: "2016-11-20" });
		expect(notifies()).toEqual([CHANGE]);
		click(trigger());
		key(
			document.body.querySelector('[data-slot="date-range-picker-content"]') as Element,
			"Escape",
		);
		expect(notifies()).toEqual([CHANGE]);
	});

	it("submits on Enter on the trigger and resets to its seed", () => {
		put(["n", "DateRangePickerRef", { value: RANGE }]);
		draw(["n"]);
		key(trigger(), "Enter");
		expect(notifies()).toEqual([SUBMIT]);
		dispatch(["n"], OPS.write, null);
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toEqual(RANGE);
	});
});

describe("in a Form", () => {
	it("gathers each value under its segment", () => {
		put(["f", "Form", {}], ["at", "TimePickerRef", { value: "09:00" }]);
		put(["f", "Form", {}], ["starts", "DateTimePickerRef", { value: "2016-11-11T19:30" }]);
		put(["f", "Form", {}], ["stay", "DateRangePickerRef", { value: { start: "", end: "" } }]);
		put(["f", "Form", {}], ["save", "ButtonRef", { label: "Save", submit: true }]);
		draw(["f"]);
		key(host.querySelector('input[type="time"]') as HTMLInputElement, "Enter");
		const form = notifies().filter((n) => n.ref.length === 1);
		expect(form).toEqual([
			{
				ref: ["f"],
				payload: {
					event: "submit",
					values: {
						at: "09:00",
						starts: "2016-11-11T19:30",
						stay: { start: "", end: "" },
					},
					button: "save",
				},
			},
		]);
	});
});
