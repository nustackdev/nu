import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "../../lib/utils";

// Multi-line input. Mirrors Input's variant + size shape (space-radius.md
// §4 TextArea). pad-y doubled vs Input to give the first line breathing
// room, `resize-y` so users can grow it but not warp the row width.
const textAreaVariants = cva(
	[
		"flex w-full rounded-md border bg-bg-surface text-text-primary",
		"placeholder:text-text-muted",
		"resize-y",
		"transition-[border-color,box-shadow] duration-fast ease-out",
		"hover:border-border-strong",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas focus-visible:border-border-strong",
		"disabled:bg-bg-sunken disabled:opacity-50 disabled:pointer-events-none",
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
				sm: "min-h-14 px-2 py-2 text-sm",
				md: "min-h-18 px-2.5 py-3 text-lg",
				lg: "min-h-24 px-3 py-4 text-lg",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

// `size` on <textarea> collides with the DOM `size` attribute (rows-like);
// we own the name for the variant.
export interface TextAreaProps
	extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "size">,
		VariantProps<typeof textAreaVariants> {
	invalid?: boolean;
}

export function TextArea({
	className,
	variant,
	size,
	invalid,
	...props
}: TextAreaProps) {
	const resolvedVariant = invalid ? "invalid" : variant;
	return (
		<textarea
			data-slot="textarea"
			aria-invalid={invalid || props["aria-invalid"]}
			className={cn(textAreaVariants({ variant: resolvedVariant, size, className }))}
			{...props}
		/>
	);
}

export { textAreaVariants };
