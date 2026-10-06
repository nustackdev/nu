// The data table's arithmetic, kept pure so it is tested without a DOM: cell
// keys, where a key press moves the focus, what a click or Space does to the
// selection, which rows a delete takes, where a move or a drop lands, and how
// a cell's value reads and parses.
//
// Positions are (row, col) indices into what is drawn. Row -1 is the header,
// and it is part of the grid only when some column sorts.

export type DataTableKind = "text" | "number" | "bool" | "select";

export type CellPos = { row: number; col: number };

/** The grid's extent: body rows, columns, and whether the header is row -1. */
export type GridDims = { rows: number; cols: number; header: boolean };

/**
 * One cell's roving key. JSON keeps any row key apart from any column key,
 * and a header cell (row `null`) apart from every body cell.
 */
export function cellKey(row: string | null, column: string): string {
	return JSON.stringify([row, column]);
}

/** How many rows PageUp and PageDown step. */
export const PAGE_ROWS = 10;

/**
 * Where a navigation key takes the focus, clamped to the grid; null for a key
 * that does not navigate. `mod` is Ctrl or Cmd: with Home and End it means the
 * whole grid, not the row.
 */
export function navigate(key: string, mod: boolean, at: CellPos, dims: GridDims): CellPos | null {
	const top = dims.header ? -1 : 0;
	const bottom = dims.rows - 1;
	const last = dims.cols - 1;
	const clampRow = (r: number) => Math.max(top, Math.min(bottom, r));
	const clampCol = (c: number) => Math.max(0, Math.min(last, c));
	switch (key) {
		case "ArrowUp":
			return { row: clampRow(at.row - 1), col: at.col };
		case "ArrowDown":
			return { row: clampRow(at.row + 1), col: at.col };
		case "ArrowLeft":
			return { row: at.row, col: clampCol(at.col - 1) };
		case "ArrowRight":
			return { row: at.row, col: clampCol(at.col + 1) };
		case "Home":
			return mod ? { row: top, col: 0 } : { row: at.row, col: 0 };
		case "End":
			return mod ? { row: Math.max(top, bottom), col: last } : { row: at.row, col: last };
		case "PageUp":
			return { row: clampRow(at.row - PAGE_ROWS), col: at.col };
		case "PageDown":
			return { row: clampRow(at.row + PAGE_ROWS), col: at.col };
		default:
			return null;
	}
}

/**
 * The next cell that takes an editor, reading row by row and wrapping across
 * rows; null at either end. `can(row, col)` says whether a cell edits.
 */
export function nextEditable(
	at: CellPos,
	back: boolean,
	dims: GridDims,
	can: (row: number, col: number) => boolean,
): CellPos | null {
	const step = back ? -1 : 1;
	let flat = at.row * dims.cols + at.col + step;
	const end = dims.rows * dims.cols;
	while (flat >= 0 && flat < end) {
		const row = Math.floor(flat / dims.cols);
		const col = flat % dims.cols;
		if (can(row, col)) return { row, col };
		flat += step;
	}
	return null;
}

/** The rows from `anchor` to `key` inclusive, in table order. */
export function selectRange(order: readonly string[], anchor: string, key: string): string[] {
	const a = order.indexOf(anchor);
	const b = order.indexOf(key);
	if (a < 0 || b < 0) return [key];
	return order.slice(Math.min(a, b), Math.max(a, b) + 1);
}

export type SelectionMode = "none" | "single" | "multi";

/**
 * The selection after a click on row `key`. Single replaces. Multi: a plain
 * click replaces, `toggle` (Cmd/Ctrl) adds or removes the row, `range`
 * (Shift) takes the rows from the anchor to it.
 */
export function clickSelection(
	mode: SelectionMode,
	selected: readonly string[],
	order: readonly string[],
	key: string,
	anchor: string | null,
	{ range = false, toggle = false }: { range?: boolean; toggle?: boolean } = {},
): string[] {
	if (mode === "none") return [...selected];
	if (mode === "single") return [key];
	if (range && anchor !== null) return selectRange(order, anchor, key);
	if (toggle) return toggleKey(selected, key);
	return [key];
}

/** Space on row `key`: single selects it, multi adds or removes it. */
export function spaceSelection(
	mode: SelectionMode,
	selected: readonly string[],
	key: string,
): string[] {
	if (mode === "none") return [...selected];
	if (mode === "single") return [key];
	return toggleKey(selected, key);
}

function toggleKey(selected: readonly string[], key: string): string[] {
	return selected.includes(key) ? selected.filter((k) => k !== key) : [...selected, key];
}

/** What a delete on row `key` takes: the selection when the row is in it, else the row. */
export function deleteTargets(selected: readonly string[], key: string): string[] {
	return selected.includes(key) ? [...selected] : [key];
}

/**
 * Where a one-step move puts row `key`, as an index into the rows without it;
 * null at the edge. Up from i is i - 1; down from i is i + 1, because the row
 * below closes the gap first.
 */
export function stepIndex(order: readonly string[], key: string, delta: -1 | 1): number | null {
	const i = order.indexOf(key);
	if (i < 0) return null;
	const to = i + delta;
	return to < 0 || to >= order.length ? null : to;
}

/**
 * Where a drop on `target`'s top or bottom half puts row `key`, as an index
 * into the rows without it; null when it would land where it is.
 */
export function dropIndex(
	order: readonly string[],
	key: string,
	target: string,
	edge: "before" | "after",
): number | null {
	const from = order.indexOf(key);
	const at = order.indexOf(target);
	if (from < 0 || at < 0 || key === target) return null;
	let to = edge === "before" ? at : at + 1;
	if (to > from) to -= 1;
	return to === from ? null : to;
}

/** Which half of a row of `height` at `top` the pointer at `y` is in. */
export function dropEdge(top: number, height: number, y: number): "before" | "after" {
	return y < top + height / 2 ? "before" : "after";
}

/** The next direction for a header click: asc first, desc on a column already asc. */
export function nextDirection(
	sort: { column: string; direction: "asc" | "desc" } | null | undefined,
	column: string,
): "asc" | "desc" {
	return sort?.column === column && sort.direction === "asc" ? "desc" : "asc";
}

/** A value as cell text: nothing for null, JSON for an object. */
export function cellText(value: unknown): string {
	if (value === null || value === undefined) return "";
	if (typeof value === "object") {
		try {
			return JSON.stringify(value);
		} catch {
			return String(value);
		}
	}
	return String(value);
}

/** A typed number, or null for empty or junk (no edit then). */
export function parseNumber(text: string): number | null {
	const t = text.trim();
	if (t === "") return null;
	const n = Number(t);
	return Number.isFinite(n) ? n : null;
}

/** The side a kind's values sit on unless a column says otherwise. */
export function defaultAlign(kind: DataTableKind): "left" | "center" | "right" {
	return kind === "number" ? "right" : kind === "bool" ? "center" : "left";
}
