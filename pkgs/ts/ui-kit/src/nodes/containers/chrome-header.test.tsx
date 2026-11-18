// The header part on chrome containers over the real tree store: a child at
// segment "header" draws in place of the string title (Card, PageSection,
// Modal, Sheet, Popover), the actions and close button stay, the dialogs are
// named by it, a grown one-line text in the header Row may shrink, and a
// Popover's "trigger" child draws inside its one button.

import { OPS } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let warned: ReturnType<typeof vi.spyOn>[];

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	warned = [vi.spyOn(console, "error"), vi.spyOn(console, "warn")];
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	for (const spy of warned) spy.mockRestore();
});

type Level = [string, string, Record<string, unknown>];

/** Mount `type` at `seg` with a header Row (an icon-free name and a badge) and a body line. */
function mount(seg: string, type: string, props: Record<string, unknown>, extra: Level[][] = []) {
	const box: Level = [seg, type, props];
	const header: Level = ["header", "Row", { gap: 2 }];
	act(() => {
		tree.getState().write([box]);
		tree.getState().write([box, header, ["name", "TextRef", { value: "web-03", lines: 1 }]]);
		tree.getState().write([box, header, ["state", "BadgeRef", { label: "healthy" }]]);
		tree.getState().write([box, ["note", "TextRef", { value: "inside the body" }]]);
		for (const chain of extra) tree.getState().write([box, ...chain]);
	});
	act(() => root.render(<NodeView path={[seg]} />));
}

const slot = (name: string, from: ParentNode = document) =>
	from.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

/** Nothing said on the console: no a11y warning from the dialog, no bad nesting. */
function quiet() {
	for (const spy of warned) expect(spy.mock.calls).toEqual([]);
}

describe("Card header", () => {
	it("draws the header in place of title and subtitle, the actions kept", () => {
		mount("c", "Card", { title: "Plain", subtitle: "under" }, [
			[["actions", "ButtonRef", { label: "Open" }]],
		]);
		const head = slot("card-header", host) as HTMLElement;
		expect(slot("card-title", head)).toBeNull();
		expect(slot("card-description", head)).toBeNull();
		const part = slot("card-header-part", head);
		expect(part?.textContent).toBe("web-03healthy");
		expect(cls(part)).toContain("min-w-0");
		expect(slot("button", slot("card-action", head) as HTMLElement)?.textContent).toBe("Open");
		expect(slot("card-content", host)?.textContent).toBe("inside the body");
	});

	it("goes back to the string title when the header child is removed", () => {
		mount("c", "Card", { title: "Plain" });
		act(() => tree.getState().remove(["c", "header"]));
		expect(slot("card-title", host)?.textContent).toBe("Plain");
		expect(slot("card-header-part", host)).toBeNull();
	});

	it("lets a grown one-line text in the header Row shrink, so it can cut", () => {
		mount("c", "Card", {});
		act(() =>
			tree
				.getState()
				.dispatch({ op: OPS.write, ref: ["c", "header"], payload: { grow: { name: 1 } } }),
		);
		const cells = [
			...(slot("card-header-part", host)?.querySelectorAll("[data-slot=row-cell]") ?? []),
		];
		expect(cells.map((c) => cls(c).includes("min-w-0"))).toEqual([true, false]);
	});
});

describe("PageSection header", () => {
	it("draws the header in place of title and description, the actions kept", () => {
		mount("s", "PageSection", { title: "Usage", description: "30 days" }, [
			[["actions", "ButtonRef", { label: "Export" }]],
		]);
		const head = slot("section-header", host) as HTMLElement;
		expect(head.querySelector("h2")).toBeNull();
		expect(head.textContent).not.toContain("30 days");
		const heading = slot("section-heading", head);
		expect(heading?.textContent).toBe("web-03healthy");
		expect(cls(heading)).toEqual(expect.arrayContaining(["min-w-0", "flex-1"]));
		expect(slot("section-actions", head)?.textContent).toBe("Export");
		expect(slot("section-body", host)?.textContent).toBe("inside the body");
	});

	it("draws a header for a header child alone", () => {
		mount("s", "PageSection", {});
		expect(slot("section-heading", host)?.textContent).toBe("web-03healthy");
	});
});

describe("Modal header", () => {
	const dialog = () => document.querySelector("[role=dialog]") as HTMLElement;

	it("draws the header as the dialog's title, the close button kept", () => {
		mount("m", "Modal", { open: true, title: "Plain" });
		expect(slot("dialog-title")).toBeNull();
		const box = slot("dialog-title-box") as HTMLElement;
		expect(box.textContent).toBe("web-03healthy");
		expect(cls(box)).toContain("min-w-0");
		expect(dialog().getAttribute("aria-labelledby")).toBe(box.id);
		expect(slot("dialog-close-icon")).not.toBeNull();
		expect(cls(slot("dialog-header"))).toContain("pr-8");
		expect(slot("modal-body")?.textContent).toBe("inside the body");
		quiet();
	});

	it("names an untitled dialog for screen readers", () => {
		act(() => tree.getState().write([["m", "Modal", { open: true }]]));
		act(() => root.render(<NodeView path={["m"]} />));
		expect(cls(slot("dialog-header"))).toContain("sr-only");
		expect(slot("dialog-title")?.textContent).toBe("Dialog");
		quiet();
	});
});

describe("Sheet header", () => {
	it("draws the header as the sheet's title, the close button kept", () => {
		mount("s", "Sheet", { open: true, title: "Plain" });
		expect(slot("sheet-title")).toBeNull();
		const box = slot("sheet-title-box") as HTMLElement;
		expect(box.textContent).toBe("web-03healthy");
		const dialog = document.querySelector("[role=dialog]") as HTMLElement;
		expect(dialog.getAttribute("aria-labelledby")).toBe(box.id);
		expect(cls(slot("sheet-header"))).not.toContain("sr-only");
		expect(slot("sheet-close-icon")).not.toBeNull();
		expect(slot("sheet-content")?.textContent).toContain("inside the body");
		expect(slot("sheet-content")?.textContent?.match(/web-03/g)).toHaveLength(1);
		quiet();
	});
});

describe("Popover header and trigger", () => {
	const panel = () => document.querySelector("[data-node=popover]") as HTMLElement | null;
	const buttons = () => host.querySelectorAll("button");

	it("draws the header over the panel in place of its title, naming the panel", () => {
		mount("p", "Popover", { icon: "settings-2", title: "Plain", open: false });
		act(() => tree.getState().dispatch({ op: OPS.write, ref: ["p"], payload: { open: true } }));
		const el = panel() as HTMLElement;
		expect(slot("popover-title", el)).toBeNull();
		const head = slot("popover-header", el) as HTMLElement;
		expect(head.textContent).toBe("web-03healthy");
		expect(el.getAttribute("aria-labelledby")).toBe(head.id);
		expect(el.getAttribute("aria-label")).toBeNull();
		expect(el.textContent).toContain("inside the body");
	});

	it("draws the trigger child inside one button, in place of label and icon", () => {
		mount("p", "Popover", { label: "Options", icon: "settings-2", variant: "outline" }, [
			[
				["trigger", "Row", { gap: 2 }],
				["who", "TextRef", { value: "Gor" }],
			],
			[
				["trigger", "Row", { gap: 2 }],
				["plan", "BadgeRef", { label: "pro" }],
			],
		]);
		expect(buttons()).toHaveLength(1);
		const button = buttons()[0];
		expect(button.textContent).toBe("Gorpro");
		expect(button.querySelector("svg")).toBeNull();
		expect(button.getAttribute("aria-label")).toBe("Open");
		expect(button.getAttribute("aria-haspopup")).toBe("dialog");
		// The trigger part never draws in the body.
		act(() => tree.getState().dispatch({ op: OPS.write, ref: ["p"], payload: { open: true } }));
		expect(panel()?.textContent).not.toContain("Gor");
		quiet();
	});

	it("names the trigger by its tooltip, else its title", () => {
		mount("p", "Popover", { tooltip: "Account", title: "Signed in" }, [
			[
				["trigger", "Row", { gap: 2 }],
				["who", "TextRef", { value: "Gor" }],
			],
		]);
		expect(buttons()[0].getAttribute("aria-label")).toBe("Account");
		act(() => tree.getState().dispatch({ op: OPS.write, ref: ["p"], payload: { tooltip: "" } }));
		expect(buttons()[0].getAttribute("aria-label")).toBe("Signed in");
	});
});
