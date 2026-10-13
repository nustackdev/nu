// The sketch board's model: normalization, config, colors and geometry.

import { describe, expect, it } from "vitest";
import {
	arrowPath,
	freehandPath,
	normalizeElements,
	SKETCH_DEFAULTS,
	sketchColor,
	sketchConfig,
} from "./sketch-board-model";

describe("normalizeElements", () => {
	it("fills style from the defaults and keeps what is given", () => {
		expect(
			normalizeElements([
				{ type: "rect", x: 0.1, y: 0.2, w: 0.3, h: 0.4 },
				{
					type: "ellipse",
					x: 0,
					y: 0,
					w: 1,
					h: 1,
					stroke: "#123456",
					fill: "red-soft",
					width: 0.1,
				},
			]),
		).toEqual([
			{ type: "rect", x: 0.1, y: 0.2, w: 0.3, h: 0.4, stroke: "ink", fill: "none", width: 0.012 },
			{ type: "ellipse", x: 0, y: 0, w: 1, h: 1, stroke: "#123456", fill: "red-soft", width: 0.1 },
		]);
	});

	it("flips negative sides and clamps to the board", () => {
		expect(normalizeElements([{ type: "rect", x: 0.5, y: 0.5, w: -0.2, h: 0.9 }])[0]).toMatchObject(
			{
				x: 0.3,
				y: 0.5,
				w: 0.2,
				h: 0.5,
			},
		);
	});

	it("reads a bare list of points as a pen stroke", () => {
		expect(
			normalizeElements([
				[
					[0.1, 0.1],
					[0.2, 0.2, 0.9],
				],
			]),
		).toEqual([
			{
				type: "path",
				points: [
					[0.1, 0.1],
					[0.2, 0.2, 0.9],
				],
				stroke: "ink",
				width: 0.012,
			},
		]);
	});

	it("drops what it cannot draw", () => {
		expect(
			normalizeElements([
				{ type: "path", points: [] },
				{ type: "line", points: [[0, 0]] },
				{ type: "rect", x: 0, y: 0, w: "x", h: 1 },
				{ type: "star" },
				null,
				"junk",
			]),
		).toEqual([]);
		expect(normalizeElements("junk")).toEqual([]);
	});
});

describe("sketchConfig", () => {
	it("defaults to every tool and control", () => {
		const c = sketchConfig({});
		expect(c.tools).toEqual(["pen", "rect", "ellipse", "line", "arrow"]);
		expect(c.controls).toHaveLength(7);
		expect(c.defaults).toEqual(SKETCH_DEFAULTS);
	});

	it("keeps known names in toolbar order and a default tool it has", () => {
		const c = sketchConfig({
			tools: ["arrow", "rect", "nope"],
			controls: [],
			defaults: { tool: "pen", size: 0.07 },
		});
		expect(c.tools).toEqual(["rect", "arrow"]);
		expect(c.controls).toEqual([]);
		expect(c.defaults).toMatchObject({ tool: "rect", size: 0.07 });
	});
});

describe("geometry and color", () => {
	it("resolves palette names through kit roles and passes CSS colors through", () => {
		expect(sketchColor("ink")).toBe("var(--text-primary)");
		expect(sketchColor("blue-soft")).toBe("var(--accent-2-soft)");
		expect(sketchColor("#e11d48")).toBe("#e11d48");
		expect(sketchColor("none")).toBe("none");
	});

	it("outlines pen ink as a closed path, a dot included", () => {
		expect(
			freehandPath(
				[
					[0.1, 0.1],
					[0.5, 0.5],
				],
				8,
				200,
				200,
			),
		).toMatch(/^M.*Z$/);
		expect(freehandPath([[0.5, 0.5]], 8, 200, 200)).toMatch(/^M.*Z$/);
	});

	it("draws an arrow as a shaft and a two-sided head", () => {
		expect(arrowPath([0, 0], [100, 0], 2).match(/M/g)).toHaveLength(2);
	});
});
