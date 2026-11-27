// Touch mode on the content components: key hints draw as they do on
// desktop, a stamp has no hover title, a json view trades its hover copies
// for one corner copy, and the toast stack moves to the top edge. Outside
// touch mode each renders as it did.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TouchProvider } from "../../lib/touch";
import { JsonView } from "./json-view";
import { Kbd } from "./kbd";
import { RelativeTime } from "./relative-time";
import { Shortcut } from "./shortcut";
import { dismissToast, Toaster, toast } from "./toast";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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
	document.body.innerHTML = "";
});

function render(touch: boolean, el: React.ReactElement) {
	act(() => {
		root.render(<TouchProvider value={touch}>{el}</TouchProvider>);
	});
}

const q = (sel: string) => document.querySelector(sel);

// Showing key hints is the app's call: the kit draws them in both modes.
describe("key hints", () => {
	for (const touch of [false, true]) {
		it(`draw ${touch ? "in touch mode" : "on desktop"}`, () => {
			render(
				touch,
				<>
					<Kbd>K</Kbd>
					<Shortcut keys={["mod", "K"]} />
				</>,
			);
			expect(q("[data-slot=kbd]")).not.toBeNull();
			expect(q("[data-slot=shortcut]")).not.toBeNull();
		});
	}
});

describe("RelativeTime", () => {
	it("has the absolute time as a hover title on desktop", () => {
		render(false, <RelativeTime ts={Date.now() - 60_000} />);
		expect(q("time")?.getAttribute("title")).toBeTruthy();
	});

	it("has no title in touch mode, unless the caller gives one", () => {
		render(true, <RelativeTime ts={Date.now() - 60_000} />);
		expect(q("time")?.hasAttribute("title")).toBe(false);
		render(true, <RelativeTime ts={Date.now() - 60_000} title="given" />);
		expect(q("time")?.getAttribute("title")).toBe("given");
	});
});

describe("JsonView", () => {
	it("has no corner copy on desktop", () => {
		render(false, <JsonView value={{ a: 1 }} />);
		expect(q("[aria-label='Copy JSON']")).toBeNull();
	});

	it("has one corner copy in touch mode", () => {
		render(true, <JsonView value={{ a: 1 }} />);
		expect(document.querySelectorAll("[aria-label='Copy JSON']")).toHaveLength(1);
	});

	it("leaves it out when the host copies, or when collapsed shut", () => {
		render(true, <JsonView value={{ a: 1 }} copyAll={false} />);
		expect(q("[aria-label='Copy JSON']")).toBeNull();
		render(true, <JsonView value={{ a: 1 }} collapseAll />);
		expect(q("[aria-label='Copy JSON']")).toBeNull();
	});

	it("routes a hovered row's copy through copyText on desktop", async () => {
		const writeText = vi.fn(() => Promise.resolve());
		Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
		Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
		try {
			render(false, <JsonView value={{ a: "x" }} />);
			// The last line is the leaf, `a`; the first is the whole object.
			const lines = document.querySelectorAll<HTMLElement>(".w-rjv-line");
			const line = lines[lines.length - 1];
			act(() => {
				line.dispatchEvent(new MouseEvent("mouseover", { bubbles: true }));
			});
			const icon = line.querySelector(".w-rjv-copied") as SVGElement;
			await act(async () => {
				icon.dispatchEvent(new MouseEvent("click", { bubbles: true }));
			});
			expect(writeText).toHaveBeenCalledWith('"x"');
			expect(line.querySelector(".w-rjv-copied.lucide-check")).not.toBeNull();
		} finally {
			delete (navigator as { clipboard?: unknown }).clipboard;
			delete (window as { isSecureContext?: unknown }).isSecureContext;
		}
	});

	// The corner copy goes through copyText: "Copied" on success only.
	for (const ok of [true, false]) {
		it(`shows copied ${ok ? "when the text got there" : "never when it did not"}`, async () => {
			const writeText = vi.fn(() => (ok ? Promise.resolve() : Promise.reject(new Error("no"))));
			Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
			Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
			try {
				render(true, <JsonView value={{ a: 1 }} />);
				await act(async () => {
					(q("[aria-label='Copy JSON']") as HTMLButtonElement).click();
				});
				expect(writeText).toHaveBeenCalledWith(JSON.stringify({ a: 1 }, null, 2));
				expect(q("[aria-label='Copied']") !== null).toBe(ok);
			} finally {
				delete (navigator as { clipboard?: unknown }).clipboard;
				delete (window as { isSecureContext?: unknown }).isSecureContext;
			}
		});
	}
});

describe("Toaster", () => {
	let id = 0;
	afterEach(() => {
		act(() => dismissToast(id));
	});

	it("stacks bottom right on desktop", () => {
		render(false, <Toaster />);
		act(() => {
			id = toast({ title: "hi" });
		});
		const vp = q("[data-slot=toast-viewport]");
		expect(vp?.className).toContain("bottom-0");
		expect(vp?.className).not.toContain("top-0");
	});

	it("stacks along the top in touch mode, clear of the notch", () => {
		render(true, <Toaster />);
		act(() => {
			id = toast({ title: "hi" });
		});
		const vp = q("[data-slot=toast-viewport]");
		expect(vp?.className).toContain("top-0");
		expect(vp?.className).toContain("safe-area-inset-top");
		expect(q("[data-slot=toast]")?.className).toContain("slide-in-from-top-1");
	});
});
