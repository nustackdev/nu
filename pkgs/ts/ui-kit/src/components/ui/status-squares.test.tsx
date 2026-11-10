// StatusSquares: the cap is honest and problems sort first.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { formatCount } from "../../lib/count";
import { StatusSquares, squaresFor } from "./status-squares";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

function mount(el: React.ReactElement) {
	act(() => {
		root.render(el);
	});
}

const tones = () =>
	[...host.querySelectorAll("[data-tone]")].map((el) => el.getAttribute("data-tone"));

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
});

describe("squaresFor", () => {
	it("fills problems first, so the cap never hides one", () => {
		expect(squaresFor({ ok: 100, empty: 3, danger: 2, info: 1 }, 4)).toEqual([
			"danger",
			"danger",
			"info",
			"ok",
		]);
	});

	it("ignores bad counts", () => {
		expect(squaresFor({ ok: -1, danger: Number.NaN, warn: 1.7 }, 10)).toEqual(["warn"]);
	});
});

describe("StatusSquares", () => {
	it("draws every item under the cap, with no ellipsis or count", () => {
		mount(<StatusSquares counts={{ ok: 3, danger: 1 }} />);
		expect(tones()).toEqual(["danger", "ok", "ok", "ok"]);
		expect(host.querySelector("[data-slot=status-squares-more]")).toBeNull();
		expect(host.querySelector("[data-slot=status-squares-total]")).toBeNull();
	});

	it("caps, then shows the ellipsis and the full count", () => {
		mount(<StatusSquares counts={{ ok: 994, danger: 3, info: 3 }} />);
		expect(tones()).toHaveLength(10);
		expect(tones().slice(0, 3)).toEqual(["danger", "danger", "danger"]);
		expect(host.querySelector("[data-slot=status-squares-more]")).not.toBeNull();
		expect(host.querySelector("[data-slot=status-squares-total]")?.textContent).toBe("1,000");
	});

	it("names every tone's count in its label", () => {
		mount(<StatusSquares counts={{ ok: 12, danger: 1 }} labels={{ danger: "failed" }} />);
		const el = host.querySelector("[data-slot=status-squares]");
		expect(el?.getAttribute("role")).toBe("img");
		expect(el?.getAttribute("aria-label")).toBe("1 failed, 12 ok");
	});

	it("keeps the count when told to and hides it when told not to", () => {
		mount(<StatusSquares counts={{ ok: 2 }} total="always" />);
		expect(host.querySelector("[data-slot=status-squares-total]")?.textContent).toBe("2");
		mount(<StatusSquares counts={{ ok: 20 }} total="never" />);
		expect(host.querySelector("[data-slot=status-squares-total]")).toBeNull();
		expect(host.querySelector("[data-slot=status-squares-more]")).not.toBeNull();
	});
});

describe("formatCount", () => {
	it("goes compact past 9,999", () => {
		expect(formatCount(9_999)).toBe("9,999");
		expect(formatCount(12_431)).toBe("12.4K");
	});
});
