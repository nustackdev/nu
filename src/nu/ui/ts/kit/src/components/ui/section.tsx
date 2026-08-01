// Section primitive. Top-level page grouping with title + description.
// Design refs:
//   primitives.md    §Section (semantic <section>, title + description + actions)
//   typography.md    §Headings (h3 = 2xl / semibold), §Body prose secondary text
//   space-radius.md  §Density Section (24 gap at md, 32 at lg)
//   palette.md       §2.3 border-subtle for the bordered separator
//
// Heading + Text primitives are not shipped yet (later phase), so title uses
// a semantic <h2> with the typography scale directly and description uses <p>.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const sectionVariants = cva("flex flex-col", {
	variants: {
		size: {
			md: "gap-6", // 24
			lg: "gap-8", // 32
		},
		bordered: {
			true: "border-t border-border-subtle pt-6",
			false: "",
		},
	},
	defaultVariants: {
		size: "md",
		bordered: false,
	},
});

export interface SectionProps
	extends Omit<React.HTMLAttributes<HTMLElement>, "title">,
		VariantProps<typeof sectionVariants> {
	// Slot: allow rich nodes (badge, icon) alongside plain text, so widen from
	// the built-in HTMLAttributes `title: string`.
	title?: React.ReactNode;
	description?: React.ReactNode;
	actions?: React.ReactNode;
}

export function Section({
	className,
	size,
	bordered,
	title,
	description,
	actions,
	children,
	...props
}: SectionProps) {
	// A Section without a title/description still renders a semantic <section>
	// so screen readers get the landmark. The header block only paints when
	// there is something to show.
	const hasHeader = Boolean(title || description || actions);
	return (
		<section
			data-slot="section"
			className={cn(sectionVariants({ size, bordered }), className)}
			{...props}
		>
			{hasHeader && (
				<div
					data-slot="section-header"
					className="flex items-start justify-between gap-4"
				>
					<div className="flex flex-col gap-1">
						{title && (
							<h2 className="text-2xl font-semibold leading-tight text-text-primary">
								{title}
							</h2>
						)}
						{description && (
							<p className="text-sm text-text-secondary">
								{description}
							</p>
						)}
					</div>
					{actions && (
						<div
							data-slot="section-actions"
							className="flex items-center gap-2 shrink-0"
						>
							{actions}
						</div>
					)}
				</div>
			)}
			{children}
		</section>
	);
}

export { sectionVariants };
