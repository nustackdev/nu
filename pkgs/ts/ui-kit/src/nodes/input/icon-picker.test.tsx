// IconPickerRef over the real tree store: a pick sends one named change and
// closes the picker, "Remove" clears with one, writes are read as a stored
// icon (junk keeps the icon it had), a read and a Form see the value, a reset
// puts the seed back, and `kinds` picks the tabs.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushOutbox, NodeView, tree, unbatch } from "../../tree";
import "..";
import { toIcon, toKinds } from "./icon-picker";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("unicode-emoji-json/data-by-group.json", () => ({
	default: [
		{
			name: "Animals & Nature",
			slug: "animals_nature",
			emojis: [{ emoji: "🐱", name: "cat face", slug: "cat_face", emoji_version: "0.6" }],
		},
	],
}));

// Radix measures its controls; jsdom has no ResizeObserver.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	window.localStorage.clear();
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	flushOutbox();
	act(() => root.unmount());
	host.remove();
	document.body.innerHTML = "";
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

type Level = [string, string | null, Record<string, unknown>?];

function put(...chain: Level[]) {
	tree.getState().write(chain.map(([seg, type, props]) => [seg, type, props ?? {}]));
}

async function draw(path: string[]) {
	await act(async () => {
		root.render(<NodeView path={path} />);
		await new Promise((r) => setTimeout(r, 0));
	});
}

function dispatch(path: string[], op: string, payload: unknown = null, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: path, payload, id }));
}

const notifies = () =>
	unbatch(sent)
		.filter((f) => f.op === OPS.notify)
		.map((f) => ({ ref: f.ref, payload: f.payload }));
const propsAt = (path: string[]) => tree.getState().getIn(path)?.props ?? {};
const trigger = () => host.querySelector("[data-slot=icon-picker-trigger]") as HTMLButtonElement;
const picker = () => document.querySelector("[data-slot=icon-picker]");
const tabs = () => [...document.querySelectorAll('[role="tab"]')].map((t) => t.textContent);
const cell = (label: string) =>
	document.querySelector<HTMLButtonElement>(`button[aria-label="${label}"]`);

async function open() {
	await act(async () => {
		trigger().click();
		await new Promise((r) => setTimeout(r, 0));
	});
}

describe("IconPickerRef", () => {
	it("shows the icon on a labelled trigger", async () => {
		put(["n", "IconPickerRef", { value: "emoji:🐱", label: "Icon" }]);
		await draw(["n"]);
		expect(trigger().textContent).toBe("🐱");
		const names = (trigger().getAttribute("aria-labelledby") ?? "").split(" ");
		expect(document.getElementById(names[0])?.textContent).toBe("Icon");
	});

	it("shows the placeholder with no icon", async () => {
		put(["n", "IconPickerRef", { value: "", placeholder: "Pick one" }]);
		await draw(["n"]);
		expect(trigger().textContent).toBe("Pick one");
	});

	it("sends one change on a pick, and closes", async () => {
		put(["n", "IconPickerRef", { value: "" }]);
		await draw(["n"]);
		await open();
		act(() => cell("cat face")?.click());
		expect(propsAt(["n"]).value).toBe("emoji:🐱");
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "change", value: "emoji:🐱" } }]);
		expect(picker()).toBeNull();
	});

	it("clears with one change on Remove, and offers none when not clearable", async () => {
		put(["n", "IconPickerRef", { value: "lucide:cpu" }]);
		await draw(["n"]);
		await open();
		const remove = [...document.querySelectorAll("button")].find((b) => b.textContent === "Remove");
		act(() => remove?.click());
		expect(propsAt(["n"]).value).toBe("");
		expect(notifies()).toEqual([{ ref: ["n"], payload: { event: "change", value: "" } }]);

		dispatch(["n"], OPS.write, { value: "lucide:cpu", clearable: false });
		await open();
		expect([...document.querySelectorAll("button")].some((b) => b.textContent === "Remove")).toBe(
			false,
		);
	});

	it("offers the kinds asked for", async () => {
		put(["n", "IconPickerRef", { value: "", kinds: ["lucide"] }]);
		await draw(["n"]);
		await open();
		expect(tabs()).toEqual([]);
		expect(cell("folder")).not.toBeNull();
	});

	it("reads writes as a stored icon, keeps it on junk, merges a map, answers a read, resets", async () => {
		put(["f", "Form", {}], ["icon", "IconPickerRef", { value: "lucide:folder" }]);
		await draw(["f"]);
		dispatch(["f", "icon"], OPS.write, "FileText");
		expect(propsAt(["f", "icon"]).value).toBe("lucide:file-text");
		dispatch(["f", "icon"], OPS.write, "mdi:home");
		expect(propsAt(["f", "icon"]).value).toBe("lucide:file-text");
		dispatch(["f", "icon"], OPS.write, { value: "emoji:🌱", label: "Icon" });
		expect(propsAt(["f", "icon"])).toMatchObject({ value: "emoji:🌱", label: "Icon" });
		dispatch(["f"], OPS.read, null, "v");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, payload: { icon: "emoji:🌱" }, id: "v" });
		dispatch(["f", "icon"], OPS.write, null);
		expect(propsAt(["f", "icon"]).value).toBe("");
		dispatch(["f", "icon"], "reset");
		expect(propsAt(["f", "icon"]).value).toBe("lucide:folder");
		expect(notifies()).toEqual([]);
	});

	it("is a disabled trigger when disabled or readonly", async () => {
		put(["n", "IconPickerRef", { value: "", readonly: true }]);
		await draw(["n"]);
		expect(trigger().disabled).toBe(true);
	});
});

describe("IconPickerRef coercion", () => {
	it("folds a write", () => {
		expect(toIcon("folder")).toBe("lucide:folder");
		expect(toIcon("", "lucide:folder")).toBe("");
		expect(toIcon(7, "emoji:🐱")).toBe("emoji:🐱");
		expect(toIcon("nope:x")).toBe("");
	});

	it("keeps known kinds, once each, both when none survive", () => {
		expect(toKinds(["lucide", "emoji", "lucide"])).toEqual(["lucide", "emoji"]);
		expect(toKinds(["glyphs"])).toEqual(["emoji", "lucide"]);
		expect(toKinds([])).toEqual(["emoji", "lucide"]);
	});
});
