// InputRef types (search with clear, password with reveal, the native ones),
// InlineEditRef (Enter saves and submits, blur saves, Escape cancels, inline
// error) and the InputGroup container, over the real tree store.

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

const notifies = () =>
	sent.filter((f) => f.op === OPS.notify).map((f) => ({ ref: f.ref, payload: f.payload }));
const propsAt = (path: string[]) => tree.getState().getIn(path)?.props ?? {};

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

const input = () => host.querySelector("input") as HTMLInputElement;
const change = (ref: string[]) => ({ ref, payload: { event: "change" } });
const submit = (ref: string[]) => ({ ref, payload: { event: "submit" } });

describe("InputRef types", () => {
	it("draws the native field for email, url, tel and number", () => {
		for (const kind of ["email", "url", "tel", "number"]) {
			put(["n", "InputRef", { value: "", type: kind }]);
			draw(["n"]);
			expect(input().type).toBe(kind);
			act(() => root.render(null));
			tree.getState().remove([]);
		}
	});

	it("search: the clear button and Escape clear the field and commit", () => {
		put(["n", "InputRef", { value: "dune", type: "search", label: "Find" }]);
		draw(["n"]);
		expect(input().type).toBe("search");
		const clear = host.querySelector('button[aria-label="Clear"]') as HTMLButtonElement;
		expect(clear.tabIndex).toBe(-1);
		act(() => clear.click());
		expect(propsAt(["n"]).value).toBe("");
		expect(notifies()).toEqual([change(["n"])]);
		expect(host.querySelector('button[aria-label="Clear"]')).toBeNull();

		type(input(), "heat");
		key(input(), "Escape");
		expect(propsAt(["n"]).value).toBe("");
		// Typed and cleared before any commit: nothing moved, nothing sent.
		expect(notifies()).toEqual([change(["n"])]);
	});

	it("search: Enter submits like any field", () => {
		put(["n", "InputRef", { value: "", type: "search" }]);
		draw(["n"]);
		type(input(), "dune");
		key(input(), "Enter");
		expect(notifies()).toEqual([change(["n"]), submit(["n"])]);
	});

	it("search: no clear button while disabled or readonly", () => {
		put(["n", "InputRef", { value: "x", type: "search", readonly: true }]);
		draw(["n"]);
		expect(host.querySelector('button[aria-label="Clear"]')).toBeNull();
	});

	it("password: the toggle reveals and hides, and sends nothing", () => {
		put(["n", "InputRef", { value: "secret", type: "password", label: "Password" }]);
		draw(["n"]);
		expect(input().type).toBe("password");
		const toggle = host.querySelector('button[aria-label="Show password"]') as HTMLButtonElement;
		expect(toggle.getAttribute("aria-pressed")).toBe("false");
		expect(toggle.getAttribute("aria-controls")).toBe(input().id);
		act(() => toggle.click());
		expect(input().type).toBe("text");
		expect(toggle.getAttribute("aria-pressed")).toBe("true");
		act(() => toggle.click());
		expect(input().type).toBe("password");
		expect(notifies()).toEqual([]);
	});
});

describe("InlineEditRef", () => {
	const shown = () => host.querySelector("button") as HTMLButtonElement;

	it("shows the text on a button, the placeholder while empty", () => {
		put(["n", "InlineEditRef", { value: "", placeholder: "Untitled", label: "Name" }]);
		draw(["n"]);
		expect(input()).toBeNull();
		expect(shown().textContent).toContain("Untitled");
		const label = host.querySelector("label") as HTMLLabelElement;
		expect(shown().getAttribute("aria-labelledby")).toContain(label.id);
	});

	it("Enter saves and submits, then hands focus back to the text", () => {
		put(["n", "InlineEditRef", { value: "Notes" }]);
		draw(["n"]);
		act(() => shown().click());
		expect(input().value).toBe("Notes");
		expect(document.activeElement).toBe(input());
		type(input(), "Ideas");
		expect(notifies()).toEqual([]);
		key(input(), "Enter");
		expect(propsAt(["n"]).value).toBe("Ideas");
		expect(notifies()).toEqual([change(["n"]), submit(["n"])]);
		expect(input()).toBeNull();
		expect(document.activeElement).toBe(shown());
		expect(shown().textContent).toContain("Ideas");
	});

	it("a blur saves, with a change only when the text moved", () => {
		put(["n", "InlineEditRef", { value: "Notes" }]);
		draw(["n"]);
		act(() => shown().click());
		blur(input());
		expect(notifies()).toEqual([]);
		act(() => shown().click());
		type(input(), "Draft");
		blur(input());
		expect(propsAt(["n"]).value).toBe("Draft");
		expect(notifies()).toEqual([change(["n"])]);
	});

	it("Escape cancels and puts the text back", () => {
		put(["n", "InlineEditRef", { value: "Notes" }]);
		draw(["n"]);
		act(() => shown().click());
		type(input(), "Oops");
		key(input(), "Escape");
		expect(input()).toBeNull();
		expect(propsAt(["n"]).value).toBe("Notes");
		expect(shown().textContent).toContain("Notes");
		expect(document.activeElement).toBe(shown());
		expect(notifies()).toEqual([]);
	});

	it("a required one saved empty is a cancel", () => {
		put(["n", "InlineEditRef", { value: "Notes", required: true }]);
		draw(["n"]);
		act(() => shown().click());
		type(input(), "  ");
		key(input(), "Enter");
		expect(propsAt(["n"]).value).toBe("Notes");
		expect(notifies()).toEqual([]);
	});

	it("draws an inline error and wires it onto the editor", () => {
		put(["n", "InlineEditRef", { value: "Notes", error: "Taken" }]);
		draw(["n"]);
		const alert = host.querySelector('[role="alert"]') as HTMLElement;
		expect(alert.textContent).toContain("Taken");
		expect(shown().getAttribute("aria-describedby")).toBe(alert.id);
		act(() => shown().click());
		expect(input().getAttribute("aria-invalid")).toBe("true");
		expect(input().getAttribute("aria-describedby")).toBe(alert.id);
		dispatch(["n"], OPS.write, { error: "" });
		expect(host.querySelector('[role="alert"]')).toBeNull();
	});

	it("readonly shows plain text, disabled a disabled button", () => {
		put(["n", "InlineEditRef", { value: "Notes", readonly: true }]);
		draw(["n"]);
		expect(host.querySelector("button")).toBeNull();
		expect(host.textContent).toContain("Notes");
		dispatch(["n"], OPS.write, { readonly: false, disabled: true });
		expect(shown().disabled).toBe(true);
	});

	it("takes a write (bare, map, null), answers a read, and resets to its seed", () => {
		put(["n", "InlineEditRef", { value: "seed" }]);
		draw(["n"]);
		dispatch(["n"], OPS.write, "bare");
		expect(propsAt(["n"]).value).toBe("bare");
		dispatch(["n"], OPS.write, { value: "mapped", placeholder: "P" });
		expect(propsAt(["n"])).toMatchObject({ value: "mapped", placeholder: "P" });
		dispatch(["n"], OPS.write, null);
		expect(propsAt(["n"]).value).toBe("");
		dispatch(["n"], OPS.write, "live");
		dispatch(["n"], OPS.read, null, "r");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: "live", id: "r" });
		dispatch(["n"], "reset");
		expect(propsAt(["n"]).value).toBe("seed");
	});

	it("lands in a Form's values, and Enter asks the Form to submit", () => {
		put(["f", "Form", {}], ["name", "InlineEditRef", { value: "Notes" }]);
		put(["f", "Form", {}], ["save", "ButtonRef", { label: "Save", submit: true }]);
		draw(["f"]);
		act(() => (host.querySelector("button:not([type=submit])") as HTMLButtonElement).click());
		type(input(), "Ideas");
		key(input(), "Enter");
		const form = notifies().filter((n) => n.ref.length === 1);
		expect(form).toEqual([
			{ ref: ["f"], payload: { event: "submit", values: { name: "Ideas" }, button: "save" } },
		]);
	});

	it("inside a Field takes the Field's label, help and error", () => {
		put(
			["fld", "Field", { label: "Name", help: "Shown in the rail", error: "Taken" }],
			["control", "InlineEditRef", { value: "Notes", label: "own" }],
		);
		draw(["fld"]);
		const labels = host.querySelectorAll("label");
		expect(labels).toHaveLength(1);
		expect(shown().id).toBe(labels[0].htmlFor);
		expect(shown().getAttribute("aria-labelledby")).toContain(labels[0].id);
		expect(shown().getAttribute("aria-describedby")).toContain("-error");
	});
});

describe("InputGroup", () => {
	function say() {
		put(["f", "Form", {}], ["say", "InputGroup", {}], ["text", "InputRef", { value: "" }]);
		put(["f", "Form", {}], ["say", "InputGroup", {}], ["send", "ButtonRef", { label: "Send" }]);
		put(["f", "Form", {}], ["save", "ButtonRef", { label: "Save", submit: true }]);
		draw(["f"]);
	}

	it("grows the field, keeps the button its own size, all on the bottom edge", () => {
		say();
		const group = host.querySelector('[data-slot="input-group"]') as HTMLElement;
		expect(group.className).toContain("items-end");
		const cells = Array.from(group.children);
		expect(cells).toHaveLength(2);
		expect(cells[0].hasAttribute("data-fill")).toBe(true);
		expect(cells[1].hasAttribute("data-fill")).toBe(false);
		expect(cells[1].querySelector("button")?.textContent).toContain("Send");
	});

	it("nests its children in a Form's values, and its field's Enter submits", () => {
		say();
		type(input(), "hi");
		key(input(), "Enter");
		const form = notifies().filter((n) => n.ref.length === 1);
		expect(form).toEqual([
			{
				ref: ["f"],
				payload: { event: "submit", values: { say: { text: "hi" } }, button: "save" },
			},
		]);
	});

	it("takes its gap from the layout", () => {
		put(["g", "InputGroup", { gap: 4 }], ["q", "InputRef", { value: "" }]);
		draw(["g"]);
		const group = host.querySelector('[data-slot="input-group"]') as HTMLElement;
		expect(group.className).toContain("gap-4");
		expect(group.className).not.toContain("gap-2");
	});
});
