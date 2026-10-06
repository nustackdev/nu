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
//
// The classes are the table recipes (lib/recipes.ts), which the markdown
// schema draws its tables with too, so a TableRef and a markdown table match.

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

// TableContext pushes density + striped intent down to rows and cells so the
// consumer only sets it once on the root.
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
		VariantProps<typeof tableVariants> {
	/** Alternate rows tinted with any variant; the `striped` variant implies it. */
	striped?: boolean;
}

export function Table({ className, variant, density, striped: stripe, ...props }: TableProps) {
	const effectiveDensity: TableDensity = density ?? "default";
	const striped = stripe ?? variant === "striped";
	return (
		<TableContext.Provider value={{ density: effectiveDensity, striped }}>
			<div className={table.frame}>
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
