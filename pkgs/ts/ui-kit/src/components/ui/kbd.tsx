import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "../../lib/utils";

// A key, or a whole combination as one: semantic `<kbd>` in the text face
// (design/primitives.md §Kbd). It draws whatever it is given and knows nothing
// of platforms: a combination spelled per platform is a `Shortcut`
// (./shortcut.tsx), which hands its text to one of these.
//
// `default` is a soft chip: a wash mixed from the text color and no border,
// so it reads on any surface in both themes. For a hint that stands apart:
// in a field, a tooltip, a list of shortcuts. `ghost` is muted text and
// nothing else, for a hint beside a label it belongs to: a menu row.
const kbdVariants = cva(
	"inline-flex items-center justify-center whitespace-nowrap rounded-sm font-sans font-medium text-xs leading-none tracking-wide",
	{
		variants: {
			variant: {
				default: "bg-text-primary/10 text-text-secondary",
				ghost: "bg-transparent text-text-muted",
			},
			size: {
				sm: "h-4.5 min-w-4.5 px-1",
				md: "h-5 min-w-5 px-1.5",
			},
		},
		compoundVariants: [
			// No chip to fill, so no box either: the text sets the size.
			{ variant: "ghost", className: "h-auto min-w-0 px-0" },
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
