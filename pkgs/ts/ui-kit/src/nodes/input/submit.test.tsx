// The send key of the multi-line inputs (./control.ts `useSubmit`): the
// text area, the code editor and the markdown editor each send on
// shift+Enter, standalone and inside a Form, with the latest text; one
// key fires the input's own submit, then the form's; `clear_on_submit`
// (the input's or the form's) puts the declared value back, in the editor's
// document too; plain Enter still breaks the line, `submit_on="enter"`
// swaps the two keys on all three alike, and cmd/ctrl+Enter is left to the
// app.

import { EditorView as CMView, runScopeHandlers } from "@codemirror/view";
import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";
import { markdownAt } from "./markdown";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// CodeMirror and ProseMirror measure through ranges; jsdom lays nothing out.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

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

afterEach(async () => {
	await act(async () => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

type Kind = "TextAreaRef" | "CodeRef" | "MarkdownRef";

/** One multi-line input, the same three ways: type, press a key, read the screen. */
type Driver = {
	type(text: string): void;
	/** Press Enter in it, the way the keyboard would. */
	enter(mods?: KeyboardEventInit): void;
	/** What the screen shows: the textarea's value, the editor's document. */
	shown(): string;
};

const SEND = { shiftKey: true };

function driver(kind: Kind): Driver {
	if (kind === "TextAreaRef") {
		const area = host.querySelector("textarea") as HTMLTextAreaElement;
		return {
			type(text) {
				const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
				act(() => {
					area.focus();
					setter?.call(area, area.value + text);
					area.dispatchEvent(new Event("input", { bubbles: true }));
				});
			},
			enter(mods = {}) {
				act(() => {
					const e = new KeyboardEvent("keydown", {
						key: "Enter",
						bubbles: true,
						cancelable: true,
						...mods,
					});
					// A key the field leaves alone is the browser's newline: type it.
					if (area.dispatchEvent(e) && !mods.ctrlKey && !mods.metaKey) {
						const setter = Object.getOwnPropertyDescriptor(
							HTMLTextAreaElement.prototype,
							"value",
						)?.set;
						setter?.call(area, `${area.value}\n`);
						area.dispatchEvent(new Event("input", { bubbles: true }));
					}
				});
			},
			shown: () => area.value,
		};
	}
	if (kind === "CodeRef") {
		const cm = CMView.findFromDOM(host.querySelector(".cm-editor") as HTMLElement) as CMView;
		return {
			type(text) {
				act(() => {
					cm.focus();
					const end = cm.state.doc.length;
					cm.dispatch({
						changes: { from: end, insert: text },
						selection: { anchor: end + text.length },
					});
				});
			},
			enter(mods = {}) {
				act(() => {
					runScopeHandlers(cm, new KeyboardEvent("keydown", { key: "Enter", ...mods }), "editor");
				});
			},
			shown: () => cm.state.doc.toString(),
		};
	}
	const handle = () => {
		const h = markdownAt(["f", "in"])?.handle ?? markdownAt(["in"])?.handle;
		if (!h) throw new Error("no editable markdown editor");
		return h;
	};
	const pm = () => host.querySelector(".nu-prose-editor") as HTMLElement;
	return {
		type(text) {
			act(() => {
				handle().focus("end");
				handle().type(text);
			});
		},
		enter(mods = {}) {
			act(() => {
				pm().dispatchEvent(
					new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true, ...mods }),
				);
			});
		},
		shown: () => handle().markdown(),
	};
}

const EDITABLE: Record<Kind, Record<string, unknown>> = {
	TextAreaRef: {},
	CodeRef: { readonly: false },
	MarkdownRef: { readonly: false },
};

function alone(kind: Kind, props: Record<string, unknown> = {}): Driver {
	tree.getState().write([["in", kind, { value: "", ...EDITABLE[kind], ...props }]]);
	act(() => root.render(<NodeView path={["in"]} />));
	return driver(kind);
}

function inForm(
	kind: Kind,
	form: Record<string, unknown> = {},
	props: Record<string, unknown> = {},
): Driver {
	tree.getState().write([
		["f", "Form", form],
		["in", kind, { value: "", ...EDITABLE[kind], ...props }],
	]);
	act(() => root.render(<NodeView path={["f"]} />));
	return driver(kind);
}

const notifies = () => sent.filter((f) => f.op === OPS.notify);
const events = () =>
	notifies().map((f) => ({ ref: f.ref, event: (f.payload as { event: string }).event }));
const submits = () =>
	notifies()
		.filter((f) => (f.payload as { event: string }).event === "submit")
		.map((f) => ({ ref: f.ref, payload: f.payload }));
const valueAt = (path: string[]) => tree.getState().getIn(path)?.props.value;

/** The markdown editor writes a trailing newline; the other two keep the text as typed. */
const text = (kind: Kind, s: string) => (kind === "MarkdownRef" ? `${s}\n` : s);

describe.each(["TextAreaRef", "CodeRef", "MarkdownRef"] as Kind[])("%s send key", (kind) => {
	it("sends on shift+Enter with the latest text, after its change", () => {
		const d = alone(kind);
		d.type("hello");
		d.enter(SEND);
		expect(events()).toEqual([
			{ ref: ["in"], event: "change" },
			{ ref: ["in"], event: "submit" },
		]);
		expect(submits()[0].payload).toEqual({ event: "submit", value: text(kind, "hello") });
		expect(d.shown()).toBe(text(kind, "hello"));
	});

	it("sends nothing on cmd/ctrl+Enter", () => {
		const d = alone(kind);
		d.type("hello");
		d.enter({ ctrlKey: true });
		d.enter({ metaKey: true });
		expect(submits()).toEqual([]);
	});

	it("swaps the keys with submit_on=enter: Enter sends, shift+Enter breaks the line", () => {
		const d = alone(kind, { submit_on: "enter" });
		d.type("a");
		d.enter(SEND);
		d.type("b");
		expect(submits()).toEqual([]);
		d.enter();
		expect(submits()[0].payload).toEqual({
			event: "submit",
			value: kind === "MarkdownRef" ? "a\n\nb\n" : "a\nb",
		});
	});

	it("submits its Form on Enter with submit_on=enter", () => {
		const d = inForm(kind, {}, { submit_on: "enter" });
		d.type("go");
		d.enter();
		expect(submits().at(-1)?.payload).toMatchObject({ values: { in: text(kind, "go") } });
	});

	it("breaks the line on plain Enter, and sends nothing", () => {
		const d = alone(kind);
		d.type("a");
		d.enter();
		d.type("b");
		expect(submits()).toEqual([]);
		expect(d.shown()).toBe(kind === "MarkdownRef" ? "a\n\nb\n" : "a\nb");
	});

	it("puts the declared value back with clear_on_submit, in the editor too", () => {
		const d = alone(kind, { clear_on_submit: true });
		d.type("gone");
		d.enter(SEND);
		expect(submits()[0].payload).toEqual({ event: "submit", value: text(kind, "gone") });
		expect(valueAt(["in"])).toBe("");
		expect(d.shown()).toBe("");
		// And it takes the next message from empty.
		d.type("next");
		d.enter(SEND);
		expect(submits()[1].payload).toEqual({ event: "submit", value: text(kind, "next") });
	});

	it("submits its Form with the latest text, after its own submit", () => {
		const d = inForm(kind);
		d.type("in a form");
		d.enter(SEND);
		expect(events()).toEqual([
			{ ref: ["f", "in"], event: "change" },
			{ ref: ["f", "in"], event: "submit" },
			{ ref: ["f"], event: "submit" },
		]);
		expect(submits().at(-1)?.payload).toEqual({
			event: "submit",
			values: { in: text(kind, "in a form") },
			button: null,
		});
	});

	it("is emptied by its Form's clear_on_submit, in the editor too", () => {
		const d = inForm(kind, { clear_on_submit: true });
		d.type("sent");
		d.enter(SEND);
		expect(submits().at(-1)?.payload).toMatchObject({ values: { in: text(kind, "sent") } });
		expect(valueAt(["f", "in"])).toBe("");
		expect(d.shown()).toBe("");
	});

	it("breaks the line on plain Enter inside a Form, and submits nothing", () => {
		const d = inForm(kind);
		d.type("a");
		d.enter();
		d.type("b");
		expect(submits()).toEqual([]);
		expect(d.shown()).toBe(kind === "MarkdownRef" ? "a\n\nb\n" : "a\nb");
	});
});

describe("send key, read-only", () => {
	it("sends nothing from a read-only code block or document", () => {
		alone("CodeRef", { readonly: true });
		const cm = CMView.findFromDOM(host.querySelector(".cm-editor") as HTMLElement) as CMView;
		act(() => {
			runScopeHandlers(
				cm,
				new KeyboardEvent("keydown", { key: "Enter", shiftKey: true }),
				"editor",
			);
		});
		act(() => root.render(null));
		tree.getState().write([["doc", "MarkdownRef", { value: "a", readonly: true }]]);
		act(() => root.render(<NodeView path={["doc"]} />));
		const pm = host.querySelector(".nu-prose-editor") as HTMLElement;
		act(() => {
			pm.dispatchEvent(
				new KeyboardEvent("keydown", { key: "Enter", shiftKey: true, bubbles: true }),
			);
		});
		expect(submits()).toEqual([]);
	});
});
