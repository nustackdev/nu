// Tables in the prose editor.
//
// A GFM pipe table is a table you can type in. The cells are ordinary
// paragraphs, so marks, code and links work in them the way they do anywhere
// else in the document, and prosemirror-tables does the grid: cell selection,
// rows and columns added and removed without the table going ragged, cells
// copied and pasted as cells.
//
// What it is held to is what markdown can write back (see ./markdown.ts). No
// column widths, so no resizing. No merged cells, so no merge command is
// bound and the menu has none. The first row is the header, whatever a
// command left there: inserting a row above the header makes the new row the
// header and the old one a body row, and the normalizer below makes the
// document say so. A column has one alignment, which every cell in it
// carries, so a row added later lines up with the rest of its column.
//
// ## Moving through
//
// Tab goes to the next cell and Shift-Tab to the previous one; Tab in the
// last cell adds a row and moves into it. Enter goes down a cell, adding a
// row at the bottom, since a GFM cell has no second line to break into. A
// line typed as `| a | b |` and finished with Enter becomes a table with
// that header (./rules.ts). Mod-Enter leaves the table into a paragraph
// below it, and the arrows reach the gap before or after a table that starts
// or ends the document (the editor's gap cursor), so a table never walls the
// caret in. Whatever is pasted or dropped into a cell is flattened to one
// line first, since a cell holds one paragraph; cells copied as cells still
// paste as cells.
//
// ## The control
//
// An editable table shows the kit's row and column handles (TableHandles,
// components/ui/table-handles.tsx), the same ones a `DataTable` shows, with
// menus from the same builders in the same words: one on the table's left
// edge level with a row, opening the row's menu (insert above / below, move
// up / down, delete row), one on its top edge over a column, opening the
// column's (insert left / right, move left / right, alignment, delete
// column); both end with "Delete table". They follow the cell under the
// pointer and show while it is over the table; working from the keyboard
// (typing, arrows, Tab) they stand on the caret's cell instead, wherever the
// pointer rests, and a handle focused or a menu open holds them too. A click
// puts the caret in a cell as well, but does not hold the handles there:
// moved away, the pointer takes them along. Opening a menu from a handle puts the caret in that row or column
// first (unless the selection already spans it), so a pick is an ordinary
// command on the selection. Shift+F10 or the Menu key opens the caret row's
// menu and Alt+Shift+F10 its column's, since Tab here moves between cells.
//
// The handles are a node view's chrome, mounted with React the way a fence's
// picker is (./fence.tsx), and they follow the read-only flip the same way:
// a read-only table draws exactly what an editable one does minus the
// handles. A menu takes focus out of the document while it is open, which
// counts as leaving it, so a pick is an ordinary edit afterwards: it lands in
// the document, the quiet-moment save picks it up, and focus goes back to the
// caret when the menu closes.

import { Trash2 } from "lucide-react";
import { GapCursor } from "prosemirror-gapcursor";
import { keymap } from "prosemirror-keymap";
import { DOMSerializer, Fragment, type Node as PMNode, Slice } from "prosemirror-model";
import {
	type Command,
	type EditorState,
	Plugin,
	TextSelection,
	type Transaction,
} from "prosemirror-state";
import {
	addColumnAfter,
	addColumnBefore,
	addRow,
	addRowAfter,
	addRowBefore,
	CellSelection,
	deleteColumn,
	deleteRow,
	deleteTable,
	goToNextCell,
	isInTable,
	selectedRect,
	selectionCell,
	TableMap,
	type TableRect,
	tableEditing,
} from "prosemirror-tables";
import type {
	EditorView,
	NodeView,
	NodeViewConstructor,
	ViewMutationRecord,
} from "prosemirror-view";
import { createRef } from "react";
import { createRoot, type Root } from "react-dom/client";
import {
	type ColumnAlign,
	columnMenu,
	rowMenu,
	TABLE_HANDLE_LEAVE_DELAY,
	type TableAction,
	type TableHandleKind,
	TableHandles,
	type TableHandlesHandle,
	type TableMenuItem,
	tableMenuText,
} from "../../components/ui/table-handles";
import { watchKeyboardUse } from "../modality";
import type { Align } from "./markdown";
import type { ProseSchema } from "./schema";

/* ============================== commands ================================= */

/**
 * Set the alignment of every column the selection touches, on every cell in
 * it. Left is the default a table reads with, so it is written as no
 * alignment at all (`---`), not `:---`.
 */
export function alignColumn(align: Align): Command {
	const value = align === "left" ? null : align;
	return (state, dispatch) => {
		if (!isInTable(state)) return false;
		if (dispatch) {
			const { map, table, tableStart, left, right } = selectedRect(state);
			const tr = state.tr;
			const seen = new Set<number>();
			for (let row = 0; row < map.height; row++) {
				for (let col = left; col < right; col++) {
					const at = map.map[row * map.width + col];
					if (seen.has(at)) continue;
					seen.add(at);
					const cell = table.nodeAt(at);
					if (cell && cell.attrs.align !== value) {
						tr.setNodeMarkup(tableStart + at, undefined, { ...cell.attrs, align: value });
					}
				}
			}
			dispatch(tr);
		}
		return true;
	};
}

/** The alignment of the column the selection starts in, as the menu shows it. */
function columnAlign(state: EditorState): Align {
	if (!isInTable(state)) return null;
	const { map, table, left } = selectedRect(state);
	for (let row = 0; row < map.height; row++) {
		const align = table.nodeAt(map.map[row * map.width + left])?.attrs.align as Align;
		if (align) return align;
	}
	return null;
}

/** A new row at the bottom, the caret in its cell under column `col`. */
function appendRow(state: EditorState, col: number): Transaction {
	const rect = selectedRect(state);
	const tr = addRow(state.tr, rect, rect.map.height);
	const table = tr.doc.nodeAt(rect.tableStart - 1) as PMNode;
	let at = rect.tableStart;
	for (let i = 0; i < table.childCount - 1; i++) at += table.child(i).nodeSize;
	const row = table.child(table.childCount - 1);
	// Into the row, past `col` cells, into the cell, into its paragraph.
	at += 1;
	for (let i = 0; i < Math.min(col, row.childCount - 1); i++) at += row.child(i).nodeSize;
	return tr.setSelection(TextSelection.create(tr.doc, at + 2)).scrollIntoView();
}

/** Tab: the next cell, or a new row from the last one. */
export const nextCell: Command = (state, dispatch) => {
	if (!isInTable(state)) return false;
	if (goToNextCell(1)(state, dispatch)) return true;
	dispatch?.(appendRow(state, 0));
	return true;
};

/** Shift-Tab: the previous cell. Held at the first one rather than leaving the document. */
export const previousCell: Command = (state, dispatch) => {
	if (!isInTable(state)) return false;
	goToNextCell(-1)(state, dispatch);
	return true;
};

/**
 * Enter in a cell: the cell below, or a new row from the bottom one. With
 * text selected it only deletes it, the way Enter replaces a selection
 * anywhere; a cell has no line to break, so that is all it replaces it with.
 * Across cells it does nothing.
 */
export const cellBelow: Command = (state, dispatch) => {
	if (!isInTable(state)) return false;
	if (state.selection instanceof CellSelection) return true;
	if (!state.selection.empty) {
		dispatch?.(state.tr.deleteSelection().scrollIntoView());
		return true;
	}
	const $cell = selectionCell(state);
	const { map, tableStart } = selectedRect(state);
	const below = map.nextCell($cell.pos - tableStart, "vert", 1);
	if (below === null) {
		dispatch?.(appendRow(state, map.findCell($cell.pos - tableStart).left));
		return true;
	}
	const $below = state.doc.resolve(tableStart + below + 2);
	dispatch?.(state.tr.setSelection(TextSelection.create(state.doc, $below.end())).scrollIntoView());
	return true;
};

/**
 * prosemirror-tables' row and column deletes answer "yes" to a dry run even
 * when they would refuse (the last row, the last column), so the menu could
 * not grey them out. These ask the real question first.
 */
const deleteRowOnly: Command = (state, dispatch) => {
	if (!isInTable(state)) return false;
	const { top, bottom, map } = selectedRect(state);
	return bottom - top < map.height && deleteRow(state, dispatch);
};

const deleteColumnOnly: Command = (state, dispatch) => {
	if (!isInTable(state)) return false;
	const { left, right, map } = selectedRect(state);
	return right - left < map.width && deleteColumn(state, dispatch);
};

/**
 * An insert that takes the caret along: a row or column is added to be typed
 * into, so the caret lands in the new cell beside (or under) the one it was
 * in, rather than staying put while the table grows around it.
 */
function inserting(command: Command, at: (rect: TableRect) => [number, number]): Command {
	return (state, dispatch) => {
		if (!isInTable(state)) return false;
		if (!dispatch) return command(state);
		const rect = selectedRect(state);
		const [row, col] = at(rect);
		let tr: Transaction | null = null;
		command(state, (t) => {
			tr = t;
		});
		if (!tr) return false;
		const done = tr as Transaction;
		const table = done.doc.nodeAt(rect.tableStart - 1);
		if (table) {
			const map = TableMap.get(table);
			const cell =
				map.map[Math.min(row, map.height - 1) * map.width + Math.min(col, map.width - 1)];
			// Into the cell, into its paragraph.
			done.setSelection(TextSelection.create(done.doc, rect.tableStart + cell + 2));
		}
		dispatch(done.scrollIntoView());
		return true;
	};
}

/**
 * Mod-Enter in a table: out of it, into a fresh paragraph right below. The way out of a table that ends the document, along with
 * the gap cursor's arrows.
 */
export const exitTable: Command = (state, dispatch) => {
	const { $head } = state.selection;
	for (let d = $head.depth; d > 0; d--) {
		if ($head.node(d).type.spec.tableRole !== "table") continue;
		const after = $head.after(d);
		if (dispatch) {
			const tr = state.tr.insert(after, state.schema.nodes.paragraph.create());
			dispatch(tr.setSelection(TextSelection.create(tr.doc, after + 1)).scrollIntoView());
		}
		return true;
	}
	return false;
};

/**
 * Up from the top row or down from the bottom one, when the table is the
 * first or last thing in its parent (the document, a quote, a list item):
 * there is no text on that side to go to, so the caret goes to the gap
 * there instead, where typing starts a paragraph. prosemirror-tables would
 * otherwise keep the caret in the table, or send it to another table's cell.
 */
export function leaveTable(dir: 1 | -1): Command {
	return (state, dispatch, view) => {
		const sel = state.selection;
		if (!(sel instanceof TextSelection) || !sel.empty || !isInTable(state)) return false;
		if (view && !view.endOfTextblock(dir > 0 ? "down" : "up")) return false;
		const { map, tableStart, top, bottom } = selectedRect(state);
		if (dir > 0 ? bottom < map.height : top > 0) return false;
		const table = state.doc.nodeAt(tableStart - 1);
		if (!table) return false;
		const at = dir > 0 ? tableStart - 1 + table.nodeSize : tableStart - 1;
		const $at = state.doc.resolve(at);
		if ((dir > 0 ? $at.nodeAfter : $at.nodeBefore) !== null) return false;
		if (!$at.parent.contentMatchAt($at.index()).defaultType?.isTextblock) return false;
		dispatch?.(state.tr.setSelection(new GapCursor($at)).scrollIntoView());
		return true;
	};
}

/**
 * A slice about to land in a cell, flattened to one line. A GFM cell holds
 * one paragraph, and blocks pasted or dropped into it would otherwise spill
 * into the next cells or split the table: their text joins with spaces,
 * marks kept. `cells` says the slice really is cells (a table copied as
 * one), which prosemirror-tables pastes as cells; ProseMirror wraps plain
 * paragraphs pasted into a cell in cells of their own, so the slice alone
 * cannot tell.
 */
function flattenIntoCell(slice: Slice, view: EditorView, cells: boolean): Slice {
	const { $from } = view.state.selection;
	let inCell = false;
	for (let d = $from.depth; d > 0 && !inCell; d--) {
		const role = $from.node(d).type.spec.tableRole;
		inCell = role === "cell" || role === "header_cell";
	}
	if (!inCell || cells) return slice;
	let blocks = false;
	slice.content.forEach((node) => {
		if (!node.isInline) blocks = true;
	});
	if (!blocks) return slice;

	const { schema } = view.state;
	const inline: PMNode[] = [];
	slice.content.descendants((node) => {
		if (!node.isTextblock) return true;
		const line: PMNode[] = [];
		node.forEach((child) => {
			if (child.isText) {
				const text = (child.text ?? "").replace(/\s*\n\s*/g, " ");
				if (text) line.push(schema.text(text, child.marks));
			} else if (child.isInline) line.push(child);
		});
		if (line.length === 0) return false;
		if (inline.length > 0) inline.push(schema.text(" "));
		inline.push(...line);
		return false;
	});
	return new Slice(Fragment.from(inline), 0, 0);
}

/**
 * Move the selected rows (or columns) one step up or down (left or right):
 * the block the selection spans trades places with the row or column next
 * to it, the selection going along. GFM has no merged cells, so this is a
 * plain permutation of the table node. The normalizer then does the rest:
 * a row moved to the top becomes the header and the old header a body row,
 * and a column's cells carry their alignment with them.
 */
export function moveCells(axis: "row" | "column", dir: -1 | 1): Command {
	return (state, dispatch) => {
		if (!isInTable(state)) return false;
		const rect = selectedRect(state);
		const { map, table, tableStart } = rect;
		const row = axis === "row";
		const [lo, hi, size] = row
			? [rect.top, rect.bottom, map.height]
			: [rect.left, rect.right, map.width];
		if (dir < 0 ? lo === 0 : hi === size) return false;
		if (!dispatch) return true;

		// The new order: the block [lo, hi) one step over, its neighbour on the other side.
		const at = [...Array(size).keys()];
		const order =
			dir < 0
				? [...at.slice(0, lo - 1), ...at.slice(lo, hi), lo - 1, ...at.slice(hi)]
				: [...at.slice(0, lo), hi, ...at.slice(lo, hi), ...at.slice(hi + 1)];
		const moved: number[] = [];
		order.forEach((was, now) => {
			moved[was] = now;
		});
		const rows: PMNode[] = [];
		if (row) for (const i of order) rows.push(table.child(i));
		else {
			table.forEach((r) => {
				rows.push(r.copy(Fragment.from(order.map((i) => r.child(i)))));
			});
		}
		const next = table.copy(Fragment.from(rows));
		const nextMap = TableMap.get(next);

		// A position in a cell, to the same place in that cell where it now sits.
		const depth = state.doc.resolve(tableStart).depth;
		const place = (pos: number) => {
			const $p = state.doc.resolve(pos);
			const cellStart = $p.depth > depth ? $p.before(depth + 2) : pos;
			const { top, left } = map.findCell(cellStart - tableStart);
			const r = row ? (moved[top] ?? top) : top;
			const c = row ? left : (moved[left] ?? left);
			return tableStart + (nextMap.map[r * nextMap.width + c] ?? 0) + (pos - cellStart);
		};
		const sel = state.selection;
		const tr = state.tr.replaceWith(tableStart, tableStart + table.content.size, next.content);
		if (sel instanceof CellSelection) {
			tr.setSelection(
				CellSelection.create(tr.doc, place(sel.$anchorCell.pos), place(sel.$headCell.pos)),
			);
		} else {
			tr.setSelection(TextSelection.create(tr.doc, place(sel.anchor), place(sel.head)));
		}
		dispatch(tr.scrollIntoView());
		return true;
	};
}

/** What the menus offer. Exported so a test can run exactly what a pick runs. */
export const tableCommands = {
	addRowBefore: inserting(addRowBefore, (r) => [r.top, r.left]),
	addRowAfter: inserting(addRowAfter, (r) => [r.bottom, r.left]),
	addColumnBefore: inserting(addColumnBefore, (r) => [r.top, r.left]),
	addColumnAfter: inserting(addColumnAfter, (r) => [r.top, r.right]),
	moveRowUp: moveCells("row", -1),
	moveRowDown: moveCells("row", 1),
	moveColumnLeft: moveCells("column", -1),
	moveColumnRight: moveCells("column", 1),
	deleteRow: deleteRowOnly,
	deleteColumn: deleteColumnOnly,
	deleteTable,
	alignColumn,
};

/* ============================== normalizer =============================== */

/**
 * Keep every table in the shape markdown writes: the first row header cells,
 * the rest body cells, and each column one alignment (the first one set down
 * it, which is the one the serializer writes). Table commands are free to
 * leave a header cell in the second row or a fresh cell with no alignment;
 * this puts the document back the way it will read after a lap.
 */
function normalizer(s: ProseSchema): Plugin {
	const { tableHeader, tableCell, table: tableType } = s.nodeType;
	return new Plugin({
		appendTransaction(trs, _old, state) {
			if (!trs.some((tr) => tr.docChanged)) return null;
			const tr = state.tr;
			state.doc.descendants((node, pos) => {
				if (node.type !== tableType) return node.isBlock && !node.isTextblock;
				const rows: { cell: PMNode; at: number; col: number; head: boolean }[][] = [];
				node.forEach((row, rowOffset, r) => {
					const cells: { cell: PMNode; at: number; col: number; head: boolean }[] = [];
					let col = 0;
					row.forEach((cell, cellOffset) => {
						cells.push({ cell, at: pos + 1 + rowOffset + 1 + cellOffset, col, head: r === 0 });
						col += Number(cell.attrs.colspan) || 1;
					});
					rows.push(cells);
				});
				const aligns = new Map<number, Align>();
				for (const row of rows) {
					for (const { cell, col } of row) {
						if (!aligns.has(col) && cell.attrs.align) aligns.set(col, cell.attrs.align as Align);
					}
				}
				for (const row of rows) {
					for (const { cell, at, col, head } of row) {
						const type = head ? tableHeader : tableCell;
						const align = aligns.get(col) ?? null;
						if (cell.type !== type || cell.attrs.align !== align) {
							tr.setNodeMarkup(at, type, { ...cell.attrs, align });
						}
					}
				}
				return false;
			});
			return tr.docChanged ? tr : null;
		},
	});
}

/* ============================== the control ============================== */

/** A cell by row and column index. */
type Spot = { row: number; col: number };

/** A command as a menu action: greyed out where it would not apply. */
function action(view: EditorView, command: Command): TableAction {
	return {
		run: () => void command(view.state, view.dispatch, view),
		disabled: !command(view.state, undefined, view),
	};
}

/** Last in both menus: the table itself. */
function deleteTableItem(view: EditorView): TableMenuItem {
	return {
		type: "item",
		id: "delete-table",
		label: tableMenuText.deleteTable,
		icon: Trash2,
		danger: true,
		onSelect: () => void tableCommands.deleteTable(view.state, view.dispatch),
	};
}

/** The row menu, read off the selection: by the time it opens the caret is in the row. */
function rowItems(view: EditorView): TableMenuItem[] {
	const c = tableCommands;
	return rowMenu({
		insertAbove: action(view, c.addRowBefore),
		insertBelow: action(view, c.addRowAfter),
		moveUp: action(view, c.moveRowUp),
		moveDown: action(view, c.moveRowDown),
		remove: action(view, c.deleteRow),
		extra: [deleteTableItem(view)],
	});
}

/** The column menu, read off the selection the same way. */
function columnItems(view: EditorView): TableMenuItem[] {
	const c = tableCommands;
	return columnMenu({
		insertLeft: action(view, c.addColumnBefore),
		insertRight: action(view, c.addColumnAfter),
		moveLeft: action(view, c.moveColumnLeft),
		moveRight: action(view, c.moveColumnRight),
		align: {
			value: columnAlign(view.state) ?? "left",
			onValueChange: (next: ColumnAlign) =>
				void c.alignColumn(next)(view.state, view.dispatch, view),
		},
		remove: action(view, c.deleteColumn),
		extra: [deleteTableItem(view)],
	});
}

/* ============================== node view ================================ */

class TableView implements NodeView {
	dom: HTMLElement;
	contentDOM: HTMLElement;
	private node: PMNode;
	private readonly view: EditorView;
	private readonly getPos: () => number | undefined;
	private readonly forget: () => void;
	private readonly scroll: HTMLElement;
	private readonly control: HTMLElement;
	private readonly root: Root;
	private readonly handles = createRef<TableHandlesHandle>();
	/** Whether the handles are mounted; null until the first `sync`. */
	private editable: boolean | null = null;
	/** The cell under the pointer, while the pointer is over the table. */
	private hover: Spot | null = null;
	/** Where the pointer last was over a cell: the handles fade out there once it leaves. */
	private lastHover: Spot | null = null;
	/** The pending leave, see TABLE_HANDLE_LEAVE_DELAY. */
	private leaving: number | null = null;
	private pointerIn = false;
	/** Focus is on a handle. */
	private handleFocus = false;
	/** Working from the keyboard: only then do the handles show on the caret's cell. */
	private keyboard = false;
	private readonly unwatch: () => void;
	/** The open menu and the cell it was opened on, held while it is open. */
	private menu: { which: TableHandleKind; at: Spot } | null = null;
	/** What `sync` last drew, to skip drawing the same again on every keystroke. */
	private drawn: { sig: string; node: PMNode } | null = null;

	constructor(
		node: PMNode,
		view: EditorView,
		getPos: () => number | undefined,
		forget: () => void,
	) {
		this.node = node;
		this.view = view;
		this.getPos = getPos;
		this.forget = forget;

		// The schema's own `toDOM` for the table, so a restyled schema's recipe
		// still applies, in a box that scrolls sideways when the table is wider
		// than the page, the way a kit `Table` does.
		const spec = node.type.spec.toDOM?.(node);
		if (!spec) throw new Error("table has no toDOM");
		const { dom: table, contentDOM } = DOMSerializer.renderSpec(document, spec);
		if (!contentDOM) throw new Error("table toDOM has no content hole");
		this.contentDOM = contentDOM;

		this.scroll = document.createElement("div");
		this.scroll.setAttribute("data-table-scroll", "");
		this.scroll.appendChild(table);

		// The handles are placed in this box, outside the scrolling one, so the
		// edges they straddle do not clip them.
		this.dom = document.createElement("div");
		this.dom.setAttribute("data-slot", "prose-table");
		this.dom.className = "relative";
		this.dom.appendChild(this.scroll);

		this.control = document.createElement("div");
		this.control.contentEditable = "false";
		this.control.setAttribute("data-table-control", "");
		this.dom.appendChild(this.control);
		this.root = createRoot(this.control);

		this.dom.addEventListener("pointerover", (e) => {
			this.stay();
			this.pointerOver(e);
		});
		// Not at once: see TABLE_HANDLE_LEAVE_DELAY.
		this.dom.addEventListener("pointerleave", () => {
			this.stay();
			this.leaving = window.setTimeout(() => {
				this.leaving = null;
				this.pointerIn = false;
				if (!this.menu) this.hover = null;
				this.sync();
			}, TABLE_HANDLE_LEAVE_DELAY);
		});
		this.control.addEventListener("focusin", () => {
			this.handleFocus = true;
			this.sync();
		});
		this.control.addEventListener("focusout", (e) => {
			if (this.control.contains(e.relatedTarget as Node | null)) return;
			this.handleFocus = false;
			this.sync();
		});
		// The whole editor, not just this table: the caret arrives here by keys
		// typed anywhere in the document.
		this.unwatch = watchKeyboardUse(view.dom, (keyboard) => {
			this.keyboard = keyboard;
			this.sync();
		});
		this.sync();
	}

	update(node: PMNode): boolean {
		if (node.type !== this.node.type) return false;
		this.node = node;
		this.sync();
		return true;
	}

	private pointerOver(e: PointerEvent): void {
		if (!this.editable) return;
		this.pointerIn = true;
		const cell = (e.target as Element | null)?.closest?.("td, th") as HTMLTableCellElement | null;
		const tr = cell?.parentElement;
		if (!this.menu && cell && tr && tr.parentElement === this.contentDOM) {
			const row = [...this.contentDOM.children].indexOf(tr);
			const col = cell.cellIndex;
			if (this.hover?.row !== row || this.hover.col !== col) this.hover = { row, col };
			this.lastHover = this.hover;
		} else if (
			!this.menu &&
			!this.hover &&
			this.lastHover &&
			this.control.contains(e.target as Node)
		) {
			// Back on a handle that had faded where it stood: it stands for that cell again.
			this.hover = this.lastHover;
		}
		this.sync();
	}

	/** The cell the caret (or the selection's head) is in, when it is in this table. */
	private caretSpot(): Spot | null {
		if (!this.holdsCaret() || !isInTable(this.view.state)) return null;
		const { top, left } = selectedRect(this.view.state);
		return { row: top, col: left };
	}

	/**
	 * What the handles stand for: the open menu's cell, else the pointer's,
	 * else the caret's. Whether they show is `sync`'s call, not this one's.
	 */
	private spot(): Spot | null {
		const rest = this.keyboard ? this.caretSpot() : (this.lastHover ?? this.caretSpot());
		return this.menu?.at ?? this.hover ?? rest;
	}

	private stay(): void {
		if (this.leaving !== null) window.clearTimeout(this.leaving);
		this.leaving = null;
	}

	private rowEl(): HTMLElement | null {
		const at = this.spot();
		return at ? ((this.contentDOM.children[at.row] as HTMLElement | undefined) ?? null) : null;
	}

	private columnEl(): HTMLElement | null {
		const at = this.spot();
		const head = this.contentDOM.children[0];
		return at && head ? ((head.children[at.col] as HTMLElement | undefined) ?? null) : null;
	}

	/**
	 * Called on every editor update, focus move and pointer move over the
	 * table: the handles show on an editable table under the pointer, holding
	 * the caret while the document has focus, or with a handle focused or its
	 * menu open.
	 */
	sync(): void {
		const editable = this.view.editable;
		if (editable !== this.editable) {
			this.editable = editable;
			this.drawn = null;
			// Read-only has no handles at all, not hidden ones, and a menu open
			// when the flip came went with them.
			if (!editable) {
				this.menu = null;
				this.hover = null;
				this.handleFocus = false;
				this.root.render(null);
			}
		}
		const show =
			editable &&
			(this.menu !== null ||
				this.pointerIn ||
				this.handleFocus ||
				(this.keyboard && this.view.hasFocus() && this.holdsCaret()));
		this.dom.toggleAttribute("data-active", show);
		if (!editable) return;

		const at = this.spot();
		const head = this.node.firstChild;
		const name =
			at && head && at.col < head.childCount ? head.child(at.col).textContent.trim() : "";
		const rowLabel = at ? tableMenuText.rowHandle(String(at.row + 1)) : tableMenuText.rowHandleIdle;
		const columnLabel = at
			? tableMenuText.columnHandle(name || String(at.col + 1))
			: tableMenuText.columnHandleIdle;
		const sig = `${show}|${at?.row}|${at?.col}|${rowLabel}|${columnLabel}`;
		if (this.drawn?.sig === sig && this.drawn.node === this.node) return;
		this.drawn = { sig, node: this.node };
		this.root.render(
			<TableHandles
				ref={this.handles}
				row={() => this.rowEl()}
				column={() => this.columnEl()}
				scroller={this.scroll}
				rowItems={() => rowItems(this.view)}
				columnItems={() => columnItems(this.view)}
				rowLabel={rowLabel}
				columnLabel={columnLabel}
				visible={show}
				onOpenChange={(which) => this.menuChange(which)}
				onCloseAutoFocus={(e) => {
					e.preventDefault();
					this.view.focus();
				}}
			/>,
		);
	}

	/** A shortcut opens a menu on the caret's cell, wherever the pointer is. */
	openMenu(which: TableHandleKind): boolean {
		this.hover = null;
		this.keyboard = true;
		this.sync();
		return this.handles.current?.open(which) ?? false;
	}

	private menuChange(which: TableHandleKind | null): void {
		if (which) {
			const at = this.spot();
			if (!at) return;
			this.menu = { which, at };
			this.selectFor(which, at);
		} else this.menu = null;
		this.sync();
	}

	/**
	 * The caret into the cell a menu was opened on, so its commands act there;
	 * left alone when the selection already spans that row (or column).
	 */
	private selectFor(which: TableHandleKind, at: Spot): void {
		const pos = this.getPos();
		if (pos === undefined) return;
		const { state } = this.view;
		if (this.holdsCaret() && isInTable(state)) {
			const r = selectedRect(state);
			const inside =
				which === "row"
					? at.row >= r.top && at.row < r.bottom
					: at.col >= r.left && at.col < r.right;
			if (inside) return;
		}
		const map = TableMap.get(this.node);
		const cell = map.map[at.row * map.width + at.col];
		if (cell === undefined) return;
		// Into the table, past `cell`, into the cell, into its paragraph.
		this.view.dispatch(state.tr.setSelection(TextSelection.create(state.doc, pos + 1 + cell + 2)));
	}

	holdsCaret(): boolean {
		const pos = this.getPos();
		if (pos === undefined) return false;
		const { from, to } = this.view.state.selection;
		return from > pos && to < pos + this.node.nodeSize;
	}

	/** The handles are not document content: their clicks and keys are their own. */
	stopEvent(e: Event): boolean {
		return this.control.contains(e.target as Node);
	}

	ignoreMutation(m: ViewMutationRecord): boolean {
		return m.type !== "selection" && !this.contentDOM.contains(m.target);
	}

	destroy(): void {
		this.stay();
		this.unwatch();
		this.forget();
		// Unmounting inside a React commit warns; the view can be torn down in one.
		queueMicrotask(() => this.root.unmount());
	}
}

/* ============================== wiring =================================== */

export type ProseTables = {
	/** Grid editing, the shape normalizer, the menu keys, and the handles following focus and read-only. */
	plugins: Plugin[];
	nodeViews: Record<string, NodeViewConstructor>;
};

/** Tables for one editor. Build one per view: it tracks that view's tables. */
export function proseTables(s: ProseSchema): ProseTables {
	const live = new Set<TableView>();
	const syncAll = () => {
		for (const table of live) table.sync();
	};

	/** Whether the clipboard being parsed held table cells; see `flattenIntoCell`. */
	let clipboardCells = false;

	/** When a shortcut last opened a menu; see the `contextmenu` handler. */
	let shortcutAt = 0;
	const openMenu =
		(which: TableHandleKind): Command =>
		(state, dispatch, view) => {
			if (!view?.editable || !isInTable(state)) return false;
			const table = [...live].find((t) => t.holdsCaret());
			if (!table) return false;
			if (!dispatch) return true;
			// Armed only when a menu did open; a key that opened none is the browser's.
			if (!table.openMenu(which)) return false;
			shortcutAt = Date.now();
			return true;
		};
	// Tab moves between cells here, so these are the keyboard's way to the handles' menus.
	const menus = keymap({
		"Shift-F10": openMenu("row"),
		ContextMenu: openMenu("row"),
		"Alt-Shift-F10": openMenu("column"),
	});

	const sync = new Plugin({
		view: () => ({ update: syncAll }),
		props: {
			// Both run before the clipboard is parsed, so the last one seen
			// describes the slice `transformPasted` gets next.
			transformPastedHTML: (html) => {
				clipboardCells = /<t[dh][\s>]/i.test(html);
				return html;
			},
			transformPastedText: (text) => {
				clipboardCells = false;
				return text;
			},
			transformPasted: (slice, view) => {
				// A drag inside the editor skips the clipboard parse: the slice is
				// the dragged content itself, unwrapped, so it can speak for itself.
				const dragged = view.dragging?.slice === slice;
				let cells = clipboardCells;
				if (dragged) {
					cells = slice.content.childCount > 0;
					slice.content.forEach((node) => {
						if (!node.type.spec.tableRole) cells = false;
					});
				}
				return flattenIntoCell(slice, view, cells);
			},
			handleDOMEvents: {
				// The key that opened a menu may send the browser's own context
				// menu right after it; the table's menu is open already.
				contextmenu: (_view, e) => {
					if (Date.now() - shortcutAt > 1000) return false;
					e.preventDefault();
					return true;
				},
				// Read-only, a drag across cells is the browser's own text selection,
				// not a tinted cell selection: prosemirror-tables never sees the press.
				mousedown: (view, e) =>
					!view.editable && !!(e.target as Element | null)?.closest?.("td, th"),
				// Focus has not settled while these run; look once it has.
				focus: () => {
					queueMicrotask(syncAll);
					return false;
				},
				blur: () => {
					queueMicrotask(syncAll);
					return false;
				},
			},
		},
	});

	return {
		plugins: [sync, menus, normalizer(s), tableEditing()],
		nodeViews: {
			[s.nodeType.table.name]: (node, view, getPos) => {
				const table: TableView = new TableView(node, view, getPos, () => live.delete(table));
				live.add(table);
				return table;
			},
		},
	};
}
