import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "../../lib/utils";

// One key cap. Semantic `<kbd>`, mono face (design/primitives.md §Kbd +
// typography.md §4 Kbd). It draws whatever it is given and knows nothing of
// platforms: a combination is a `Shortcut` (./shortcut.tsx), which names the
// keys and lays out one cap each.
//
// `default` sits on the sunken well, for a hint standing on its own (a
// tooltip, a footer). `ghost` drops the well and goes muted, for a hint inside
// something that already has a box (an input, a menu row). Fixed heights, so
// caps of different glyphs line up in a row.
const kbdVariants = cva(
	"inline-flex items-center justify-center rounded-sm border font-mono font-medium text-xs leading-none",
	{
		variants: {
			variant: {
				default: "border-border-subtle bg-bg-sunken text-text-secondary",
				ghost: "border-transparent bg-transparent text-text-muted",
			},
			size: {
				sm: "h-4 min-w-4 px-1",
				md: "h-4.5 min-w-4.5 px-1.5",
			},
		},
		compoundVariants: [
			// No well to fill, so no pad either: the glyphs set the width.
			{ variant: "ghost", className: "min-w-0 px-0" },
		],
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface KbdProps
	extends React.HTMLAttributes<HTMLElement>,
		VariantProps<typeof kbdVariants> {}

export function Kbd({ className, variant, size, ...props }: KbdProps) {
	return (
		<kbd data-slot="kbd" className={cn(kbdVariants({ variant, size, className }))} {...props} />
	);
}

export { kbdVariants };
