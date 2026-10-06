// DataTable: a table you can work in. One tab stop, arrows between cells,
// edits in place, rows that select, sort, insert, delete and move.
//
// Design refs:
//   a11y.md        §4 grid pattern (role grid / row / gridcell / columnheader,
//                  aria-selected, aria-sort, aria-readonly), roving tabindex
//   primitives.md  §Table (built on the Table family and its recipes)
//
// ## The split
//
// The kit owns how a grid behaves, the host owns what it means. The rows are
// the host's, and so is every bit of state that outlives a render: the sort
// (`sort`) and the selection (`selected`). The kit reports intents and never
// acts on them:
//
//   onSort(column, direction)   a header click, or Enter / Space on one
//   onSelect(keys)              the whole next selection
//   onActivate(key, index, e)   a row click, or Enter on a cell that does not edit
//   onEdit(edit)                a cell's new value, typed by its column's kind
//   onAdd(index)                "a new row at index"; the host decides what is in it
//   onDelete(keys)              these rows, please
//   onMove(key, index)          this row to there (index counts rows without it)
//
// Every feature is on only when its callback is given; with none the table
// reads. An edit is a request: the cell shows the old value until the host
// hands back rows that carry the new one, and a host that refuses changes
// nothing. So a server confirms every edit and the grid never runs ahead of it.
//
// ## Keyboard
//
// Cells are one roving tab stop (`useRovingFocus` over cell keys); the header
// row joins the grid when some column sorts. Arrows move a cell, Home / End to
// the row's ends, Ctrl/Cmd + Home / End to the grid's, PageUp / PageDown ten
// rows. Enter or F2 edits a cell that edits (a bool flips, a select opens),
// Enter elsewhere activates. While editing: Enter commits, Escape cancels, both
// back on the cell; Tab / Shift+Tab commit and edit the next / previous text,
// number or select cell, wrapping rows. Space flips an editable bool, else
// selects the row (multi: toggles it); Shift + Up / Down extends a multi
// selection, Ctrl/Cmd + A takes every row. Delete / Backspace deletes the
// selection when the focused row is in it, else that row. Alt + Up / Down
// moves the row. Shift+F10 or the Menu key opens the focused row's menu,
// Alt+Shift+F10 its column's (on a header both open the column's); Escape
// closes it, back on the cell. Tab out of a cell that is not editing goes to
// the row handle, then the column handle, then "Add row", then out.
//
// ## Mouse
//
// A click focuses the cell, selects (Shift for a range, Cmd/Ctrl to toggle)
// and activates; a double click edits; a bool's checkbox flips on a click; a
// sortable header sorts. The handles (`TableHandles`) follow the cell under
// the pointer, else the focused one, and show while the pointer or the focus
// is in the table: the row handle on the left edge opens the row's menu
// (insert above / below, move up / down, delete), the column handle on the
// top edge the column's (sort ascending / descending); a handle with nothing
// to offer is not drawn. Right-click is the second way in: "Edit cell", then
// the row's menu, the same items from the same builders. With `onMove` rows
// also drag, a line marking where the drop lands. "Add row" sits under the
// table when `onAdd` is given.
//
// ## Out of scope
//
// Virtualization, pagination, merged cells, column resize, range selection of
// cells, clipboard, type-to-edit, optimistic edits, and sorting or filtering
// in the browser: the host sorts, the grid shows what it is handed.

import { ChevronDown, ChevronUp, Pencil, Plus, SquareCheck } from "lucide-react";
import type * as React from "react";
import {
	useCallback,
	useEffect,
	useImperativeHandle,
	useLayoutEffect,
	useMemo,
	useRef,
	useState,
} from "react";
import { table } from "../../lib/recipes";
import { ROVING_KEY, useRovingFocus } from "../../lib/roving";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import { Checkbox } from "./checkbox";
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "./context-menu";
import {
	type CellPos,
	cellKey,
	cellText,
	clickSelection,
	type DataTableKind,
	defaultAlign,
	deleteTargets,
	dropEdge,
	dropIndex,
	type GridDims,
	navigate,
	nextDirection,
	nextEditable,
	parseNumber,
	selectRange,
	spaceSelection,
	stepIndex,
} from "./data-table-model";
import { EmptyState } from "./empty-state";
import { InlineEdit } from "./inline-edit";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";
import {
	columnMenu,
	rowMenu,
	type TableHandleKind,
	TableHandles,
	type TableHandlesHandle,
	TableMenuContextItems,
	type TableMenuItem,
	tableMenuKey,
	tableMenuText,
} from "./table-handles";

export type { DataTableKind } from "./data-table-model";

export type DataTableColumn = {
	/** Stable id; sort and edit events name it. */
	key: string;
	/** Header text, the key when not given. */
	label?: string;
	/** How values show and edit. "text" by default. */
	kind?: DataTableKind;
	/** The choices of a "select" column. */
	options?: readonly string[];
	/** True by default when the table takes edits (`onEdit`). */
	editable?: boolean;
	/** Right for number, center for bool, left otherwise, unless given. */
	align?: "left" | "center" | "right";
	/** A CSS width hint, eg "8rem" or "30%". */
	width?: string;
	/** True by default when the table sorts (`onSort`). */
	sortable?: boolean;
};

/** One row: a stable key, and its values by column index. */
export type DataTableRow = { key: string; cells: readonly unknown[] };

export type DataTableSort = { column: string; direction: "asc" | "desc" } | null;

export type DataTableEdit = {
	key: string;
	index: number;
	column: string;
	value: unknown;
	previous: unknown;
};

export type DataTableHandle = {
	/** Move keyboard focus to a body cell. */
	focusCell: (rowKey: string, columnKey: string) => void;
};

export type DataTableProps = {
	"aria-label": string;
	columns: readonly DataTableColumn[];
	rows: readonly DataTableRow[];
	density?: "compact" | "default" | "comfortable";
	striped?: boolean;
	variant?: "default" | "borderless";
	sort?: DataTableSort;
	onSort?: (column: string, direction: "asc" | "desc") => void;
	/** "none" by default. */
	selection?: "none" | "single" | "multi";
	/** Selected row keys. */
	selected?: readonly string[];
	/** The whole next selection. */
	onSelect?: (keys: string[]) => void;
	/** A row click, or Enter on a cell that does not edit. */
	onActivate?: (key: string, index: number, e: React.KeyboardEvent | React.MouseEvent) => void;
	onEdit?: (edit: DataTableEdit) => void;
	/** A new row at `index`; the host decides what is in it. */
	onAdd?: (index: number) => void;
	onDelete?: (keys: string[]) => void;
	/** Row `key` to `index`, counted among the rows without it. */
	onMove?: (key: string, index: number) => void;
	/** Draws a cell that is not being edited; return undefined for the default look. */
	renderCell?: (value: unknown, column: DataTableColumn, row: DataTableRow) => React.ReactNode;
	/** What the body shows with no rows. */
	empty?: React.ReactNode;
	className?: string;
	ref?: React.Ref<DataTableHandle>;
};

/** A column with its defaults filled in. */
type Col = DataTableColumn & {
	kind: DataTableKind;
	label: string;
	editable: boolean;
	sortable: boolean;
	align: "left" | "center" | "right";
};

/** What the focus should land on once the host's rows come back. */
type Pending = {
	row: string;
	col: string;
	index: number;
	/** What was asked: a delete is answered once the row is gone, a move once it sits at `index`. */
	ask?: "delete" | "move";
};

const ALIGN = { left: "text-left", center: "text-center", right: "text-right" } as const;
const FLEX_ALIGN = {
	left: "justify-start",
	center: "justify-center",
	right: "justify-end",
} as const;

/** A cell by keys, as the handles stand for it: a null row is the header. */
type Spot = { row: string | null; col: string };

/** A cell's spot from its roving key (`cellKey` is JSON of the pair). */
function spotOf(key: string | null): Spot | null {
	if (key === null) return null;
	const [row, col] = JSON.parse(key) as [string | null, string];
	return { row, col };
}

/** A control inside a cell handles its own click; the cell leaves it alone. */
function onControl(e: React.SyntheticEvent): boolean {
	return (e.target as HTMLElement).closest("button, input, a, [role=checkbox]") !== null;
}

export function DataTable({
	"aria-label": label,
	columns,
	rows,
	density = "default",
	striped = false,
	variant = "default",
	sort = null,
	onSort,
	selection = "none",
	selected = [],
	onSelect,
	onActivate,
	onEdit,
	onAdd,
	onDelete,
	onMove,
	renderCell,
	empty,
	className,
	ref,
}: DataTableProps) {
	const cols = useMemo<Col[]>(
		() =>
			columns.map((c) => {
				const kind = c.kind ?? "text";
				const choices = kind !== "select" || (c.options?.length ?? 0) > 0;
				return {
					...c,
					kind,
					label: c.label ?? c.key,
					editable: onEdit !== undefined && (c.editable ?? true) && choices,
					sortable: onSort !== undefined && (c.sortable ?? true),
					align: c.align ?? defaultAlign(kind),
				};
			}),
		[columns, onEdit, onSort],
	);
	const order = useMemo(() => rows.map((r) => r.key), [rows]);
	const header = cols.some((c) => c.sortable);
	const dims: GridDims = { rows: rows.length, cols: cols.length, header };
	const multi = selection === "multi";
	const selecting = selection !== "none" && onSelect !== undefined;

	const keys = useMemo(() => {
		const out: string[] = [];
		if (header) for (const c of cols) out.push(cellKey(null, c.key));
		for (const r of rows) for (const c of cols) out.push(cellKey(r.key, c.key));
		return out;
	}, [header, cols, rows]);
	const firstSelected = rows.find((r) => selected.includes(r.key));
	const { containerRef, tabKey, setActiveKey, focusKey } = useRovingFocus(
		keys,
		firstSelected && cols[0] ? cellKey(firstSelected.key, cols[0].key) : null,
	);

	const [editing, setEditing] = useState<{ row: string; col: string } | null>(null);
	const editingRef = useRef(editing);
	editingRef.current = editing;
	const anchor = useRef<string | null>(null);
	const pending = useRef<Pending | null>(null);
	const addButton = useRef<HTMLButtonElement | null>(null);
	// Set by a cell that has a menu to offer, read by the body: a right-click
	// anywhere else (the empty state) opens no menu, not an empty one.
	const menuOffered = useRef(false);
	// The cell a right-click opened the menu on, by keys: rows may change under it.
	const [menuAt, setMenuAt] = useState<Pending | null>(null);
	const menuTarget = useRef<Pending | null>(null);
	// "Edit cell" waits for the menu to close: an editor opened under the
	// menu would lose its focus to the menu's trap and commit at once.
	const editAfterMenu = useRef(false);
	const [drag, setDrag] = useState<string | null>(null);
	const [aim, setAim] = useState<{ key: string; edge: "before" | "after" } | null>(null);

	// The handles: the cell under the pointer, whether the focus is in the
	// table, and the cell a handle's menu was opened on (held while it is open,
	// so the pointer wandering off does not move what the menu acts on).
	const box = useRef<HTMLDivElement | null>(null);
	const handles = useRef<TableHandlesHandle | null>(null);
	const [hover, setHover] = useState<Spot | null>(null);
	const [focusIn, setFocusIn] = useState(false);
	const [handleAt, setHandleAt] = useState<Spot | null>(null);
	// With its row's index then, so a delete puts the focus where the row was.
	const handleTarget = useRef<(Spot & { index: number }) | null>(null);
	// A shortcut asks for a menu: opened once the handles stand on the focused cell.
	const [shortcut, setShortcut] = useState<TableHandleKind | null>(null);
	// When a shortcut last opened a menu: the browser's own context menu event
	// that the same key may send right after opens nothing.
	const shortcutAt = useRef(0);

	const focusCell = useCallback(
		(rowKey: string, columnKey: string) => focusKey(cellKey(rowKey, columnKey)),
		[focusKey],
	);
	useImperativeHandle(ref, () => ({ focusCell }), [focusCell]);

	const focusAt = useCallback(
		(at: CellPos) => {
			const c = cols[at.col];
			if (!c) return;
			if (at.row < 0) focusKey(cellKey(null, c.key));
			else {
				const r = rows[at.row];
				if (r) focusKey(cellKey(r.key, c.key));
			}
		},
		[cols, rows, focusKey],
	);

	/** Focus a row's cell, or what now sits where the row was when it is gone. */
	const restore = useCallback(
		(p: Pending) => {
			const col = Math.max(
				0,
				cols.findIndex((c) => c.key === p.col),
			);
			const still = order.indexOf(p.row);
			if (still >= 0) focusAt({ row: still, col });
			else if (rows.length > 0) focusAt({ row: Math.min(p.index, rows.length - 1), col });
			else if (header) focusAt({ row: -1, col });
			else if (addButton.current) addButton.current.focus();
			else
				containerRef.current?.querySelector<HTMLElement>("[data-slot=data-table-empty]")?.focus();
		},
		[cols, order, rows.length, header, focusAt, containerRef],
	);

	// A delete or a move takes the focused cell's row out of the DOM, or moves
	// it, and the focus with it. Once the host's rows come back, put the focus
	// on the moved row, or on what now sits where the deleted one was; unless
	// the focus has gone somewhere else meanwhile (a menu puts it back itself).
	useLayoutEffect(() => {
		const was = editingRef.current;
		if (was && !order.includes(was.row)) setEditing(null);
		const p = pending.current;
		if (!p) return;
		pending.current = null;
		// Rows that do not answer the request (it was refused, and these came
		// from something else) leave the focus alone.
		const answered = p.ask === "delete" ? !order.includes(p.row) : order.indexOf(p.row) === p.index;
		if (!answered) return;
		const active = document.activeElement;
		const box = containerRef.current;
		if (active && active !== document.body && box && !box.contains(active)) return;
		restore(p);
	}, [rows]);

	// --- Intents ---------------------------------------------------------------

	const emitEdit = useCallback(
		(index: number, col: Col, value: unknown) => {
			const row = rows[index];
			if (!row || !onEdit) return;
			const previous = row.cells[cols.indexOf(col)];
			if (value === previous) return;
			onEdit({ key: row.key, index, column: col.key, value, previous });
		},
		[rows, cols, onEdit],
	);

	/** Start editing a cell: an editor for text, number and select, a flip for bool. */
	const startEdit = useCallback(
		(at: CellPos) => {
			const col = cols[at.col];
			const row = rows[at.row];
			if (!col?.editable || !row) return;
			if (col.kind === "bool") {
				emitEdit(at.row, col, row.cells[at.col] !== true);
				return;
			}
			setEditing({ row: row.key, col: col.key });
		},
		[cols, rows, emitEdit],
	);

	/** End the edit in flight, focus back on its cell or not. */
	const endEdit = useCallback(
		(refocus: boolean) => {
			const was = editingRef.current;
			setEditing(null);
			if (refocus && was) focusCell(was.row, was.col);
		},
		[focusCell],
	);

	/** A typed value from an editor, as the column's kind; undefined is no edit. */
	const typed = (col: Col, text: string, previous: unknown): unknown => {
		if (col.kind === "number") {
			const n = parseNumber(text);
			return n === null ? undefined : n;
		}
		return text === cellText(previous) ? undefined : text;
	};

	const commitText = (at: CellPos, text: string) => {
		const col = cols[at.col];
		const row = rows[at.row];
		if (!col || !row) return;
		const value = typed(col, text, row.cells[at.col]);
		if (value !== undefined) emitEdit(at.row, col, value);
	};

	/** Tab out of an editor: commit, then edit the next text, number or select cell. */
	const tabOn = (at: CellPos, text: string, back: boolean) => {
		commitText(at, text);
		tabFrom(at, back);
	};

	/** Edit the next / previous text, number or select cell; at the end, back on this one. */
	const tabFrom = (at: CellPos, back: boolean) => {
		const next = nextEditable(at, back, dims, (_row, c) => {
			const col = cols[c];
			return !!col?.editable && col.kind !== "bool";
		});
		const row = next ? rows[next.row] : undefined;
		const col = next ? cols[next.col] : undefined;
		if (!row || !col) {
			endEdit(true);
			return;
		}
		setActiveKey(cellKey(row.key, col.key));
		setEditing({ row: row.key, col: col.key });
	};

	const select = useCallback(
		(keys: string[]) => {
			if (selecting) onSelect?.(keys);
		},
		[selecting, onSelect],
	);

	const remove = (index: number, colKey: string) => {
		const row = rows[index];
		if (!row || !onDelete) return;
		pending.current = { row: row.key, col: colKey, index, ask: "delete" };
		onDelete(deleteTargets(selected, row.key));
	};

	const step = (index: number, colKey: string, delta: -1 | 1) => {
		const row = rows[index];
		if (!row || !onMove) return;
		const to = stepIndex(order, row.key, delta);
		if (to === null) return;
		pending.current = { row: row.key, col: colKey, index: to, ask: "move" };
		onMove(row.key, to);
	};

	const sortBy = (col: Col) => {
		if (col.sortable) onSort?.(col.key, nextDirection(sort, col.key));
	};

	// --- Menus -----------------------------------------------------------------

	/** The row menu for row `r`, built from the row features that are on. */
	const rowItems = (r: number, colKey: string): TableMenuItem[] => {
		const row = rows[r];
		if (!row) return [];
		const n = deleteTargets(selected, row.key).length;
		return rowMenu({
			insertAbove: onAdd && (() => onAdd(r)),
			insertBelow: onAdd && (() => onAdd(r + 1)),
			moveUp: onMove && { run: () => step(r, colKey, -1), disabled: r === 0 },
			moveDown: onMove && { run: () => step(r, colKey, 1), disabled: r === rows.length - 1 },
			remove: onDelete && (() => remove(r, colKey)),
			removeLabel: n > 1 ? tableMenuText.deleteRows(n) : undefined,
		});
	};

	/** The column menu: sorting, for now, when the column sorts. */
	const columnItems = (c: number): TableMenuItem[] => {
		const col = cols[c];
		if (!col?.sortable || !onSort) return [];
		return columnMenu({
			sort: {
				ascending: () => onSort(col.key, "asc"),
				descending: () => onSort(col.key, "desc"),
			},
		});
	};

	/** Open a handle's menu from the keyboard, on the focused cell. */
	const openByKey = (which: TableHandleKind) => {
		setHover(null);
		setShortcut(which);
	};

	// Once the render with the hover dropped is in, the handles stand on the
	// focused cell: open there.
	useLayoutEffect(() => {
		if (!shortcut) return;
		setShortcut(null);
		// Armed only when a menu did open: else a right-click right after is its own.
		if (handles.current?.open(shortcut)) shortcutAt.current = Date.now();
	}, [shortcut]);

	// --- Keyboard ------------------------------------------------------------

	const onHeadKeyDown = (e: React.KeyboardEvent, c: number) => {
		const col = cols[c];
		if (!col) return;
		// A header has no row: both shortcuts open its column's menu.
		if (tableMenuKey(e)) {
			e.preventDefault();
			openByKey("column");
			return;
		}
		const mod = e.ctrlKey || e.metaKey;
		if (e.altKey || e.shiftKey || (mod && e.key !== "Home" && e.key !== "End")) return;
		const to = navigate(e.key, mod, { row: -1, col: c }, dims);
		if (to) {
			e.preventDefault();
			focusAt(to);
			return;
		}
		if ((e.key === "Enter" || e.key === " ") && col.sortable) {
			e.preventDefault();
			sortBy(col);
		}
	};

	const onCellKeyDown = (e: React.KeyboardEvent, r: number, c: number) => {
		const row = rows[r];
		const col = cols[c];
		if (!row || !col) return;
		pending.current = null;
		const menu = tableMenuKey(e);
		if (menu) {
			e.preventDefault();
			openByKey(menu);
			return;
		}
		const mod = e.ctrlKey || e.metaKey;
		const at = { row: r, col: c };

		// Cmd/Ctrl takes Home, End and A; any other chord (Cmd+Left is the
		// browser's Back on a Mac) passes through untouched.
		if (mod) {
			if (e.altKey || e.shiftKey) return;
			if (e.key === "Home" || e.key === "End") {
				const to = navigate(e.key, true, at, dims);
				if (to) {
					e.preventDefault();
					focusAt(to);
				}
			} else if ((e.key === "a" || e.key === "A") && multi && selecting) {
				e.preventDefault();
				select([...order]);
			}
			return;
		}

		if (e.altKey) {
			if ((e.key === "ArrowUp" || e.key === "ArrowDown") && onMove) {
				e.preventDefault();
				step(r, col.key, e.key === "ArrowUp" ? -1 : 1);
			}
			return;
		}
		if (e.shiftKey && multi && (e.key === "ArrowUp" || e.key === "ArrowDown")) {
			e.preventDefault();
			const to = navigate(e.key, false, at, { ...dims, header: false });
			const target = to ? rows[to.row] : undefined;
			if (!to || !target) return;
			if (anchor.current === null || !order.includes(anchor.current)) anchor.current = row.key;
			focusAt(to);
			select(selectRange(order, anchor.current, target.key));
			return;
		}
		const to = e.shiftKey ? null : navigate(e.key, false, at, dims);
		if (to) {
			e.preventDefault();
			focusAt(to);
			return;
		}
		switch (e.key) {
			case "Enter":
			case "F2":
				if (col.editable) {
					e.preventDefault();
					startEdit(at);
				} else if (e.key === "Enter" && onActivate) {
					e.preventDefault();
					onActivate(row.key, r, e);
				}
				break;
			case " ":
				if (col.editable && col.kind === "bool") {
					e.preventDefault();
					startEdit(at);
				} else if (selecting) {
					e.preventDefault();
					anchor.current = row.key;
					select(spaceSelection(selection, selected, row.key));
				}
				break;
			case "Delete":
			case "Backspace":
				if (onDelete) {
					e.preventDefault();
					remove(r, col.key);
				}
				break;
			default:
				break;
		}
	};

	// --- Mouse ---------------------------------------------------------------

	const onCellClick = (e: React.MouseEvent<HTMLElement>, r: number) => {
		const row = rows[r];
		if (!row) return;
		pending.current = null;
		// Keep the keyboard on the cell, so the arrows work next.
		const el = e.currentTarget;
		if (!el.contains(document.activeElement)) el.focus({ preventScroll: true });
		if (onControl(e)) return;
		if (selecting) {
			const range = e.shiftKey && multi;
			const toggle = (e.metaKey || e.ctrlKey) && multi;
			const next = clickSelection(selection, selected, order, row.key, anchor.current, {
				range,
				toggle,
			});
			// A click that changes nothing (a second click of a double click, or a
			// click on the row already selected) asks for nothing.
			const same = next.length === selected.length && next.every((k) => selected.includes(k));
			if (!same) select(next);
			if (!range || anchor.current === null || !order.includes(anchor.current)) {
				anchor.current = row.key;
			}
		}
		onActivate?.(row.key, r, e);
	};

	/** The right-click menu: edit the cell, then the row's menu. */
	const menuItems = (at: CellPos): TableMenuItem[] | null => {
		const col = cols[at.col];
		const row = rows[at.row];
		if (!col || !row) return null;
		const items: TableMenuItem[] = [];
		if (col.editable) {
			const bool = col.kind === "bool";
			items.push({
				type: "item",
				id: "edit",
				label: bool ? "Toggle" : "Edit cell",
				icon: bool ? SquareCheck : Pencil,
				onSelect: () => {
					if (bool) startEdit(at);
					else editAfterMenu.current = true;
				},
			});
		}
		const more = rowItems(at.row, col.key);
		if (items.length > 0 && more.length > 0)
			items.push({ type: "separator", id: "edit-separator" });
		items.push(...more);
		return items.length ? items : null;
	};

	const onCellContextMenu = (e: React.MouseEvent<HTMLElement>, r: number, c: number) => {
		const row = rows[r];
		const col = cols[c];
		if (!row || !col) return;
		pending.current = null;
		// The context menu event a menu shortcut sends after it: the shortcut's
		// own menu is open already, so this one opens nothing.
		if (Date.now() - shortcutAt.current < 1000) return;
		if (!menuItems({ row: r, col: c })) return;
		menuOffered.current = true;
		e.currentTarget.focus({ preventScroll: true });
		if (selecting && !selected.includes(row.key)) {
			anchor.current = row.key;
			select(clickSelection(selection, selected, order, row.key, null));
		}
		menuTarget.current = { row: row.key, col: col.key, index: r };
		editAfterMenu.current = false;
		setMenuAt(menuTarget.current);
	};

	// --- Drag ----------------------------------------------------------------

	const dragProps = (
		key: string,
	): React.HTMLAttributes<HTMLTableRowElement> & {
		draggable?: boolean;
	} => {
		if (!onMove || editing?.row === key) return {};
		return {
			draggable: true,
			onDragStart: (e) => {
				e.dataTransfer.effectAllowed = "move";
				e.dataTransfer.setData("text/plain", key);
				pending.current = null;
				setDrag(key);
			},
			onDragEnd: () => {
				setDrag(null);
				setAim(null);
			},
			onDragOver: (e) => {
				if (!drag || drag === key) {
					if (aim) setAim(null);
					return;
				}
				e.preventDefault();
				e.dataTransfer.dropEffect = "move";
				const box = e.currentTarget.getBoundingClientRect();
				const edge = dropEdge(box.top, box.height, e.clientY);
				if (aim?.key !== key || aim.edge !== edge) setAim({ key, edge });
			},
			onDragLeave: (e) => {
				if (!e.currentTarget.contains(e.relatedTarget as Node | null) && aim?.key === key) {
					setAim(null);
				}
			},
			onDrop: (e) => {
				if (!drag) return;
				e.preventDefault();
				const box = e.currentTarget.getBoundingClientRect();
				const to = dropIndex(order, drag, key, dropEdge(box.top, box.height, e.clientY));
				setDrag(null);
				setAim(null);
				if (to !== null) onMove(drag, to);
			},
		};
	};

	// Drop the drag marks if the rows change under a drag.
	useEffect(() => {
		if (drag && !order.includes(drag)) setDrag(null);
	}, [order, drag]);

	// --- Cells ---------------------------------------------------------------

	/** A row's name for a control's label: its first cell's text, or its key. */
	const rowName = (row: DataTableRow) => {
		const first = cols[0]?.kind === "bool" ? "" : cellText(row.cells[0]);
		return first !== "" ? first : row.key;
	};

	const display = (value: unknown, col: Col, row: DataTableRow, r: number): React.ReactNode => {
		const custom = renderCell?.(value, col, row);
		if (custom !== undefined) return custom;
		if (col.kind === "bool") {
			return (
				<Checkbox
					checked={value === true}
					disabled={!col.editable}
					tabIndex={-1}
					aria-label={`${col.label}, ${rowName(row)}`}
					className="align-middle disabled:cursor-default"
					// No focus on a press: the cell keeps it, and the arrows with it.
					onMouseDown={(e) => e.preventDefault()}
					onCheckedChange={() => emitEdit(r, col, value !== true)}
				/>
			);
		}
		return cellText(value);
	};

	const editor = (value: unknown, col: Col, at: CellPos, rowKey: string, label: string) => {
		if (col.kind === "select") {
			const current = cellText(value);
			return (
				<Select
					open
					value={current === "" ? undefined : current}
					onValueChange={(v) => {
						emitEdit(at.row, col, v);
					}}
					onOpenChange={(open) => {
						if (!open) endEdit(false);
					}}
				>
					<SelectTrigger
						size="sm"
						variant="ghost"
						tabIndex={-1}
						aria-label={label}
						className={cn(table.editor, table.editorField, table.editorPad[density], "w-full")}
					>
						<SelectValue />
					</SelectTrigger>
					<SelectContent
						// Radix keeps Tab inside an open list; here it moves the edit on, as
						// it does from a text editor. A pick was already sent; leaving is no edit.
						onKeyDown={(e) => {
							if (e.key !== "Tab") return;
							e.preventDefault();
							e.stopPropagation();
							tabFrom(at, e.shiftKey);
						}}
						// The list is gone by now, and the trigger with it: back to the cell.
						onCloseAutoFocus={(e) => {
							e.preventDefault();
							if (!editingRef.current) restore({ row: rowKey, col: col.key, index: at.row });
						}}
					>
						{(col.options ?? [])
							.filter((o) => o !== "")
							.map((o) => (
								<SelectItem key={o} value={o}>
									{o}
								</SelectItem>
							))}
					</SelectContent>
				</Select>
			);
		}
		return (
			<div className={table.editor}>
				<InlineEdit
					initial={cellText(value)}
					label={label}
					inputMode={col.kind === "number" ? "decimal" : undefined}
					className={cn(
						table.editorField,
						table.editorPad[density],
						col.kind === "number" && "tabular-nums",
						ALIGN[col.align],
					)}
					onCommit={(text, how) => {
						commitText(at, text);
						endEdit(how === "enter");
					}}
					onCancel={() => endEdit(true)}
					onTab={(text, back) => tabOn(at, text, back)}
				/>
			</div>
		);
	};

	const hasMenu =
		onAdd !== undefined ||
		onMove !== undefined ||
		onDelete !== undefined ||
		cols.some((c) => c.editable);

	const body = (
		<TableBody
			onContextMenu={
				hasMenu
					? (e) => {
							// Runs before the menu's own handler: no cell offered one, so no menu.
							if (!menuOffered.current) e.preventDefault();
							menuOffered.current = false;
						}
					: undefined
			}
		>
			{rows.length === 0 ? (
				<TableRow role="row" aria-rowindex={2} className="hover:bg-transparent">
					<TableCell
						role="gridcell"
						data-slot="data-table-empty"
						colSpan={Math.max(1, cols.length)}
						// With no header in the grid and no rows, the grid keeps its one
						// tab stop here.
						tabIndex={header ? undefined : 0}
						className={cn("p-0", table.gridCell)}
					>
						{empty ?? <EmptyState size="sm">No rows</EmptyState>}
					</TableCell>
				</TableRow>
			) : null}
			{rows.map((row, r) => {
				const isSelected = selected.includes(row.key);
				const aimed = aim?.key === row.key ? aim.edge : null;
				return (
					<TableRow
						key={row.key}
						role="row"
						data-row={row.key}
						aria-rowindex={r + 2}
						aria-selected={selection !== "none" ? isSelected : undefined}
						selected={isSelected}
						className={cn(drag === row.key && "opacity-50")}
						{...dragProps(row.key)}
					>
						{cols.map((col, c) => {
							const key = cellKey(row.key, col.key);
							const value = row.cells[c];
							const isEditing = editing?.row === row.key && editing.col === col.key;
							return (
								<TableCell
									key={col.key}
									role="gridcell"
									tabIndex={key === tabKey ? 0 : -1}
									{...{ [ROVING_KEY]: key }}
									aria-readonly={col.editable ? undefined : true}
									data-editing={isEditing || undefined}
									className={cn(
										table.gridCell,
										ALIGN[col.align],
										col.kind === "number" && "tabular-nums",
										isEditing && "relative",
										multi && "select-none",
										aimed === "before" && table.dropBefore,
										aimed === "after" && table.dropAfter,
									)}
									onFocus={(e) => {
										if (e.target === e.currentTarget) setActiveKey(key);
									}}
									onKeyDown={(e) => {
										if (e.target === e.currentTarget) onCellKeyDown(e, r, c);
									}}
									onClick={(e) => onCellClick(e, r)}
									onDoubleClick={(e) => {
										if (!onControl(e) && col.kind !== "bool") startEdit({ row: r, col: c });
									}}
									onContextMenu={hasMenu ? (e) => onCellContextMenu(e, r, c) : undefined}
								>
									{isEditing ? (
										<>
											{/* Holds the column's width while the editor lies over the cell. */}
											<span aria-hidden="true" className="invisible">
												{cellText(value) || " "}
											</span>
											{editor(value, col, { row: r, col: c }, row.key, `Edit ${col.label}`)}
										</>
									) : (
										display(value, col, row, r)
									)}
								</TableCell>
							);
						})}
					</TableRow>
				);
			})}
		</TableBody>
	);

	// --- Handles -------------------------------------------------------------

	// What the handles stand for: the cell a menu is open on, else the one
	// under the pointer, else the focused one.
	const spot = handleAt ?? hover ?? spotOf(tabKey);
	const spotRow = spot?.row != null ? order.indexOf(spot.row) : -1;
	const spotCol = spot ? cols.findIndex((c) => c.key === spot.col) : -1;
	const handleRow = spotRow >= 0 ? rows[spotRow] : undefined;
	const handleCol = spotCol >= 0 ? cols[spotCol] : undefined;

	const pointerOver = (e: PointerEvent) => {
		if (handleAt || drag) return;
		const target = e.target as Element;
		const td = target.closest?.("td, th") as HTMLTableCellElement | null;
		if (!td || !box.current?.contains(td)) return;
		const tr = td.parentElement as HTMLElement | null;
		const col = cols[td.cellIndex];
		if (!tr || !col) return;
		const row = tr.dataset.row ?? null;
		// The empty state's row stands for no row and no column.
		if (row === null && !tr.closest("thead")) return;
		if (hover?.row !== row || hover.col !== col.key) setHover({ row, col: col.key });
	};
	const onPointer = useRef(pointerOver);
	onPointer.current = pointerOver;

	// Listened for natively: the boxes are layout, not controls, and the menus
	// portalled out of them are none of their business. The pointer counts
	// over the table and its handles; the focus anywhere in the component, so
	// Shift+Tab back from "Add row" finds the handles there.
	useEffect(() => {
		const el = box.current;
		const all = containerRef.current;
		if (!el || !all) return;
		const over = (e: PointerEvent) => onPointer.current(e);
		const leave = () => setHover(null);
		const focusin = () => setFocusIn(true);
		const focusout = (e: FocusEvent) => {
			if (!all.contains(e.relatedTarget as Node | null)) setFocusIn(false);
		};
		el.addEventListener("pointerover", over);
		el.addEventListener("pointerleave", leave);
		all.addEventListener("focusin", focusin);
		all.addEventListener("focusout", focusout);
		return () => {
			el.removeEventListener("pointerover", over);
			el.removeEventListener("pointerleave", leave);
			all.removeEventListener("focusin", focusin);
			all.removeEventListener("focusout", focusout);
		};
	}, [containerRef]);

	/** Back to the cell a handle's menu was opened on, or where its row was. */
	const backFromHandle = () => {
		const at = handleTarget.current;
		handleTarget.current = null;
		if (!at) return;
		if (at.row !== null) {
			restore({ row: at.row, col: at.col, index: at.index });
		} else if (header) focusKey(cellKey(null, at.col));
		else if (tabKey) focusKey(tabKey);
	};

	const handleEls = (
		<TableHandles
			ref={handles}
			row={() =>
				handleRow
					? ([...(box.current?.querySelectorAll<HTMLElement>("tbody > tr[data-row]") ?? [])].find(
							(tr) => tr.dataset.row === handleRow.key,
						) ?? null)
					: null
			}
			column={() =>
				handleCol
					? (box.current?.querySelectorAll<HTMLElement>("thead > tr > th")[spotCol] ?? null)
					: null
			}
			scroller={() => box.current?.querySelector<HTMLElement>(":scope > div") ?? null}
			// Read when the menu opens; drawn whenever a row feature is on, hidden
			// while no row is active (the header, say), so the tab order holds still.
			rowItems={
				onAdd || onMove || onDelete
					? () => (handleRow && handleCol ? rowItems(spotRow, handleCol.key) : [])
					: []
			}
			columnItems={handleCol ? columnItems(spotCol) : []}
			rowLabel={
				handleRow ? tableMenuText.rowHandle(rowName(handleRow)) : tableMenuText.rowHandleIdle
			}
			columnLabel={
				handleCol ? tableMenuText.columnHandle(handleCol.label) : tableMenuText.columnHandleIdle
			}
			visible={hover !== null || focusIn}
			onOpenChange={(which) => {
				if (which) {
					pending.current = null;
					handleTarget.current = spot && { ...spot, index: Math.max(0, spotRow) };
					setHandleAt(spot);
				} else setHandleAt(null);
			}}
			onCloseAutoFocus={(e) => {
				e.preventDefault();
				backFromHandle();
			}}
		/>
	);

	return (
		<div
			ref={containerRef}
			data-slot="data-table"
			className={cn("flex min-w-0 flex-col items-start gap-1.5", className)}
		>
			{/* The box the handles sit in: outside the sideways scroll, so they are not clipped. */}
			<div ref={box} className="relative w-full">
				<Table
					role="grid"
					aria-label={label}
					aria-rowcount={Math.max(1, rows.length) + 1}
					aria-multiselectable={multi ? true : undefined}
					variant={variant}
					density={density}
					striped={striped}
				>
					<TableHeader>
						<TableRow role="row" aria-rowindex={1} className="hover:bg-transparent">
							{cols.map((col, c) => {
								const active = sort?.column === col.key ? sort.direction : null;
								const key = cellKey(null, col.key);
								return (
									<TableHead
										key={col.key}
										role="columnheader"
										style={col.width ? { width: col.width } : undefined}
										aria-sort={
											col.sortable
												? active === "asc"
													? "ascending"
													: active === "desc"
														? "descending"
														: "none"
												: undefined
										}
										{...(header
											? {
													tabIndex: key === tabKey ? 0 : -1,
													[ROVING_KEY]: key,
													onFocus: () => setActiveKey(key),
													onKeyDown: (e: React.KeyboardEvent) => onHeadKeyDown(e, c),
												}
											: {})}
										onClick={
											header
												? (e: React.MouseEvent<HTMLElement>) => {
														e.currentTarget.focus({ preventScroll: true });
														sortBy(col);
													}
												: undefined
										}
										className={cn(
											ALIGN[col.align],
											header && table.gridCell,
											col.sortable && "cursor-pointer select-none hover:text-text-primary",
											active && "text-text-primary",
										)}
									>
										<span className={cn("inline-flex items-center gap-1", FLEX_ALIGN[col.align])}>
											{col.label}
											{active === "asc" ? (
												<ChevronUp aria-hidden="true" className="size-3.5" />
											) : null}
											{active === "desc" ? (
												<ChevronDown aria-hidden="true" className="size-3.5" />
											) : null}
										</span>
									</TableHead>
								);
							})}
						</TableRow>
					</TableHeader>
					{hasMenu ? (
						<ContextMenu
							onOpenChange={(open) => {
								if (!open) setMenuAt(null);
							}}
						>
							<ContextMenuTrigger asChild>{body}</ContextMenuTrigger>
							<ContextMenuContent
								className="min-w-48"
								onCloseAutoFocus={(e) => {
									// Back to the cell, or where its row was if a delete or a
									// move took it away; then the edit "Edit cell" asked for.
									e.preventDefault();
									const at = menuTarget.current;
									if (!at) return;
									restore(at);
									if (editAfterMenu.current) {
										editAfterMenu.current = false;
										const row = order.indexOf(at.row);
										const col = cols.findIndex((c) => c.key === at.col);
										if (row >= 0 && col >= 0) startEdit({ row, col });
									}
								}}
							>
								{menuAt && order.includes(menuAt.row) ? (
									<TableMenuContextItems
										items={
											menuItems({
												row: order.indexOf(menuAt.row),
												col: Math.max(
													0,
													cols.findIndex((c) => c.key === menuAt.col),
												),
											}) ?? []
										}
									/>
								) : null}
							</ContextMenuContent>
						</ContextMenu>
					) : (
						body
					)}
				</Table>
				{handleEls}
			</div>
			{onAdd ? (
				<Button
					ref={addButton}
					variant="ghost"
					size="sm"
					onClick={() => {
						pending.current = null;
						onAdd(rows.length);
					}}
				>
					<Plus />
					Add row
				</Button>
			) : null}
		</div>
	);
}
