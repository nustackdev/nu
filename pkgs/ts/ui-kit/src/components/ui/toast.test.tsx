// The toast store: what `toast()` hands back, how long a toast stays by tone,
// how the stack keeps to its limit, and how a closed toast stays drawn until
// its fade out is over. `dismissToast` on an unknown or closed id does nothing.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
	dismissToast,
	TOAST_DANGER_DURATION,
	TOAST_DURATION,
	TOAST_EXIT,
	TOAST_LIMIT,
	type ToastEntry,
	Toaster,
	toast,
	useToasts,
} from "./toast";

// React 19 wants this before render or it logs a warning per test.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let shown: ToastEntry[] = [];

function Probe() {
	shown = useToasts();
	return null;
}

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

beforeEach(() => {
	vi.useFakeTimers();
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	mount(<Probe />);
});

afterEach(() => {
	// The store is module level: empty it so each test starts from nothing.
	act(() => {
		for (const e of shown) dismissToast(e.id);
		vi.runAllTimers();
	});
	act(() => root.unmount());
	host.remove();
	vi.useRealTimers();
});

describe("toast", () => {
	it("returns a fresh id and fills in tone and duration", () => {
		let a = 0;
		let b = 0;
		act(() => {
			a = toast({ title: "Saved" });
			b = toast({ title: "Slow", tone: "warn", duration: 1000 });
		});
		expect(b).toBeGreaterThan(a);
		expect(shown.map((e) => [e.id, e.tone, e.duration, e.description, e.open])).toEqual([
			[a, "neutral", TOAST_DURATION, "", true],
			[b, "warn", 1000, "", true],
		]);
	});

	it("keeps a danger toast longer", () => {
		act(() => {
			toast({ title: "Failed", tone: "danger" });
		});
		expect(shown[0].duration).toBe(TOAST_DANGER_DURATION);
	});

	it("closes the oldest past the limit and drops it once it has faded", () => {
		const ids: number[] = [];
		act(() => {
			for (let i = 0; i < TOAST_LIMIT + 2; i++) ids.push(toast({ title: `t${i}` }));
		});
		expect(shown.filter((e) => e.open).map((e) => e.id)).toEqual(ids.slice(2));
		expect(shown.filter((e) => !e.open).map((e) => e.id)).toEqual(ids.slice(0, 2));
		act(() => {
			vi.advanceTimersByTime(TOAST_EXIT);
		});
		expect(shown.map((e) => e.id)).toEqual(ids.slice(2));
	});
});

describe("dismissToast", () => {
	it("closes a toast, which stays drawn until its fade out ends", () => {
		let id = 0;
		act(() => {
			id = toast({ title: "Copied" });
		});
		act(() => dismissToast(id));
		expect(shown).toEqual([expect.objectContaining({ id, open: false })]);
		act(() => {
			vi.advanceTimersByTime(TOAST_EXIT - 1);
		});
		expect(shown).toHaveLength(1);
		act(() => {
			vi.advanceTimersByTime(1);
		});
		expect(shown).toEqual([]);
	});

	it("does nothing for an unknown id or one already closed", () => {
		let id = 0;
		act(() => {
			id = toast({ title: "Once" });
		});
		const before = shown;
		act(() => dismissToast(id + 100));
		expect(shown).toBe(before);
		act(() => dismissToast(id));
		const closed = shown;
		act(() => dismissToast(id));
		expect(shown).toBe(closed);
	});

	it("does not let a later toast cut a closing one short", () => {
		let id = 0;
		act(() => {
			id = toast({ title: "First" });
		});
		act(() => dismissToast(id));
		act(() => {
			toast({ title: "Second" });
		});
		expect(shown.map((e) => [e.id === id, e.open])).toEqual([
			[true, false],
			[false, true],
		]);
	});
});

describe("Toaster", () => {
	it("draws each toast's title and description", () => {
		mount(
			<>
				<Probe />
				<Toaster />
			</>,
		);
		act(() => {
			toast({ title: "Plane removed", description: "It is in the trash" });
		});
		expect(document.body.textContent).toContain("Plane removed");
		expect(document.body.textContent).toContain("It is in the trash");
	});
});
