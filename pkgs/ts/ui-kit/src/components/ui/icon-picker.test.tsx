// The icon picker, rendered in jsdom: pick, search, keyboard, remove, the
// recent picks under the caller's key, the field around it, and the touch
// sheet with thumb-sized cells and no tooltips.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TouchProvider } from "../../lib/touch";
import { IconMark } from "./icon-mark";
import { IconPicker, IconPickerField, type IconPickerProps } from "./icon-picker";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("unicode-emoji-json/data-by-group.json", () => ({
	default: [
		{
			name: "Animals & Nature",
			slug: "animals_nature",
			emojis: [
				{ emoji: "🐱", name: "cat face", slug: "cat_face", emoji_version: "0.6" },
				{ emoji: "🌱", name: "seedling", slug: "seedling", emoji_version: "0.6" },
			],
		},
	],
}));

let host: HTMLDivElement;
let root: Root;
const onPick = vi.fn();
const onRemove = vi.fn();

/** Let the emoji's dynamic import land inside an act. */
async function settle() {
	await act(async () => {
		await new Promise((r) => setTimeout(r, 0));
	});
}

/** Render, and let the emoji load inside the act so no update lands outside it. */
async function render(props: Partial<IconPickerProps> = {}) {
	await act(async () => {
		root.render(<IconPicker value="" onPick={onPick} onRemove={onRemove} {...props} />);
		await new Promise((r) => setTimeout(r, 0));
	});
}

const cell = (label: string) =>
	document.querySelector<HTMLButtonElement>(`button[aria-label="${label}"]`);
const search = () => {
	const el = document.querySelector<HTMLInputElement>('input[type="search"]');
	if (!el) throw new Error("no search");
	return el;
};
const shown = () =>
	[...document.querySelectorAll("button[data-cell]")].map((b) => b.getAttribute("aria-label"));
const tabs = () => [...document.querySelectorAll('[role="tab"]')].map((t) => t.textContent);
const button = (text: string) =>
	[...document.querySelectorAll("button")].find((b) => b.textContent === text);

/** Set a React-controlled input's value the way typing would. */
function type(text: string) {
	const el = search();
	const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
	act(() => {
		set?.call(el, text);
		el.dispatchEvent(new Event("input", { bubbles: true }));
	});
}

/** Switch to the Icons tab the way a click does: Radix tabs go on mousedown. */
function toIcons() {
	const tab = [...document.querySelectorAll('[role="tab"]')].find((t) => t.textContent === "Icons");
	act(() => {
		tab?.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, button: 0 }));
	});
}

function key(el: Element, k: string) {
	act(() => {
		el.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
	});
}

beforeEach(() => {
	window.localStorage.clear();
	host = document.createElement("div");
	document.body.append(host);
	root = createRoot(host);
	onPick.mockClear();
	onRemove.mockClear();
	// Radix measures with ResizeObserver and vaul asks matchMedia on open;
	// jsdom has neither.
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
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	document.body.innerHTML = "";
	vi.unstubAllGlobals();
});

describe("IconPicker", () => {
	it("opens on the emoji first, loading them, with the caret in the search", async () => {
		act(() => {
			root.render(<IconPicker value="" onPick={onPick} />);
		});
		expect(tabs()).toEqual(["Emoji", "Icons"]);
		expect(document.activeElement).toBe(search());
		expect(host.querySelector('[role="status"]')?.getAttribute("aria-label")).toBe("Loading emoji");
		await settle();
		expect(host.querySelector('[role="status"]')).toBeNull();
		act(() => cell("cat face")?.click());
		expect(onPick).toHaveBeenCalledWith("emoji:🐱");
	});

	it("picks an icon from the icons tab, named by a tooltip on desktop", async () => {
		await render();
		toIcons();
		expect(cell("folder")?.getAttribute("title")).toBe("folder");
		act(() => cell("folder")?.click());
		expect(onPick).toHaveBeenCalledWith("lucide:folder");
	});

	it("filters by name and keyword, and Enter takes the first match", async () => {
		await render();
		toIcons();
		type("stopwatch");
		expect(shown()).toEqual(["timer"]);
		key(search(), "Enter");
		expect(onPick).toHaveBeenCalledWith("lucide:timer");
		type("no such icon");
		expect(host.textContent).toContain("Nothing matches");
	});

	it("moves through the grid with the arrows, by cell and by row", async () => {
		await render();
		toIcons();
		key(search(), "ArrowDown");
		const first = document.activeElement as HTMLElement;
		expect(first.dataset.cell).toBe("0");
		key(first, "ArrowRight");
		expect((document.activeElement as HTMLElement).dataset.cell).toBe("1");
		key(document.activeElement as Element, "ArrowDown");
		expect((document.activeElement as HTMLElement).dataset.cell).toBe("10");
		key(document.activeElement as Element, "ArrowUp");
		key(document.activeElement as Element, "ArrowUp");
		expect(document.activeElement).toBe(search());
	});

	it("opens on the icons for a lucide value, marks it and removes it", async () => {
		await render({ value: "lucide:cpu" });
		expect(cell("cpu")?.getAttribute("aria-pressed")).toBe("true");
		act(() => button("Remove")?.click());
		expect(onRemove).toHaveBeenCalled();
	});

	it("offers no remove with nothing to remove, or no onRemove", async () => {
		await render();
		expect(button("Remove")).toBeUndefined();
		await render({ value: "emoji:🌱", onRemove: undefined });
		expect(button("Remove")).toBeUndefined();
	});

	it("names its own remove button", async () => {
		await render({ value: "emoji:🌱", removeLabel: "Clear" });
		expect(button("Clear")).toBeDefined();
	});

	it("keeps recent picks under the caller's key and leads with them", async () => {
		await render({ value: "emoji:🌱", recentKey: "app.icons" });
		expect(cell("seedling")?.getAttribute("aria-pressed")).toBe("true");
		act(() => cell("cat face")?.click());
		expect(JSON.parse(window.localStorage.getItem("app.icons") ?? "[]")).toEqual(["emoji:🐱"]);
		act(() => root.unmount());
		root = createRoot(host);
		await render({ recentKey: "app.icons" });
		expect(host.querySelector("section")?.getAttribute("aria-label")).toBe("Recent");
	});

	it("keeps no recent picks when the key is null", async () => {
		await render({ recentKey: null });
		act(() => cell("cat face")?.click());
		expect(window.localStorage.length).toBe(0);
	});

	it("offers only the kinds asked for, and a custom pack", async () => {
		await render({
			kinds: ["lucide"],
			pack: [{ label: "Mine", icons: [["rocket", "launch"], ["cpu"]] }],
		});
		expect(tabs()).toEqual([]);
		expect(shown()).toEqual(["rocket", "cpu"]);
		expect(host.querySelector("section")?.getAttribute("aria-label")).toBe("Mine");
	});
});

describe("IconPickerField", () => {
	const trigger = () =>
		document.querySelector<HTMLButtonElement>('[data-slot="icon-picker-trigger"]');

	it("shows the placeholder, then the pick, and closes", async () => {
		const changed = vi.fn();
		act(() => root.render(<IconPickerField onValueChange={changed} aria-label="Icon" />));
		expect(trigger()?.textContent).toBe("No icon");
		act(() => trigger()?.click());
		await settle();
		toIcons();
		act(() => cell("folder")?.click());
		expect(changed).toHaveBeenCalledWith("lucide:folder");
		expect(trigger()?.querySelector('[data-slot="icon-mark"]')?.getAttribute("data-kind")).toBe(
			"lucide",
		);
		expect(document.querySelector('[data-slot="icon-picker"]')).toBeNull();
	});

	it("removes back to empty when clearable", async () => {
		const changed = vi.fn();
		act(() =>
			root.render(
				<IconPickerField defaultValue="emoji:🌱" onValueChange={changed} aria-label="Icon" />,
			),
		);
		act(() => trigger()?.click());
		await settle();
		act(() => button("Remove")?.click());
		expect(changed).toHaveBeenCalledWith("");
		expect(trigger()?.textContent).toBe("No icon");
	});
});

describe("IconMark", () => {
	it("draws a glyph, an emoji, or the fallback, and nothing for junk alone", () => {
		act(() =>
			root.render(
				<>
					<IconMark icon="lucide:folder" />
					<IconMark icon="emoji:🌱" size="lg" label="Seedling" />
					<IconMark icon="nope:x" fallback="emoji:🐱" />
					<IconMark icon="nope:x" />
				</>,
			),
		);
		const marks = [...host.querySelectorAll('[data-slot="icon-mark"]')];
		expect(marks.map((m) => m.getAttribute("data-kind"))).toEqual(["lucide", "emoji", "emoji"]);
		expect(marks[0].getAttribute("aria-hidden")).toBe("true");
		expect(marks[1].getAttribute("role")).toBe("img");
		expect(marks[1].getAttribute("aria-label")).toBe("Seedling");
		expect(marks[1].className).toContain("leading-none");
		expect(marks[2].textContent).toBe("🐱");
	});
});

describe("IconPicker on touch", () => {
	const touch = (node: React.ReactNode) =>
		act(() => root.render(<TouchProvider value={true}>{node}</TouchProvider>));
	const sheet = () => document.querySelector('[data-slot="bottom-sheet-content"]');

	it("opens the field's picker in a bottom sheet", async () => {
		touch(<IconPickerField defaultValue="lucide:cpu" aria-label="Icon" />);
		act(() =>
			document.querySelector<HTMLButtonElement>('[data-slot="icon-picker-trigger"]')?.click(),
		);
		await settle();
		expect(sheet()?.querySelector('[data-slot="icon-picker"]')).not.toBeNull();
		expect(cell("cpu")?.getAttribute("aria-pressed")).toBe("true");
	});

	it("sizes cells for the thumb, drops tooltips and leaves the caret alone", async () => {
		await act(async () => {
			root.render(
				<TouchProvider value={true}>
					<IconPicker value="" onPick={onPick} kinds={["lucide"]} />
				</TouchProvider>,
			);
			await new Promise((r) => setTimeout(r, 0));
		});
		const first = cell("file text");
		expect(first?.className).toContain("h-11");
		expect(first?.hasAttribute("title")).toBe(false);
		expect(document.activeElement).not.toBe(search());
		// Before the sheet is measured, seven columns a row.
		const row = first?.parentElement;
		expect(row?.style.gridTemplateColumns).toBe("repeat(7, minmax(0, 1fr))");
		expect(row?.children).toHaveLength(7);
		act(() => first?.click());
		expect(onPick).toHaveBeenCalledWith("lucide:file-text");
	});
});
