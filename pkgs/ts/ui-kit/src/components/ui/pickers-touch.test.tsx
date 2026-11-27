// The pickers in touch mode: each opens a bottom sheet from the same parts it
// uses on desktop. Select names its pick on the trigger while the sheet is
// shut and picks from a sheet row; Combobox pins its search on top of the
// sheet; Autocomplete types in the sheet and hands Enter back to the field
// in the page; the date pickers put the calendar in a sheet.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TouchProvider } from "../../lib/touch";
import { Autocomplete } from "./autocomplete";
import {
	Combobox,
	ComboboxContent,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "./combobox";
import { DatePicker, DateRangePicker } from "./date-picker";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	// Radix measures with ResizeObserver, cmdk scrolls rows and vaul asks
	// matchMedia on open; jsdom has none of them.
	vi.stubGlobal("matchMedia", () => ({
		matches: false,
		addEventListener() {},
		removeEventListener() {},
	}));
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
});

const touch = (node: React.ReactNode) =>
	act(() => root.render(<TouchProvider value={true}>{node}</TouchProvider>));
const sheet = () => document.querySelector('[data-slot="bottom-sheet-content"]');

function fruits(props: { open?: boolean; onValueChange?: (v: string) => void }) {
	return (
		<Select defaultValue="banana" defaultOpen={props.open} onValueChange={props.onValueChange}>
			<SelectTrigger>
				<SelectValue placeholder="Pick" />
			</SelectTrigger>
			<SelectContent>
				<SelectItem value="apple">Apple</SelectItem>
				<SelectItem value="banana">Banana</SelectItem>
			</SelectContent>
		</Select>
	);
}

describe("Select", () => {
	it("names the pick on the trigger while the sheet is shut", () => {
		touch(fruits({}));
		expect(sheet()).toBeNull();
		const trigger = document.querySelector('[data-slot="select-trigger"]');
		expect(trigger?.textContent).toBe("Banana");
		expect(trigger?.getAttribute("role")).toBe("combobox");
	});

	it("picks from a sheet row and closes", () => {
		const picked = vi.fn();
		touch(fruits({ open: true, onValueChange: picked }));
		const rows = sheet()?.querySelectorAll<HTMLButtonElement>('[data-slot="select-item"]');
		expect(rows?.length).toBe(2);
		expect(rows?.[1].getAttribute("aria-selected")).toBe("true");
		act(() => rows?.[0].click());
		expect(picked).toHaveBeenCalledWith("apple");
		expect(document.querySelector('[data-slot="select-trigger"]')?.textContent).toBe("Apple");
	});

	it("stays the Radix select on desktop", () => {
		act(() => root.render(fruits({})));
		expect(document.querySelector('[data-slot="select-trigger"]')?.textContent).toBe("Banana");
		expect(sheet()).toBeNull();
	});
});

describe("Combobox", () => {
	it("opens a sheet with the search on top and rows under it", () => {
		touch(
			<Combobox defaultOpen value="b">
				<ComboboxTrigger>pick</ComboboxTrigger>
				<ComboboxContent>
					<ComboboxInput placeholder="Search" />
					<ComboboxList>
						<ComboboxItem value="a">A</ComboboxItem>
						<ComboboxItem value="b">B</ComboboxItem>
					</ComboboxList>
				</ComboboxContent>
			</Combobox>,
		);
		const s = sheet();
		expect(s?.querySelector('[data-slot="combobox-input-wrap"]')?.className).toContain("sticky");
		const rows = s?.querySelectorAll('[data-slot="combobox-item"]');
		expect(rows?.length).toBe(2);
		expect(rows?.[0].className).toContain("min-h-11");
		// The keyboard stays down until the search is tapped.
		expect(document.activeElement?.getAttribute("data-slot")).not.toBe("combobox-input");
	});
});

describe("Autocomplete", () => {
	it("types in the sheet and hands Enter to the field in the page", () => {
		const keys = vi.fn();
		const picks = vi.fn();
		function Sample() {
			return (
				<Autocomplete
					aria-label="City"
					value="l"
					onValueChange={() => {}}
					onPick={picks}
					onKeyDown={(e) => keys(e.key, e.currentTarget)}
					options={[
						{ value: "Lisbon", label: "Lisbon" },
						{ value: "Berlin", label: "Berlin" },
					]}
				/>
			);
		}
		touch(<Sample />);
		const field = document.querySelector<HTMLInputElement>('[data-slot="autocomplete"] input');
		expect(field?.inputMode).toBe("none");
		act(() => field?.click());
		const s = sheet();
		expect(s).not.toBeNull();
		const rows = s?.querySelectorAll('[data-slot="autocomplete-item"]');
		expect(rows?.length).toBe(2);
		const inSheet = s?.querySelector<HTMLInputElement>("input");
		act(() => {
			inSheet?.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
		});
		expect(keys).toHaveBeenCalledWith("Enter", field);
		expect(picks).not.toHaveBeenCalled();
	});
});

describe("DatePicker", () => {
	it("puts the calendar in a sheet with 44px days", () => {
		touch(<DatePicker defaultValue={new Date(2026, 10, 12)} />);
		const trigger = document.querySelector<HTMLButtonElement>('[data-slot="date-picker-trigger"]');
		act(() => trigger?.click());
		const s = sheet();
		expect(s?.querySelector('[data-slot="date-picker-content"]')).not.toBeNull();
		expect(
			s?.querySelector("button[name], td button, [role=gridcell] button")?.className,
		).toContain("size-11");
	});

	it("shows one month and a Done button for a range", () => {
		touch(<DateRangePicker />);
		act(() =>
			document.querySelector<HTMLButtonElement>('[data-slot="date-picker-trigger"]')?.click(),
		);
		const s = sheet();
		expect(s?.querySelectorAll("table").length).toBe(1);
		const done = Array.from(s?.querySelectorAll("button") ?? []).find(
			(b) => b.textContent === "Done",
		);
		expect(done).toBeDefined();
	});
});
