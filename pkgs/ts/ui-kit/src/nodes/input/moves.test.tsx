// The moving inputs (`Moves` on the Python side): each sends `{event:
// "input", value}` while its value moves, then `{event: "change", value}`
// when it commits. Discrete inputs send no `input`. Every payload carries
// the value, so no handler needs a read back.

import { EditorView as CMView, runScopeHandlers } from "@codemirror/view";
import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { flushOutbox, NodeView, tree, unbatch } from "../../tree";
import "..";
import { markdownAt } from "./markdown";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix sliders measure; jsdom lays nothing out.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;

// A selection change scrolls into view, which measures a range.
const noRects = () => Object.assign([], { item: () => null }) as unknown as DOMRectList;
Range.prototype.getClientRects ??= noRects;
Range.prototype.getBoundingClientRect ??= () => new DOMRect();

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
	flushOutbox();
	await act(async () => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

/** Every notify payload sent so far, batches opened, the outbox flushed first. */
function payloads(): Record<string, unknown>[] {
	flushOutbox();
	return unbatch(sent)
		.filter((f) => f.op === OPS.notify)
		.map((f) => f.payload as Record<string, unknown>);
}

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

const field = () => host.querySelector("input") as HTMLInputElement;

describe("text inputs send input per keystroke", () => {
	it("InputRef: input per keystroke, then change with the value", () => {
		mount("InputRef", { value: "" });
		type(field(), "D");
		type(field(), "Du");
		blur(field());
		expect(payloads()).toEqual([
			{ event: "input", value: "D" },
			{ event: "input", value: "Du" },
			{ event: "change", value: "Du" },
		]);
	});

	it("sends nothing on the wire until the window or a commit", () => {
		mount("InputRef", { value: "" });
		type(field(), "a");
		expect(sent).toEqual([]);
		blur(field());
		// The change takes the queued input with it, in order, in one frame.
		expect(sent.map((f) => f.op)).toEqual([OPS.batch]);
	});

	it("TextAreaRef", () => {
		mount("TextAreaRef", { value: "" });
		const area = host.querySelector("textarea") as HTMLTextAreaElement;
		type(area, "hi");
		blur(area);
		expect(payloads()).toEqual([
			{ event: "input", value: "hi" },
			{ event: "change", value: "hi" },
		]);
	});

	it("NumberInputRef: typing and a stepper both move it", () => {
		mount("NumberInputRef", { value: 1, step: 1 });
		type(field(), "4");
		blur(field());
		act(() => host.querySelector<HTMLButtonElement>('[aria-label="Increment"]')?.click());
		expect(payloads()).toEqual([
			{ event: "input", value: 4 },
			{ event: "change", value: 4 },
			{ event: "input", value: 5 },
			{ event: "change", value: 5 },
		]);
	});

	it("AutocompleteRef: the typed text", () => {
		mount("AutocompleteRef", { value: "", options: ["Atlantis"] });
		type(field(), "At");
		blur(field());
		expect(payloads()).toEqual([
			{ event: "input", value: "At" },
			{ event: "change", value: "At" },
		]);
	});

	it("InlineEditRef: the text in the editor, while the value waits for the save", () => {
		mount("InlineEditRef", { value: "Notes" });
		act(() => host.querySelector<HTMLButtonElement>("button")?.click());
		const input = host.querySelector("input") as HTMLInputElement;
		type(input, "Idea");
		expect(tree.getState().getIn(["n"])?.props.value).toBe("Notes");
		key(input, "Enter");
		expect(payloads()).toEqual([
			{ event: "input", value: "Idea" },
			{ event: "change", value: "Idea" },
			{ event: "submit", value: "Idea" },
		]);
	});

	it("TagInputRef: the draft next to the tags, a tag added is the change", () => {
		mount("TagInputRef", { value: ["a"] });
		type(field(), "b");
		key(field(), "Enter");
		expect(payloads()).toEqual([
			{ event: "input", value: ["a"], draft: "b" },
			{ event: "change", value: ["a", "b"] },
		]);
	});
});

describe("drag inputs send input per tick", () => {
	it("SliderRef: a key moves then commits", () => {
		mount("SliderRef", { value: 5, min: 0, max: 10, step: 1 });
		const thumb = host.querySelector("[role=slider]") as HTMLElement;
		act(() => thumb.focus());
		key(thumb, "ArrowRight");
		expect(payloads()).toEqual([
			{ event: "input", value: 6 },
			{ event: "change", value: 6 },
		]);
	});

	it("RangeSliderRef: the pair", () => {
		mount("RangeSliderRef", { value: [20, 60] });
		const high = host.querySelectorAll("[role=slider]")[1] as HTMLElement;
		act(() => high.focus());
		key(high, "ArrowRight");
		expect(payloads()).toEqual([
			{ event: "input", value: [20, 61] },
			{ event: "change", value: [20, 61] },
		]);
	});

	it("ColorPickerRef: the hex", () => {
		mount("ColorPickerRef", { value: "#ff0000" });
		act(() => host.querySelector<HTMLButtonElement>("[data-slot=color-picker-trigger]")?.click());
		const area = document.querySelector('[aria-label="Saturation and brightness"]') as HTMLElement;
		act(() => area.focus());
		key(area, "ArrowDown", { shiftKey: true });
		expect(payloads()).toEqual([
			{ event: "input", value: "#e60000" },
			{ event: "change", value: "#e60000" },
		]);
	});
});

describe("SketchRef: input per point, change per stroke", () => {
	function fire(el: HTMLElement, kind: string, x: number, y: number) {
		const e = new MouseEvent(kind, { bubbles: true, cancelable: true, clientX: x, clientY: y });
		Object.defineProperty(e, "pointerId", { value: 1 });
		Object.defineProperty(e, "pointerType", { value: "mouse" });
		Object.defineProperty(e, "pressure", { value: 0.5 });
		act(() => {
			el.dispatchEvent(e);
		});
	}

	it("sends the board with the stroke in flight last, then the committed board", () => {
		mount("SketchRef", { width: 200, value: [] });
		const el = host.querySelector("[data-slot=sketch-board-surface]") as HTMLElement;
		el.getBoundingClientRect = () => new DOMRect(0, 0, 200, 200);
		el.setPointerCapture = () => {};
		fire(el, "pointerdown", 20, 40);
		fire(el, "pointermove", 60, 80);
		fire(el, "pointerup", 60, 80);
		const out = payloads();
		expect(out.map((p) => p.event)).toEqual(["input", "input", "change"]);
		const points = (p: Record<string, unknown>) =>
			(p.value as { points: number[][] }[])[0].points.map((pt) => pt.slice(0, 2));
		expect(points(out[0])).toEqual([[0.1, 0.2]]);
		expect(points(out[1])).toEqual([
			[0.1, 0.2],
			[0.3, 0.4],
		]);
		expect(points(out[2])).toEqual(points(out[1]));
		expect(out[2].value).toEqual(tree.getState().getIn(["n"])?.props.value);
	});
});

describe("editors send input per edit", () => {
	it("CodeRef: the buffer, then the commit", () => {
		mount("CodeRef", { value: "", readonly: false });
		const cm = CMView.findFromDOM(host.querySelector(".cm-editor") as HTMLElement) as CMView;
		act(() => {
			cm.focus();
			cm.dispatch({ changes: { from: 0, insert: "x = 1" } });
		});
		expect(tree.getState().getIn(["n"])?.props.value).toBe("");
		act(() => {
			runScopeHandlers(
				cm,
				new KeyboardEvent("keydown", { key: "Enter", shiftKey: true }),
				"editor",
			);
		});
		expect(payloads()).toEqual([
			{ event: "input", value: "x = 1" },
			{ event: "change", value: "x = 1" },
			{ event: "submit", value: "x = 1" },
		]);
	});

	it("MarkdownRef: the document as markdown, then the save", () => {
		mount("MarkdownRef", { value: "a\n", readonly: false });
		const doc = markdownAt(["n"])?.handle;
		if (!doc) throw new Error("no editable markdown editor");
		act(() => {
			doc.focus("end");
			doc.type("b");
			doc.commit();
		});
		expect(payloads()).toEqual([
			{ event: "input", value: "ab\n" },
			{ event: "change", value: "ab\n" },
		]);
	});
});

describe("discrete inputs", () => {
	it("send a change with the value and no input", () => {
		mount("CheckboxRef", { value: false, label: "Done" });
		act(() => host.querySelector<HTMLButtonElement>("button")?.click());
		expect(payloads()).toEqual([{ event: "change", value: true }]);
	});
});
