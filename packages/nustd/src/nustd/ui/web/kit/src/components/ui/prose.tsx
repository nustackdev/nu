// Prose primitive.
//
// Wrapper for Markdown output. No Tailwind Typography plugin, no external
// stylesheet: everything reaches tokens via arbitrary-variant selectors so
// the whole prose block themes automatically with .dark.
//
// The class list is long by design (each selector targets one element); this
// keeps the primitive dependency-free and tuneable per element.

import type * as React from "react";

import { cn } from "../../lib/utils";

const proseSelectors = [
	// container defaults
	"font-display text-text-primary text-base leading-normal",
	"max-w-none",
	// headings
	"[&_h1]:font-display [&_h1]:text-3xl [&_h1]:font-bold [&_h1]:text-text-primary [&_h1]:mt-6 [&_h1]:mb-3",
	"[&_h2]:font-display [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:text-text-primary [&_h2]:mt-5 [&_h2]:mb-2",
	"[&_h3]:font-display [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:text-text-primary [&_h3]:mt-4 [&_h3]:mb-2",
	"[&_h4]:font-display [&_h4]:text-lg [&_h4]:font-semibold [&_h4]:text-text-primary [&_h4]:mt-4 [&_h4]:mb-2",
	"[&_h5]:font-display [&_h5]:text-base [&_h5]:font-semibold [&_h5]:text-text-primary [&_h5]:mt-3 [&_h5]:mb-1",
	"[&_h6]:font-display [&_h6]:text-sm [&_h6]:font-semibold [&_h6]:text-text-secondary [&_h6]:mt-3 [&_h6]:mb-1 [&_h6]:uppercase [&_h6]:tracking-[0.02em]",
	// paragraphs
	"[&_p]:my-2 [&_p]:text-base [&_p]:text-text-primary",
	// lists
	"[&_ul]:my-2 [&_ul]:pl-5 [&_ul]:list-disc [&_ul]:text-text-primary",
	"[&_ol]:my-2 [&_ol]:pl-5 [&_ol]:list-decimal [&_ol]:text-text-primary",
	"[&_li]:my-0.5 [&_li]:leading-normal",
	// blockquote
	"[&_blockquote]:my-3 [&_blockquote]:pl-3 [&_blockquote]:border-l-2 [&_blockquote]:border-accent-line [&_blockquote]:text-text-secondary [&_blockquote]:italic",
	// inline code and pre
	"[&_code]:font-mono [&_code]:text-sm [&_code]:bg-bg-sunken [&_code]:text-text-primary [&_code]:rounded-sm [&_code]:px-1 [&_code]:py-0.5",
	"[&_pre]:my-3 [&_pre]:font-mono [&_pre]:text-sm [&_pre]:bg-bg-sunken [&_pre]:text-text-primary [&_pre]:border [&_pre]:border-border-subtle [&_pre]:rounded-md [&_pre]:p-3 [&_pre]:overflow-x-auto",
	// nested pre>code cancels the inline chip look
	"[&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:border-0",
	// anchors
	"[&_a]:text-accent-2 [&_a]:underline [&_a]:underline-offset-2 [&_a:hover]:text-accent-2-hover",
	// horizontal rule
	"[&_hr]:my-4 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-border-subtle",
	// tables (basic)
	"[&_table]:my-3 [&_table]:w-full [&_table]:border-collapse",
	"[&_th]:text-left [&_th]:font-semibold [&_th]:text-sm [&_th]:text-text-secondary [&_th]:border-b [&_th]:border-border-default [&_th]:px-2 [&_th]:py-1.5",
	"[&_td]:text-sm [&_td]:text-text-primary [&_td]:border-b [&_td]:border-border-subtle [&_td]:px-2 [&_td]:py-1.5",
	// images
	"[&_img]:max-w-full [&_img]:rounded-md",
	// strong / em
	"[&_strong]:font-semibold [&_strong]:text-text-primary",
	"[&_em]:italic",
].join(" ");

export interface ProseProps extends React.HTMLAttributes<HTMLDivElement> {}

function Prose({ className, ...props }: ProseProps) {
	return (
		<div
			data-slot="prose"
			className={cn("nu-prose", proseSelectors, className)}
			{...props}
		/>
	);
}

export { Prose };
