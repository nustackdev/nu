// Input nodes over the real tree store: ButtonRef's icon and tooltip.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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
	vi.restoreAllMocks();
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(op: string, payload: unknown, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: ["n"], payload, id }));
}

const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);
// A tooltip's trigger takes over the button's data-slot, so an icon button
// under one is found by its square size class instead.
const iconButton = () => host.querySelector<HTMLElement>("button.size-8");

describe("ButtonRef", () => {
	it("draws an icon-only button as an IconButton named by its tooltip", () => {
		mount("ButtonRef", { label: "", icon: "refresh-cw", tooltip: "Reload", variant: "ghost" });
		const btn = iconButton();
		expect(btn).not.toBeNull();
		expect(btn?.getAttribute("data-slot")).toBe("tooltip-trigger");
		expect(btn?.getAttribute("aria-label")).toBe("Reload");
		expect(btn?.querySelector("svg")).not.toBeNull();
		expect(btn?.textContent).toBe("");
		expect(slot("button")).toBeNull();
	});

	it("falls back to the icon name for the accessible name", () => {
		mount("ButtonRef", { label: "", icon: "trash-2" });
		expect(slot("icon-button")?.getAttribute("aria-label")).toBe("trash-2");
	});

	it("draws the icon before the label", () => {
		mount("ButtonRef", { label: "Add", icon: "plus" });
		const btn = slot("button");
		expect(btn?.firstElementChild?.tagName.toLowerCase()).toBe("svg");
		expect(btn?.textContent).toBe("Add");
	});

	it("falls back to the label on an unknown icon, warning once", () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
		mount("ButtonRef", { label: "Go", icon: "no-such-glyph" });
		expect(slot("icon-button")).toBeNull();
		expect(slot("button")?.textContent).toBe("Go");
		expect(slot("button")?.querySelector("svg")).toBeNull();
		dispatch(OPS.write, { label: "Go again" });
		expect(warn).toHaveBeenCalledTimes(1);
		expect(String(warn.mock.calls[0][0])).toContain("no-such-glyph");
	});

	it("notifies on click and picks up an icon from a later write", () => {
		mount("ButtonRef", { label: "Run" });
		act(() => slot("button")?.click());
		expect(sent.map((f) => f.op)).toEqual([OPS.notify]);
		dispatch(OPS.write, { label: "", icon: "play", tooltip: "Run" });
		expect(iconButton()?.getAttribute("aria-label")).toBe("Run");
	});
});
