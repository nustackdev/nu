// Table primitive family. Plain <table> + cva variants; no radix.
//
// Design refs:
//   primitives.md    §Table (compound parts, variants, density, states)
//   palette.md       §2.1 backgrounds, §2.3 borders, §2.4 accent-wash
//   space-radius.md  §Density Table (rows 24/28/32, cell pad 6x8, header 8x8)
//   typography.md    §4 Table cell (sm 400 for cells, sm 600 uppercase for header)
//   a11y.md          §4 <th scope>, aria-sort on sortable headers
//
// Density: compact / default / comfortable -> row heights 24 / 28 / 32.

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "../../lib/utils";

const tableVariants = cva(
	// w-full so tables fill their host; text-sm is the row baseline (12px per typography.md §4).
	"w-full caption-bottom text-sm text-text-primary border-separate border-spacing-0",
	{
		variants: {
			variant: {
				default: "border border-border-default rounded-md overflow-hidden",
				// Borderless variant drops the outer frame; useful when the table
				// sits inside a Card / Panel that already draws it.
				borderless: "border-0",
				// Striped variant alternates row bg for scan density.
				striped: "border border-border-default rounded-md overflow-hidden",
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
	},
);

// Row height per density lives on the row, cell padding derived to match.
const rowHeightByDensity = {
	compact: "h-6", // 24
	default: "h-7", // 28
	comfortable: "h-8", // 32
} as const;

const cellPadByDensity = {
	compact: "px-2 py-1",
	default: "px-2.5 py-1.5",
	comfortable: "px-3 py-2",
} as const;

// TableContext pushes density + striped intent down to rows and cells so the
// consumer only sets it once on the root.
type Density = keyof typeof rowHeightByDensity;
interface TableCtx {
	density: Density;
	striped: boolean;
}
const TableContext = React.createContext<TableCtx>({
	density: "default",
	striped: false,
});

export interface TableProps
	extends React.TableHTMLAttributes<HTMLTableElement>,
		VariantProps<typeof tableVariants> {}

export function Table({
	className,
	variant,
	density,
	...props
}: TableProps) {
	const effectiveDensity: Density = density ?? "default";
	const striped = variant === "striped";
	return (
		<TableContext.Provider value={{ density: effectiveDensity, striped }}>
			<div className="w-full overflow-x-auto">
				<table
					data-slot="table"
					data-density={effectiveDensity}
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
	return (
		<thead
			data-slot="table-header"
			className={cn("bg-bg-sunken", className)}
			{...props}
		/>
	);
}

export function TableBody({
	className,
	...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
	return (
		<tbody
			data-slot="table-body"
			className={cn("", className)}
			{...props}
		/>
	);
}

export function TableFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
	return (
		<tfoot
			data-slot="table-footer"
			className={cn(
				"bg-bg-sunken border-t border-border-subtle font-medium",
				className,
			)}
			{...props}
		/>
	);
}

export interface TableRowProps
	extends React.HTMLAttributes<HTMLTableRowElement> {
	selected?: boolean;
}

export function TableRow({
	className,
	selected,
	...props
}: TableRowProps) {
	const { density, striped } = React.useContext(TableContext);
	return (
		<tr
			data-slot="table-row"
			data-state={selected ? "selected" : undefined}
			className={cn(
				rowHeightByDensity[density],
				"transition-colors duration-fast ease-out",
				"hover:bg-bg-elevated",
				// Striped rows: hit the odd body row with sunken tint. Header/footer
				// stay untouched since they own their own bg.
				striped && "even:bg-bg-sunken/40",
				"data-[state=selected]:bg-accent-wash",
				// Bottom border on every row draws the internal divider.
				"[&>td]:border-b [&>td]:border-border-subtle",
				"[&>th]:border-b [&>th]:border-border-default",
				className,
			)}
			{...props}
		/>
	);
}

export interface TableHeadProps
	extends React.ThHTMLAttributes<HTMLTableCellElement> {}

// Header cell. text-xs uppercase + medium weight per the IDE-flavored table
// header tier (typography.md §4 Table).
export function TableHead({
	className,
	...props
}: TableHeadProps) {
	const { density } = React.useContext(TableContext);
	return (
		<th
			data-slot="table-head"
			scope={props.scope ?? "col"}
			className={cn(
				cellPadByDensity[density],
				"text-left align-middle whitespace-nowrap",
				"text-text-secondary text-xs font-medium uppercase tracking-wide",
				className,
			)}
			{...props}
		/>
	);
}

export interface TableCellProps
	extends React.TdHTMLAttributes<HTMLTableCellElement> {}

export function TableCell({ className, ...props }: TableCellProps) {
	const { density } = React.useContext(TableContext);
	return (
		<td
			data-slot="table-cell"
			className={cn(
				cellPadByDensity[density],
				"align-middle text-sm text-text-primary",
				className,
			)}
			{...props}
		/>
	);
}

export function TableCaption({
	className,
	...props
}: React.HTMLAttributes<HTMLTableCaptionElement>) {
	return (
		<caption
			data-slot="table-caption"
			className={cn("mt-2 text-xs text-text-muted", className)}
			{...props}
		/>
	);
}

export { tableVariants };
