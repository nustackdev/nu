// The prose document schema.
//
// ProseMirror is a document engine; a schema is how you tell it what a
// document is allowed to be. Ours says: paragraphs, three heading levels,
// two list flavours, a quote, a rule, and four inline marks. That is a few
// paragraphs of prose and nothing wider.
//
// What is deliberately absent is what keeps this safe to embed. There is no
// node for a program, a section or a page, so the engine cannot represent a
// document bigger than one Ref's value and cannot grow opinions about
// ordering or lifecycle above it. Whatever hosts the Ref owns those.
//
// Styling comes from the ancestor by default: the renderer mounts the view
// inside the kit's `Prose` container, whose descendant selectors style `p`,
// `h1`, `li` and friends exactly the way `MarkdownRef` renders them. So a
// document looks the same whether you are reading it or typing in it, and
// `toDOM` hands out no classes at all.
//
// A downstream package that registers its own prose entry (see
// `registerRefEntry`) can pass its own recipes instead, which is why this is
// a factory and not a module singleton.

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
	bulletList?: string;
	orderedList?: string;
	listItem?: string;
	rule?: string;
	strong?: string;
	em?: string;
	code?: string;
	link?: string;
};

export type ProseNodeTypes = {
	paragraph: NodeType;
	heading: NodeType;
	blockquote: NodeType;
	bulletList: NodeType;
	orderedList: NodeType;
	listItem: NodeType;
	rule: NodeType;
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

/** `{ class: x }` only when x is a non-empty string, so `class=""` never ships. */
function attrs(cls: string | undefined, extra: Record<string, string> = {}) {
	return cls ? { ...extra, class: cls } : extra;
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
				// Deeper headings exist in pasted HTML. Markdown only ever stores
				// three, so they fold down rather than round-trip to nothing.
				{ tag: "h4", attrs: { level: 3 } },
				{ tag: "h5", attrs: { level: 3 } },
				{ tag: "h6", attrs: { level: 3 } },
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

		horizontal_rule: {
			group: "block",
			parseDOM: [{ tag: "hr" }],
			toDOM: () => ["hr", attrs(classes.rule)],
		},

		text: { group: "inline" },
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
					href: String(mark.attrs.href),
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
			bulletList: schema.nodes.bullet_list,
			orderedList: schema.nodes.ordered_list,
			listItem: schema.nodes.list_item,
			rule: schema.nodes.horizontal_rule,
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
