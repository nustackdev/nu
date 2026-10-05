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
// The table the caret is in shows one button in its corner, the kit's
// IconButton, opening the kit's DropdownMenu: rows, columns, alignment,
// delete. It is a node view's chrome, mounted with React the way a fence's
// picker is (./fence.tsx), and it follows the read-only flip the same way, so
// a read-only table draws exactly what an editable one does minus the button.
// The menu takes focus out of the document while it is open, which counts as
// leaving it, so a pick is an ordinary edit afterwards: it lands in the
// document, the quiet-moment save picks it up, and focus goes back to the
// caret when the menu closes.

import {
	BetweenHorizontalEnd,
	BetweenHorizontalStart,
	BetweenVerticalEnd,
	BetweenVerticalStart,
	Ellipsis,
	Trash2,
} from "lucide-react";
import { GapCursor } from "prosemirror-gapcursor";
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
import { useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { IconButton } from "../../components/ui/icon-button";
import { cn } from "../utils";
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

/** What the menu offers. Exported so a test can run exactly what a pick runs. */
export const tableCommands = {
	addRowBefore: inserting(addRowBefore, (r) => [r.top, r.left]),
	addRowAfter: inserting(addRowAfter, (r) => [r.bottom, r.left]),
	addColumnBefore: inserting(addColumnBefore, (r) => [r.top, r.left]),
	addColumnAfter: inserting(addColumnAfter, (r) => [r.top, r.right]),
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

type Icon = typeof Trash2;

const INSERTS: [string, Icon, Command][] = [
	["Insert row above", BetweenHorizontalStart, tableCommands.addRowBefore],
	["Insert row below", BetweenHorizontalEnd, tableCommands.addRowAfter],
	["Insert column left", BetweenVerticalStart, tableCommands.addColumnBefore],
	["Insert column right", BetweenVerticalEnd, tableCommands.addColumnAfter],
];

// No icons here: the radio dot sits where an item's icon does, so the labels line up.
const ALIGNS: [string, Align & string][] = [
	["Align left", "left"],
	["Align center", "center"],
	["Align right", "right"],
];

const DELETES: [string, Command][] = [
	["Delete row", tableCommands.deleteRow],
	["Delete column", tableCommands.deleteColumn],
	["Delete table", tableCommands.deleteTable],
];

type ControlProps = {
	view: EditorView;
	onOpenChange: (open: boolean) => void;
};

function TableMenu({ view, onOpenChange }: ControlProps) {
	// Re-read on open: what applies depends on where the caret is now.
	const [, setTick] = useState(0);
	const run = (command: Command) => {
		command(view.state, view.dispatch, view);
	};
	const can = (command: Command) => command(view.state, undefined, view);
	const align = columnAlign(view.state) ?? "left";
	return (
		<DropdownMenu
			modal={false}
			onOpenChange={(open) => {
				if (open) setTick((t) => t + 1);
				onOpenChange(open);
			}}
		>
			<DropdownMenuTrigger asChild>
				<IconButton
					variant="secondary"
					size="xs"
					aria-label="Table options"
					// Opens on press; keeping the press from moving focus keeps the caret.
					onMouseDown={(e) => e.preventDefault()}
				>
					<Ellipsis />
				</IconButton>
			</DropdownMenuTrigger>
			<DropdownMenuContent
				align="end"
				className="w-48"
				onCloseAutoFocus={(e) => {
					e.preventDefault();
					view.focus();
				}}
			>
				{INSERTS.map(([label, Icon, command]) => (
					<DropdownMenuItem key={label} disabled={!can(command)} onSelect={() => run(command)}>
						<Icon />
						{label}
					</DropdownMenuItem>
				))}
				<DropdownMenuSeparator />
				<DropdownMenuRadioGroup
					value={align}
					onValueChange={(next) => run(tableCommands.alignColumn(next as Align))}
				>
					{ALIGNS.map(([label, value]) => (
						<DropdownMenuRadioItem key={value} value={value}>
							{label}
						</DropdownMenuRadioItem>
					))}
				</DropdownMenuRadioGroup>
				<DropdownMenuSeparator />
				{DELETES.map(([label, command]) => (
					<DropdownMenuItem
						key={label}
						variant={command === tableCommands.deleteTable ? "danger" : "default"}
						disabled={!can(command)}
						onSelect={() => run(command)}
					>
						<Trash2 />
						{label}
					</DropdownMenuItem>
				))}
			</DropdownMenuContent>
		</DropdownMenu>
	);
}

/* ============================== node view ================================ */

class TableView implements NodeView {
	dom: HTMLElement;
	contentDOM: HTMLElement;
	private node: PMNode;
	private readonly view: EditorView;
	private readonly getPos: () => number | undefined;
	private readonly forget: () => void;
	private readonly control: HTMLElement;
	private readonly root: Root;
	/** The menu is open: the control stays while focus is in it. */
	private open = false;
	/** Whether the control is mounted; null until the first `sync`. */
	private editable: boolean | null = null;
	/** What `sync` last drew; null until the first one. */
	private shown: boolean | null = null;

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

		const scroll = document.createElement("div");
		scroll.setAttribute("data-table-scroll", "");
		scroll.appendChild(table);

		this.dom = document.createElement("div");
		this.dom.setAttribute("data-slot", "prose-table");
		this.dom.appendChild(scroll);

		this.control = document.createElement("div");
		this.control.contentEditable = "false";
		this.control.setAttribute("data-table-control", "");
		this.dom.appendChild(this.control);
		this.root = createRoot(this.control);
		this.sync();
	}

	update(node: PMNode): boolean {
		if (node.type !== this.node.type) return false;
		this.node = node;
		this.sync();
		return true;
	}

	/**
	 * Called on every editor update and on focus moving: the control shows on
	 * an editable table holding the caret while the document has focus (or
	 * its own menu does).
	 */
	sync(): void {
		const editable = this.view.editable;
		if (editable !== this.editable) {
			this.editable = editable;
			// Read-only has no control at all, not a hidden one, and a menu
			// open when the flip came went with it.
			if (!editable) this.open = false;
			this.root.render(
				editable ? (
					<TableMenu
						view={this.view}
						onOpenChange={(open) => {
							this.open = open;
							this.sync();
						}}
					/>
				) : null,
			);
		}
		const show = editable && (this.open || (this.view.hasFocus() && this.holdsCaret()));
		if (show === this.shown) return;
		this.shown = show;
		this.dom.toggleAttribute("data-active", show);
		// Hidden is `invisible` as well, so the button is out of the tab order too.
		this.control.className = cn(
			"absolute -top-2.5 -right-2.5 z-10 transition-opacity duration-fast",
			show ? "opacity-100" : "invisible opacity-0",
		);
	}

	private holdsCaret(): boolean {
		const pos = this.getPos();
		if (pos === undefined) return false;
		const { from, to } = this.view.state.selection;
		return from > pos && to < pos + this.node.nodeSize;
	}

	/** The control is not document content: its clicks and keys are its own. */
	stopEvent(e: Event): boolean {
		return this.control.contains(e.target as Node);
	}

	ignoreMutation(m: ViewMutationRecord): boolean {
		return m.type !== "selection" && !this.contentDOM.contains(m.target);
	}

	destroy(): void {
		this.forget();
		// Unmounting inside a React commit warns; the view can be torn down in one.
		queueMicrotask(() => this.root.unmount());
	}
}

/* ============================== wiring =================================== */

export type ProseTables = {
	/** Grid editing, the shape normalizer, and the control following focus and read-only. */
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
		plugins: [sync, normalizer(s), tableEditing()],
		nodeViews: {
			[s.nodeType.table.name]: (node, view, getPos) => {
				const table: TableView = new TableView(node, view, getPos, () => live.delete(table));
				live.add(table);
				return table;
			},
		},
	};
}
