// Grid over the real tree store: one cell per child in insertion order, the
// track list off max_columns and min_cell_width, a "grid" flow for each
// child, and the per child maps (span, align_self) the grid keeps.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	gridPlace,
	gridSpan,
	gridTemplate,
	templateTracks,
	trackCount,
} from "../../components/ui/grid";
import { NodeView, register, tree, useFlow } from "../../tree";
import "..";
import { readingOrder, readPlace } from "./grid";
import { readSpans } from "./layout";

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
	write(["g", "Grid", { max_columns: 0, min_cell_width: 240 }]);
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

	it("puts the track list for max_columns and min_cell_width inline", () => {
		expect(grid().style.gridTemplateColumns).toBe(gridTemplate(0, 240, 4));
		expect(grid().style.gridTemplateColumns).toContain("auto-fill");
		expect(grid().style.gridTemplateColumns).toContain("240px");

		act(() =>
			tree
				.getState()
				.dispatch({ op: "write", ref: ["g"], payload: { max_columns: 3, min_cell_width: 200 } }),
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

	it("maps gap, padding, justify and align to classes, on the scale Row uses", () => {
		act(() =>
			tree.getState().dispatch({
				op: "write",
				ref: ["g"],
				payload: { gap: 2, padding: 3, align: "start", justify: "center" },
			}),
		);
		expect(grid().className).toContain("gap-2");
		expect(grid().className).toContain("p-3");
		expect(grid().className).toContain("items-start");
		expect(grid().className).toContain("justify-items-center");

		act(() =>
			tree.getState().dispatch({ op: "write", ref: ["g"], payload: { gap: 7, align: "sideways" } }),
		);
		expect(grid().className).toContain("gap-7");
		expect(grid().className).toContain("items-stretch");

		act(() => tree.getState().dispatch({ op: "write", ref: ["g"], payload: { gap: 16 } }));
		expect(grid().className).toContain("gap-16");
		expect(grid().style.gridTemplateColumns).toBe(gridTemplate(0, 240, 16));
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
				payload: { max_columns: 3, span: { hero: { cols: 2, rows: 2 } } },
			}),
		);
		write(["g", "Grid"], ["hero", "Card"]);
		write(["g", "Grid"], ["a", "Card"]);
		const [hero, a] = cells();
		expect(hero.style.gridColumn).toBe("span 2 / span 2");
		expect(hero.style.gridRow).toBe("span 2 / span 2");
		expect(a.style.gridColumn).toBe("");
	});

	it("merges one set_child span into the map and drops a span back to 1 by 1", () => {
		write(["g", "Grid"], ["a", "Card"]);
		write(["g", "Grid"], ["b", "Card"]);
		const span = (key: string, cols: number, rows = 1) =>
			act(() =>
				tree
					.getState()
					.dispatch({ op: "set_child", ref: ["g"], payload: { key, span: { cols, rows } } }),
			);
		span("a", 2);
		span("b", 1, 3);
		expect(tree.getState().getIn(["g"])?.props.span).toEqual({
			a: { cols: 2, rows: 1 },
			b: { cols: 1, rows: 3 },
		});
		span("a", 1);
		expect(tree.getState().getIn(["g"])?.props.span).toEqual({ b: { cols: 1, rows: 3 } });
		expect(cells()[0].style.gridColumn).toBe("");
		expect(cells()[1].style.gridRow).toBe("span 3 / span 3");
	});

	it("aligns one cell by its key", () => {
		act(() =>
			tree
				.getState()
				.dispatch({ op: "set_child", ref: ["g"], payload: { key: "a", align_self: "end" } }),
		);
		write(["g", "Grid"], ["a", "Card"]);
		expect(cells()[0].className).toContain("self-end");
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
		// max_columns 4, min 140, 12px gaps: four at 800, two at 336, one at 200.
		expect(trackCount(800, 4, 140, 12)).toBe(4);
		expect(trackCount(336, 4, 140, 12)).toBe(2);
		expect(trackCount(200, 4, 140, 12)).toBe(1);
		// max_columns 0: as many as fit at min width.
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

describe("Grid placed", () => {
	const board = (props: Record<string, unknown> = {}) =>
		act(() =>
			tree.getState().dispatch({
				op: "write",
				ref: ["g"],
				payload: { cols: "2fr 1fr", rows: "64px 1fr", ...props },
			}),
		);

	it("lays the track template out instead of the equal tracks", () => {
		board();
		expect(grid().dataset.mode).toBe("placed");
		expect(grid().style.gridTemplateColumns).toBe("2fr 1fr");
		expect(grid().style.gridTemplateRows).toBe("64px 1fr");
	});

	it("puts a cell at its place and leaves the rest empty", () => {
		board();
		write(["g", "Grid"], ["1,1", "TextRef", { value: "late" }]);
		write(["g", "Grid"], ["0,0", "TextRef", { value: "first" }]);
		const [a, b] = cells();
		expect(a.dataset.cell).toBe("0,0");
		expect(a.style.gridRow).toBe("1");
		expect(a.style.gridColumn).toBe("1");
		expect(b.dataset.cell).toBe("1,1");
		expect(b.style.gridRow).toBe("2");
		expect(b.style.gridColumn).toBe("2");
		expect(cells()).toHaveLength(2);
	});

	it("spans a place, clipped at the board's last column", () => {
		board({ span: { "0,0": { cols: 2, rows: 1 }, "1,1": { cols: 3, rows: 2 } } });
		write(["g", "Grid"], ["0,0", "Card"]);
		write(["g", "Grid"], ["1,1", "Card"]);
		const [hero, side] = cells();
		expect(hero.style.gridColumn).toBe("1 / span 2");
		expect(side.style.gridColumn).toBe("2");
		expect(side.style.gridRow).toBe("2 / span 2");
	});

	it("lets keyed children flow into free places, after the placed ones", () => {
		board();
		write(["g", "Grid"], ["note", "TextRef", { value: "n" }]);
		write(["g", "Grid"], ["0,1", "TextRef", { value: "p" }]);
		expect(cells().map((c) => c.dataset.cell)).toEqual(["0,1", "note"]);
		expect(cells()[1].style.gridRow).toBe("");
	});

	it("drops a hidden cell and leaves its place empty", () => {
		board();
		write(["g", "Grid"], ["0,0", "TextRef", { value: "a" }]);
		write(["g", "Grid"], ["0,1", "TextRef", { value: "b" }]);
		act(() => tree.getState().dispatch({ op: "hide", ref: ["g", "0,0"], payload: null }));
		expect(cells().map((c) => c.dataset.cell)).toEqual(["0,1"]);
		expect(cells()[0].style.gridColumn).toBe("2");
	});

	it("refuses a template that is not track sizes", () => {
		board({ cols: "1fr; background: red", rows: "url(x)" });
		expect(grid().dataset.mode).toBe("flow");
		expect(grid().style.gridTemplateColumns).toContain("auto-fill");
	});

	it("reads a count as that many equal tracks", () => {
		board({ cols: 3, rows: null });
		expect(grid().style.gridTemplateColumns).toBe("repeat(3, minmax(0, 1fr))");
		expect(grid().style.gridTemplateRows).toBe("");
	});

	it("counts the tracks a template names", () => {
		expect(templateTracks("2fr 1fr")).toBe(2);
		expect(templateTracks("240px minmax(0, 1fr) auto")).toBe(3);
		expect(templateTracks("repeat(3, minmax(0, 1fr))")).toBe(3);
		expect(templateTracks("200px repeat(2, 1fr 2fr)")).toBe(5);
		expect(templateTracks("repeat(auto-fill, minmax(100px, 1fr))")).toBe(Number.POSITIVE_INFINITY);
	});

	it("places from zero-based row and column", () => {
		expect(gridPlace(0, 0, 1, 1, 2)).toEqual({ gridRow: "1", gridColumn: "1" });
		expect(gridPlace(2, 1, 4, 2, 3)).toEqual({ gridRow: "3 / span 2", gridColumn: "2 / span 2" });
	});

	it("reads places and puts them in reading order", () => {
		expect(readPlace("3,12")).toEqual([3, 12]);
		expect(readPlace("a,1")).toBeNull();
		expect(readPlace("2")).toBeNull();
		expect(readingOrder(["1,0", "note", "0,2", "1", "0,0", "0"])).toEqual([
			"0,0",
			"0,2",
			"1,0",
			"note",
			"0",
			"1",
		]);
	});

	it("takes height and scroll", () => {
		board({ height: 320, scroll: "y" });
		expect(grid().style.height).toBe("320px");
		expect(grid().className).toContain("overflow-y-auto");
	});
});
