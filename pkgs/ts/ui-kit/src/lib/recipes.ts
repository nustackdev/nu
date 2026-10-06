// Element recipes: one look per element.
//
// A table, a list, a heading and a code box each show up in two places: as a
// kit component on a page (`Table`, `List`, `Heading`, `Code`) and as an
// element in a markdown document (the prose schema's `toDOM`, the fence node
// view). Both read their classes from here, so a markdown table and a
// TableRef are drawn by the same class list, not by two lists kept in step.
//
// Every value is a full class string written out literally. Tailwind finds
// classes by scanning source text, so a class assembled from fragments at
// run time would never be generated. Joining whole strings is fine; splicing
// parts of one class name is not.
//
// What stays out: spacing between blocks in a document and the reading size
// belong to `Prose`, the density of a page to the component. A recipe is the
// element's own look and nothing about where it sits.

/* ================================= table ================================= */

type TableDensity = "compact" | "default" | "comfortable";

/**
 * Plain `<table>` + `border-separate`, so the rounded frame clips cleanly.
 * Row dividers are cell borders; inside a frame the last row drops its own,
 * the frame already draws that edge.
 */
const table = {
	/** The box around the table: it scrolls sideways when the table is wider. */
	frame: "w-full overflow-x-auto",
	/** The table element itself. text-sm is the row baseline. */
	root: "w-full caption-bottom text-sm text-text-primary border-separate border-spacing-0",
	/**
	 * The outer frame. It draws the bottom edge, so the last row drops its own
	 * divider under it (a header with no rows under it too); a borderless table
	 * keeps that divider as its closing line.
	 */
	framed: [
		"border border-border-default rounded-md overflow-hidden",
		"[&_tr:last-child:not(thead>*)>*]:border-b-0",
		"[&:not(:has(tbody>tr))_thead>tr>*]:border-b-0",
	].join(" "),
	/** No outer frame, for a table inside a Card or Panel that draws one. */
	borderless: "border-0",
	/** The header section. The cells carry the same tint, see `head`. */
	header: "bg-bg-sunken",
	/** The footer section; its first row draws the divider above it. */
	footer: [
		"bg-bg-sunken font-medium [&>tr>*]:bg-bg-sunken",
		"[&>tr:first-child>*]:border-t [&>tr:first-child>*]:border-border-subtle",
	].join(" "),
	/**
	 * A row. Markdown has no `<thead>`: its header row is the first body row,
	 * so the row stays neutral and the header tint lives on the header cell.
	 */
	row: [
		"transition-colors duration-fast ease-out",
		"hover:bg-bg-elevated",
		"data-[state=selected]:bg-accent-wash",
	].join(" "),
	/** Alternate rows get a sunken tint for scan density. */
	striped: "even:bg-bg-sunken/40",
	/** Row height per density: 24 / 28 / 32. */
	rowHeight: {
		compact: "h-6",
		default: "h-7",
		comfortable: "h-8",
	} satisfies Record<TableDensity, string>,
	/** Cell padding per density, header and body alike. */
	cellPad: {
		compact: "px-2 py-1",
		default: "px-2.5 py-1.5",
		comfortable: "px-3 py-2",
	} satisfies Record<TableDensity, string>,
	/** Header cell: the IDE-flavoured header tier, xs uppercase medium. */
	head: [
		"text-left align-middle whitespace-nowrap bg-bg-sunken",
		"text-text-secondary text-xs font-medium uppercase tracking-wide",
		"border-b border-border-default",
	].join(" "),
	/** Body cell. */
	cell: "align-middle text-sm text-text-primary border-b border-border-subtle",
	caption: "mt-2 text-xs text-text-muted",
};

/* ================================= list ================================== */

/**
 * Markers, indent and item spacing. The text size is the host's: `List` sets
 * the kit's text-base, `Prose` its reading size a step up.
 */
const list = {
	base: [
		"pl-5 text-text-primary",
		"[&>li]:my-0.5 [&>li:first-child]:mt-0 [&>li:last-child]:mb-0",
	].join(" "),
	bullet: "list-disc",
	number: "list-decimal",
};

/* ================================ heading ================================ */

const headingBase = "font-display text-text-primary";

/** The heading sizes, as `Heading` names them. */
const headingSize = {
	display: "text-display font-bold",
	"3xl": "text-3xl font-bold",
	"2xl": "text-2xl font-semibold",
	xl: "text-xl font-semibold",
	lg: "text-lg font-semibold",
};

/**
 * A document heading by level. h1..h4 are `Heading` sizes; h5 and h6 sit
 * below anything a page uses, so they exist only here.
 */
const headingLevel: Record<number, string> = {
	1: [headingBase, headingSize["3xl"]].join(" "),
	2: [headingBase, headingSize["2xl"]].join(" "),
	3: [headingBase, headingSize.xl].join(" "),
	4: [headingBase, headingSize.lg].join(" "),
	5: [headingBase, "text-base font-semibold"].join(" "),
	6: "font-display text-sm font-semibold text-text-secondary uppercase tracking-[0.02em]",
};

const heading = { base: headingBase, size: headingSize, level: headingLevel };

/* ================================= code ================================== */

/** The box a code block sits in: a `Code` block and a markdown fence alike. */
const codeBox =
	"relative w-full overflow-hidden rounded-md bg-bg-sunken border border-border-subtle";

export { codeBox, heading, list, type TableDensity, table };
