// The prose document schema.
//
// ProseMirror is a document engine; a schema is how you tell it what a
// document is allowed to be. Ours says: paragraphs, six heading levels,
// three list flavours (bullets, numbers, checkboxes), a quote, a code fence,
// a table, a rule, inline images and four inline marks. That is a document's
// worth of prose and nothing wider.
//
// What is deliberately absent is what keeps this safe to embed. There is no
// node for a program, a section or a page, so the engine cannot represent a
// document bigger than one Ref's value and cannot grow opinions about
// ordering or lifecycle above it. Whatever hosts the Ref owns those.
//
// Styling comes from the ancestor by default: the renderer mounts the view
// inside the kit's `Prose` container, whose descendant selectors style `p`,
// `h1`, `li` and friends. So a document looks the same whether you are reading
// it or typing in it, and `toDOM` hands out no classes at all.
//
// Every URL that reaches the DOM goes through `safeUrl` first. The value is a
// string anyone upstream may have written, and a `javascript:` link rendered
// as-is is script on click.
//
// A downstream package that registers its own prose type (see `register`)
// can pass its own recipes instead, which is why this is a factory and not
// a module singleton.

import {
	type MarkSpec,
	type MarkType,
	type NodeSpec,
	type NodeType,
	Schema,
} from "prosemirror-model";

/** Per-element class recipes handed to `toDOM`. Empty means "inherit". */
export type ProseClasses = {
	paragraph?: string;
	heading?: (level: number) => string;
	blockquote?: string;
	codeBlock?: string;
	bulletList?: string;
	orderedList?: string;
	listItem?: string;
	taskList?: string;
	taskItem?: string;
	table?: string;
	tableRow?: string;
	tableHeader?: string;
	tableCell?: string;
	rule?: string;
	image?: string;
	strong?: string;
	em?: string;
	code?: string;
	link?: string;
};

export type ProseNodeTypes = {
	paragraph: NodeType;
	heading: NodeType;
	blockquote: NodeType;
	codeBlock: NodeType;
	bulletList: NodeType;
	orderedList: NodeType;
	listItem: NodeType;
	taskList: NodeType;
	taskItem: NodeType;
	table: NodeType;
	tableRow: NodeType;
	tableHeader: NodeType;
	tableCell: NodeType;
	rule: NodeType;
	image: NodeType;
};

export type ProseMarkTypes = {
	strong: MarkType;
	em: MarkType;
	code: MarkType;
	link: MarkType;
};

export type ProseSchema = {
	schema: Schema;
	nodeType: ProseNodeTypes;
	markType: ProseMarkTypes;
};

/**
 * A URL fit for an `href` or `src`, or "" when it is not. Web, mail and
 * relative URLs pass; anything with another scheme (`javascript:`, `data:`,
 * `vbscript:`) does not.
 */
export function safeUrl(url: string): string {
	const u = url.trim();
	const scheme = /^([a-z][a-z0-9+.-]*):/i.exec(u);
	if (!scheme) return u;
	return ["http", "https", "mailto"].includes(scheme[1].toLowerCase()) ? u : "";
}

/** `{ class: x }` only when x is a non-empty string, so `class=""` never ships. */
function attrs(cls: string | undefined, extra: Record<string, string> = {}) {
	return cls ? { ...extra, class: cls } : extra;
}

const ALIGNS = ["left", "center", "right"];

/** A cell's alignment as the DOM carries it, or null for the default. */
function readAlign(dom: HTMLElement): string | null {
	const align = (dom.style.textAlign || dom.getAttribute("align") || "").toLowerCase();
	return ALIGNS.includes(align) ? align : null;
}

/** A header or body cell: same attributes, same content, its own tag. */
function cellSpec(tag: "th" | "td", role: string, cls: string | undefined): NodeSpec {
	return {
		content: "paragraph",
		attrs: {
			colspan: { default: 1 },
			rowspan: { default: 1 },
			align: {
				default: null,
				validate: (value) => {
					if (value !== null && !ALIGNS.includes(value as string)) {
						throw new RangeError(`table cell align must be null or one of ${ALIGNS}`);
					}
				},
			},
		},
		tableRole: role,
		isolating: true,
		parseDOM: [{ tag, getAttrs: (dom) => ({ align: readAlign(dom as HTMLElement) }) }],
		toDOM: (node) => {
			const align = node.attrs.align as string | null;
			return [tag, attrs(cls, align ? { style: `text-align: ${align}` } : {}), 0];
		},
	};
}

export function createProseSchema(classes: ProseClasses = {}): ProseSchema {
	const nodes: Record<string, NodeSpec> = {
		doc: { content: "block+" },

		paragraph: {
			content: "inline*",
			group: "block",
			parseDOM: [{ tag: "p" }],
			toDOM: () => ["p", attrs(classes.paragraph), 0],
		},

		heading: {
			attrs: { level: { default: 1 } },
			content: "inline*",
			group: "block",
			defining: true,
			parseDOM: [
				{ tag: "h1", attrs: { level: 1 } },
				{ tag: "h2", attrs: { level: 2 } },
				{ tag: "h3", attrs: { level: 3 } },
				{ tag: "h4", attrs: { level: 4 } },
				{ tag: "h5", attrs: { level: 5 } },
				{ tag: "h6", attrs: { level: 6 } },
			],
			toDOM: (node) => {
				const level = node.attrs.level as number;
				return [`h${level}`, attrs(classes.heading?.(level)), 0];
			},
		},

		blockquote: {
			content: "block+",
			group: "block",
			defining: true,
			parseDOM: [{ tag: "blockquote" }],
			toDOM: () => ["blockquote", attrs(classes.blockquote), 0],
		},

		// A fenced block: literal text, no marks, the language as an attribute.
		// `code` is what makes Enter insert a newline instead of splitting it.
		code_block: {
			attrs: { language: { default: "" } },
			content: "text*",
			marks: "",
			group: "block",
			code: true,
			defining: true,
			parseDOM: [
				{
					tag: "pre",
					preserveWhitespace: "full",
					getAttrs: (dom) => ({
						language: (dom as HTMLElement).getAttribute("data-language") ?? "",
					}),
				},
			],
			toDOM: (node) => {
				const language = node.attrs.language as string;
				const extra: Record<string, string> = language ? { "data-language": language } : {};
				return ["pre", attrs(classes.codeBlock, extra), ["code", 0]];
			},
		},

		bullet_list: {
			content: "list_item+",
			group: "block",
			parseDOM: [{ tag: "ul" }],
			toDOM: () => ["ul", attrs(classes.bulletList), 0],
		},

		ordered_list: {
			attrs: { order: { default: 1 } },
			content: "list_item+",
			group: "block",
			parseDOM: [
				{
					tag: "ol",
					getAttrs: (dom) => ({
						order: Number((dom as HTMLElement).getAttribute("start")) || 1,
					}),
				},
			],
			toDOM: (node) => {
				const order = node.attrs.order as number;
				const extra: Record<string, string> = {};
				if (order !== 1) extra.start = String(order);
				return ["ol", attrs(classes.orderedList, extra), 0];
			},
		},

		list_item: {
			// `paragraph block*` is what makes splitListItem / sinkListItem behave.
			content: "paragraph block*",
			defining: true,
			parseDOM: [{ tag: "li" }],
			toDOM: () => ["li", attrs(classes.listItem), 0],
		},

		// A checklist: GFM's `- [ ]` / `- [x]`. Its own list type rather than a
		// flag on `list_item`, so a bullet list never grows a checkbox by
		// accident and the input rules can tell the two apart.
		//
		// Both parse rules outrank the plain `ul` / `li` ones, and `toDOM`
		// lays the item out as checkbox + body. The checkbox is not editable
		// content: the editor's node view (./editor.tsx) owns the click.
		task_list: {
			content: "task_item+",
			group: "block",
			parseDOM: [{ tag: "ul[data-task-list]", priority: 60 }],
			toDOM: () => ["ul", attrs(classes.taskList, { "data-task-list": "" }), 0],
		},

		task_item: {
			attrs: { checked: { default: false } },
			content: "paragraph block*",
			defining: true,
			parseDOM: [
				{
					tag: "li[data-task-item]",
					priority: 60,
					getAttrs: (dom) => ({
						checked: (dom as HTMLElement).getAttribute("data-checked") === "true",
					}),
				},
			],
			toDOM: (node) => [
				"li",
				attrs(classes.taskItem, {
					"data-task-item": "",
					"data-checked": String(node.attrs.checked),
				}),
				[
					"span",
					{ contenteditable: "false", "data-task-box": "" },
					["input", node.attrs.checked ? { type: "checkbox", checked: "" } : { type: "checkbox" }],
				],
				["div", { "data-task-body": "" }, 0],
			],
		},

		// A GFM table, in the shape prosemirror-tables works on (`tableRole`),
		// held to what a pipe table can say. A cell is one paragraph, since GFM
		// cells hold inline content only; the table commands fill new cells
		// with `createAndFill`, which makes exactly that. The first row is the
		// header. `align` is the column's, from the delimiter row, kept on every
		// cell of the column because that is where the table commands look.
		// The spans exist because prosemirror-tables reads them; markdown has
		// no merged cells, so they are always 1 coming in, pasted HTML too.
		table: {
			content: "table_row+",
			tableRole: "table",
			isolating: true,
			group: "block",
			parseDOM: [{ tag: "table" }],
			toDOM: () => ["table", attrs(classes.table), ["tbody", 0]],
		},

		table_row: {
			content: "(table_cell | table_header)*",
			tableRole: "row",
			parseDOM: [{ tag: "tr" }],
			toDOM: () => ["tr", attrs(classes.tableRow), 0],
		},

		table_header: cellSpec("th", "header_cell", classes.tableHeader),

		table_cell: cellSpec("td", "cell", classes.tableCell),

		horizontal_rule: {
			group: "block",
			parseDOM: [{ tag: "hr" }],
			toDOM: () => ["hr", attrs(classes.rule)],
		},

		text: { group: "inline" },

		image: {
			inline: true,
			attrs: { src: { default: "" }, alt: { default: "" } },
			group: "inline",
			draggable: true,
			parseDOM: [
				{
					tag: "img[src]",
					getAttrs: (dom) => ({
						src: (dom as HTMLElement).getAttribute("src") ?? "",
						alt: (dom as HTMLElement).getAttribute("alt") ?? "",
					}),
				},
			],
			toDOM: (node) => [
				"img",
				attrs(classes.image, {
					src: safeUrl(String(node.attrs.src)),
					alt: String(node.attrs.alt),
				}),
			],
		},
	};

	const marks: Record<string, MarkSpec> = {
		// Order matters: it is the order marks nest in when serialized, so link
		// wraps emphasis rather than the other way round.
		link: {
			attrs: { href: { default: "" } },
			inclusive: false,
			parseDOM: [
				{
					tag: "a[href]",
					getAttrs: (dom) => ({
						href: (dom as HTMLElement).getAttribute("href") ?? "",
					}),
				},
			],
			toDOM: (mark) => [
				"a",
				attrs(classes.link, {
					href: safeUrl(String(mark.attrs.href)),
					target: "_blank",
					rel: "noreferrer",
				}),
				0,
			],
		},

		strong: {
			parseDOM: [
				{ tag: "strong" },
				{ tag: "b" },
				{ style: "font-weight=bold" },
				{ style: "font-weight=700" },
			],
			toDOM: () => ["strong", attrs(classes.strong), 0],
		},

		em: {
			parseDOM: [{ tag: "em" }, { tag: "i" }, { style: "font-style=italic" }],
			toDOM: () => ["em", attrs(classes.em), 0],
		},

		// Code excludes everything else, the way markdown's backticks do: the
		// span between them is literal, so bold-inside-code has no serialization.
		code: {
			excludes: "_",
			parseDOM: [{ tag: "code" }],
			toDOM: () => ["code", attrs(classes.code), 0],
		},
	};

	const schema = new Schema({ nodes, marks });

	return {
		schema,
		nodeType: {
			paragraph: schema.nodes.paragraph,
			heading: schema.nodes.heading,
			blockquote: schema.nodes.blockquote,
			codeBlock: schema.nodes.code_block,
			bulletList: schema.nodes.bullet_list,
			orderedList: schema.nodes.ordered_list,
			listItem: schema.nodes.list_item,
			taskList: schema.nodes.task_list,
			taskItem: schema.nodes.task_item,
			table: schema.nodes.table,
			tableRow: schema.nodes.table_row,
			tableHeader: schema.nodes.table_header,
			tableCell: schema.nodes.table_cell,
			rule: schema.nodes.horizontal_rule,
			image: schema.nodes.image,
		},
		markType: {
			strong: schema.marks.strong,
			em: schema.marks.em,
			code: schema.marks.code,
			link: schema.marks.link,
		},
	};
}

/** The kit's own schema. Unstyled by `toDOM`; `Prose` styles it from above. */
export const proseSchema: ProseSchema = createProseSchema();
