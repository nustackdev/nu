// The transport's arithmetic: clock and spoken times, seek clamping, the
// buffered run under the playhead, the key map, and waveform peaks.

import { describe, expect, it } from "vitest";
import {
	bufferedEnd,
	clampTime,
	computePeaks,
	formatRate,
	formatTime,
	fractionOf,
	type KeyState,
	keyCommand,
	resamplePeaks,
	spokenTime,
	timeAt,
} from "./model";

describe("formatTime", () => {
	it("reads minutes and seconds, hours when the scale reaches one", () => {
		expect(formatTime(0)).toBe("0:00");
		expect(formatTime(7.9)).toBe("0:07");
		expect(formatTime(225)).toBe("3:45");
		expect(formatTime(3729)).toBe("1:02:09");
		expect(formatTime(12, 3729)).toBe("0:00:12");
	});

	it("reads unknown as dashes and a negative as zero", () => {
		expect(formatTime(Number.NaN)).toBe("--:--");
		expect(formatTime(Number.POSITIVE_INFINITY)).toBe("--:--");
		expect(formatTime(-3)).toBe("0:00");
	});
});

describe("spokenTime", () => {
	it("says each unit it has, singular where it should", () => {
		expect(spokenTime(0)).toBe("0 seconds");
		expect(spokenTime(1)).toBe("1 second");
		expect(spokenTime(65)).toBe("1 minute 5 seconds");
		expect(spokenTime(120)).toBe("2 minutes");
		expect(spokenTime(3601)).toBe("1 hour 1 second");
		expect(spokenTime(Number.NaN)).toBe("unknown");
	});
});

describe("seek math", () => {
	it("clamps into the duration, or only at zero when it is unknown", () => {
		expect(clampTime(-1, 10)).toBe(0);
		expect(clampTime(12, 10)).toBe(10);
		expect(clampTime(4, 10)).toBe(4);
		expect(clampTime(400, Number.NaN)).toBe(400);
		expect(clampTime(400, Number.POSITIVE_INFINITY)).toBe(400);
		expect(clampTime(Number.NaN, 10)).toBe(0);
	});

	it("turns times into fractions and back", () => {
		expect(fractionOf(5, 20)).toBe(0.25);
		expect(fractionOf(30, 20)).toBe(1);
		expect(fractionOf(5, Number.NaN)).toBe(0);
		expect(timeAt(0.25, 20)).toBe(5);
		expect(timeAt(2, 20)).toBe(20);
		expect(timeAt(0.5, Number.NaN)).toBe(0);
	});

	it("prints rates without trailing zeros", () => {
		expect(formatRate(1)).toBe("1x");
		expect(formatRate(1.25)).toBe("1.25x");
		expect(formatRate(0.5)).toBe("0.5x");
	});
});

describe("bufferedEnd", () => {
	const ranges = (...r: [number, number][]) => ({
		length: r.length,
		start: (i: number) => r[i][0],
		end: (i: number) => r[i][1],
	});

	it("is the end of the run under the playhead", () => {
		expect(bufferedEnd(ranges([0, 12], [30, 40]), 5)).toBe(12);
		expect(bufferedEnd(ranges([0, 12], [30, 40]), 35)).toBe(40);
	});

	it("is the playhead itself in a gap, and zero with nothing", () => {
		expect(bufferedEnd(ranges([0, 12], [30, 40]), 20)).toBe(20);
		expect(bufferedEnd(null, 3)).toBe(0);
	});
});

describe("keyCommand", () => {
	const s: KeyState = { time: 30, duration: 100, playing: true, volume: 0.5, muted: false };
	const key = (k: string, over: Partial<KeyState> = {}, shift = false) =>
		keyCommand(k, shift, { ...s, ...over }, { fineStep: 1 / 25, fullscreen: true });

	it("plays and pauses on space and k", () => {
		expect(key(" ")).toEqual({ kind: "toggle" });
		expect(key("k")).toEqual({ kind: "toggle" });
	});

	it("seeks 5s on j l and the arrows, 15s with shift, clamped", () => {
		expect(key("j")).toEqual({ kind: "seek", to: 25 });
		expect(key("ArrowRight")).toEqual({ kind: "seek", to: 35 });
		expect(key("l", {}, true)).toEqual({ kind: "seek", to: 45 });
		expect(key("ArrowLeft", { time: 2 })).toEqual({ kind: "seek", to: 0 });
		expect(key("l", { time: 98 })).toEqual({ kind: "seek", to: 100 });
	});

	it("jumps to tenths on the digits and to the ends on home and end", () => {
		expect(key("0")).toEqual({ kind: "seek", to: 0 });
		expect(key("7")).toEqual({ kind: "seek", to: 70 });
		expect(key("Home")).toEqual({ kind: "seek", to: 0 });
		expect(key("End")).toEqual({ kind: "seek", to: 100 });
		expect(key("5", { duration: Number.NaN })).toBeNull();
	});

	it("steps a frame on , and . only while paused", () => {
		expect(key(".")).toBeNull();
		const fwd = key(".", { playing: false });
		const back = key(",", { playing: false });
		expect(fwd?.kind === "seek" && fwd.to).toBeCloseTo(30.04);
		expect(back?.kind === "seek" && back.to).toBeCloseTo(29.96);
	});

	it("moves the volume a tenth, from zero when muted, and mutes on m", () => {
		expect(key("ArrowUp")).toEqual({ kind: "volume", to: 0.6 });
		expect(key("ArrowDown", { volume: 0.05 })).toEqual({ kind: "volume", to: 0 });
		expect(key("ArrowUp", { muted: true })).toEqual({ kind: "volume", to: 0.1 });
		expect(key("ArrowUp", { volume: 1 })).toEqual({ kind: "volume", to: 1 });
		expect(key("m")).toEqual({ kind: "mute" });
	});

	it("takes f only where there is a full screen, and leaves other keys", () => {
		expect(key("f")).toEqual({ kind: "fullscreen" });
		expect(keyCommand("f", false, s, { fineStep: 0.1 })).toBeNull();
		expect(key("x")).toBeNull();
		expect(key("Tab")).toBeNull();
	});
});

describe("peaks", () => {
	const round = (a: Float32Array) => Array.from(a, (v) => Math.round(v * 1e4) / 1e4);

	it("takes the loudest sample per slice across channels, scaled to 1", () => {
		const left = [0, 0.1, -0.5, 0.2, 0, 0, 0.25, 0];
		const right = [0, 0, 0, 0, 0, -0.1, 0, 0];
		expect(round(computePeaks([left, right], 4))).toEqual([0.2, 1, 0.2, 0.5]);
	});

	it("is all zeros for silence and empty for no buckets", () => {
		expect(round(computePeaks([[0, 0, 0, 0]], 2))).toEqual([0, 0]);
		expect(computePeaks([[1]], 0).length).toBe(0);
		expect(round(computePeaks([], 3))).toEqual([0, 0, 0]);
	});

	it("handles more buckets than samples", () => {
		expect(round(computePeaks([[0.5, 1]], 4))).toEqual([0.5, 0.5, 1, 1]);
	});

	it("resamples to bars by the loudest peak each covers", () => {
		expect(resamplePeaks([0.1, 0.9, 0.2, 0.3, 0.4, 0.1], 3)).toEqual([0.9, 0.3, 0.4]);
		expect(resamplePeaks([0.5, 1], 4)).toEqual([0.5, 0.5, 1, 1]);
		expect(resamplePeaks([], 2)).toEqual([0, 0]);
	});
});
