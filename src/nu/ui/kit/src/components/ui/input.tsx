import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "../../lib/utils";

// Text field. Sizes 24 / 32 / 40 match Button row heights so form rows sit
// flush (space-radius.md §4 Input). Pad-x = 10 at md, closer to the border
// than shadcn's 12, to earn the Fleet-flavored feel called out in the doc.
//
// `invalid` variant flips border + focus ring to the danger hue and is kept
// in sync with the `aria-invalid` attribute: consumers pass either the
// `invalid` prop or `aria-invalid`, both wire the same visual state.
const inputVariants = cva(
	[
		"flex w-full rounded-md border bg-bg-surface text-text-primary",
		"placeholder:text-text-muted",
		"transition-[border-color,box-shadow] duration-fast ease-out",
		"hover:border-border-strong",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas focus-visible:border-border-strong",
		"disabled:bg-bg-sunken disabled:opacity-50 disabled:pointer-events-none",
		// `aria-invalid` variant so consumers can wire the invalid look
		// through the a11y attribute directly, without the `invalid` prop.
		"aria-invalid:border-status-danger aria-invalid:focus-visible:ring-status-danger/40 aria-invalid:focus-visible:border-status-danger",
	].join(" "),
	{
		variants: {
			variant: {
				default: "border-border-default focus-visible:ring-ring",
				invalid:
					"border-status-danger focus-visible:ring-status-danger/40 focus-visible:border-status-danger",
			},
			size: {
				sm: "h-6 px-2 py-1 text-sm",
				md: "h-8 px-2.5 py-1.5 text-lg",
				lg: "h-10 px-3 py-2 text-lg",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

// `size` on <input> collides with the DOM `size` attribute; we own the name.
export interface InputProps
	extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
		VariantProps<typeof inputVariants> {
	invalid?: boolean;
}

export function Input({
	className,
	variant,
	size,
	invalid,
	type = "text",
	...props
}: InputProps) {
	const resolvedVariant = invalid ? "invalid" : variant;
	return (
		<input
			data-slot="input"
			type={type}
			aria-invalid={invalid || props["aria-invalid"]}
			className={cn(inputVariants({ variant: resolvedVariant, size, className }))}
			{...props}
		/>
	);
}

export { inputVariants };
