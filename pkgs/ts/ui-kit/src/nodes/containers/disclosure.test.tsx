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
