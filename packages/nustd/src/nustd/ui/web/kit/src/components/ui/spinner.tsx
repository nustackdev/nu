// Spinner primitive.
//
// role=status per a11y.md §4. SVG-based rotate instead of a lucide icon so we
// control stroke width and gap arc directly.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const spinnerVariants = cva("inline-block shrink-0 animate-spin", {
	variants: {
		size: {
			sm: "size-3.5", // 14px
			md: "size-4", // 16px
			lg: "size-5", // 20px
			xl: "size-6", // 24px
		},
		tone: {
			default: "text-accent",
			neutral: "text-text-secondary",
			onSolid: "text-accent-fg",
			info: "text-status-info",
			danger: "text-status-danger",
			warn: "text-status-warn",
			ok: "text-status-ok",
		},
	},
	defaultVariants: {
		size: "md",
		tone: "default",
	},
});

export interface SpinnerProps
	extends Omit<React.HTMLAttributes<HTMLSpanElement>, "children">,
		VariantProps<typeof spinnerVariants> {
	label?: string;
}

function Spinner({
	className,
	size,
	tone,
	label = "Loading",
	...props
}: SpinnerProps) {
	return (
		<span
			role="status"
			aria-label={label}
			data-slot="spinner"
			className={cn(spinnerVariants({ size, tone }), className)}
			{...props}
		>
			<svg
				viewBox="0 0 24 24"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
				className="size-full"
				aria-hidden="true"
			>
				<circle
					cx="12"
					cy="12"
					r="9"
					stroke="currentColor"
					strokeOpacity="0.25"
					strokeWidth="2.5"
				/>
				<path
					d="M21 12a9 9 0 0 0-9-9"
					stroke="currentColor"
					strokeWidth="2.5"
					strokeLinecap="round"
				/>
			</svg>
		</span>
	);
}

export { Spinner, spinnerVariants };
