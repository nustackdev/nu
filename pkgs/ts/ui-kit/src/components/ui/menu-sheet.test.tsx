// Menus in touch mode: DropdownMenu and ContextMenu render a bottom sheet of
// rows from the same parts, keep Radix's select semantics (a tap selects and
// closes, preventDefault keeps it open, checkbox and radio report), expand a
// submenu in place and drop shortcut hints. ContextMenu opens on a held
// finger, not on one that moves. The command palette goes full screen with a
// Cancel. Desktop keeps the Radix menus.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TouchProvider } from "../../lib/touch";
import {
	CommandInput,
	CommandItem,
	CommandList,
	CommandPalette,
	CommandShortcut,
} from "./command-palette";
import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuTrigger,
} from "./context-menu";
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuShortcut,
	DropdownMenuSub,
	DropdownMenuSubContent,
	DropdownMenuSubTrigger,
	DropdownMenuTrigger,
} from "./dropdown-menu";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	// Radix's popper and cmdk measure with ResizeObserver, which jsdom lacks.
	vi.stubGlobal(
		"ResizeObserver",
		class {
			observe() {}
			unobserve() {}
			disconnect() {}
		},
	);
	Element.prototype.scrollIntoView ??= () => {};
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	document.body.innerHTML = "";
	vi.unstubAllGlobals();
	vi.useRealTimers();
});

const touch = (node: React.ReactNode) => <TouchProvider value={true}>{node}</TouchProvider>;
const sheet = () => document.querySelector('[data-slot="bottom-sheet-content"]');
const row = (text: string) =>
	[...document.querySelectorAll<HTMLElement>('[data-slot="menu-sheet-item"]')].find(
		(el) => el.textContent?.trim() === text,
	);

describe("DropdownMenu", () => {
	function Menu({
		onEdit,
		onKeep,
		onWrap,
		onDensity,
	}: {
		onEdit?: () => void;
		onKeep?: () => void;
		onWrap?: (v: boolean) => void;
		onDensity?: (v: string) => void;
	}) {
		return (
			<DropdownMenu defaultOpen>
				<DropdownMenuTrigger>open</DropdownMenuTrigger>
				<DropdownMenuContent align="start" className="w-64 p-2">
					<DropdownMenuItem onSelect={onEdit}>
						Edit
						<DropdownMenuShortcut keys={["mod", "E"]} />
					</DropdownMenuItem>
					<DropdownMenuItem
						onSelect={(e) => {
							e.preventDefault();
							onKeep?.();
						}}
					>
						Keep
					</DropdownMenuItem>
					<DropdownMenuCheckboxItem checked={false} onCheckedChange={onWrap}>
						Wrap
					</DropdownMenuCheckboxItem>
					<DropdownMenuRadioGroup value="a" onValueChange={onDensity}>
						<DropdownMenuRadioItem value="a">A</DropdownMenuRadioItem>
						<DropdownMenuRadioItem value="b">B</DropdownMenuRadioItem>
					</DropdownMenuRadioGroup>
					<DropdownMenuSub>
						<DropdownMenuSubTrigger>Share</DropdownMenuSubTrigger>
						<DropdownMenuSubContent>
							<DropdownMenuItem>Copy link</DropdownMenuItem>
						</DropdownMenuSubContent>
					</DropdownMenuSub>
				</DropdownMenuContent>
			</DropdownMenu>
		);
	}

	it("is the anchored Radix menu on desktop", () => {
		act(() => root.render(<Menu />));
		expect(document.querySelector('[data-slot="dropdown-menu-content"]')).not.toBeNull();
		expect(document.querySelector('[data-slot="dropdown-menu-shortcut"]')).not.toBeNull();
		expect(sheet()).toBeNull();
	});

	it("is a sheet of rows in touch mode, with no shortcut hints", () => {
		act(() => root.render(touch(<Menu />)));
		expect(sheet()).not.toBeNull();
		expect(document.querySelector('[data-slot="dropdown-menu-content"]')).toBeNull();
		expect(document.querySelector('[data-slot="dropdown-menu-shortcut"]')).toBeNull();
		const body = sheet()?.querySelector('[data-slot="bottom-sheet-body"]');
		expect(body?.className).toContain("p-2");
		expect(body?.className).not.toContain("w-64");
		expect(row("Edit")).toBeDefined();
	});

	it("selects and closes on a tap, stays open when the handler prevents it", () => {
		const onEdit = vi.fn();
		const onKeep = vi.fn();
		act(() => root.render(touch(<Menu onEdit={onEdit} onKeep={onKeep} />)));
		act(() => row("Keep")?.click());
		expect(onKeep).toHaveBeenCalledOnce();
		expect(sheet()?.getAttribute("data-state")).toBe("open");
		act(() => row("Edit")?.click());
		expect(onEdit).toHaveBeenCalledOnce();
		expect(sheet()?.getAttribute("data-state") ?? "closed").toBe("closed");
	});

	it("reports checkbox and radio rows", () => {
		const onWrap = vi.fn();
		const onDensity = vi.fn();
		act(() => root.render(touch(<Menu onWrap={onWrap} onDensity={onDensity} />)));
		const wrap = row("Wrap");
		expect(wrap?.getAttribute("role")).toBe("checkbox");
		expect(wrap?.getAttribute("aria-checked")).toBe("false");
		act(() => wrap?.click());
		expect(onWrap).toHaveBeenCalledWith(true);

		// The tap closed the sheet: open a fresh one.
		act(() => root.render(touch(<Menu key="again" onWrap={onWrap} onDensity={onDensity} />)));
		expect(row("A")?.getAttribute("aria-checked")).toBe("true");
		act(() => row("B")?.click());
		expect(onDensity).toHaveBeenCalledWith("b");
	});

	it("expands a submenu in place and keeps the sheet open", () => {
		act(() => root.render(touch(<Menu />)));
		expect(row("Copy link")).toBeUndefined();
		const share = row("Share");
		expect(share?.getAttribute("aria-expanded")).toBe("false");
		act(() => share?.click());
		expect(share?.getAttribute("aria-expanded")).toBe("true");
		expect(row("Copy link")).toBeDefined();
		expect(sheet()?.getAttribute("data-state")).toBe("open");
	});
});

describe("ContextMenu", () => {
	const menu = (
		<ContextMenu>
			<ContextMenuTrigger>
				<div data-testid="region">region</div>
			</ContextMenuTrigger>
			<ContextMenuContent>
				<ContextMenuItem>Rename</ContextMenuItem>
			</ContextMenuContent>
		</ContextMenu>
	);
	const region = () => document.querySelector('[data-slot="context-menu-trigger"]') as HTMLElement;
	const pointer = (type: string, x = 10, y = 10) => {
		const e = new MouseEvent(type, {
			bubbles: true,
			cancelable: true,
			clientX: x,
			clientY: y,
			button: 0,
		});
		act(() => {
			region().dispatchEvent(e);
		});
	};

	it("opens a sheet on a held finger", () => {
		vi.useFakeTimers();
		act(() => root.render(touch(menu)));
		pointer("pointerdown");
		act(() => vi.advanceTimersByTime(400));
		expect(sheet()).toBeNull();
		act(() => vi.advanceTimersByTime(200));
		expect(sheet()).not.toBeNull();
		expect(row("Rename")).toBeDefined();
	});

	it("does not open when the finger moves (a scroll) or lifts early", () => {
		vi.useFakeTimers();
		act(() => root.render(touch(menu)));
		pointer("pointerdown");
		pointer("pointermove", 10, 40);
		act(() => vi.advanceTimersByTime(800));
		expect(sheet()).toBeNull();
		pointer("pointerdown");
		pointer("pointerup");
		act(() => vi.advanceTimersByTime(800));
		expect(sheet()).toBeNull();
	});

	it("opens on the platform's own contextmenu event too", () => {
		act(() => root.render(touch(menu)));
		pointer("contextmenu");
		expect(sheet()).not.toBeNull();
	});
});

describe("CommandPalette", () => {
	const palette = (
		<CommandPalette open onOpenChange={() => {}}>
			<CommandInput placeholder="Search" />
			<CommandList>
				<CommandItem>
					Go
					<CommandShortcut keys={["G"]} />
				</CommandItem>
			</CommandList>
		</CommandPalette>
	);
	const content = () => document.querySelector('[data-slot="command-palette-content"]');

	it("is a centered dialog on desktop", () => {
		act(() => root.render(palette));
		expect(content()?.className).toContain("max-w-lg");
		expect(document.querySelector('[data-slot="command-palette-shortcut"]')).not.toBeNull();
		expect(content()?.textContent).not.toContain("Cancel");
	});

	it("is a full screen with a Cancel in touch mode", () => {
		act(() => root.render(touch(palette)));
		expect(content()?.className).toContain("h-dvh");
		expect(content()?.className).not.toContain("max-w-lg");
		expect(document.querySelector('[data-slot="command-palette-shortcut"]')).toBeNull();
		expect(content()?.textContent).toContain("Cancel");
	});
});
