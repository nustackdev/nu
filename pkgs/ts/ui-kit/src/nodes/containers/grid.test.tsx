// Grid over the real tree store: one cell per child in insertion order, the
// track list off columns and min_width, a "grid" flow for each child, and
// the spans the grid keeps for its cells.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { gridSpan, gridTemplate, trackCount } from "../../components/ui/grid";
import { NodeView, register, tree, useFlow } from "../../tree";
import "..";
import { readSpans } from "./grid";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

// A leaf that prints the flow its parent hands it.
function FlowProbe() {
	return <span data-probe>{useFlow()}</span>;
}
register("GridTestProbe", { component: FlowProbe });

const grid = () => host.querySelector("[data-slot=grid]") as HTMLElement;
const cells = () => [...host.querySelectorAll<HTMLElement>("[data-slot=grid-cell]")];

function write(...chain: [string, string, Record<string, unknown>?][]) {
	act(() => {
		tree
			.getState()
			.write(chain.map(([seg, type, props]) => (props ? [seg, type, props] : [seg, type])));
	});
}

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	write(["g", "Grid", { columns: 0, min_width: 240, gap: 4, align: "stretch", padding: 0 }]);
	act(() => root.render(<NodeView path={["g"]} />));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

describe("Grid", () => {
	it("draws one cell per child, in insertion order", () => {
		write(["g", "Grid"], ["b", "TextRef", { value: "two" }]);
		write(["g", "Grid"], ["a", "TextRef", { value: "one" }]);
		write(["g", "Grid"], ["c", "BadgeRef", { label: "three" }]);
		expect(cells().map((c) => c.dataset.cell)).toEqual(["b", "a", "c"]);
		expect(cells().map((c) => c.textContent)).toEqual(["two", "one", "three"]);
	});

	it("puts the track list for columns and min_width inline", () => {
		expect(grid().style.gridTemplateColumns).toBe(gridTemplate(0, 240, 4));
		expect(grid().style.gridTemplateColumns).toContain("auto-fill");
		expect(grid().style.gridTemplateColumns).toContain("240px");

		act(() =>
			tree
				.getState()
				.dispatch({ op: "write", ref: ["g"], payload: { columns: 3, min_width: 200 } }),
		);
		const tracks = grid().style.gridTemplateColumns;
		expect(tracks).toBe(gridTemplate(3, 200, 4));
		expect(tracks).toContain("200px");
		expect(tracks).toContain("/ 3");
	});

	it("caps at N columns by sharing the row after the gaps", () => {
		expect(gridTemplate(3, 240, 4)).toBe(
			"repeat(auto-fill, minmax(min(100%, max(240px, (100% - 2 * var(--spacing) * 4) / 3)), 1fr))",
		);
		expect(gridTemplate(0, 200, 2)).toBe("repeat(auto-fill, minmax(min(100%, 200px), 1fr))");
	});

	it("maps gap, padding and align to classes, falling back on unknown values", () => {
		act(() =>
			tree
				.getState()
				.dispatch({ op: "write", ref: ["g"], payload: { gap: 2, padding: 3, align: "start" } }),
		);
		expect(grid().className).toContain("gap-2");
		expect(grid().className).toContain("p-3");
		expect(grid().className).toContain("items-start");

		act(() =>
			tree.getState().dispatch({ op: "write", ref: ["g"], payload: { gap: 7, align: "sideways" } }),
		);
		expect(grid().className).toContain("gap-4");
		expect(grid().className).toContain("items-stretch");
	});

	it("hands every child a grid flow", () => {
		write(["g", "Grid"], ["p", "GridTestProbe"]);
		write(["g", "Grid"], ["q", "GridTestProbe"]);
		const probes = [...host.querySelectorAll("[data-probe]")].map((el) => el.textContent);
		expect(probes).toEqual(["grid", "grid"]);
	});

	it("hands a card's children a block flow again", () => {
		write(["g", "Grid"], ["card", "Card"], ["p", "GridTestProbe"]);
		expect(host.querySelector("[data-probe]")?.textContent).toBe("block");
	});
});

describe("Grid spans", () => {
	it("places a spanning cell over its tracks and leaves the rest plain", () => {
		act(() =>
			tree.getState().dispatch({
				op: "write",
				ref: ["g"],
				payload: { columns: 3, spans: { hero: { cols: 2, rows: 2 } } },
			}),
		);
		write(["g", "Grid"], ["hero", "Card"]);
		write(["g", "Grid"], ["a", "Card"]);
		const [hero, a] = cells();
		expect(hero.style.gridColumn).toBe("span 2 / span 2");
		expect(hero.style.gridRow).toBe("span 2 / span 2");
		expect(a.style.gridColumn).toBe("");
	});

	it("merges one set_span into the map and drops a span back to 1 by 1", () => {
		write(["g", "Grid"], ["a", "Card"]);
		write(["g", "Grid"], ["b", "Card"]);
		const span = (key: string, cols: number, rows = 1) =>
			act(() =>
				tree.getState().dispatch({ op: "set_span", ref: ["g"], payload: { key, cols, rows } }),
			);
		span("a", 2);
		span("b", 1, 3);
		expect(tree.getState().getIn(["g"])?.props.spans).toEqual({
			a: { cols: 2, rows: 1 },
			b: { cols: 1, rows: 3 },
		});
		span("a", 1);
		expect(tree.getState().getIn(["g"])?.props.spans).toEqual({ b: { cols: 1, rows: 3 } });
		expect(cells()[0].style.gridColumn).toBe("");
		expect(cells()[1].style.gridRow).toBe("span 3 / span 3");
	});

	it("turns on dense backfill", () => {
		act(() => tree.getState().dispatch({ op: "write", ref: ["g"], payload: { dense: true } }));
		expect(grid().className).toContain("grid-flow-row-dense");
	});

	it("ignores malformed spans", () => {
		expect(readSpans({ a: { cols: 0 }, b: "2", c: { cols: 2.7 }, d: null })).toEqual({
			c: { cols: 2, rows: 1 },
		});
		expect(readSpans([1, 2])).toEqual({});
	});

	it("counts the tracks auto-fill lays out at a width", () => {
		// columns 4, min 140, 12px gaps: four at 800, two at 336, one at 200.
		expect(trackCount(800, 4, 140, 12)).toBe(4);
		expect(trackCount(336, 4, 140, 12)).toBe(2);
		expect(trackCount(200, 4, 140, 12)).toBe(1);
		// columns 0: as many as fit at min width.
		expect(trackCount(1000, 0, 240, 16)).toBe(3);
		expect(trackCount(0, 3, 240, 16)).toBe(1);
	});

	it("clamps a span to the tracks there are, and stacks it flat in one", () => {
		expect(gridSpan(3, 2, 2)).toEqual({
			gridColumn: "span 2 / span 2",
			gridRow: "span 2 / span 2",
		});
		expect(gridSpan(2, 2, 1)).toEqual({ gridColumn: undefined, gridRow: undefined });
		expect(gridSpan(2, 1, Number.POSITIVE_INFINITY).gridColumn).toBe("span 2 / span 2");
	});
});
