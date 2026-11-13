// Forms past submit (./control.ts): the checks a Form runs before it sends,
// the program's own errors (`set_errors`), the `focus` op, a disabled
// Fieldset or Form cascading to every control in it, the null empties of
// the pick-or-nothing inputs, and Code / Markdown `readonly`.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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

const propsAt = (path: string[]) => tree.getState().getIn(path)?.props ?? {};
const formSubmits = () =>
	sent.filter((f) => f.op === OPS.notify && f.ref.length === 1).map((f) => f.payload);

function type(el: HTMLInputElement, text: string) {
	const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value")?.set;
	act(() => {
		setter?.call(el, text);
		el.dispatchEvent(new Event("input", { bubbles: true }));
	});
}

function enter(el: Element) {
	act(() => {
		el.dispatchEvent(
			new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }),
		);
	});
}

function signup() {
	put(
		["f", "Form", {}],
		["name", "Field", { label: "Name" }],
		["control", "InputRef", { value: "", required: true }],
	);
	put(["f", "Form", {}], ["email", "InputRef", { value: "", type: "email", label: "Email" }]);
	put(
		["f", "Form", {}],
		["age", "Field", { label: "Age" }],
		["control", "NumberInputRef", { value: null, min: 18 }],
	);
	put(["f", "Form", {}], ["save", "ButtonRef", { label: "Save", submit: true }]);
	draw(["f"]);
}

const inputs = () => Array.from(host.querySelectorAll("input")) as HTMLInputElement[];

describe("Form checks", () => {
	it("drops a submit with a required field empty, shows it on the Field and focuses it", () => {
		signup();
		const [name] = inputs();
		act(() => (host.querySelector('button[name="save"]') as HTMLButtonElement).click());
		expect(formSubmits()).toEqual([]);
		expect(propsAt(["f", "name"]).check).toBe("This field is required");
		expect(name.getAttribute("aria-invalid")).toBe("true");
		expect(host.querySelector('[role="alert"]')?.textContent).toContain("required");
		expect(document.activeElement).toBe(name);
		expect(host.querySelector("form")?.noValidate).toBe(true);
	});

	it("clears a check on the next edit, and submits once every check passes", () => {
		signup();
		const [name, email, age] = inputs();
		enter(name);
		expect(propsAt(["f", "name"]).check).not.toBe("");
		type(name, "Ada");
		expect(propsAt(["f", "name"]).check).toBe("");
		type(email, "not an email");
		type(age, "12");
		enter(name);
		expect(formSubmits()).toEqual([]);
		expect(propsAt(["f", "email"]).check).toBe("Enter an email address");
		expect(propsAt(["f", "age"]).check).toBe("Must be at least 18");
		// A bare control gets the Field chrome for its message (drawn anew, the
		// one time), and keeps its label.
		const framed = inputs()[1];
		expect(framed.getAttribute("aria-invalid")).toBe("true");
		expect(host.querySelector(`label[for="${framed.id}"]`)?.textContent).toContain("Email");
		expect(document.activeElement).toBe(framed);
		type(framed, "ada@example.com");
		expect(inputs()[1]).toBe(framed);
		type(age, "36");
		enter(name);
		expect(formSubmits()).toEqual([
			{
				event: "submit",
				values: { name: "Ada", email: "ada@example.com", age: 36 },
				button: "save",
			},
		]);
	});

	it("checks max_length and pattern, and skips what is disabled", () => {
		put(["f", "Form", {}], ["code", "InputRef", { value: "abcd", max_length: 3 }]);
		put(["f", "Form", {}], ["zip", "InputRef", { value: "12a", pattern: "[0-9]+" }]);
		put(
			["f", "Form", {}],
			["off", "Fieldset", { disabled: true }],
			["x", "InputRef", { value: "", required: true }],
		);
		draw(["f"]);
		enter(inputs()[0]);
		expect(formSubmits()).toEqual([]);
		expect(propsAt(["f", "code"]).check).toBe("Must be at most 3 characters");
		expect(propsAt(["f", "zip"]).check).toBe("Does not match the expected format");
		expect(propsAt(["f", "off", "x"]).check).toBeUndefined();
	});
});

describe("Form set_errors", () => {
	it("lands each message on its Field or control, focuses the first, and clears with {}", () => {
		signup();
		const [name] = inputs();
		dispatch(["f"], "set_errors", { email: "Taken", age: "Too young" });
		expect(propsAt(["f", "email"]).error).toBe("Taken");
		expect(propsAt(["f", "age"]).error).toBe("Too young");
		expect(propsAt(["f", "name"]).error ?? "").toBe("");
		const email = inputs()[1];
		expect(email.getAttribute("aria-invalid")).toBe("true");
		expect(document.activeElement).toBe(email);
		expect(name.getAttribute("aria-invalid")).toBeNull();
		dispatch(["f"], "set_errors", {});
		expect(propsAt(["f", "email"]).error).toBe("");
		expect(host.querySelector('[role="alert"]')).toBeNull();
	});

	it("reaches nested inputs by the same keys as the values", () => {
		put(
			["f", "Form", {}],
			["addr", "Fieldset", {}],
			["city", "Field", { label: "City" }],
			["control", "InputRef", { value: "" }],
		);
		draw(["f"]);
		dispatch(["f"], "set_errors", { addr: { city: "Unknown city" } });
		expect(propsAt(["f", "addr", "city"]).error).toBe("Unknown city");
		expect(document.activeElement).toBe(inputs()[0]);
	});
});

describe("submit value", () => {
	it("an input's submit carries the value it sent, before clear_on_submit empties it", () => {
		put(["a", "InputRef", { value: "", clear_on_submit: true }]);
		draw(["a"]);
		type(inputs()[0], "Dune");
		enter(inputs()[0]);
		const submit = sent.find(
			(f) => f.op === OPS.notify && (f.payload as { event?: string }).event === "submit",
		);
		expect(submit?.payload).toEqual({ event: "submit", value: "Dune" });
		expect(propsAt(["a"]).value).toBe("");
	});
});

describe("focus", () => {
	it("focuses the control on the op, also when it lands before the draw", () => {
		put(["a", "InputRef", { value: "" }]);
		dispatch(["a"], "focus");
		draw(["a"]);
		expect(document.activeElement).toBe(inputs()[0]);
		(document.activeElement as HTMLElement).blur();
		draw(["a"]);
		expect(document.activeElement).not.toBe(inputs()[0]);
		dispatch(["a"], "focus");
		expect(document.activeElement).toBe(inputs()[0]);
	});

	it("focuses a picker's trigger", () => {
		put(["s", "SelectRef", { value: null, options: ["a", "b"] }]);
		draw(["s"]);
		dispatch(["s"], "focus");
		expect(document.activeElement?.getAttribute("role")).toBe("combobox");
	});
});

describe("disabled cascade", () => {
	it("disables every control and button under a disabled Fieldset", () => {
		put(["fs", "Fieldset", { disabled: true }], ["name", "InputRef", { value: "" }]);
		put(
			["fs", "Fieldset", { disabled: true }],
			["kind", "SelectRef", { value: null, options: ["a"] }],
		);
		put(["fs", "Fieldset", { disabled: true }], ["go", "ButtonRef", { label: "Go" }]);
		draw(["fs"]);
		expect(inputs()[0].disabled).toBe(true);
		expect((host.querySelector('[role="combobox"]') as HTMLButtonElement).disabled).toBe(true);
		expect((host.querySelector("button[data-slot=button]") as HTMLButtonElement).disabled).toBe(
			true,
		);
		dispatch(["fs"], OPS.write, { disabled: false });
		expect(inputs()[0].disabled).toBe(false);
	});

	it("a disabled Form disables its controls and submits nothing", () => {
		put(["f", "Form", { disabled: true }], ["name", "InputRef", { value: "x" }]);
		draw(["f"]);
		expect(inputs()[0].disabled).toBe(true);
		act(() => (host.querySelector("form") as HTMLFormElement).requestSubmit());
		expect(formSubmits()).toEqual([]);
	});
});

describe("null empties", () => {
	it("NumberInput, Select and DatePicker hold null when empty, and a form carries it", () => {
		put(["f", "Form", {}], ["n", "NumberInputRef", { value: 3 }]);
		put(["f", "Form", {}], ["s", "SelectRef", { value: "a", options: ["a"] }]);
		put(["f", "Form", {}], ["d", "DatePickerRef", { value: "2024-01-02" }]);
		draw(["f"]);
		type(inputs()[0], "");
		expect(propsAt(["f", "n"]).value).toBeNull();
		dispatch(["f", "s"], OPS.write, "");
		dispatch(["f", "d"], OPS.write, null);
		expect(propsAt(["f", "s"]).value).toBeNull();
		expect(propsAt(["f", "d"]).value).toBeNull();
		dispatch(["f"], OPS.read, null, "r");
		expect(sent.at(-1)?.payload).toEqual({ n: null, s: null, d: null });
		dispatch(["f", "n"], OPS.write, "nope");
		expect(propsAt(["f", "n"]).value).toBeNull();
	});
});

describe("Code and Markdown readonly", () => {
	it("are read-only unless told otherwise, and only an editor is gathered", () => {
		put(["f", "Form", {}], ["shown", "CodeRef", { value: "a" }]);
		put(["f", "Form", {}], ["typed", "CodeRef", { value: "b", readonly: false }]);
		put(["f", "Form", {}], ["doc", "MarkdownRef", { value: "c", readonly: true }]);
		draw(["f"]);
		dispatch(["f"], OPS.read, null, "r");
		expect(sent.at(-1)?.payload).toEqual({ typed: "b" });
	});
});
