// Touch mode for the overlays group: a dialog is a bottom sheet from the same
// parts (and a `sheet={false}` one stays a dialog), a side sheet takes the
// whole width, and tooltips, an IconButton's `tip` and OverflowTooltip never
// open. Each next to its desktop shape, which must not change.

import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TouchProvider } from "../../lib/touch";
import {
	Dialog,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "./dialog";
import { IconButton } from "./icon-button";
import { OverflowTooltip } from "./overflow-tooltip";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { Sheet, SheetContent, SheetTitle } from "./sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	// Radix's popper measures with ResizeObserver, which jsdom lacks.
	vi.stubGlobal(
		"ResizeObserver",
		class {
			observe() {}
			unobserve() {}
			disconnect() {}
		},
	);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	document.body.innerHTML = "";
	vi.unstubAllGlobals();
});

const touch = (node: ReactNode) => <TouchProvider value={true}>{node}</TouchProvider>;
const q = (sel: string) => document.querySelector(sel);

describe("Dialog", () => {
	const dialog = (sheet?: boolean) => (
		<Dialog defaultOpen sheet={sheet}>
			<DialogContent width={420} className="p-2">
				<DialogHeader>
					<DialogTitle>Delete project</DialogTitle>
					<DialogDescription>Cannot be undone.</DialogDescription>
				</DialogHeader>
				<DialogFooter>
					<DialogClose>Cancel</DialogClose>
					<DialogClose>Delete</DialogClose>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);

	it("is a centered dialog on desktop", () => {
		act(() => root.render(dialog()));
		const content = q('[data-slot="dialog-content"]') as HTMLElement;
		expect(content).not.toBeNull();
		expect(content.style.maxWidth).toBe("420px");
		expect(q('[data-slot="dialog-close-icon"]')).not.toBeNull();
		expect(q('[data-slot="bottom-sheet-content"]')).toBeNull();
	});

	it("is a bottom sheet in touch mode, from the same parts", () => {
		act(() => root.render(touch(dialog())));
		const sheet = q('[data-slot="bottom-sheet-content"]') as HTMLElement;
		expect(sheet).not.toBeNull();
		expect(sheet.style.maxWidth).toBe("");
		expect(q('[data-slot="dialog-content"]')).toBeNull();
		// No corner close: the sheet drags down.
		expect(q('[data-slot="dialog-close-icon"]')).toBeNull();
		// Named by its title, the caller's classes on the body.
		const title = q('[data-slot="dialog-title"]');
		expect(title?.textContent).toBe("Delete project");
		expect(sheet.getAttribute("aria-labelledby")).toBe(title?.id);
		const body = sheet.querySelector('[data-slot="bottom-sheet-body"]');
		expect(body?.className).toContain("p-2");
		// Actions stacked full width, the main one (last) first.
		const footer = q('[data-slot="dialog-footer"]');
		expect(footer?.className).toContain("flex-col-reverse");
		expect(footer?.className).not.toContain("sm:flex-row");
	});

	it("stays a dialog in touch mode with sheet={false}", () => {
		act(() => root.render(touch(dialog(false))));
		expect(q('[data-slot="dialog-content"]')).not.toBeNull();
		expect(q('[data-slot="bottom-sheet-content"]')).toBeNull();
	});
});

describe("Sheet", () => {
	const sheet = (
		<Sheet defaultOpen>
			<SheetContent side="right" width={320}>
				<SheetTitle>Edit host</SheetTitle>
			</SheetContent>
		</Sheet>
	);

	it("is a 320px drawer on desktop", () => {
		act(() => root.render(sheet));
		const content = q('[data-slot="sheet-content"]') as HTMLElement;
		expect(content.style.width).toBe("320px");
		expect(content.className).not.toContain("w-full");
	});

	it("takes the whole width in touch mode", () => {
		act(() => root.render(touch(sheet)));
		const content = q('[data-slot="sheet-content"]') as HTMLElement;
		expect(content.style.width).toBe("");
		expect(content.className).toContain("w-full");
		expect(content.className).toContain("safe-area-inset-top");
	});
});

describe("Popover", () => {
	it("keeps a style width off the sheet in touch mode", () => {
		act(() =>
			root.render(
				touch(
					<Popover defaultOpen>
						<PopoverTrigger>open</PopoverTrigger>
						<PopoverContent style={{ width: 260, height: 200 }}>body</PopoverContent>
					</Popover>,
				),
			),
		);
		const sheet = q('[data-slot="bottom-sheet-content"]') as HTMLElement;
		expect(sheet.style.width).toBe("");
		expect(sheet.style.height).toBe("200px");
	});
});

describe("Tooltips", () => {
	const tip = (
		<TooltipProvider>
			<Tooltip defaultOpen>
				<TooltipTrigger>hover me</TooltipTrigger>
				<TooltipContent>the hint</TooltipContent>
			</Tooltip>
		</TooltipProvider>
	);

	it("opens on desktop", () => {
		act(() => root.render(tip));
		expect(q('[data-slot="tooltip-content"]')).not.toBeNull();
	});

	it("never opens in touch mode, the trigger kept", () => {
		act(() => root.render(touch(tip)));
		expect(q('[data-slot="tooltip-content"]')).toBeNull();
		expect(q('[data-slot="tooltip-trigger"]')?.textContent).toBe("hover me");
	});

	it("drops an IconButton's tip in touch mode", () => {
		const button = (
			<TooltipProvider>
				<IconButton aria-label="Copy" tip="Copy">
					x
				</IconButton>
			</TooltipProvider>
		);
		act(() => root.render(button));
		expect(q('[data-slot="icon-button"]')?.getAttribute("data-slot")).toBe("icon-button");
		expect(q('[data-slot="icon-button"]')?.hasAttribute("data-state")).toBe(true);
		act(() => root.render(touch(button)));
		const bare = q('[data-slot="icon-button"]');
		expect(bare?.hasAttribute("data-state")).toBe(false);
		expect(bare?.getAttribute("aria-label")).toBe("Copy");
	});

	it("renders OverflowTooltip's trigger bare in touch mode", () => {
		const cut = (
			<TooltipProvider>
				<OverflowTooltip label="a long name">
					<span data-testid="name">a long name</span>
				</OverflowTooltip>
			</TooltipProvider>
		);
		act(() => root.render(cut));
		expect(q('[data-testid="name"]')?.hasAttribute("data-state")).toBe(true);
		act(() => root.render(touch(cut)));
		expect(q('[data-testid="name"]')?.hasAttribute("data-state")).toBe(false);
	});
});
