// Disclosure containers over the real tree store: what open state leaves on
// screen, the change each user toggle or dismiss emits, and what a read answers.

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

function mount(seg: string, type: string, props: Record<string, unknown>) {
	act(() => {
		tree.getState().write([[seg, type, props]]);
		tree.getState().write([
			[seg, type],
			["note", "TextRef", { value: "inside the body" }],
		]);
	});
	act(() => root.render(<NodeView path={[seg]} />));
}

function write(seg: string, payload: unknown) {
	act(() => {
		tree.getState().dispatch({ op: OPS.write, ref: [seg], payload });
	});
}

describe("Collapsible", () => {
	const trigger = () => host.querySelector("[data-slot=collapsible-trigger]") as HTMLButtonElement;
	const body = () => host.textContent?.includes("inside the body") ?? false;

	it("renders its title and hides the body when closed", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		expect(trigger().textContent).toBe("Details");
		expect(trigger().getAttribute("aria-expanded")).toBe("false");
		expect(body()).toBe(false);
	});

	it("renders its children when open", () => {
		mount("c", "Collapsible", { title: "Details", open: true });
		expect(trigger().getAttribute("aria-expanded")).toBe("true");
		expect(body()).toBe(true);
	});

	it("toggles locally and notifies the new open state", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		act(() => trigger().click());
		expect(body()).toBe(true);
		expect(sent).toEqual([
			{ op: OPS.notify, ref: ["c"], payload: { event: "change", value: true }, id: undefined },
		]);
		act(() => trigger().click());
		expect(body()).toBe(false);
		expect(sent.at(-1)?.payload).toEqual({ event: "change", value: false });
	});

	it("opens, closes and retitles from a server write without notifying", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		write("c", { open: true });
		expect(body()).toBe(true);
		write("c", { title: "More" });
		expect(trigger().textContent).toBe("More");
		expect(body()).toBe(true);
		write("c", { open: false });
		expect(body()).toBe(false);
		expect(sent).toEqual([]);
	});
});

// A header Row under `seg` at `key`: a line of text and a button in it.
function header(seg: string, type: string, key: string) {
	act(() => {
		tree.getState().write([
			[seg, type],
			[key, "Row"],
			["name", "TextRef", { value: "read_file" }],
		]);
		tree.getState().write([
			[seg, type],
			[key, "Row"],
			["go", "ButtonRef", { label: "Open" }],
		]);
	});
}

const rowTrigger = () => host.querySelector("[data-row-trigger]") as HTMLButtonElement;
const headerBox = () => host.querySelector("[data-slot=trigger-row-header]") as HTMLElement;
const headerText = () =>
	[...headerBox().querySelectorAll("*")].find(
		(el) => el.children.length === 0 && el.textContent === "read_file",
	) as HTMLElement;
const headerButton = () => headerBox().querySelector("button") as HTMLButtonElement;

describe("Collapsible header", () => {
	const body = () => host.textContent?.includes("inside the body") ?? false;

	it("draws the header in place of the title, chevron kept", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		header("c", "Collapsible", "header");
		expect(host.textContent).not.toContain("Details");
		expect(headerBox().textContent).toContain("read_file");
		expect(rowTrigger().querySelector("svg")).not.toBeNull();
		expect(rowTrigger().contains(headerButton())).toBe(false);
		expect(body()).toBe(false);
	});

	it("names the trigger by the header box", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		header("c", "Collapsible", "header");
		expect(rowTrigger().getAttribute("aria-labelledby")).toBe(headerBox().id);
		expect(rowTrigger().getAttribute("aria-expanded")).toBe("false");
		act(() => rowTrigger().click());
		const content = host.querySelector("[data-slot=collapsible-content]") as HTMLElement;
		expect(rowTrigger().getAttribute("aria-controls")).toBe(content.id);
	});

	it("toggles and notifies on a click on the row's text", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		header("c", "Collapsible", "header");
		act(() => headerText().click());
		expect(body()).toBe(true);
		expect(sent).toEqual([
			{ op: OPS.notify, ref: ["c"], payload: { event: "change", value: true }, id: undefined },
		]);
		act(() => rowTrigger().click());
		expect(body()).toBe(false);
		expect(sent.at(-1)?.payload).toEqual({ event: "change", value: false });
	});

	it("lets a button in the header click without toggling", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		header("c", "Collapsible", "header");
		act(() => headerButton().click());
		expect(body()).toBe(false);
		expect(sent.map((f) => f.ref)).toEqual([["c", "header", "go"]]);
	});

	it("keeps one focusable trigger, first in the row, for Space and Enter", () => {
		mount("c", "Collapsible", { title: "Details", open: false });
		header("c", "Collapsible", "header");
		const row = host.querySelector("[data-slot=trigger-row]") as HTMLElement;
		const trigger = rowTrigger();
		// A native button: the browser turns Space and Enter into its click,
		// which Radix toggles on. jsdom does not, so the click stands in.
		expect(trigger.tagName).toBe("BUTTON");
		expect(trigger.getAttribute("type")).toBe("button");
		expect(row.querySelector("button")).toBe(trigger);
		trigger.focus();
		expect(document.activeElement).toBe(trigger);
		act(() => trigger.click());
		expect(trigger.getAttribute("aria-expanded")).toBe("true");
		expect(document.activeElement).toBe(trigger);
	});

	it("keeps the header out of the body", () => {
		mount("c", "Collapsible", { title: "Details", open: true });
		header("c", "Collapsible", "header");
		const content = host.querySelector("[data-slot=collapsible-content]");
		expect(content?.textContent).not.toContain("read_file");
		expect(content?.textContent).toContain("inside the body");
	});
});

describe("Accordion header", () => {
	const sections = [
		{ id: "one", label: "One" },
		{ id: "two", label: "Two" },
	];
	const regions = () =>
		[...host.querySelectorAll("[role=region][data-state=open]")].map((r) => r.textContent);

	function mountAcc() {
		act(() => {
			tree.getState().write([["a", "Accordion", { sections, open: [] }]]);
			tree.getState().write([
				["a", "Accordion"],
				["one", "TextRef", { value: "first" }],
			]);
		});
		header("a", "Accordion", "header:one");
		act(() => root.render(<NodeView path={["a"]} />));
	}

	it("draws a section's header in place of its label, the others keep theirs", () => {
		mountAcc();
		expect(headerBox().textContent).toContain("read_file");
		expect(host.textContent).not.toContain("One");
		expect(host.textContent).toContain("Two");
		expect(rowTrigger().getAttribute("aria-labelledby")).toBe(headerBox().id);
		expect(rowTrigger().closest("h3")).not.toBeNull();
	});

	it("does not list a header key as a stray", () => {
		mountAcc();
		expect(host.textContent).not.toContain("not drawn");
	});

	it("names a header for an id no section has", () => {
		mountAcc();
		header("a", "Accordion", "header:nope");
		expect(host.textContent).toContain('"header:nope" not drawn, no section has that id');
	});

	it("toggles on the row's text and notifies, not on a button in the header", () => {
		mountAcc();
		act(() => headerButton().click());
		expect(regions()).toEqual([]);
		expect(sent.map((f) => f.ref)).toEqual([["a", "header:one", "go"]]);
		act(() => headerText().click());
		expect(regions()).toEqual(["first"]);
		expect(sent.at(-1)).toEqual({
			op: OPS.notify,
			ref: ["a"],
			payload: { event: "change", value: ["one"] },
			id: undefined,
		});
	});
});

describe("Sheet", () => {
	// The sheet portals to <body>, out of `host`.
	const content = () => document.querySelector("[data-slot=sheet-content]") as HTMLElement | null;
	const pressEscape = () =>
		act(() => {
			document.activeElement?.dispatchEvent(
				new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
			);
		});

	it("renders nothing while closed", () => {
		mount("s", "Sheet", { open: false, title: "Edit host" });
		expect(content()).toBeNull();
	});

	it("renders its title and children when open, on its side, at its width", () => {
		mount("s", "Sheet", { open: true, title: "Edit host", side: "left", width: 560 });
		const el = content();
		expect(el).not.toBeNull();
		expect(el?.querySelector("[data-slot=sheet-title]")?.textContent).toBe("Edit host");
		expect(el?.textContent).toContain("inside the body");
		expect(el?.className).toContain("left-0");
		expect(el?.style.width).toBe("560px");
	});

	it("closes on Escape and emits a change to false", () => {
		mount("s", "Sheet", { open: true, title: "Edit host" });
		pressEscape();
		expect(sent).toEqual([
			{ op: OPS.notify, ref: ["s"], payload: { event: "change", value: false }, id: undefined },
		]);
		expect(tree.getState().getIn(["s"])?.props.open).toBe(false);
	});

	it("closes on the close button, and a server write opens it again", () => {
		mount("s", "Sheet", { open: true, title: "Edit host" });
		act(() => (document.querySelector("[data-slot=sheet-close-icon]") as HTMLElement).click());
		expect(sent.at(-1)?.payload).toEqual({ event: "change", value: false });
		expect(tree.getState().getIn(["s"])?.props.open).toBe(false);
		write("s", { open: true });
		expect(tree.getState().getIn(["s"])?.props.open).toBe(true);
	});

	it("never notifies when not dismissible, and draws no close button", () => {
		mount("s", "Sheet", { open: true, title: "Edit host", dismissible: false });
		pressEscape();
		expect(sent).toEqual([]);
		expect(document.querySelector("[data-slot=sheet-close-icon]")).toBeNull();
	});

	it("closes and reopens from a server write", () => {
		mount("s", "Sheet", { open: true, title: "Edit host" });
		write("s", { open: false });
		expect(content()).toBeNull();
		write("s", { open: true, title: "Again" });
		expect(content()?.querySelector("[data-slot=sheet-title]")?.textContent).toBe("Again");
		expect(sent).toEqual([]);
	});
});

describe("Popover", () => {
	// The panel portals to <body>, out of `host`.
	const trigger = () => host.querySelector("button") as HTMLButtonElement;
	const panel = () => document.querySelector("[data-node=popover]") as HTMLElement | null;

	it("draws an icon trigger named by its tooltip, and no panel while closed", () => {
		mount("p", "Popover", { icon: "settings-2", tooltip: "Settings", open: false });
		expect(trigger().getAttribute("aria-label")).toBe("Settings");
		expect(trigger().getAttribute("aria-expanded")).toBe("false");
		expect(panel()).toBeNull();
	});

	it("draws a labelled trigger when it has a label", () => {
		mount("p", "Popover", { label: "Options", open: false });
		expect(trigger().textContent).toBe("Options");
	});

	it("opens on a click, shows its body and notifies", () => {
		mount("p", "Popover", { icon: "settings-2", tooltip: "Settings", open: false });
		act(() => {
			trigger().dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, button: 0 }));
			trigger().click();
		});
		expect(panel()?.textContent).toContain("inside the body");
		expect(sent.at(-1)).toEqual({
			op: OPS.notify,
			ref: ["p"],
			payload: { event: "change", value: true },
			id: undefined,
		});
		expect(tree.getState().getIn(["p"])?.props.open).toBe(true);
	});

	it("opens and closes from a server write without notifying, at its width", () => {
		mount("p", "Popover", { icon: "settings-2", open: false, width: 360 });
		write("p", { open: true });
		expect(panel()?.style.width).toBe("360px");
		expect(panel()?.textContent).toContain("inside the body");
		write("p", { open: false });
		expect(sent).toEqual([]);
	});
});
