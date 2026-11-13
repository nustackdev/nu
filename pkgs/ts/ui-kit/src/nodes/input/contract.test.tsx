// The input contract over the real tree store (./control.ts): every notify
// names its event, a commit sends one change only when the value moved,
// Enter submits without blurring, a Form gathers its values on submit, a
// reset puts the seeds back, and a Field wires its label, help and error onto
// the control itself.

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

function type(el: HTMLInputElement | HTMLTextAreaElement, text: string) {
	const proto = Object.getPrototypeOf(el);
	const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
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

describe("InputRef commits", () => {
	it("sends one change then one submit on Enter, and nothing on the blur after", () => {
		put(["n", "InputRef", { value: "" }]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		input.focus();
		type(input, "Dune");
		expect(propsAt(["n"]).value).toBe("Dune");
		expect(notifies()).toEqual([]);
		key(input, "Enter");
		expect(notifies()).toEqual([
			{ ref: ["n"], payload: { event: "change" } },
			{ ref: ["n"], payload: { event: "submit" } },
		]);
		expect(document.activeElement).toBe(input);
		blur(input);
		expect(notifies()).toHaveLength(2);
	});

	it("sends nothing on a blur when the value did not move", () => {
		put(["n", "InputRef", { value: "same" }]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		blur(input);
		type(input, "other");
		type(input, "same");
		blur(input);
		expect(notifies()).toEqual([]);
	});

	it("submits on Enter with no change, and ignores Enter while composing", () => {
		put(["n", "InputRef", { value: "x" }]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		key(input, "Enter", { isComposing: true });
		expect(notifies()).toEqual([]);
		key(input, "Enter");
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "submit" } }]);
	});

	it("clears to its seed after a submit when asked", () => {
		put(["n", "InputRef", { value: "", clear_on_submit: true }]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "note");
		key(input, "Enter");
		expect(propsAt(["n"]).value).toBe("");
	});

	it("takes the common props onto the element", () => {
		put([
			"n",
			"InputRef",
			{ value: "", disabled: true, required: true, readonly: true, size: "sm" },
		]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		expect(input.disabled).toBe(true);
		expect(input.required).toBe(true);
		expect(input.readOnly).toBe(true);
		expect(input.getAttribute("aria-required")).toBe("true");
	});

	it("merges chrome from a map write and keeps the value a string", () => {
		put(["n", "InputRef", { value: "a", label: "" }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, { label: "Title", placeholder: "Type" });
		expect(host.querySelector("label")?.textContent).toBe("Title");
		expect(propsAt(["n"])).toMatchObject({ value: "a", placeholder: "Type" });
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toBe("");
	});
});

describe("TextAreaRef submit keys", () => {
	it("keeps Enter a newline and submits on cmd/ctrl+Enter", () => {
		put(["n", "TextAreaRef", { value: "" }]);
		draw(["n"]);
		const area = host.querySelector("textarea") as HTMLTextAreaElement;
		type(area, "hi");
		key(area, "Enter");
		expect(notifies()).toEqual([]);
		key(area, "Enter", { ctrlKey: true });
		expect(notifies()).toEqual([
			{ ref: ["n"], payload: { event: "change" } },
			{ ref: ["n"], payload: { event: "submit" } },
		]);
	});

	it("submits on Enter as a composer, shift+Enter stays a newline", () => {
		put(["n", "TextAreaRef", { value: "", submit_on: "enter" }]);
		draw(["n"]);
		const area = host.querySelector("textarea") as HTMLTextAreaElement;
		key(area, "Enter", { shiftKey: true });
		expect(notifies()).toEqual([]);
		key(area, "Enter");
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "submit" } }]);
	});
});

describe("NumberInputRef commits", () => {
	it("sends one change on Enter after typing, not one per keystroke", () => {
		put(["n", "NumberInputRef", { value: 1 }]);
		draw(["n"]);
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "4");
		type(input, "42");
		key(input, "Enter");
		expect(notifies()).toEqual([
			{ ref: ["n"], payload: { event: "change" } },
			{ ref: ["n"], payload: { event: "submit" } },
		]);
		expect(propsAt(["n"]).value).toBe(42);
	});

	it("commits a stepper at once", () => {
		put(["n", "NumberInputRef", { value: 1, step: 1 }]);
		draw(["n"]);
		act(() => host.querySelector<HTMLButtonElement>('[aria-label="Increment"]')?.click());
		expect(propsAt(["n"]).value).toBe(2);
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "change" } }]);
	});
});

describe("pickers", () => {
	it("send a named change on each toggle, the value on `value`", () => {
		put(["n", "CheckboxRef", { value: false, label: "Watched" }]);
		draw(["n"]);
		act(() => host.querySelector<HTMLButtonElement>("button")?.click());
		expect(propsAt(["n"]).value).toBe(true);
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "change" } }]);
		dispatch(["n"], OPS.read, null, "r");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: true, id: "r" });
	});

	it("take no toggle when readonly", () => {
		put(["n", "SwitchRef", { value: false, readonly: true }]);
		draw(["n"]);
		act(() => host.querySelector<HTMLButtonElement>("button")?.click());
		expect(propsAt(["n"]).value).toBe(false);
		expect(notifies()).toEqual([]);
	});
});

describe("ButtonRef in forms", () => {
	it("is a plain button unless it submits, and names itself when it does", () => {
		put(["f", "Form", {}], ["cancel", "ButtonRef", { label: "Cancel" }]);
		put(["f", "Form", {}], ["go", "ButtonRef", { label: "Go", submit: true }]);
		draw(["f"]);
		const [cancel, go] = Array.from(host.querySelectorAll("button"));
		expect(cancel.getAttribute("type")).toBe("button");
		expect(go.getAttribute("type")).toBe("submit");
		expect(go.getAttribute("name")).toBe("go");
	});

	it("spins and takes no clicks while loading", () => {
		put(["n", "ButtonRef", { label: "Save", loading: true }]);
		draw(["n"]);
		const btn = host.querySelector("button") as HTMLButtonElement;
		expect(btn.getAttribute("aria-busy")).toBe("true");
		expect(btn.disabled).toBe(true);
		act(() => btn.click());
		expect(notifies()).toEqual([]);
	});

	it("sends a named click", () => {
		put(["n", "ButtonRef", { label: "Run" }]);
		draw(["n"]);
		act(() => host.querySelector("button")?.click());
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "click" } }]);
	});
});

describe("Form", () => {
	function movieForm(extra: Record<string, unknown> = {}) {
		put(
			["f", "Form", extra],
			["title", "Field", { label: "Title" }],
			["control", "InputRef", { value: "" }],
		);
		put(["f", "Form", extra], ["meta", "Row", {}], ["year", "NumberInputRef", { value: 2000 }]);
		put(["f", "Form", extra], ["meta", "Row", {}], ["seen", "SwitchRef", { value: false }]);
		put(["f", "Form", extra], ["cancel", "ButtonRef", { label: "Cancel" }]);
		put(["f", "Form", extra], ["save", "ButtonRef", { label: "Save", submit: true }]);
		draw(["f"]);
	}

	const formNotifies = () => notifies().filter((n) => n.ref.length === 1);

	it("submits once on Enter in a field, with the values and the default button", () => {
		movieForm();
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "Dune");
		key(input, "Enter");
		expect(formNotifies()).toEqual([
			{
				ref: ["f"],
				payload: {
					event: "submit",
					values: { title: "Dune", meta: { year: 2000, seen: false } },
					button: "save",
				},
			},
		]);
	});

	it("does not submit on a Cancel click, and says which button submitted", () => {
		movieForm();
		const [cancel, save] = Array.from(host.querySelectorAll("button[data-slot=button]"));
		act(() => (cancel as HTMLButtonElement).click());
		expect(formNotifies()).toEqual([]);
		act(() => (save as HTMLButtonElement).click());
		expect(formNotifies()).toHaveLength(1);
		expect(formNotifies()[0].payload).toMatchObject({ event: "submit", button: "save" });
	});

	it("answers a read with the same values, and a reset puts the seeds back", () => {
		movieForm();
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "Arrival");
		dispatch(["f", "meta", "seen"], OPS.write, true);
		dispatch(["f"], OPS.read, null, "v");
		expect(sent.at(-1)).toMatchObject({
			op: OPS.read,
			id: "v",
			payload: { title: "Arrival", meta: { year: 2000, seen: true } },
		});
		dispatch(["f"], "reset");
		expect(propsAt(["f", "title", "control"]).value).toBe("");
		expect(propsAt(["f", "meta", "seen"]).value).toBe(false);
	});

	it("clears after a submit when asked, and drops submits while busy", () => {
		movieForm({ clear_on_submit: true, busy_on_submit: true });
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "Heat");
		key(input, "Enter");
		expect(propsAt(["f", "title", "control"]).value).toBe("");
		expect(propsAt(["f"]).busy).toBe(true);
		key(input, "Enter");
		expect(formNotifies()).toHaveLength(1);
		const save = host.querySelector('button[name="save"]');
		expect(save?.getAttribute("aria-busy")).toBe("true");
	});
});

describe("Field", () => {
	it("labels the control and puts help, error and required on it", () => {
		put(
			["f", "Field", { label: "Title", help: "As released", error: "", required: true }],
			["control", "InputRef", { value: "", label: "ignored" }],
		);
		draw(["f"]);
		const input = host.querySelector("input") as HTMLInputElement;
		const labels = host.querySelectorAll("label");
		expect(labels).toHaveLength(1);
		expect(labels[0].getAttribute("for")).toBe(input.id);
		expect(input.required).toBe(true);
		expect(input.getAttribute("aria-describedby")).toBe(`${input.id}-help`);
		expect(input.hasAttribute("aria-invalid")).toBe(false);

		dispatch(["f"], OPS.write, { error: "Needs a title" });
		expect(input.getAttribute("aria-invalid")).toBe("true");
		expect(input.getAttribute("aria-describedby")).toBe(`${input.id}-help ${input.id}-error`);
		const alert = host.querySelector('[role="alert"]');
		expect(alert?.id).toBe(`${input.id}-error`);
		expect(alert?.textContent).toBe("Needs a title");
		expect(host.querySelector("[data-slot=field-help]")?.textContent).toBe("As released");
	});

	it("names a radio group by its label", () => {
		put(
			["f", "Field", { label: "Genre" }],
			["control", "RadioGroupRef", { value: "", options: ["drama", "comedy"] }],
		);
		draw(["f"]);
		const group = host.querySelector('[role="radiogroup"]');
		const label = host.querySelector("label");
		expect(group?.getAttribute("aria-labelledby")).toBe(label?.id);
	});
});
