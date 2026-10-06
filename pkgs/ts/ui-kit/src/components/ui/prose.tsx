// Prose primitive.
//
// The kit's reading surface. Body copy sits at text-lg, a step above the kit's
// dense text-base, and code and inline text scale with it, so long-form text
// reads like a document while controls around it stay compact. The box
// carries its own small vertical padding; its blocks never push past it.
//
// Where the looks come from: a heading, a list and a table are drawn by the
// element recipes (lib/recipes.ts), which the kit's prose schema puts on the
// elements themselves, the same classes `Heading`, `List` and `Table` use.
// What is left here is what only a document has: the reading size, the
// spacing between blocks, and the elements no kit component draws (quotes,
// inline code, links, rules, images, checklists, a table cell's paragraph).
//
// No Tailwind Typography plugin, no external stylesheet: everything reaches
// tokens via arbitrary-variant selectors so the whole prose block themes
// automatically with .dark.

import type * as React from "react";

import { cn } from "../../lib/utils";

const proseSelectors = [
	// container defaults
	"font-display text-text-primary text-lg leading-normal",
	"max-w-none py-1",
	// Block margins space blocks apart, never the block from its own box: the
	// first child drops its top, the last its bottom, at every depth. Beats the
	// per-element margins below on specificity, not on order. The box's own
	// edge air is the padding above, which never collapses into a wrapper.
	"[&_*:first-child]:mt-0 [&_*:last-child]:mb-0",
	// headings: the space around them (their look is the heading recipe)
	"[&_h1]:mt-6 [&_h1]:mb-3 [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:mt-4 [&_h3]:mb-2",
	"[&_h4]:mt-4 [&_h4]:mb-2 [&_h5]:mt-3 [&_h5]:mb-1 [&_h6]:mt-3 [&_h6]:mb-1",
	// paragraphs
	"[&_p]:my-2.5 [&_p]:text-lg [&_p]:text-text-primary",
	// lists: the space around them (markers, indent and item spacing are the
	// list recipe; items read at the container's size)
	"[&_ul]:my-2.5 [&_ol]:my-2.5",
	// checklists: the box sits on the first line, a done item goes quiet
	"[&_[data-task-list]]:list-none [&_[data-task-list]]:pl-0",
	"[&_[data-task-item]]:flex [&_[data-task-item]]:items-start [&_[data-task-item]]:gap-2",
	"[&_[data-task-box]]:flex [&_[data-task-box]]:h-[1lh] [&_[data-task-box]]:shrink-0 [&_[data-task-box]]:items-center",
	"[&_[data-task-body]]:min-w-0 [&_[data-task-body]]:flex-1",
	"[&_[data-checked=true]>[data-task-body]>p]:text-text-muted [&_[data-checked=true]>[data-task-body]>p]:line-through",
	// blockquote
	"[&_blockquote]:my-3 [&_blockquote]:pl-3 [&_blockquote]:border-l-2 [&_blockquote]:border-accent-line [&_blockquote]:text-text-secondary [&_blockquote]:italic",
	// inline code and pre
	"[&_code]:font-mono [&_code]:text-base [&_code]:bg-bg-sunken [&_code]:text-text-primary [&_code]:rounded-sm [&_code]:px-1 [&_code]:py-0.5",
	"[&_pre]:my-3 [&_pre]:font-mono [&_pre]:text-base [&_pre]:bg-bg-sunken [&_pre]:text-text-primary [&_pre]:border [&_pre]:border-border-subtle [&_pre]:rounded-md [&_pre]:p-3 [&_pre]:overflow-x-auto",
	// nested pre>code cancels the inline chip look
	"[&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:border-0",
	// anchors
	"[&_a]:text-accent-2 [&_a]:underline [&_a]:underline-offset-2 [&_a:hover]:text-accent-2-hover",
	// horizontal rule
	"[&_hr]:my-4 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-border-subtle",
	// tables: the space around them and the box the editor wraps each one in,
	// which scrolls sideways when the table is wider than the page. The table
	// itself is the table recipe, `Table`'s look at its default density.
	"[&_[data-slot=prose-table]]:relative [&_[data-slot=prose-table]]:my-3 [&_[data-table-scroll]]:w-full [&_[data-table-scroll]]:overflow-x-auto",
	"[&_table]:my-3",
	// A cell's paragraph is the cell's text: no paragraph air, the cell's size,
	// line height and color, so a markdown row is as tall as a `Table` row.
	// Code steps down with it, as it does from body copy.
	"[&_:is(th,td)_p]:my-0 [&_:is(th,td)_p]:[font-size:inherit] [&_:is(th,td)_p]:[line-height:inherit] [&_:is(th,td)_p]:[color:inherit]",
	"[&_:is(th,td)_code]:text-xs [&_:is(th,td)_code]:normal-case [&_:is(th,td)_code]:tracking-normal",
	// images
	"[&_img]:max-w-full [&_img]:rounded-md",
	// strong / em
	"[&_strong]:font-semibold [&_strong]:text-text-primary",
	"[&_em]:italic",
].join(" ");

export interface ProseProps extends React.HTMLAttributes<HTMLDivElement> {}

function Prose({ className, ...props }: ProseProps) {
	return <div data-slot="prose" className={cn("nu-prose", proseSelectors, className)} {...props} />;
}

export { Prose };
