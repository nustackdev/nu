// Table primitive family. Plain <table> + cva variants; no radix.
//
// Design refs:
//   primitives.md    §Table (compound parts, variants, density, states)
//   palette.md       backgrounds, borders
//   space-radius.md  §Density Table (rows 24/28/32, cell pad 6x8, header 8x8)
//   typography.md    §4 Table cell (sm 400 for cells, sm 600 uppercase for header)
//   a11y.md          §4 <th scope>, aria-sort on sortable headers
//
// Density: compact / default / comfortable -> row heights 24 / 28 / 32.
//
// The classes are the table recipes (lib/recipes.ts), which the markdown
// schema draws its tables with too, so a DataTableRef and a markdown table match.
//
// Columns: both nu tables (the content Table and the DataTable) describe a
// column with one record, and lay it out with the helpers at the end of this
// file: `align` (start | center | end), `width` / `minWidth` / `maxWidth`
// (CSS lengths), `wrap` (wrap | nowrap | truncate, truncate being one line
// with an ellipsis and the full text as the title) and `hideBelow` (px of
// the table's width under which the column is not drawn; it stays in the
// DOM with display:none, so column indexes stay stable).
//
// Narrow: a table that does not fit its frame scrolls sideways inside it, and
// while it does its first column stays pinned to the frame's start edge, so
// each row still says whose it is. That is width, not touch: a narrow desktop
// column pins the same way a phone does, and a table that fits renders as it
// always has. The frame marks itself (`data-pinned`, and `data-scrolled` once
// moved off the start) and index.css draws the pin; the pinned cells take
// the ground of whatever the table sits on, read here, so the columns
// scrolling under them do not show through. A host whose first column is not
// one column (a row span down it) opts out with `data-unpinned` on the table.

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { type TableDensity, table } from "../../lib/recipes";
import { cn } from "../../lib/utils";

const tableVariants = cva(table.root, {
	variants: {
		variant: {
			default: table.framed,
			borderless: table.borderless,
			striped: table.framed,
		},
		density: {
			compact: "",
			default: "",
			comfortable: "",
		},
	},
	defaultVariants: {
		variant: "default",
		density: "default",
	},
});

// TableContext pushes density + the striped variant down to rows and cells so
// the consumer only sets it once on the root.
interface TableCtx {
	density: TableDensity;
	striped: boolean;
}
const TableContext = React.createContext<TableCtx>({
	density: "default",
	striped: false,
});

export interface TableProps
	extends React.TableHTMLAttributes<HTMLTableElement>,
		VariantProps<typeof tableVariants> {}

export function Table({ className, variant, density, ...props }: TableProps) {
	const effectiveDensity: TableDensity = density ?? "default";
	const striped = variant === "striped";
	const [frame, setFrame] = React.useState<HTMLDivElement | null>(null);
	usePinnedColumn(frame);
	return (
		<TableContext.Provider value={{ density: effectiveDensity, striped }}>
			<div ref={setFrame} data-slot="table-frame" className={table.frame}>
				<table
					data-slot="table"
					data-density={effectiveDensity}
					data-variant={variant ?? "default"}
					className={cn(tableVariants({ variant, density }), className)}
					{...props}
				/>
			</div>
		</TableContext.Provider>
	);
}

export function TableHeader({
	className,
	...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
	return <thead data-slot="table-header" className={cn(table.header, className)} {...props} />;
}

export function TableBody({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
	return <tbody data-slot="table-body" className={cn("", className)} {...props} />;
}

export function TableFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
	return <tfoot data-slot="table-footer" className={cn(table.footer, className)} {...props} />;
}

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
	selected?: boolean;
}

export function TableRow({ className, selected, ...props }: TableRowProps) {
	const { density, striped } = React.useContext(TableContext);
	return (
		<tr
			data-slot="table-row"
			data-state={selected ? "selected" : undefined}
			className={cn(table.rowHeight[density], table.row, striped && table.striped, className)}
			{...props}
		/>
	);
}

export interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {}

// Header cell. text-xs uppercase + medium weight per the IDE-flavored table
// header tier (typography.md §4 Table).
export function TableHead({ className, ...props }: TableHeadProps) {
	const { density } = React.useContext(TableContext);
	return (
		<th
			data-slot="table-head"
			scope={props.scope ?? "col"}
			className={cn(table.cellPad[density], table.head, className)}
			{...props}
		/>
	);
}

export interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {}

export function TableCell({ className, ...props }: TableCellProps) {
	const { density } = React.useContext(TableContext);
	return (
		<td
			data-slot="table-cell"
			className={cn(table.cellPad[density], table.cell, className)}
			{...props}
		/>
	);
}

export function TableCaption({
	className,
	...props
}: React.HTMLAttributes<HTMLTableCaptionElement>) {
	return <caption data-slot="table-caption" className={cn(table.caption, className)} {...props} />;
}

export { tableVariants };

// ---- the pinned first column ----------------------------------------------

/** The first background up the tree that is not see-through: what the table sits on. */
function groundOf(el: HTMLElement): string | null {
	for (let at: HTMLElement | null = el.parentElement; at; at = at.parentElement) {
		const bg = getComputedStyle(at).backgroundColor;
		if (bg && bg !== "transparent" && !/(,\s*0|\/\s*0)\)$/.test(bg)) return bg;
	}
	return null;
}

/**
 * Marks `frame` while its table is wider than it (`data-pinned`) and once it
 * has scrolled off its start (`data-scrolled`), and keeps `--table-ground` on
 * it while pinned. Attributes set straight on the element: the table does
 * not render again as it scrolls.
 */
function usePinnedColumn(frame: HTMLDivElement | null) {
	React.useLayoutEffect(() => {
		if (!frame || typeof ResizeObserver === "undefined") return;
		const tableEl = frame.querySelector<HTMLTableElement>(":scope > table");
		const ground = () => {
			const bg = groundOf(frame);
			if (bg) frame.style.setProperty("--table-ground", bg);
			else frame.style.removeProperty("--table-ground");
		};
		const scrolled = () => {
			const over = frame.hasAttribute("data-pinned");
			frame.toggleAttribute("data-scrolled", over && Math.abs(frame.scrollLeft) > 0);
		};
		const measure = () => {
			const over = (tableEl?.scrollWidth ?? 0) > frame.clientWidth + 1;
			if (over) ground();
			frame.toggleAttribute("data-pinned", over);
			scrolled();
		};
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(frame);
		if (tableEl) observer.observe(tableEl);
		// A theme is a class or an attribute on the document element: the
		// ground changes color under the table without anything resizing.
		const theme = new MutationObserver(() => {
			if (frame.hasAttribute("data-pinned")) ground();
		});
		theme.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["class", "style", "data-theme"],
		});
		frame.addEventListener("scroll", scrolled, { passive: true });
		return () => {
			observer.disconnect();
			theme.disconnect();
			frame.removeEventListener("scroll", scrolled);
		};
	}, [frame]);
}

// ---- columns -------------------------------------------------------------

/** Where a column's cells sit, logical so it follows the writing direction. */
export type ColumnAlign = "start" | "center" | "end";

/** How a column's text breaks: onto more lines, never, or clipped with an ellipsis. */
export type ColumnWrap = "wrap" | "nowrap" | "truncate";

/** How a column lays out, every length already CSS. */
export type ColumnLayout = {
	align?: ColumnAlign;
	width?: string;
	minWidth?: string;
	maxWidth?: string;
	wrap?: ColumnWrap;
	/** Px of the table's width under which the column is not drawn. */
	hideBelow?: number;
};

/** The text alignment class per column alignment. */
export const COLUMN_ALIGN: Record<ColumnAlign, string> = {
	start: "text-start",
	center: "text-center",
	end: "text-end",
};

/** The flex alignment (along the cell) per column alignment. */
export const COLUMN_JUSTIFY: Record<ColumnAlign, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
};

/** The flex alignment (across a stacked cell) per column alignment. */
export const COLUMN_ITEMS: Record<ColumnAlign, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
};

const WRAP_CLASSES: Record<ColumnWrap, string | undefined> = {
	wrap: undefined,
	nowrap: "whitespace-nowrap",
	truncate: "overflow-hidden text-ellipsis whitespace-nowrap",
};

/** The header cell's style: the column's starting width, and none at all when hidden. */
export function columnHeadStyle(
	col: ColumnLayout,
	hidden: boolean,
): React.CSSProperties | undefined {
	if (hidden) return { display: "none" };
	return col.width ? { width: col.width } : undefined;
}

/** A body cell's style: none at all when the column is hidden. */
export function columnCellStyle(hidden: boolean): React.CSSProperties | undefined {
	return hidden ? { display: "none" } : undefined;
}

/**
 * What a cell holds, in the column's box: its min and max width (a table
 * cell itself ignores both) and its wrap. A column that asks for neither
 * draws its content bare. `title` is the full text a truncated cell shows on
 * hover.
 */
export function ColumnBox({
	col,
	title,
	className,
	children,
}: {
	col: ColumnLayout;
	title?: string;
	className?: string;
	children?: React.ReactNode;
}) {
	const wrap = col.wrap ?? "wrap";
	if (!col.minWidth && !col.maxWidth && wrap === "wrap" && !className) return <>{children}</>;
	const truncate = wrap === "truncate";
	return (
		<div
			data-slot="table-column-box"
			title={truncate ? title : undefined}
			className={cn("min-w-0", WRAP_CLASSES[wrap], className)}
			style={{
				minWidth: col.minWidth,
				// A truncated column clips at its max width, else at its width.
				maxWidth: col.maxWidth ?? (truncate ? col.width : undefined),
			}}
		>
			{children}
		</div>
	);
}

/**
 * The indexes of the columns to leave out at the current width of `el`:
 * each whose `hideBelow` is more than that width. Measures only while some
 * column asks, and hides nothing until measured.
 */
export function useHiddenColumns(
	el: HTMLElement | null,
	columns: readonly ColumnLayout[],
): ReadonlySet<number> {
	const asks = columns.some((c) => (c.hideBelow ?? 0) > 0);
	const [width, setWidth] = React.useState<number | null>(null);
	React.useLayoutEffect(() => {
		if (!el || !asks || typeof ResizeObserver === "undefined") return;
		const measure = () => setWidth(el.clientWidth);
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [el, asks]);
	return React.useMemo(() => {
		const out = new Set<number>();
		if (!asks || width === null) return out;
		columns.forEach((c, i) => {
			if ((c.hideBelow ?? 0) > width) out.add(i);
		});
		return out;
	}, [asks, width, columns]);
}
