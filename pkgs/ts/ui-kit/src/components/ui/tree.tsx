// Tree: nested rows that fold, one tab stop, arrows inside, optional rename
// and drag.
//
// Design refs:
//   a11y.md   §4 tree pattern (role tree / treeitem, aria-expanded, level,
//             posinset, setsize), roving tabindex
//   motion.md §3 row washes (bg + opacity, duration-fast ease-out)
//
// ## The split
//
// The kit owns how a tree behaves, the app owns what it means. The tree is the
// app's (`source`), and so is every bit of state that outlives a render:
// which rows are open (`expanded`), which one is selected (`selectedKey`). The
// kit reports intents and never acts on them:
//
//   onToggle(key, open)   a fold or an unfold
//   onSelect(key)         a click, Space, or focus when selection follows it
//   onActivate(key, e)    Enter or a double click: "do the thing"
//   onRename(key, title)  an inline rename committed (F2 starts one)
//   onMove(move)          a drop: the key, its new parent and index
//
// Rename and drag are on only when their callback is given.
//
// ## Two parts
//
// `Tree` draws the rows, owns the keyboard, the rename in flight and the drag.
// `renderItem` draws each row's content from a `TreeItemState`, usually as a
// `TreeItem`: the row shell with an icon lane (the fold chevron swaps into it
// on hover), a label, a hover-revealed actions lane and a right-click menu.
// An app that wants another row spreads `item.props` on its own element.
//
// The rows are flat siblings, never nested in each other's DOM, so one row's
// hover is its own and hovering a child leaves its parent alone. The indent
// alone carries depth.
//
// Geometry and washes are CSS variables (`--tree-*` in index.css), so an app
// retunes a tree without touching it.

import { ChevronRight } from "lucide-react";
import type * as React from "react";
import { Fragment, useCallback, useImperativeHandle, useMemo, useState } from "react";
import { ROVING_KEY, useRovingFocus } from "../../lib/roving";
import { cn } from "../../lib/utils";
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "./context-menu";
import { IconButton } from "./icon-button";
import { InlineEdit } from "./inline-edit";
import { useTreeDrag } from "./tree-drag";
import { flattenTree, type TreeMove, type TreeRow, type TreeSource } from "./tree-model";

/** What `renderItem` gets for one row. */
export type TreeItemState = {
	row: TreeRow;
	/** Position among the visible rows. */
	index: number;
	selected: boolean;
	/** The one row in the tab order. */
	tabbable: boolean;
	/** Whether the row folds: it has children, or the tree folds leaves too. */
	foldable: boolean;
	/** A rename is in flight on this row. */
	renaming: boolean;
	/** Some row is being dragged, so no row should sit in its hover look. */
	dragging: boolean;
	/** This row is the one being dragged. */
	dragged: boolean;
	/** A drop would land inside this row. */
	dropInto: boolean;
	toggle: () => void;
	/** Start an inline rename. A no-op when the tree takes no renames. */
	startRename: () => void;
	/** End the rename with `title` (null: unchanged), focus back on the row or not. */
	endRename: (title: string | null, refocus: boolean) => void;
	/** Everything the treeitem element needs. `TreeItem` spreads it for you. */
	props: React.HTMLAttributes<HTMLDivElement> & {
		[ROVING_KEY]: string;
		draggable?: boolean;
	};
};

export type TreeHandle = {
	/** Move keyboard focus to a row. */
	focusKey: (key: string) => void;
};

export type TreeProps = {
	"aria-label": string;
	source: TreeSource;
	expanded: ReadonlySet<string>;
	onToggle: (key: string, open: boolean) => void;
	selectedKey?: string | null;
	onSelect?: (key: string) => void;
	/** Arrows move the selection, not just the focus (a file list does this). */
	selectionFollowsFocus?: boolean;
	onActivate?: (key: string, e: React.KeyboardEvent | React.MouseEvent) => void;
	onRename?: (key: string, title: string) => void;
	onMove?: (move: TreeMove) => void;
	/** Whether a row may be dragged. Every row by default. */
	canDrag?: (key: string) => boolean;
	/** The type a dragged key travels under, for drop targets outside the tree. */
	dragMime?: string;
	/** Leaves fold too: unfolding one shows `renderEmptyBranch`. */
	foldLeaves?: boolean;
	/** Runs before the tree's own keys. `preventDefault()` claims the key. */
	onItemKeyDown?: (e: React.KeyboardEvent, row: TreeRow) => void;
	renderItem: (item: TreeItemState) => React.ReactNode;
	/** What an open row with no children shows under itself. */
	renderEmptyBranch?: (row: TreeRow) => React.ReactNode;
	/** What the tree shows with no rows at all. */
	empty?: React.ReactNode;
	className?: string;
	ref?: React.Ref<TreeHandle>;
};

/** Left pad for a row at `depth`. Depth is data, so it is an inline style. */
export function treeIndent(depth: number): React.CSSProperties {
	return { paddingLeft: `calc(var(--tree-row-pad) + ${depth} * var(--tree-indent))` };
}

/** A control inside a row handles its own click; the row leaves it alone. */
function onControl(e: React.SyntheticEvent): boolean {
	return (e.target as HTMLElement).closest("button, input, a, [role=menuitem]") !== null;
}

export function Tree({
	"aria-label": label,
	source,
	expanded,
	onToggle,
	selectedKey = null,
	onSelect,
	selectionFollowsFocus = false,
	onActivate,
	onRename,
	onMove,
	canDrag,
	dragMime,
	foldLeaves = false,
	onItemKeyDown,
	renderItem,
	renderEmptyBranch,
	empty,
	className,
	ref,
}: TreeProps) {
	const rows = useMemo(() => flattenTree(source, expanded), [source, expanded]);
	const keys = useMemo(() => rows.map((r) => r.key), [rows]);
	const { containerRef, tabKey, setActiveKey, focusKey, focusIndex, handleArrows } = useRovingFocus(
		keys,
		selectedKey,
	);
	const [renaming, setRenaming] = useState<string | null>(null);

	useImperativeHandle(ref, () => ({ focusKey }), [focusKey]);

	const noMove = useCallback(() => {}, []);
	const drag = useTreeDrag({
		source,
		rows,
		onMove: onMove ?? noMove,
		canDrag,
		mime: dragMime,
	});

	const startRename = useCallback(
		(key: string) => {
			if (onRename) setRenaming(key);
		},
		[onRename],
	);

	const onKeyDown = useCallback(
		(e: React.KeyboardEvent, row: TreeRow, index: number) => {
			onItemKeyDown?.(e, row);
			if (e.defaultPrevented) return;
			if (handleArrows(e, index)) return;
			const foldable = row.hasChildren || foldLeaves;
			switch (e.key) {
				case "ArrowRight":
					// Unfold a folded row; step into an open one's first child.
					e.preventDefault();
					if (!row.expanded && foldable) onToggle(row.key, true);
					else if (row.expanded && row.hasChildren) focusIndex(index + 1);
					break;
				case "ArrowLeft":
					// Fold an open row; otherwise climb to the parent.
					e.preventDefault();
					if (row.expanded) onToggle(row.key, false);
					else if (row.parent !== null) focusKey(row.parent);
					break;
				case "Enter":
					e.preventDefault();
					onActivate?.(row.key, e);
					break;
				case " ":
					e.preventDefault();
					onSelect?.(row.key);
					break;
				case "F2":
					if (!onRename) break;
					e.preventDefault();
					startRename(row.key);
					break;
				default:
					break;
			}
		},
		[
			onItemKeyDown,
			handleArrows,
			foldLeaves,
			onToggle,
			focusIndex,
			focusKey,
			onActivate,
			onSelect,
			onRename,
			startRename,
		],
	);

	const dropLine = (depth: number, edge: "before" | "after") => (
		<span
			aria-hidden="true"
			className={cn(
				"pointer-events-none absolute right-0 h-0.5 rounded-full bg-accent",
				edge === "before" ? "-top-px" : "-bottom-px",
			)}
			style={{
				left: `calc(var(--tree-row-pad) + ${depth} * var(--tree-indent) + var(--tree-lane))`,
			}}
		/>
	);

	return (
		// `contents`: a box for the drag's leave only; rows and tail stay laid
		// out by whatever holds the tree.
		<div className="contents" {...(onMove ? drag.leaveProps : {})}>
			<div
				role="tree"
				aria-label={label}
				ref={containerRef}
				data-slot="tree"
				className={cn("flex flex-col gap-(--tree-row-gap)", className)}
			>
				{rows.map((row, index) => {
					const key = row.key;
					const aimed = drag.target?.key === key ? drag.target.edge : null;
					const foldable = row.hasChildren || foldLeaves;
					const item: TreeItemState = {
						row,
						index,
						selected: key === selectedKey,
						tabbable: key === tabKey,
						foldable,
						renaming: renaming === key,
						dragging: drag.dragKey !== null,
						dragged: drag.dragKey === key,
						dropInto: aimed === "into",
						toggle: () => onToggle(key, !row.expanded),
						startRename: () => startRename(key),
						endRename: (title, refocus) => {
							setRenaming(null);
							if (title !== null) onRename?.(key, title);
							if (refocus) focusKey(key);
						},
						props: {
							role: "treeitem",
							tabIndex: key === tabKey ? 0 : -1,
							[ROVING_KEY]: key,
							"aria-selected": key === selectedKey,
							"aria-expanded": foldable ? row.expanded : undefined,
							"aria-level": row.depth + 1,
							"aria-posinset": row.pos,
							"aria-setsize": row.size,
							style: treeIndent(row.depth),
							onFocus: () => {
								setActiveKey(key);
								if (selectionFollowsFocus && key !== selectedKey) onSelect?.(key);
							},
							onKeyDown: (e) => onKeyDown(e, row, index),
							onClick: (e) => {
								// Keep the keyboard on the row, so the arrows work next:
								// Safari and Firefox on macOS never focus a clicked link.
								const el = e.currentTarget;
								if (!el.contains(document.activeElement)) el.focus({ preventScroll: true });
								if (!onControl(e)) onSelect?.(key);
							},
							onDoubleClick: (e) => {
								if (!onControl(e)) onActivate?.(key, e);
							},
							...(onMove && renaming !== key ? drag.itemProps(key) : {}),
						},
					};
					return (
						<Fragment key={key}>
							<div role="none" className="relative">
								{renderItem(item)}
								{aimed === "before" || aimed === "after" ? dropLine(row.depth, aimed) : null}
							</div>
							{row.expanded && !row.hasChildren && renderEmptyBranch ? (
								<div
									role="none"
									className="flex h-(--tree-row) items-center text-sm text-text-muted"
									style={treeIndent(row.depth + 1)}
								>
									{renderEmptyBranch(row)}
								</div>
							) : null}
						</Fragment>
					);
				})}
				{rows.length === 0 ? empty : null}
			</div>
			{onMove ? (
				<div data-slot="tree-tail" className="relative min-h-8 flex-1" {...drag.tailProps}>
					{drag.target?.key === null ? dropLine(0, "before") : null}
				</div>
			) : null}
		</div>
	);
}

// ============================== TreeItem ===================================

/*
 * The lane swap, CSS only. At rest a row shows its icon. While the row is
 * hovered, or it or its chevron has keyboard focus, the chevron shows in the
 * icon's place. JS hover state is not used on purpose: it flickers, and it
 * sticks after a drag because the browser never sends the leave. Off while a
 * drag is in flight, so no row sits in its hover look under a passing row.
 */
const ICON_OUT =
	"group-hover/tree-row:opacity-0 group-focus-visible/tree-row:opacity-0 group-has-focus-visible/tree-lane:opacity-0";
const CHEVRON_IN =
	"group-hover/tree-row:opacity-100 group-focus-visible/tree-row:opacity-100 focus-visible:opacity-100";

/*
 * The actions lane takes no width at rest and its own width only while
 * revealed, so a title at rest runs to the row's end instead of truncating
 * against buttons nobody can see. Hidden is `w-0`, never `display: none`, so
 * the buttons stay reachable by keyboard; focus inside reveals them, and so
 * does a menu they opened that is still open.
 */
const ACTIONS = cn(
	"flex w-0 shrink-0 items-center justify-end gap-px overflow-hidden",
	"pointer-events-none opacity-0 transition-opacity duration-fast ease-out",
	"group-hover/tree-row:pointer-events-auto group-hover/tree-row:w-auto group-hover/tree-row:opacity-100",
	"group-focus-visible/tree-row:pointer-events-auto group-focus-visible/tree-row:w-auto group-focus-visible/tree-row:opacity-100",
	"has-focus-visible:pointer-events-auto has-focus-visible:w-auto has-focus-visible:opacity-100",
	"[&:has([data-state=open])]:pointer-events-auto [&:has([data-state=open])]:w-auto [&:has([data-state=open])]:opacity-100",
);

export type TreeItemProps = {
	item: TreeItemState;
	/** The row's text: the default label, what a rename opens with, its name. */
	title: string;
	/** Drawn in the lane; the fold chevron swaps in on hover. */
	icon?: React.ReactNode;
	/** Replaces the default label (eg a link). Not shown while renaming. */
	label?: React.ReactNode;
	/** Buttons revealed on hover or keyboard focus, at the row's end. */
	actions?: React.ReactNode;
	/** Items for the right-click menu. */
	menu?: React.ReactNode;
	/** Where focus goes when the right-click menu closes. */
	onMenuCloseAutoFocus?: (e: Event) => void;
	/** A quieter wash than selected, eg a row open somewhere else. */
	highlighted?: boolean;
	className?: string;
};

export function TreeItem({
	item,
	title,
	icon,
	label,
	actions,
	menu,
	onMenuCloseAutoFocus,
	highlighted = false,
	className,
}: TreeItemProps) {
	const { row, selected, foldable, renaming, dragging } = item;
	const swap = icon !== undefined && foldable && !dragging;

	const lane = (
		<span className="group/tree-lane mr-(--tree-gap) grid w-(--tree-lane) shrink-0 place-items-center *:[grid-area:1/1]">
			{icon !== undefined ? (
				<span
					className={cn(
						"pointer-events-none flex size-4 shrink-0 items-center justify-center text-text-muted [&_svg]:size-4",
						"transition-opacity duration-fast ease-out",
						swap && ICON_OUT,
					)}
				>
					{icon}
				</span>
			) : null}
			{foldable ? (
				<IconButton
					variant="ghost"
					size="xs"
					ring="inset"
					tabIndex={-1}
					aria-label={row.expanded ? "Collapse" : "Expand"}
					aria-expanded={row.expanded}
					// No focus on a press (nothing lingers once the pointer
					// leaves) and no drag of the row from here.
					onMouseDown={(e) => e.preventDefault()}
					onClick={(e) => {
						e.stopPropagation();
						item.toggle();
					}}
					className={cn(
						"transition-[opacity,background-color,color] duration-fast ease-out",
						icon !== undefined && "opacity-0",
						swap && CHEVRON_IN,
					)}
				>
					<ChevronRight
						className={cn(
							"transition-transform duration-fast ease-out",
							row.expanded && "rotate-90",
						)}
					/>
				</IconButton>
			) : null}
		</span>
	);

	const body = (
		<div
			data-slot="tree-item"
			{...item.props}
			className={cn(
				"group/tree-row relative flex h-(--tree-row) items-center rounded-md pr-(--tree-row-pad-end)",
				"cursor-default select-none text-lg text-text-secondary",
				"transition-colors duration-fast ease-out",
				// Offset 0: a scrolling parent would clip the kit's 2px offset.
				"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
				selected
					? "bg-(--tree-selected) text-text-primary"
					: highlighted
						? "bg-(--tree-highlight) hover:bg-(--tree-hover)"
						: "hover:bg-(--tree-hover) hover:text-text-primary",
				item.dragged && "opacity-50",
				item.dropInto && "ring-2 ring-accent ring-inset",
				className,
			)}
		>
			{lane}
			{renaming ? (
				<InlineEdit
					initial={title}
					label={`Rename ${title}`}
					onCommit={(value, how) => {
						const next = value.trim();
						const changed = next !== "" && next !== title.trim();
						item.endRename(changed ? next : null, how === "enter");
					}}
					onCancel={() => item.endRename(null, true)}
				/>
			) : (
				(label ?? <span className="min-w-0 flex-1 truncate">{title}</span>)
			)}
			{actions ? <div className={ACTIONS}>{actions}</div> : null}
		</div>
	);

	if (!menu) return body;
	return (
		<ContextMenu>
			<ContextMenuTrigger asChild>{body}</ContextMenuTrigger>
			<ContextMenuContent
				className="min-w-52"
				onCloseAutoFocus={(e) => {
					onMenuCloseAutoFocus?.(e);
					// "Rename" from the menu: focus belongs to the edit, and handing
					// it back to the row would blur, and so commit, the edit at once.
					if (item.renaming) e.preventDefault();
				}}
			>
				{menu}
			</ContextMenuContent>
		</ContextMenu>
	);
}
