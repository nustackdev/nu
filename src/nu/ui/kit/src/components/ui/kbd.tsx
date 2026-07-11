import type * as React from "react";
import { cn } from "../../lib/utils";

// Keyboard shortcut chip. Semantic `<kbd>`, mono face, sits on the sunken
// well (design/primitives.md §Kbd + typography.md §4 Kbd).
export type KbdProps = React.HTMLAttributes<HTMLElement>;

export function Kbd({ className, ...props }: KbdProps) {
	return (
		<kbd
			data-slot="kbd"
			className={cn(
				"inline-flex items-center justify-center rounded-sm border border-border-subtle bg-bg-sunken text-text-secondary font-mono font-medium text-xs px-1.5 py-0.5 leading-none",
				className,
			)}
			{...props}
		/>
	);
}
