// Input nodes over the real tree store: ButtonRef's icon and tooltip,
// ToggleRef's press, write and read, and SelectRef's searchable picker.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, registry, tree } from "../../tree";
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

const props = () => tree.getState().getIn(["n"])?.props ?? {};
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

describe("ToggleRef", () => {
	it("flips pressed and notifies on press", () => {
		mount("ToggleRef", { label: "", icon: "bold", pressed: false });
		const t = slot("toggle");
		expect(t?.getAttribute("aria-label")).toBe("bold");
		expect(t?.getAttribute("aria-pressed")).toBe("false");
		act(() => t?.click());
		expect(props().pressed).toBe(true);
		expect(slot("toggle")?.getAttribute("aria-pressed")).toBe("true");
		expect(sent.map((f) => f.op)).toEqual([OPS.notify]);
	});

	it("lands a bare write on pressed and merges a map", () => {
		mount("ToggleRef", { label: "Wrap", icon: "", pressed: false });
		dispatch(OPS.write, true);
		expect(props().pressed).toBe(true);
		dispatch(OPS.write, { label: "Pin", icon: "pin" });
		expect(props()).toMatchObject({ label: "Pin", icon: "pin", pressed: true });
		expect(slot("toggle")?.querySelector("svg")).not.toBeNull();
		dispatch(OPS.write, null);
		expect(props().pressed).toBe(false);
	});

	it("answers a read with the pressed state", () => {
		mount("ToggleRef", { label: "Pin", pressed: true });
		dispatch(OPS.read, null, "r1");
		expect(sent).toEqual([expect.objectContaining({ op: OPS.read, payload: true, id: "r1" })]);
	});
});

describe("SelectRef", () => {
	const options = [
		{ value: "nu", label: "Nu" },
		{ value: "nulog", label: "nulog" },
	];

	it("renders the Combobox trigger when searchable", () => {
		mount("SelectRef", { options, selected: "nu", searchable: true });
		const trigger = slot("combobox-trigger");
		expect(trigger).not.toBeNull();
		expect(trigger?.getAttribute("role")).toBe("combobox");
		expect(trigger?.textContent).toBe("Nu");
		expect(slot("select-trigger")).toBeNull();
	});

	it("shows the placeholder, muted, with nothing picked", () => {
		mount("SelectRef", { options, selected: "", placeholder: "Pick one", searchable: true });
		const trigger = slot("combobox-trigger");
		expect(trigger?.textContent).toBe("Pick one");
		expect(trigger?.hasAttribute("data-placeholder")).toBe(true);
	});

	it("keeps the plain Select by default", () => {
		mount("SelectRef", { options, selected: "nu" });
		expect(slot("select-trigger")).not.toBeNull();
		expect(slot("combobox-trigger")).toBeNull();
	});

	it("keeps the read contract when searchable", () => {
		mount("SelectRef", { options, selected: "", searchable: true });
		dispatch(OPS.write, "nulog");
		expect(slot("combobox-trigger")?.textContent).toBe("nulog");
		dispatch(OPS.read, null, "r2");
		expect(sent).toEqual([expect.objectContaining({ op: OPS.read, payload: "nulog", id: "r2" })]);
	});

	it("fills a Row's free width", () => {
		expect(registry.SelectRef.fill).toBe(true);
	});
});
