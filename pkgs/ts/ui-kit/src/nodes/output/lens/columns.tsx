// Miller columns over whatever a server hands down.
//
// One cascade of columns, one cursor, and a callback that says where the
// cursor went. What the columns describe, where they were read from, how they
// were produced: none of that is here. This draws a list of lists and reports
// a path, the same deal the code editor next door strikes with one string.
//
// ## What it owns and what it does not
//
// The cursor between columns is the server's: every move goes out through
// `onNavigate` as a whole resolved path and comes back as a new `cursor` and a
// new `columns`. The cursor *within* a column is local and never leaves - up
// and down are a read of what is already on screen, and asking a server where
// to put a highlight would be a round trip per keypress.
//
// ## The three row tiers
//
// They must never collapse into each other, because the difference between
// them is the navigation model rather than decoration:
//
//   hover   neutral, weakest. "the pointer is here."
//   trail   neutral, stronger, plus a muted rail. "this row opened the column
//           to its right." Every column left of the last has exactly one.
//   cursor  accent fill plus an accent rail. "this is where the keyboard is."
//           Exactly one on the surface, always in the rightmost column.
//
// Finder makes this exact split, and it is why a deep path stays readable: the
// eye finds the one accent row instantly and the trail behind it reads as
// history rather than as five competing selections. The rail carries the
// distinction a second time so it survives without colour.

import { ChevronRight } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import {
	Breadcrumb,
	BreadcrumbEllipsis,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "../../../components/ui/breadcrumb";
import { Kbd } from "../../../components/ui/kbd";
import { Skeleton } from "../../../components/ui/skeleton";
import { useKeyScope } from "../../../lib/keyboard";
import { cn } from "../../../lib/utils";
import {
	type Column,
	type Entry,
	glyphTone,
	kindIcon,
	kindLabel,
	rowIcon,
	SENTINEL,
	SENTINEL_LABEL,
	valueTone,
} from "./types";

export type LensColumnsProps = {
	/** The cascade, root column first. One per segment of `cursor`, plus one. */
	columns: Column[];
	/** Where the cascade was read. Owned by whoever renders this. */
	cursor: string[];
	/** A move. The whole new path, already resolved, never a push or a pop. */
	onNavigate: (cursor: string[]) => void;
	/** Pixels. A column browser scrolls both ways, so it takes a height. */
	height?: number;
	className?: string;
};

const HEIGHT = 420;

// 24px rows, 12px mono. This is the densest surface the kit draws: the point
// is a few hundred rows in front of someone, scannable. Vertical padding does
// no work at this size, the row height is the rhythm.
const ROW = "h-6";
const HEAD = "h-7";
const COL = "w-64";
const COL_LEAF = "w-[26rem]";

const rowClass = (cursor: boolean, trail: boolean) =>
	cn(
		"group/row relative flex w-full items-center gap-1.5 pr-2 pl-2",
		ROW,
		"text-left font-mono text-sm outline-none transition-colors",
		!cursor && !trail && "text-text-secondary hover:bg-bg-sunken",
		trail && "bg-bg-sunken text-text-primary",
		cursor && "bg-accent-soft text-text-primary",
	);

const railClass = (cursor: boolean, trail: boolean) =>
	cn(
		"absolute top-0 bottom-0 left-0 w-0.5",
		cursor ? "bg-accent" : trail ? "bg-text-muted" : "hidden",
	);

const columnClass = (leaf: boolean) =>
	cn(
		"flex min-h-0 shrink-0 flex-col border-r border-border-subtle bg-bg-canvas",
		leaf ? COL_LEAF : COL,
	);

const headClass = (active: boolean) =>
	cn(
		"flex shrink-0 items-center gap-1.5 border-b-2 px-2",
		HEAD,
		"bg-bg-surface text-xs text-text-muted select-none",
		active ? "border-b-accent" : "border-b-border-subtle",
	);

const emptyClass = cn(
	"flex flex-1 flex-col items-center justify-center gap-1.5 px-3 py-6",
	"text-center text-xs text-text-muted select-none",
);

const chipClass = cn(
	"inline-flex items-center rounded-sm border border-dashed px-1",
	"font-mono text-xs leading-none",
);

/* ============================== pieces =================================== */

/** A value cell, rendered by type. */
function ValueCell({ entry }: { entry: Entry }) {
	const vtype = entry.vtype ?? "";
	const tone = valueTone(vtype);
	if (SENTINEL.has(vtype)) {
		return (
			<span className={cn("shrink-0 text-xs", tone, chipClass)}>
				{SENTINEL_LABEL[vtype] ?? vtype}
			</span>
		);
	}
	if (!entry.preview) return null;
	return (
		<span
			className={cn("max-w-[55%] shrink truncate text-right text-xs", tone)}
			title={entry.preview}
		>
			{entry.preview}
		</span>
	);
}

function Row({
	entry,
	id,
	level,
	cursor,
	trail,
	onOpen,
}: {
	entry: Entry;
	id: string;
	level: number;
	cursor: boolean;
	trail: boolean;
	onOpen: () => void;
}) {
	const el = useRef<HTMLButtonElement | null>(null);
	const Glyph = rowIcon(entry.kind, entry.vtype ?? "");

	// Keep the cursor in view on a keyboard walk. `nearest`, so a click never
	// yanks the column and only an off-screen key press moves it.
	useLayoutEffect(() => {
		if (cursor) el.current?.scrollIntoView({ block: "nearest" });
	}, [cursor]);

	return (
		<button
			id={id}
			ref={el}
			type="button"
			// The container owns the keyboard, so rows stay out of the tab order:
			// tabbing past a 200-row column takes one press, not two hundred.
			tabIndex={-1}
			role="treeitem"
			aria-level={level}
			aria-selected={cursor}
			aria-expanded={entry.navigable ? trail : undefined}
			className={rowClass(cursor, trail)}
			onClick={onOpen}
		>
			<span className={railClass(cursor, trail)} aria-hidden="true" />
			<Glyph
				className={cn("size-3 shrink-0", glyphTone(entry.vtype ?? "", entry.navigable))}
				aria-hidden="true"
			/>
			<span className="min-w-0 flex-1 truncate" title={entry.key}>
				{entry.key}
			</span>
			<ValueCell entry={entry} />
			<ChevronRight
				className={cn("size-3 shrink-0", entry.navigable ? "text-text-muted" : "invisible")}
				aria-hidden="true"
			/>
		</button>
	);
}

/**
 * The leaf column's reader pane: one value, in full, wrapped.
 *
 * A leaf is one value, and a value that is three kilobytes of source has
 * nothing to do with a 24px cell. So the leaf column drops the row grammar and
 * becomes a reader, with its type stated once in the header.
 */
function LeafBody({ entry }: { entry: Entry }) {
	const vtype = entry.vtype ?? "";
	if (SENTINEL.has(vtype)) {
		return (
			<div className={emptyClass}>
				<span className={cn(chipClass, valueTone(vtype))}>{SENTINEL_LABEL[vtype] ?? vtype}</span>
				<span>
					{vtype === "empty"
						? "this slot has never been written"
						: vtype === "none"
							? "the slot holds null"
							: "the read did not produce a value"}
				</span>
			</div>
		);
	}
	const body = entry.text ?? entry.preview;
	if (!body) return <div className={emptyClass}>no value</div>;
	return (
		<>
			<div className="min-h-0 flex-1 overflow-auto p-3 font-mono text-sm leading-relaxed break-words whitespace-pre-wrap">
				{body}
			</div>
			{entry.clipped ? (
				<div className="shrink-0 border-t border-border-subtle px-3 py-1 text-xs text-text-muted select-none">
					clipped, the value is longer than shown
				</div>
			) : null}
		</>
	);
}

function ColumnPanel({
	col,
	colIdx,
	active,
	trailKey,
	cursorIdx,
	rowId,
	onOpen,
}: {
	col: Column;
	colIdx: number;
	active: boolean;
	trailKey: string | null;
	cursorIdx: number;
	rowId: (colIdx: number, i: number) => string;
	onOpen: (colIdx: number, key: string) => void;
}) {
	const leaf = col.kind === "leaf";
	const vtype = leaf ? (col.entries[0]?.vtype ?? "") : "";
	// On a leaf column the header states the value's TYPE, the only thing about
	// it a header can usefully say; everywhere else it states the structural
	// kind, which is what the rows below are.
	const Glyph = leaf ? rowIcon(col.kind, vtype) : kindIcon(col.kind);
	const capped = col.total > col.entries.length;

	return (
		<div className={columnClass(leaf)}>
			<div className={headClass(active)}>
				<Glyph
					className={cn("size-3 shrink-0", active ? "text-accent" : "text-text-muted")}
					aria-hidden="true"
				/>
				<span className="font-medium tracking-[0.02em] uppercase">
					{leaf ? vtype || kindLabel(col.kind) : kindLabel(col.kind)}
				</span>
				{leaf ? null : (
					<span className="ml-auto font-mono tabular-nums">
						{capped ? `${col.entries.length}/${col.total}` : col.total}
					</span>
				)}
			</div>

			{leaf && col.entries[0] ? (
				<LeafBody entry={col.entries[0]} />
			) : col.entries.length === 0 ? (
				<div className={emptyClass}>
					<span>nothing here</span>
					<span>this {kindLabel(col.kind)} holds no entries</span>
				</div>
			) : (
				<>
					{/* biome-ignore lint/a11y/useSemanticElements: the tree lives on the scroll host; a column is one level of it */}
					<div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto" role="group">
						{col.entries.map((e, i) => (
							<Row
								key={`${colIdx}::${e.key}`}
								id={rowId(colIdx, i)}
								entry={e}
								level={colIdx + 1}
								cursor={active && i === cursorIdx}
								trail={!active && e.key === trailKey}
								onOpen={() => onOpen(colIdx, e.key)}
							/>
						))}
					</div>
					{capped ? (
						<div className="shrink-0 border-t border-border-subtle px-2 py-1 font-mono text-xs text-text-muted select-none">
							first {col.entries.length} of {col.total}
						</div>
					) : null}
				</>
			)}
		</div>
	);
}

/** Placeholder for the column being fetched. Same geometry, so nothing jumps. */
function SkeletonColumn() {
	return (
		<div className={columnClass(false)} aria-hidden="true">
			<div className={headClass(true)}>
				<Skeleton shape="text" className="h-3 w-16" />
			</div>
			<div className="min-h-0 flex-1 overflow-hidden">
				{[0, 1, 2, 3, 4, 5].map((i) => (
					<div key={i} className={cn("flex items-center gap-1.5 px-2", ROW)}>
						<Skeleton shape="circle" className="size-3" />
						<Skeleton shape="text" className="h-2.5" style={{ width: `${70 - i * 8}%` }} />
					</div>
				))}
			</div>
		</div>
	);
}

/** The path trail. Collapses the middle so a deep path never eats the bar. */
function PathTrail({ cursor, onJump }: { cursor: string[]; onJump: (depth: number) => void }) {
	// Root plus five segments reads fine at 1440; past that the middle folds,
	// because the useful crumbs on a deep path are the root (jump home) and the
	// last few (where you are).
	const KEEP = 3;
	const folded = cursor.length > 5;
	const shown = folded ? cursor.slice(cursor.length - KEEP) : cursor;
	const offset = folded ? cursor.length - KEEP : 0;
	const crumb = "font-mono text-sm whitespace-nowrap";

	return (
		<Breadcrumb className="flex min-w-0 flex-1 items-center overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
			<BreadcrumbList className="flex-nowrap gap-1">
				<BreadcrumbItem>
					{cursor.length === 0 ? (
						<BreadcrumbPage className={crumb}>root</BreadcrumbPage>
					) : (
						<BreadcrumbLink
							className={crumb}
							onClick={(e) => {
								e.preventDefault();
								onJump(0);
							}}
						>
							root
						</BreadcrumbLink>
					)}
				</BreadcrumbItem>
				{folded ? (
					<>
						<BreadcrumbSeparator />
						<BreadcrumbItem>
							<BreadcrumbEllipsis />
						</BreadcrumbItem>
					</>
				) : null}
				{shown.map((seg, i) => {
					const depth = offset + i + 1;
					const last = depth === cursor.length;
					return (
						<BreadcrumbItem key={`${depth}-${seg}`}>
							<BreadcrumbSeparator />
							{last ? (
								<BreadcrumbPage className={crumb}>{seg}</BreadcrumbPage>
							) : (
								<BreadcrumbLink
									className={crumb}
									onClick={(e) => {
										e.preventDefault();
										onJump(depth);
									}}
								>
									{seg}
								</BreadcrumbLink>
							)}
						</BreadcrumbItem>
					);
				})}
			</BreadcrumbList>
		</Breadcrumb>
	);
}

/* ============================== the surface ============================== */

export function LensColumns({
	columns,
	cursor,
	onNavigate,
	height = HEIGHT,
	className,
}: LensColumnsProps) {
	const host = useRef<HTMLDivElement | null>(null);
	const [focused, setFocused] = useState<Record<number, number>>({});
	// How deep the move in flight goes, or null. Drives the skeleton: a drill
	// should show the column arriving, not a frozen surface with nothing to say
	// for a round trip.
	const [pending, setPending] = useState<number | null>(null);

	// A cascade landed, whichever move asked for it. Nothing is in flight now.
	useEffect(() => setPending(null), [columns]);

	// The live column is always the last one. In Miller columns the cursor is
	// singular by construction: clicking an earlier column does not activate it,
	// it renavigates, which drops every column to its right.
	const activeCol = Math.max(0, columns.length - 1);
	const rows = columns[activeCol]?.entries.length ?? 0;
	const cursorIdx = Math.min(focused[activeCol] ?? 0, Math.max(0, rows - 1));

	const go = useCallback(
		(next: string[]) => {
			setPending(next.length);
			onNavigate(next);
		},
		[onNavigate],
	);

	/** Open `key` from column `colIdx`: everything right of it is replaced. */
	const open = useCallback(
		(colIdx: number, rowKey: string) => {
			host.current?.focus();
			// Park this column's cursor on the row being opened before the answer
			// lands, so popping back returns here. The columns to the right are
			// about to be replaced, so their cursors go with them.
			const idx = columns[colIdx]?.entries.findIndex((e) => e.key === rowKey) ?? -1;
			setFocused((prev) => {
				const kept: Record<number, number> = {};
				for (const k of Object.keys(prev)) {
					const i = Number(k);
					if (i < colIdx) kept[i] = prev[i];
				}
				if (idx >= 0) kept[colIdx] = idx;
				return kept;
			});
			go([...cursor.slice(0, colIdx), rowKey]);
		},
		[columns, cursor, go],
	);

	const move = useCallback(
		(to: (i: number, last: number) => number) => {
			const last = rows - 1;
			setFocused((prev) => ({
				...prev,
				[activeCol]: Math.max(0, Math.min(last, to(cursorIdx, last))),
			}));
		},
		[activeCol, cursorIdx, rows],
	);

	const keys = useKeyScope<HTMLDivElement>({
		ArrowDown: () => move((i) => i + 1),
		ArrowUp: () => move((i) => i - 1),
		PageDown: () => move((i) => i + 10),
		PageUp: () => move((i) => i - 10),
		Home: () => move(() => 0),
		End: () => move((_, last) => last),
		ArrowRight: () => {
			const entry = columns[activeCol]?.entries[cursorIdx];
			if (entry?.navigable) open(activeCol, entry.key);
		},
		Enter: () => {
			const entry = columns[activeCol]?.entries[cursorIdx];
			if (entry?.navigable) open(activeCol, entry.key);
		},
		ArrowLeft: () => {
			if (cursor.length) go(cursor.slice(0, -1));
		},
		Escape: () => {
			if (cursor.length) go(cursor.slice(0, -1));
		},
	});

	// Keep the live column in view when the path gets *deeper*. Without this a
	// deep path walks off the right edge and the keyboard cursor ends up
	// somewhere nobody can see.
	//
	// Only on the way in. Pinning to scrollWidth after a pop yanks the view left
	// by a whole column on top of the column already vanishing, which reads as
	// the surface dropping out from under you. On the way back the browser's own
	// clamp is the gentler answer.
	const painted = useRef(columns.length);
	useLayoutEffect(() => {
		const el = host.current;
		const grew = columns.length > painted.current;
		painted.current = columns.length;
		if (el && (grew || (pending !== null && pending >= columns.length))) {
			el.scrollLeft = el.scrollWidth;
		}
	}, [columns.length, pending]);

	const rowId = useCallback((colIdx: number, i: number) => `lens-r${colIdx}-${i}`, []);
	// A move is in flight and it goes deeper than what is painted: show the
	// column arriving. A pop needs no placeholder, it only removes.
	const arriving = pending !== null && pending >= columns.length;

	return (
		<div
			className={cn(
				"flex w-full min-w-0 flex-col overflow-hidden rounded-md border border-border-subtle bg-bg-canvas text-text-primary",
				className,
			)}
			style={{ height }}
		>
			<div className="flex h-8 shrink-0 items-center gap-3 border-b border-border-subtle bg-bg-surface px-2">
				<PathTrail cursor={cursor} onJump={(d) => go(cursor.slice(0, d))} />
				<div className="flex shrink-0 items-center gap-1.5 text-xs text-text-muted select-none">
					<span className="flex items-center gap-1">
						<Kbd aria-label="Up arrow">&#8593;</Kbd>
						<Kbd aria-label="Down arrow">&#8595;</Kbd>
						move
					</span>
					<span className="flex items-center gap-1">
						<Kbd aria-label="Right arrow">&#8594;</Kbd>
						open
					</span>
					<span className="flex items-center gap-1">
						<Kbd aria-label="Left arrow">&#8592;</Kbd>
						back
					</span>
				</div>
			</div>

			<div
				ref={host}
				role="tree"
				aria-label="Shape lens"
				aria-activedescendant={columns.length ? rowId(activeCol, cursorIdx) : undefined}
				className="flex min-h-0 flex-1 overflow-x-auto overflow-y-hidden outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-inset"
				// Spelled out rather than spread: the tab stop is what makes this
				// the focus target the rows point at, and a spread hides that from
				// anything reading the markup, a11y lint included.
				tabIndex={keys.tabIndex}
				onKeyDown={keys.onKeyDown}
			>
				{columns.map((col, i) => (
					<ColumnPanel
						// Position is the identity here: column three is the third
						// column, and a cascade is replaced whole on every move.
						key={`col-${i}`}
						col={col}
						colIdx={i}
						active={i === activeCol && !arriving}
						trailKey={cursor[i] ?? null}
						cursorIdx={cursorIdx}
						rowId={rowId}
						onOpen={open}
					/>
				))}
				{arriving ? <SkeletonColumn /> : null}
				{columns.length === 0 && !arriving ? (
					<>
						<SkeletonColumn />
						<SkeletonColumn />
					</>
				) : null}
				{/* Past the last column. A browser that just stops halfway across
				    reads as a broken layout; carrying the header rule to the right
				    edge makes the surface read as one grid the columns fill in. */}
				<div className={cn("flex min-h-0 flex-1 flex-col bg-bg-canvas", "min-w-64")}>
					<div className={cn(HEAD, "shrink-0 border-b-2 border-b-border-subtle bg-bg-surface")} />
				</div>
			</div>
		</div>
	);
}
