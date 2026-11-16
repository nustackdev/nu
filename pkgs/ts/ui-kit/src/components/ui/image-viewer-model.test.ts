// The image viewer's geometry: fit, limits, the pan clamp, zoom toward a point.

import { describe, expect, it } from "vitest";
import {
	canPan,
	clampView,
	fitScale,
	fitView,
	MAX_SCALE,
	panBy,
	pixelAt,
	scaleLimits,
	stepScale,
	toggleView,
	wheelScale,
	zoomAt,
	zoomLabel,
} from "./image-viewer-model";

const BOX = { w: 400, h: 300 };
const PHOTO = { w: 4000, h: 2000 };
const SPRITE = { w: 16, h: 16 };

describe("fit and limits", () => {
	it("fits the long side, up or down", () => {
		expect(fitScale(PHOTO, BOX)).toBe(0.1);
		expect(fitScale(SPRITE, BOX)).toBe(18.75);
	});

	it("reads 1 while either side has no size", () => {
		expect(fitScale({ w: 0, h: 0 }, BOX)).toBe(1);
		expect(fitScale(PHOTO, { w: 0, h: 0 })).toBe(1);
	});

	it("zooms out to fit or 1:1 and in to the max or four fits", () => {
		expect(scaleLimits(PHOTO, BOX)).toEqual({ min: 0.1, max: MAX_SCALE });
		expect(scaleLimits(SPRITE, BOX)).toEqual({ min: 1, max: 75 });
		expect(scaleLimits({ w: 400, h: 300 }, BOX).max).toBe(MAX_SCALE);
	});

	it("centres the fitted image", () => {
		expect(fitView(PHOTO, BOX)).toEqual({ scale: 0.1, x: 0, y: 50 });
	});
});

describe("clampView", () => {
	it("centres a side that fits and covers the box with one that does not", () => {
		const v = clampView({ scale: 0.15, x: 999, y: 999 }, PHOTO, BOX);
		// 600 x 300: wider than the box, exactly as tall.
		expect(v).toEqual({ scale: 0.15, x: 0, y: 0 });
		expect(clampView({ scale: 0.15, x: -999, y: 0 }, PHOTO, BOX).x).toBe(-200);
	});

	it("holds the scale inside the limits", () => {
		expect(clampView({ scale: 0.01, x: 0, y: 0 }, PHOTO, BOX).scale).toBe(0.1);
		expect(clampView({ scale: 999, x: 0, y: 0 }, PHOTO, BOX).scale).toBe(MAX_SCALE);
	});
});

describe("zoomAt", () => {
	it("keeps the image pixel under the point where it was", () => {
		const start = { scale: 1, x: -1000, y: -500 };
		const at = { x: 100, y: 80 };
		const before = pixelAt(start, at, PHOTO);
		const next = zoomAt(start, 2, at, PHOTO, BOX);
		expect(next.scale).toBe(2);
		expect(pixelAt(next, at, PHOTO)).toEqual(before);
	});

	it("still clamps after the zoom", () => {
		const v = zoomAt(fitView(PHOTO, BOX), 1, { x: 0, y: 0 }, PHOTO, BOX);
		expect(v).toEqual({ scale: 1, x: 0, y: 0 });
	});
});

describe("stepScale", () => {
	const limits = scaleLimits(PHOTO, BOX);

	it("walks the ladder from wherever it is", () => {
		expect(stepScale(1, 1, limits)).toBe(1.5);
		expect(stepScale(1, -1, limits)).toBe(0.75);
		expect(stepScale(1.2, 1, limits)).toBe(1.5);
		expect(stepScale(1.2, -1, limits)).toBe(1);
	});

	it("stops at the limits", () => {
		expect(stepScale(0.1, -1, limits)).toBe(0.1);
		expect(stepScale(32, 1, limits)).toBe(32);
	});
});

describe("wheelScale", () => {
	it("zooms in on a wheel up and out on a wheel down", () => {
		expect(wheelScale(1, -100, 0, false)).toBeGreaterThan(1);
		expect(wheelScale(1, 100, 0, false)).toBeLessThan(1);
	});

	it("reads a line delta like its pixels and caps a flick", () => {
		expect(wheelScale(1, 3, 1, false)).toBeCloseTo(wheelScale(1, 48, 0, false));
		expect(wheelScale(1, -10_000, 0, false)).toBeCloseTo(Math.exp(0.5));
	});

	it("moves a pinch faster per delta than a wheel", () => {
		expect(wheelScale(1, -10, 0, true)).toBeGreaterThan(wheelScale(1, -10, 0, false));
	});
});

describe("pan", () => {
	it("pans only while the image is larger than the box", () => {
		const fit = fitView(PHOTO, BOX);
		expect(canPan(fit, PHOTO, BOX)).toBe(false);
		expect(panBy(fit, 50, 50, PHOTO, BOX)).toEqual(fit);
		const close = { scale: 1, x: -100, y: -100 };
		expect(canPan(close, PHOTO, BOX)).toBe(true);
		expect(panBy(close, 50, 30, PHOTO, BOX)).toEqual({ scale: 1, x: -50, y: -70 });
		expect(panBy(close, 500, 500, PHOTO, BOX)).toEqual({ scale: 1, x: 0, y: 0 });
	});
});

describe("toggleView", () => {
	it("goes from fit to 1:1 on a large image and back", () => {
		const fit = fitView(PHOTO, BOX);
		const close = toggleView(fit, { x: 200, y: 150 }, PHOTO, BOX);
		expect(close.scale).toBe(1);
		expect(toggleView(close, { x: 0, y: 0 }, PHOTO, BOX)).toEqual(fit);
	});

	it("doubles the fit on a small image", () => {
		const fit = fitView(SPRITE, BOX);
		expect(toggleView(fit, { x: 200, y: 150 }, SPRITE, BOX).scale).toBe(fit.scale * 2);
	});
});

describe("readouts", () => {
	it("names the pixel under the point, null off the image", () => {
		const v = { scale: 10, x: 5, y: 5 };
		expect(pixelAt(v, { x: 5, y: 5 }, SPRITE)).toEqual({ x: 0, y: 0 });
		expect(pixelAt(v, { x: 164, y: 20 }, SPRITE)).toEqual({ x: 15, y: 1 });
		expect(pixelAt(v, { x: 4, y: 20 }, SPRITE)).toBeNull();
		expect(pixelAt(v, { x: 165, y: 20 }, SPRITE)).toBeNull();
	});

	it("says the zoom as a whole percent", () => {
		expect(zoomLabel(1)).toBe("100%");
		expect(zoomLabel(0.0523)).toBe("5%");
		expect(zoomLabel(18.75)).toBe("1875%");
	});
});
