// RelativeTime: compact text, exact turnover, one shared timer.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
	formatRelativeTime,
	nextChange,
	pendingWakes,
	RelativeTime,
	wakeAt,
} from "./relative-time";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const S = 1_000;
const M = 60 * S;
const H = 60 * M;
const D = 24 * H;

describe("formatRelativeTime", () => {
	it("words ago across magnitudes", () => {
		expect(formatRelativeTime(-3 * S)).toBe("just now");
		expect(formatRelativeTime(2 * S)).toBe("just now");
		expect(formatRelativeTime(42 * S)).toBe("42s ago");
		expect(formatRelativeTime(4 * M + 59 * S)).toBe("4m ago");
		expect(formatRelativeTime(3 * H)).toBe("3h ago");
		expect(formatRelativeTime(3 * D)).toBe("3d ago");
		expect(formatRelativeTime(65 * D)).toBe("2mo ago");
		expect(formatRelativeTime(800 * D)).toBe("2y ago");
	});

	it("words a duration in two units", () => {
		expect(formatRelativeTime(12 * S, "duration")).toBe("12s");
		expect(formatRelativeTime(3 * M + 12 * S, "duration")).toBe("3m 12s");
		expect(formatRelativeTime(2 * H + 4 * M + 30 * S, "duration")).toBe("2h 4m");
		expect(formatRelativeTime(3 * D + 4 * H, "duration")).toBe("3d 4h");
	});
});

describe("nextChange", () => {
	it("lands on the boundary where the text turns over", () => {
		expect(nextChange(1 * S)).toBe(5 * S);
		expect(nextChange(42_300)).toBe(43 * S);
		expect(nextChange(4 * M + 10 * S)).toBe(5 * M);
		expect(nextChange(3 * H + 1)).toBe(4 * H);
		expect(nextChange(3 * M + 12_500, "duration")).toBe(3 * M + 13 * S);
		expect(nextChange(2 * H + 4 * M + 30 * S, "duration")).toBe(2 * H + 5 * M);
		expect(nextChange(3 * D + 10 * M, "duration")).toBe(3 * D + H);
	});

	it("agrees with formatRelativeTime: same text before, new text at", () => {
		for (const mode of ["ago", "duration"] as const) {
			for (const e of [0, 999, 4_999, 59_999, 61_000, H - 1, H + 5, D - 1, 40 * D]) {
				const at = nextChange(e, mode);
				expect(formatRelativeTime(at - 1, mode)).toBe(formatRelativeTime(e, mode));
				expect(formatRelativeTime(at, mode)).not.toBe(formatRelativeTime(e, mode));
			}
		}
	});
});

describe("shared clock", () => {
	let host: HTMLDivElement;
	let root: Root;
	const T0 = Date.UTC(2026, 10, 10, 12, 0, 0);

	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(T0);
		host = document.createElement("div");
		document.body.appendChild(host);
		root = createRoot(host);
	});

	afterEach(() => {
		act(() => root.unmount());
		host.remove();
		vi.useRealTimers();
	});

	const texts = () => [...host.querySelectorAll("time")].map((el) => el.textContent);

	it("holds one timer for many instances", () => {
		act(() => {
			root.render(
				<div>
					{Array.from({ length: 50 }, (_, i) => (
						// biome-ignore lint/suspicious/noArrayIndexKey: a fixed list, never reordered
						<RelativeTime key={i} ts={T0 - i * M} />
					))}
				</div>,
			);
		});
		expect(pendingWakes()).toBe(50);
		expect(vi.getTimerCount()).toBe(1);
	});

	it("ticks live and stops when unmounted", () => {
		act(() => {
			root.render(
				<>
					<RelativeTime ts={T0 - 50 * S} />
					<RelativeTime ts={T0 - 3 * M - 12 * S} mode="duration" />
				</>,
			);
		});
		expect(texts()).toEqual(["50s ago", "3m 12s"]);
		act(() => vi.advanceTimersByTime(10 * S));
		expect(texts()).toEqual(["1m ago", "3m 22s"]);
		act(() => root.render(null));
		expect(pendingWakes()).toBe(0);
		expect(vi.getTimerCount()).toBe(0);
	});

	it("titles the absolute time and marks a bad stamp", () => {
		act(() => root.render(<RelativeTime ts={T0 - H} />));
		const el = host.querySelector("time");
		expect(el?.getAttribute("dateTime")).toBe(new Date(T0 - H).toISOString());
		expect(el?.getAttribute("title")).toBeTruthy();
		act(() => root.render(<RelativeTime ts={Number.NaN} />));
		expect(host.textContent).toBe("-");
		expect(pendingWakes()).toBe(0);
	});

	it("wakes a waiter once, at its due time", () => {
		const fire = vi.fn();
		wakeAt(T0 + 2 * S, fire);
		act(() => vi.advanceTimersByTime(1_999));
		expect(fire).not.toHaveBeenCalled();
		act(() => vi.advanceTimersByTime(1));
		expect(fire).toHaveBeenCalledTimes(1);
		expect(pendingWakes()).toBe(0);
	});
});
