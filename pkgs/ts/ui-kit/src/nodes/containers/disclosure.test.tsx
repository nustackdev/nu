// Disclosure containers over the real tree store: what open state leaves on
// screen, and the notify each user toggle or dismiss sends out.

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
		expect(sent).toEqual([{ op: OPS.notify, ref: ["c"], payload: { open: true }, id: undefined }]);
		act(() => trigger().click());
		expect(body()).toBe(false);
		expect(sent.at(-1)?.payload).toEqual({ open: false });
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

	it("renders its title and children when open, on its side", () => {
		mount("s", "Sheet", { open: true, title: "Edit host", side: "left", size: "lg" });
		const el = content();
		expect(el).not.toBeNull();
		expect(el?.querySelector("[data-slot=sheet-title]")?.textContent).toBe("Edit host");
		expect(el?.textContent).toContain("inside the body");
		expect(el?.className).toContain("left-0");
		expect(el?.className).toContain("w-[35rem]");
	});

	it("closes on Escape and notifies {open: false}", () => {
		mount("s", "Sheet", { open: true, title: "Edit host" });
		pressEscape();
		expect(sent).toEqual([{ op: OPS.notify, ref: ["s"], payload: { open: false }, id: undefined }]);
		expect(tree.getState().getIn(["s"])?.props.open).toBe(false);
	});

	it("closes on the close button, and a server write opens it again", () => {
		mount("s", "Sheet", { open: true, title: "Edit host" });
		act(() => (document.querySelector("[data-slot=sheet-close-icon]") as HTMLElement).click());
		expect(sent.at(-1)?.payload).toEqual({ open: false });
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
