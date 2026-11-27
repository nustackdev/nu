// Touch mode on the content components: key hints draw nothing, a stamp has
// no hover title, a json view trades its hover copies for one corner copy,
// and the toast stack moves to the top edge. Outside touch mode each renders
// as it did.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
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

describe("key hints", () => {
	it("draw on desktop", () => {
		render(
			false,
			<>
				<Kbd>K</Kbd>
				<Shortcut keys={["mod", "K"]} />
			</>,
		);
		expect(q("[data-slot=kbd]")).not.toBeNull();
		expect(q("[data-slot=shortcut]")).not.toBeNull();
	});

	it("draw nothing in touch mode", () => {
		render(
			true,
			<>
				<Kbd>K</Kbd>
				<Shortcut keys={["mod", "K"]} />
			</>,
		);
		expect(q("kbd")).toBeNull();
	});
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
