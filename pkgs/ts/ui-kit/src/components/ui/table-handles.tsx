// TableHandles: the row and column handles a table shows under the pointer.
//
// Design refs:
//   primitives.md  §DropdownMenu, §ContextMenu (the menus these open)
//   a11y.md        §3 menus (Shift+F10 / the Menu key), §4 named icon buttons
//
// A right-click menu is invisible until you know it is there. A handle is a
// button you can see: one on the table's left edge, level with the row under
// the pointer (or the focused one), and one on its top edge, over that row's
// column. Each opens the menu of what can be done to that row or column. The
// kit's `DataTable` and the markdown editor's tables mount the same handles
// with menus from the same builders, so the two read, look and answer the
// keyboard alike.
//
// ## The menu model
//
// `TableMenuItem` is one item of a handle's menu: an action, a radio choice, a
// submenu or a separator. `rowMenu` and `columnMenu` hold the wording and the
// grouping: a host hands them the actions it has, as callbacks (or
// `{ run, disabled }`), and an action it leaves out is an item not shown;
// empty groups drop out with their separators. The words are exported
// (`tableMenuText`), so tests can hold both tables to them. A host renders
// the list in a handle's dropdown (`TableHandles` does) or in a context menu
// (`TableMenuContextItems`), so a right-click offers the same items in the
// same words.
//
// ## The handles
//
// Two kit IconButtons, each a DropdownMenu trigger, absolutely placed in the
// nearest positioned ancestor. That box must sit outside the table's
// sideways-scroll box, or the handles straddling its edges would be clipped.
// The host says which row (`<tr>`) and which column (its header cell) the
// handles stand for, and whether they show (`visible`); the handles measure
// themselves onto those, again when the table scrolls sideways or changes
// size. A column scrolled out of sight hides its handle. Hidden is
// `invisible`, so a hidden handle is no tab stop. While a menu is open both
// stay shown. The looks are the `tableHandle` recipe (lib/recipes.ts).
//
// ## Keyboard
//
// Shift+F10 and the Menu key open the row menu, Alt+Shift+F10 the column menu
// (`tableMenuKey` reads a key event the same way for every host; the host
// calls `open` on the handle). The arrows move in the menu, Escape closes it;
// where focus goes then is the host's (`onCloseAutoFocus`), the cell or caret
// the menu was opened from.

import {
	ArrowDown,
	ArrowDownWideNarrow,
	ArrowLeft,
	ArrowRight,
	ArrowUp,
	ArrowUpNarrowWide,
	BetweenHorizontalEnd,
	BetweenHorizontalStart,
	BetweenVerticalEnd,
	BetweenVerticalStart,
	GripHorizontal,
	GripVertical,
	type LucideIcon,
	Pencil,
	Shapes,
	Trash2,
} from "lucide-react";
import type * as React from "react";
import {
	useCallback,
	useEffect,
	useImperativeHandle,
	useLayoutEffect,
	useRef,
	useState,
} from "react";
import { tableHandle } from "../../lib/recipes";
import { cn } from "../../lib/utils";
import {
	ContextMenuItem,
	ContextMenuRadioGroup,
	ContextMenuRadioItem,
	ContextMenuSeparator,
	ContextMenuSub,
	ContextMenuSubContent,
	ContextMenuSubTrigger,
} from "./context-menu";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuSeparator,
	DropdownMenuSub,
	DropdownMenuSubContent,
	DropdownMenuSubTrigger,
	DropdownMenuTrigger,
} from "./dropdown-menu";
import { IconButton } from "./icon-button";

/* ================================ model ================================== */

export type TableMenuItem =
	| {
			type: "item";
			id: string;
			label: string;
			icon?: LucideIcon;
			danger?: boolean;
			disabled?: boolean;
			onSelect: () => void;
	  }
	| {
			type: "radio";
			id: string;
			value: string;
			options: readonly { value: string; label: string }[];
			onValueChange: (value: string) => void;
	  }
	| { type: "sub"; id: string; label: string; icon?: LucideIcon; items: readonly TableMenuItem[] }
	| { type: "separator"; id: string };

/** An action a host offers: a callback, or one that is there but greyed out. */
export type TableAction = (() => void) | { run: () => void; disabled?: boolean };

/** A one-of-many setting: the current value and what a pick does. */
export type TableChoice<V extends string = string> = {
	value: V;
	onValueChange: (value: V) => void;
};

/** Every word the handles and their menus say, one place for both tables. */
export const tableMenuText = {
	insertRowAbove: "Insert row above",
	insertRowBelow: "Insert row below",
	moveRowUp: "Move row up",
	moveRowDown: "Move row down",
	deleteRow: "Delete row",
	deleteRows: (n: number) => `Delete ${n} rows`,
	insertColumnLeft: "Insert column left",
	insertColumnRight: "Insert column right",
	moveColumnLeft: "Move column left",
	moveColumnRight: "Move column right",
	sortAscending: "Sort ascending",
	sortDescending: "Sort descending",
	renameColumn: "Rename column",
	columnType: "Column type",
	kinds: { text: "Text", number: "Number", bool: "Checkbox", select: "Select" },
	alignLeft: "Align left",
	alignCenter: "Align center",
	alignRight: "Align right",
	deleteColumn: "Delete column",
	deleteTable: "Delete table",
	/** A row handle's name, by the row's own name. */
	rowHandle: (name: string) => `Row ${name} options`,
	/** A column handle's name, by the column's header text. */
	columnHandle: (name: string) => `Column ${name} options`,
	/** The names while no row or column is active (the handle is hidden then). */
	rowHandleIdle: "Row options",
	columnHandleIdle: "Column options",
} as const;

/** The keys that open each menu, as `aria-keyshortcuts` says them. */
export const tableMenuKeys = {
	row: "Shift+F10 ContextMenu",
	column: "Alt+Shift+F10",
} as const;

export type TableHandleKind = "row" | "column";

/**
 * How long the handles wait, once the pointer leaves the table and its
 * handles, before they go. A handle straddles the table's edge, so the pointer
 * on its way to one, or a hand a pixel off it, leaves now and then; coming
 * back within this is no leave at all. While they wait, and while they fade
 * after, the handles keep their place: one that jumped to another row as the
 * pointer slipped off it could not be found again by moving back.
 */
export const TABLE_HANDLE_LEAVE_DELAY = 300;

/**
 * Which menu a key event asks for: Shift+F10 or the Menu key the row's,
 * Alt+Shift+F10 the column's, anything else none.
 */
export function tableMenuKey(e: {
	key: string;
	shiftKey: boolean;
	altKey: boolean;
	ctrlKey: boolean;
	metaKey: boolean;
}): TableHandleKind | null {
	if (e.ctrlKey || e.metaKey) return null;
	if (e.key === "ContextMenu" && !e.altKey) return "row";
	if (e.key !== "F10" || !e.shiftKey) return null;
	return e.altKey ? "column" : "row";
}

function act(
	id: string,
	label: string,
	icon: LucideIcon | undefined,
	a: TableAction | undefined,
	danger = false,
): TableMenuItem | null {
	if (!a) return null;
	const run = typeof a === "function" ? a : a.run;
	const disabled = typeof a === "function" ? false : !!a.disabled;
	return { type: "item", id, label, icon, danger, disabled, onSelect: run };
}

/** Groups joined by separators; empty groups drop out, so none leads, trails or doubles. */
function grouped(groups: readonly (readonly (TableMenuItem | null)[])[]): TableMenuItem[] {
	const out: TableMenuItem[] = [];
	let n = 0;
	for (const group of groups) {
		const items = group.filter((i): i is TableMenuItem => i !== null && i.type !== "separator");
		if (items.length === 0) continue;
		if (out.length > 0) out.push({ type: "separator", id: `separator-${n++}` });
		out.push(...items);
	}
	return out;
}

export type RowMenuActions = {
	insertAbove?: TableAction;
	insertBelow?: TableAction;
	moveUp?: TableAction;
	moveDown?: TableAction;
	remove?: TableAction;
	/** What delete says, "Delete row" unless given (eg "Delete 3 rows"). */
	removeLabel?: string;
	/** A last group of the host's own (markdown: "Delete table"). */
	extra?: readonly TableMenuItem[];
};

/** A row's menu: insert | move | delete | the host's extra. */
export function rowMenu(a: RowMenuActions): TableMenuItem[] {
	const t = tableMenuText;
	return grouped([
		[
			act("insert-above", t.insertRowAbove, BetweenHorizontalStart, a.insertAbove),
			act("insert-below", t.insertRowBelow, BetweenHorizontalEnd, a.insertBelow),
		],
		[
			act("move-up", t.moveRowUp, ArrowUp, a.moveUp),
			act("move-down", t.moveRowDown, ArrowDown, a.moveDown),
		],
		[act("delete-row", a.removeLabel ?? t.deleteRow, Trash2, a.remove, true)],
		a.extra ?? [],
	]);
}

export type ColumnKind = keyof typeof tableMenuText.kinds;
export type ColumnAlign = "left" | "center" | "right";

export type ColumnMenuActions = {
	insertLeft?: TableAction;
	insertRight?: TableAction;
	moveLeft?: TableAction;
	moveRight?: TableAction;
	/** Sort the column; either direction may be left out. */
	sort?: { ascending?: TableAction; descending?: TableAction };
	rename?: TableAction;
	/** The column's kind, a submenu of radio choices. */
	kind?: TableChoice<ColumnKind>;
	align?: TableChoice<ColumnAlign>;
	remove?: TableAction;
	/** A last group of the host's own (markdown: "Delete table"). */
	extra?: readonly TableMenuItem[];
};

/** A column's menu: insert | move | sort | rename, type | align | delete | the host's extra. */
export function columnMenu(a: ColumnMenuActions): TableMenuItem[] {
	const t = tableMenuText;
	const kind = a.kind;
	const align = a.align;
	return grouped([
		[
			act("insert-left", t.insertColumnLeft, BetweenVerticalStart, a.insertLeft),
			act("insert-right", t.insertColumnRight, BetweenVerticalEnd, a.insertRight),
		],
		[
			act("move-left", t.moveColumnLeft, ArrowLeft, a.moveLeft),
			act("move-right", t.moveColumnRight, ArrowRight, a.moveRight),
		],
		[
			act("sort-ascending", t.sortAscending, ArrowUpNarrowWide, a.sort?.ascending),
			act("sort-descending", t.sortDescending, ArrowDownWideNarrow, a.sort?.descending),
		],
		[
			act("rename", t.renameColumn, Pencil, a.rename),
			kind
				? {
						type: "sub",
						id: "kind",
						label: t.columnType,
						icon: Shapes,
						items: [
							{
								type: "radio",
								id: "kind-choice",
								value: kind.value,
								options: (Object.keys(t.kinds) as ColumnKind[]).map((k) => ({
									value: k,
									label: t.kinds[k],
								})),
								onValueChange: (v) => kind.onValueChange(v as ColumnKind),
							},
						],
					}
				: null,
		],
		[
			// No icons on radio items: the dot sits where an icon would, so the labels line up.
			align
				? {
						type: "radio",
						id: "align",
						value: align.value,
						options: [
							{ value: "left", label: t.alignLeft },
							{ value: "center", label: t.alignCenter },
							{ value: "right", label: t.alignRight },
						],
						onValueChange: (v) => align.onValueChange(v as ColumnAlign),
					}
				: null,
		],
		[act("delete-column", t.deleteColumn, Trash2, a.remove, true)],
		a.extra ?? [],
	]);
}

/* ============================== renderers ================================ */

// The kit's dropdown and context menus take the same props part for part;
// one walk over the items draws either.
type Parts = {
	Item: React.ComponentType<{
		disabled?: boolean;
		variant?: "default" | "danger";
		onSelect?: () => void;
		children?: React.ReactNode;
	}>;
	Separator: React.ComponentType;
	RadioGroup: React.ComponentType<{
		value?: string;
		onValueChange?: (value: string) => void;
		children?: React.ReactNode;
	}>;
	RadioItem: React.ComponentType<{ value: string; children?: React.ReactNode }>;
	Sub: React.ComponentType<{ children?: React.ReactNode }>;
	SubTrigger: React.ComponentType<{ children?: React.ReactNode }>;
	SubContent: React.ComponentType<{ className?: string; children?: React.ReactNode }>;
};

const DROPDOWN: Parts = {
	Item: DropdownMenuItem,
	Separator: DropdownMenuSeparator,
	RadioGroup: DropdownMenuRadioGroup,
	RadioItem: DropdownMenuRadioItem,
	Sub: DropdownMenuSub,
	SubTrigger: DropdownMenuSubTrigger,
	SubContent: DropdownMenuSubContent,
};

const CONTEXT: Parts = {
	Item: ContextMenuItem,
	Separator: ContextMenuSeparator,
	RadioGroup: ContextMenuRadioGroup,
	RadioItem: ContextMenuRadioItem,
	Sub: ContextMenuSub,
	SubTrigger: ContextMenuSubTrigger,
	SubContent: ContextMenuSubContent,
};

function renderItems(P: Parts, items: readonly TableMenuItem[]): React.ReactNode {
	return items.map((item) => {
		switch (item.type) {
			case "separator":
				return <P.Separator key={item.id} />;
			case "radio":
				return (
					<P.RadioGroup key={item.id} value={item.value} onValueChange={item.onValueChange}>
						{item.options.map((o) => (
							<P.RadioItem key={o.value} value={o.value}>
								{o.label}
							</P.RadioItem>
						))}
					</P.RadioGroup>
				);
			case "sub": {
				const Icon = item.icon;
				return (
					<P.Sub key={item.id}>
						<P.SubTrigger>
							{Icon ? <Icon /> : null}
							{item.label}
						</P.SubTrigger>
						<P.SubContent className="min-w-40">{renderItems(P, item.items)}</P.SubContent>
					</P.Sub>
				);
			}
			default: {
				const Icon = item.icon;
				return (
					<P.Item
						key={item.id}
						disabled={item.disabled}
						variant={item.danger ? "danger" : "default"}
						onSelect={item.onSelect}
					>
						{Icon ? <Icon /> : null}
						{item.label}
					</P.Item>
				);
			}
		}
	});
}

/** The items as a kit DropdownMenu's content. */
export function TableMenuDropdownItems({ items }: { items: readonly TableMenuItem[] }) {
	return <>{renderItems(DROPDOWN, items)}</>;
}

/** The items as a kit ContextMenu's content. */
export function TableMenuContextItems({ items }: { items: readonly TableMenuItem[] }) {
	return <>{renderItems(CONTEXT, items)}</>;
}

/* ================================ handles ================================ */

/** An element, or a lookup run when the handles measure (a ref's element, say). */
export type TableAnchor = HTMLElement | null | (() => HTMLElement | null);

/** A menu's items, or a thunk read when the menu opens. */
export type TableMenuItems = readonly TableMenuItem[] | (() => readonly TableMenuItem[]);

export type TableHandlesHandle = {
	/** Open a handle's menu, as a shortcut does; false when that handle is not there. */
	open: (which: TableHandleKind) => boolean;
	/** Close whichever menu is open. */
	close: () => void;
};

export type TableHandlesProps = {
	/** The active row's `<tr>`; null hides the row handle. */
	row: TableAnchor;
	/** The active column's header cell; null hides the column handle. */
	column: TableAnchor;
	/** The box that scrolls the table sideways, so the handles follow its scroll. */
	scroller?: TableAnchor;
	/** No items (an empty list) is no handle of that kind at all. */
	rowItems?: TableMenuItems;
	columnItems?: TableMenuItems;
	/** Each handle's accessible name, eg "Row 3 options". */
	rowLabel: string;
	columnLabel: string;
	/** Whether the host shows the handles now; an open menu keeps them shown. */
	visible: boolean;
	/**
	 * Hidden handles stay tab stops: for a host whose handles come next in the
	 * tab order while the focus is in it, so Tab still reaches one whose table
	 * was last used with the pointer.
	 */
	reachable?: boolean;
	onOpenChange?: (which: TableHandleKind | null) => void;
	/** Where focus goes once a menu closes; the host's cell or caret. */
	onCloseAutoFocus?: (e: Event) => void;
	ref?: React.Ref<TableHandlesHandle>;
};

type Point = { x: number; y: number } | null;

function resolve(a: TableAnchor | undefined): HTMLElement | null {
	return typeof a === "function" ? a() : (a ?? null);
}

function itemsOf(items: TableMenuItems | undefined, open: boolean): readonly TableMenuItem[] {
	if (!items) return [];
	if (typeof items === "function") return open ? items() : [];
	return items;
}

/** The box a handle is placed in: its offset parent (the parent where layout is not run). */
function placedIn(el: HTMLElement | null): HTMLElement | null {
	const box = el?.offsetParent ?? el?.parentElement ?? null;
	return box instanceof HTMLElement ? box : null;
}

const samePoint = (a: Point, b: Point) =>
	a === b || (a !== null && b !== null && a.x === b.x && a.y === b.y);

export function TableHandles({
	row,
	column,
	scroller,
	rowItems,
	columnItems,
	rowLabel,
	columnLabel,
	visible,
	reachable = false,
	onOpenChange,
	onCloseAutoFocus,
	ref,
}: TableHandlesProps) {
	const [open, setOpen] = useState<TableHandleKind | null>(null);
	const openRef = useRef(open);
	openRef.current = open;
	const [at, setAt] = useState<{ row: Point; column: Point }>({ row: null, column: null });
	const rowBox = useRef<HTMLSpanElement | null>(null);
	const columnBox = useRef<HTMLSpanElement | null>(null);

	const hasRow = typeof rowItems === "function" || (rowItems?.length ?? 0) > 0;
	const hasColumn = typeof columnItems === "function" || (columnItems?.length ?? 0) > 0;

	// Measured against the box the handles are placed in, whatever it is.
	const measure = useRef((): { row: Point; column: Point } | null => null);
	measure.current = () => {
		const box = placedIn(rowBox.current ?? columnBox.current);
		if (!box) return null;
		const b = box.getBoundingClientRect();
		const ox = b.left + box.clientLeft;
		const oy = b.top + box.clientTop;
		const s = resolve(scroller)?.getBoundingClientRect();
		const r = resolve(row)?.getBoundingClientRect();
		const c = resolve(column)?.getBoundingClientRect();
		const rowAt: Point = r
			? {
					x: Math.round(Math.max(r.left, s?.left ?? r.left) - ox),
					y: Math.round(r.top + r.height / 2 - oy),
				}
			: null;
		let columnAt: Point = null;
		if (c) {
			const mid = c.left + c.width / 2;
			if (!s || (mid >= s.left && mid <= s.right)) {
				columnAt = { x: Math.round(mid - ox), y: Math.round(c.top - oy) };
			}
		}
		setAt((prev) =>
			samePoint(prev.row, rowAt) && samePoint(prev.column, columnAt)
				? prev
				: { row: rowAt, column: columnAt },
		);
		return { row: rowAt, column: columnAt };
	};

	// Every render: the host re-renders when what the handles stand for moves.
	// A row or column taken away under its open menu (a delete from another
	// tab, a document replaced) closes the menu: it has nothing left to act on.
	useLayoutEffect(() => {
		measure.current();
		const which = openRef.current;
		if (which && !resolve(which === "row" ? row : column)) change(null);
	});

	// And when the table scrolls sideways or changes size under them.
	const bound = useRef<{ els: (Element | null)[]; off: () => void } | null>(null);
	useLayoutEffect(() => {
		const anchor = resolve(row) ?? resolve(column);
		const els = [
			anchor?.closest("table") ?? null,
			resolve(scroller),
			placedIn(rowBox.current ?? columnBox.current),
		];
		const was = bound.current;
		if (was?.els.every((e, i) => e === els[i])) return;
		was?.off();
		const on = () => measure.current();
		const ro = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(on);
		for (const el of els) if (el) ro?.observe(el);
		const scroll = els[1];
		scroll?.addEventListener("scroll", on, { passive: true });
		window.addEventListener("resize", on);
		bound.current = {
			els,
			off: () => {
				ro?.disconnect();
				scroll?.removeEventListener("scroll", on);
				window.removeEventListener("resize", on);
			},
		};
	});
	useEffect(
		() => () => {
			bound.current?.off();
			bound.current = null;
		},
		[],
	);

	const change = useCallback(
		(which: TableHandleKind | null) => {
			if (openRef.current === which) return;
			openRef.current = which;
			setOpen(which);
			onOpenChange?.(which);
		},
		[onOpenChange],
	);

	useImperativeHandle(
		ref,
		() => ({
			open: (which) => {
				const el = which === "row" ? hasRow && resolve(row) : hasColumn && resolve(column);
				if (!el) return false;
				// A column scrolled out of sight has no handle to anchor a menu to:
				// bring it in first, and give up if it still has none.
				el.scrollIntoView?.({ block: "nearest", inline: "nearest" });
				if (!measure.current()?.[which]) return false;
				change(which);
				return true;
			},
			close: () => change(null),
		}),
		[change, hasRow, hasColumn, row, column],
	);

	const shown = visible || open !== null;

	const handle = (
		which: TableHandleKind,
		point: Point,
		items: readonly TableMenuItem[],
		label: string,
		box: React.RefObject<HTMLSpanElement | null>,
	) => {
		const on = shown && point !== null;
		return (
			<span
				ref={box}
				data-table-handle={which}
				aria-hidden={on || reachable ? undefined : true}
				className={cn(
					tableHandle.base,
					tableHandle[which],
					on
						? tableHandle.shown
						: point === null
							? tableHandle.hidden
							: reachable
								? tableHandle.reachable
								: tableHandle.faded,
				)}
				style={point ? { left: point.x, top: point.y } : undefined}
			>
				<DropdownMenu
					modal={false}
					open={open === which}
					onOpenChange={(o) => {
						if (o) change(which);
						else if (openRef.current === which) change(null);
					}}
				>
					<DropdownMenuTrigger asChild>
						<IconButton
							variant="secondary"
							size="xs"
							aria-label={label}
							aria-keyshortcuts={tableMenuKeys[which]}
							// Faded, it answers the pointer but is no tab stop.
							tabIndex={on || reachable ? undefined : -1}
							// Opens on press; keeping the press from moving focus keeps the cell or caret.
							onMouseDown={(e) => e.preventDefault()}
							// The keys it advertises open its own menu here too.
							onKeyDown={(e) => {
								if (!tableMenuKey(e)) return;
								e.preventDefault();
								change(which);
							}}
							// The browser's menu would cover the handle's own.
							onContextMenu={(e) => e.preventDefault()}
						>
							{which === "row" ? <GripVertical /> : <GripHorizontal />}
						</IconButton>
					</DropdownMenuTrigger>
					<DropdownMenuContent
						side="bottom"
						align="start"
						className="w-48"
						onCloseAutoFocus={onCloseAutoFocus}
					>
						<TableMenuDropdownItems items={items} />
					</DropdownMenuContent>
				</DropdownMenu>
			</span>
		);
	};

	return (
		<>
			{hasRow ? handle("row", at.row, itemsOf(rowItems, open === "row"), rowLabel, rowBox) : null}
			{hasColumn
				? handle(
						"column",
						at.column,
						itemsOf(columnItems, open === "column"),
						columnLabel,
						columnBox,
					)
				: null}
		</>
	);
}
