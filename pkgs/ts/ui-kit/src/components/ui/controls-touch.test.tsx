// The form controls in touch mode: every small control opts into the tap
// area, FileInput asks for a tap and not a drop, and InlineEditRef's pencil
// shows without a hover. Outside touch mode each renders as before.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { TouchProvider } from "../../lib/touch";
import { NodeView, tree } from "../../tree";
import "../../nodes";
import { Checkbox } from "./checkbox";
import { FileInput } from "./file-input";
import { NumberInput } from "./number-input";
import { RadioGroup, RadioGroupItem } from "./radio-group";
import { SegmentedControl, SegmentedControlItem } from "./segmented-control";
import { Slider } from "./slider";
import { Switch } from "./switch";
import { Toggle } from "./toggle";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures its controls; jsdom does not.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

const draw = (node: React.ReactNode, touch: boolean) =>
	act(() => root.render(<TouchProvider value={touch}>{node}</TouchProvider>));

const tapped = (slot: string) =>
	Array.from(host.querySelectorAll(`[data-slot="${slot}"]`)).every((el) =>
		el.classList.contains("nu-tap"),
	);

describe("tap areas", () => {
	it("every small control opts in", () => {
		draw(
			<>
				<Checkbox aria-label="c" />
				<Switch aria-label="s" />
				<Toggle aria-label="t">T</Toggle>
				<RadioGroup aria-label="r">
					<RadioGroupItem value="a" aria-label="a" />
				</RadioGroup>
				<SegmentedControl aria-label="seg">
					<SegmentedControlItem value="a">A</SegmentedControlItem>
				</SegmentedControl>
				<Slider defaultValue={[10, 20]} />
			</>,
			true,
		);
		for (const slot of [
			"checkbox",
			"switch",
			"toggle",
			"radio-group-item",
			"segmented-control-item",
			"slider-thumb",
		]) {
			expect(host.querySelector(`[data-slot="${slot}"]`), slot).not.toBeNull();
			expect(tapped(slot), slot).toBe(true);
		}
	});

	it("number input steppers opt in", () => {
		draw(<NumberInput aria-label="n" value={1} />, true);
		const steppers = host.querySelectorAll(
			'button[aria-label="Decrement"], button[aria-label="Increment"]',
		);
		expect(steppers).toHaveLength(2);
		for (const b of steppers) expect(b.classList.contains("nu-tap")).toBe(true);
	});
});

describe("FileInput", () => {
	it("asks for a tap in touch mode", () => {
		draw(<FileInput onFiles={() => {}} />, true);
		expect(host.textContent).toContain("Tap to choose a file");
		draw(<FileInput multiple onFiles={() => {}} />, true);
		expect(host.textContent).toContain("Tap to choose files");
	});

	it("asks for a drop or a click on desktop", () => {
		draw(<FileInput onFiles={() => {}} />, false);
		expect(host.textContent).toContain("Drop a file or click to choose");
	});

	it("keeps the caller's prompt in touch mode", () => {
		draw(<FileInput prompt="Add a poster" onFiles={() => {}} />, true);
		expect(host.textContent).toContain("Add a poster");
	});
});

describe("InlineEditRef", () => {
	const pencil = () => host.querySelector('[data-slot="inline-edit-ref"] button svg');

	it("shows the pencil without a hover in touch mode", () => {
		tree.getState().write([["n", "InlineEditRef", { value: "Notes" }]]);
		draw(<NodeView path={["n"]} />, true);
		expect(pencil()?.classList.contains("opacity-100")).toBe(true);
		expect(pencil()?.classList.contains("opacity-0")).toBe(false);
	});

	it("reveals the pencil on hover on desktop", () => {
		tree.getState().write([["n", "InlineEditRef", { value: "Notes" }]]);
		draw(<NodeView path={["n"]} />, false);
		expect(pencil()?.classList.contains("opacity-0")).toBe(true);
		expect(pencil()?.classList.contains("group-hover:opacity-100")).toBe(true);
	});
});
