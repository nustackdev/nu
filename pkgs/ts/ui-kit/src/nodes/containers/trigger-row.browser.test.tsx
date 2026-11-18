// A header row on a disclosure, driven in a real browser.
//
// disclosure.test.tsx pins the wiring in jsdom, which does not turn a key on
// a button into its click. This runs in Firefox: real clicks on the row's
// text and on a button in it, Tab then Enter and Space on the trigger. The
// browser project runs without the Tailwind build, so looks (ring, hover,
// truncation) are for the stories, not for here.

import { userEvent } from "@vitest/browser/context";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	tree.getState().setSender(() => {});
});

afterEach(async () => {
	await act(async () => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

const NAME = "run_tests tests/nustd/ui";

function mount(seg: string, type: string, props: Record<string, unknown>, key: string) {
	const row: [string, string, Record<string, unknown>] = [
		key,
		"Row",
		{ gap: 2, grow: { name: 1 } },
	];
	act(() => {
		const s = tree.getState();
		s.write([[seg, type, props]]);
		s.write([[seg, type], row, ["name", "TextRef", { value: NAME, lines: 1 }]]);
		s.write([[seg, type], row, ["go", "ButtonRef", { label: "Stop" }]]);
	});
	act(() => root.render(<NodeView path={[seg]} />));
}

const trigger = () => host.querySelector("[data-row-trigger]") as HTMLButtonElement;
const name = () =>
	[...host.querySelectorAll("[data-slot=trigger-row-header] *")].find(
		(el) => el.children.length === 0 && el.textContent === NAME,
	) as HTMLElement;
const button = () => host.querySelector("[data-slot=trigger-row-header] button") as HTMLElement;
const expanded = () => trigger().getAttribute("aria-expanded");

describe.each([
	["Collapsible", { open: false }, "header"],
	["Accordion", { sections: [{ id: "s", label: "S" }], open: [] }, "header:s"],
])("%s header row in a real browser", (type, props, key) => {
	it("toggles on a click on the text, not on the button", async () => {
		mount("d", type, props, key);
		await userEvent.click(button());
		expect(expanded()).toBe("false");
		await userEvent.click(name());
		await expect.poll(expanded).toBe("true");
	});

	it("toggles from Enter and Space on the focused trigger", async () => {
		mount("d", type, props, key);
		await userEvent.tab();
		expect(document.activeElement).toBe(trigger());
		await userEvent.keyboard("{Enter}");
		await expect.poll(expanded).toBe("true");
		await userEvent.keyboard(" ");
		await expect.poll(expanded).toBe("false");
	});
});
